"""PyQt6 -> PySide6 port helper for the native desktop (OS-P0-a, owner decision D9).

Three modes, all offline and without importing Qt:

  --check [PATH ...] [--ref REF]   per-file counts of PyQt6 imports, pyqtSignal, pyqtSlot,
                                   pyqtProperty and sip, plus how many places --apply would change
  --apply DIR                      rewrite *.py files in DIR in place (use a scratch copy, never the
                                   repository checkout); running it twice changes nothing the second time
  --lint [PATH ...] [--ref REF]    file:line list of risky patterns the rewrite cannot fix (D9 section 4)

--ref reads files from a git ref (for example origin/main) with `git show`, listing only the named
paths, so no checkout is needed. The rewrite works on Python tokens: names and import statements
change, comments and prose strings do not (except a string that is exactly the binding name, as in
a find_spec(...) call or a forbidden-import tuple, and Python source held in a string).

Rewrite rules (--apply); OLD is the PyQt 6 package name and NEW the PySide 6 one:
  * `from OLD import sip` -> `import shiboken6`
  * `sip.isdeleted(x)` -> `(not shiboken6.isValid(x))`, `not sip.isdeleted(x)` -> `shiboken6.isValid(x)`
  * `sip.delete(x)` -> `shiboken6.delete(x)`
  * name OLD -> NEW (imports and attribute access)
  * names pyqt-Signal/-Slot/-Property -> `Signal`/`Slot`/`Property`
  * a string literal that is exactly OLD -> NEW, same quotes
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import re
import subprocess
import sys
import tokenize
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

# Spelled in two pieces so that running the tool over its own source leaves it unchanged.
OLD = "Py" + "Qt6"
NEW = "Py" + "Side6"
RENAMES = {"pyqt" + "Signal": "Signal", "pyqt" + "Slot": "Slot", "pyqt" + "Property": "Property"}

DEFAULT_PATHS = ("quantgen_desktop", "tests", "tools", "core", "ui", "data", "packaging", "mobile",
                 "main.py", "config.py")
# The tool and its own test describe the old names on purpose; never rewrite or count them.
SELF_PATHS = ("tools/qt_port/", "tests/qt_port_acceptance.py")
# Never listed, read or searched (repository rule): the protected cache folder.
FORBIDDEN_PREFIXES = ("docs/asset_expansion/cache",)


# ---------------------------------------------------------------- token helpers

def _tokens(text: str):
    return list(tokenize.generate_tokens(io.StringIO(text).readline))


def _offsets(text: str):
    starts, pos = [0], 0
    for line in text.splitlines(keepends=True):
        pos += len(line)
        starts.append(pos)
    return starts


def _significant(tokens):
    skip = {tokenize.NL, tokenize.NEWLINE, tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT}
    return [t for t in tokens if t.type not in skip]


def _match_paren(sig, open_index):
    depth = 0
    for i in range(open_index, len(sig)):
        if sig[i].type == tokenize.OP and sig[i].string in "([{":
            depth += 1
        elif sig[i].type == tokenize.OP and sig[i].string in ")]}":
            depth -= 1
            if depth == 0:
                return i
    return None


# ---------------------------------------------------------------- rewrite

SIP_IMPORT = re.compile(r"^(?P<indent>[ \t]*)from[ \t]+" + OLD + r"[ \t]+import[ \t]+sip[ \t]*(?P<tail>#.*)?$", re.M)


# Code-looking use of the binding inside a string literal; prose such as "PyQt6 native" is not matched.
EMBEDDED_CODE = re.compile(r"(\bfrom\s+|\bimport\s+)" + OLD + r"\b|['\"]" + OLD + r"['\"]")
LITERAL = re.compile(r"^(?P<prefix>[rRbBuU]*)(?P<q>'''|\"\"\"|'|\")(?P<body>.*)(?P=q)$", re.S)


def _rewrite_literal(literal: str):
    m = LITERAL.match(literal)
    if not m or "b" in m.group("prefix").lower():
        return literal, []
    body = m.group("body")
    new_body, inner = rewrite(body)
    if not inner:  # not tokenizable as code on its own: plain word-level replacement
        changes = []
        def sub(pattern, repl, text, kind):
            def one(mm):
                changes.append(Change(kind, text.count("\n", 0, mm.start()) + 1))
                return mm.expand(repl)
            return re.sub(pattern, one, text)
        new_body = sub(r"(['\"])" + OLD + r"\1", r"\1" + NEW + r"\1", body, "binding string")
        new_body = sub(r"(\bfrom\s+|\bimport\s+)" + OLD + r"\b", r"\1" + NEW, new_body, "binding name")
        new_body = sub(r"\b" + OLD + r"(?=\.Qt)", NEW, new_body, "binding name")
        for a, b in RENAMES.items():
            new_body = sub(r"\b" + a + r"\b", b, new_body, a)
        new_body = sub(r"\bsip\.delete\(", "shiboken6.delete(", new_body, "sip.delete")
        inner = changes
    return f"{m.group('prefix')}{m.group('q')}{new_body}{m.group('q')}", inner


@dataclass
class Change:
    kind: str
    line: int


def rewrite(text: str):
    """Return (new_text, [Change]) for one Python source."""
    changes: list[Change] = []

    def sip_import(m):
        changes.append(Change("sip import", text.count("\n", 0, m.start()) + 1))
        tail = (" " + m.group("tail")) if m.group("tail") else ""
        return f"{m.group('indent')}import shiboken6{tail}"

    text = SIP_IMPORT.sub(sip_import, text)
    try:
        tokens = _tokens(text)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return text, changes
    sig = _significant(tokens)
    starts = _offsets(text)
    off = lambda pos: starts[pos[0] - 1] + pos[1]
    edits: list[tuple[int, int, str]] = []
    i = 0
    while i < len(sig):
        tok = sig[i]
        # sip.isdeleted(...) / sip.delete(...), with an optional leading `not`
        if (tok.type == tokenize.NAME and tok.string == "sip" and i + 3 < len(sig)
                and sig[i + 1].string == "." and sig[i + 2].string in ("isdeleted", "delete")
                and sig[i + 3].string == "(" and not (i > 0 and sig[i - 1].string == ".")):
            close = _match_paren(sig, i + 3)
            if close is not None:
                inner = text[off(sig[i + 3].end):off(sig[close].start)]
                negated = i > 0 and sig[i - 1].type == tokenize.NAME and sig[i - 1].string == "not"
                if sig[i + 2].string == "delete":
                    edits.append((off(tok.start), off(sig[close].end), f"shiboken6.delete({inner})"))
                    changes.append(Change("sip.delete", tok.start[0]))
                elif negated:
                    edits.append((off(sig[i - 1].start), off(sig[close].end), f"shiboken6.isValid({inner})"))
                    changes.append(Change("sip.isdeleted", tok.start[0]))
                else:
                    edits.append((off(tok.start), off(sig[close].end), f"(not shiboken6.isValid({inner}))"))
                    changes.append(Change("sip.isdeleted", tok.start[0]))
                i = close + 1
                continue
        if tok.type == tokenize.NAME and tok.string == OLD:
            edits.append((off(tok.start), off(tok.end), NEW))
            changes.append(Change("binding name", tok.start[0]))
        elif tok.type == tokenize.NAME and tok.string in RENAMES:
            edits.append((off(tok.start), off(tok.end), RENAMES[tok.string]))
            changes.append(Change(tok.string, tok.start[0]))
        elif tok.type == tokenize.STRING and tok.string in (f"'{OLD}'", f'"{OLD}"'):
            q = tok.string[0]
            edits.append((off(tok.start), off(tok.end), f"{q}{NEW}{q}"))
            changes.append(Change("binding string", tok.start[0]))
        elif tok.type == tokenize.STRING and EMBEDDED_CODE.search(tok.string):
            # Python source held in a string (a subprocess program, a forbidden-import tuple).
            new_literal, inner = _rewrite_literal(tok.string)
            if new_literal != tok.string:
                edits.append((off(tok.start), off(tok.end), new_literal))
                changes.extend(Change(ch.kind + " (in string)", tok.start[0] + ch.line - 1) for ch in inner)
        i += 1
    for start, end, new in sorted(edits, reverse=True):
        text = text[:start] + new + text[end:]
    return text, changes


# ---------------------------------------------------------------- counts

@dataclass
class Counts:
    imports: int = 0
    signal: int = 0
    slot: int = 0
    prop: int = 0
    sip: int = 0
    prose: int = 0
    changes: int = 0

    def any(self):
        return any((self.imports, self.signal, self.slot, self.prop, self.sip, self.prose))


IMPORT_LINE = re.compile(r"^\s*(from\s+" + OLD + r"(\.\w+)*\s+import\b|import\s+" + OLD + r"\b)")


def count(text: str) -> Counts:
    c = Counts()
    c.imports = sum(1 for line in text.splitlines() if IMPORT_LINE.match(line))
    try:
        tokens = _tokens(text)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        tokens = []
    for tok in tokens:
        if tok.type == tokenize.NAME:
            c.signal += tok.string == "pyqt" + "Signal"
            c.slot += tok.string == "pyqt" + "Slot"
            c.prop += tok.string == "pyqt" + "Property"
            c.sip += tok.string == "sip"
        elif tok.type in (tokenize.STRING, tokenize.COMMENT) and OLD in tok.string \
                and tok.string not in (f"'{OLD}'", f'"{OLD}"'):
            c.prose += 1
    c.changes = len(rewrite(text)[1])
    return c


# ---------------------------------------------------------------- lint (D9 section 4 groups)

FALLBACK_FONT_API = ("addApplicationFallbackFontFamily", "applicationFallbackFontFamilies",
                     "removeApplicationFallbackFontFamily", "setApplicationFallbackFontFamilies")


@dataclass
class Finding:
    path: str
    line: int
    group: str
    message: str


def _call_name(node):
    f = node.func
    return f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else None)


def _names_in(node):
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}



def _bound_method_shot(sig, i):
    """True for `singleShot(<ms>, self.<attr>[.<attr>])`: two arguments, the second a bound method of self."""
    if i + 1 >= len(sig) or sig[i + 1].string != "(":
        return False
    depth, args, current = 0, [], []
    for tok in sig[i + 1:]:
        if tok.string in "([{" and tok.type == tokenize.OP:
            depth += 1
            if depth == 1:
                continue
        elif tok.string in ")]}" and tok.type == tokenize.OP:
            depth -= 1
            if depth == 0:
                args.append(current)
                break
        if depth == 1 and tok.string == ",":
            args.append(current); current = []
            continue
        current.append(tok.string)
    if len(args) != 2:
        return False
    second = args[1]
    return (len(second) >= 3 and second[0] == "self" and all(x == "." for x in second[1::2])
            and all(x.isidentifier() for x in second[2::2]))

def lint(text: str, path: str) -> list[Finding]:
    out: list[Finding] = []
    add = lambda line, group, msg: out.append(Finding(path, line, group, msg))
    try:
        tokens = _tokens(text)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        tokens = []
    sig = _significant(tokens)
    for i, tok in enumerate(sig):
        if tok.type != tokenize.NAME:
            continue
        prev = sig[i - 1].string if i else ""
        nxt = sig[i + 1].string if i + 1 < len(sig) else ""
        if tok.string == "QChar":
            add(tok.start[0], "8-font", "QChar does not exist in PySide6")
        elif tok.string in FALLBACK_FONT_API:
            add(tok.start[0], "8-font", f"QFontDatabase.{tok.string} does not exist in PySide6")
        elif tok.string == "print" and prev == "." and nxt == "(":
            add(tok.start[0], "1-print", "QTextDocument.print is print_ in PySide6; accept both names")
        elif tok.string == "receivers" and prev == "." and nxt == "(":
            add(tok.start[0], "3-receivers", "QObject.receivers(bound signal) fails in PySide6; record the connection yourself")
        elif (tok.string == "setWeight" and prev == "." and nxt == "(" and i + 2 < len(sig)
              and sig[i + 2].type == tokenize.NUMBER):
            add(tok.start[0], "10-int-enum", "QFont.setWeight(<number>) raises TypeError in PySide6 (inside paintEvent it "
                "leaves the painter open and the app crashes); write QFont.Weight(<number>)")
        elif tok.string == "singleShot" and prev == "." and _bound_method_shot(sig, i):
            add(tok.start[0], "6-bound", "singleShot(ms, self.method): PyQt6 drops it when the object is deleted, "
                "PySide6 still calls it (trial: segfault and memory blow-up); use a child QTimer(self)")
        elif tok.string == "singleShot" and prev == ".":
            add(tok.start[0], "6-deferred", "deferred call: check the target widget is still alive when it fires (review)")
        elif tok.string == "sip" and nxt == "." and i + 2 < len(sig) and sig[i + 2].string not in ("isdeleted", "delete"):
            add(tok.start[0], "sip", f"sip.{sig[i + 2].string} has no automatic shiboken6 rewrite")
        elif tok.string.startswith("pyqt") and tok.string not in RENAMES:
            add(tok.start[0], "name", f"{tok.string} has no automatic PySide6 rewrite")
        elif tok.string in ("PYQT_VERSION", "PYQT_VERSION_STR", "QVariant"):
            add(tok.start[0], "name", f"{tok.string} does not exist in PySide6")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return sorted(out, key=lambda f: (f.line, f.group))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _call_name(node)
            if name == "findChildren" and node.args and isinstance(node.args[0], ast.Tuple):
                add(node.lineno, "2-findChildren", "findChildren with a tuple of types fails in PySide6; ask one type at a time")
            elif name == "addItem" and len(node.args) >= 2 and isinstance(node.func, ast.Attribute):
                data = node.args[1]
                if not isinstance(data, ast.Constant):
                    add(node.lineno, "4-combo-data", "combo item data is not a constant: a str Enum comes back as plain str in PySide6; convert it back when read (review)")
            elif name and name.startswith("setItemDelegate") and node.args:
                arg = node.args[-1]
                if isinstance(arg, ast.Call):
                    add(node.lineno, "9-delegate", "delegate created inline and not kept on self: keep a Python reference (crash risk)")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "eventFilter":
            params = [a.arg for a in node.args.args]
            watched = params[1] if len(params) >= 3 and params[0] == "self" else (params[0] if params else None)
            if not watched:
                continue
            for sub in ast.walk(node):
                if isinstance(sub, ast.Compare) and any(isinstance(op, (ast.In, ast.NotIn)) for op in sub.ops) \
                        and isinstance(sub.left, ast.Name) and sub.left.id == watched:
                    add(sub.lineno, "5-qobject-key", f"'{watched} in ...' inside eventFilter hashes a Qt object; compare with 'is' or id()")
                elif isinstance(sub, ast.Subscript) and isinstance(sub.slice, ast.Name) and sub.slice.id == watched:
                    add(sub.lineno, "5-qobject-key", f"Qt object '{watched}' used as a dict key inside eventFilter")
                elif isinstance(sub, ast.Call) and _call_name(sub) in ("get", "pop", "add", "discard", "setdefault") \
                        and sub.args and isinstance(sub.args[0], ast.Name) and sub.args[0].id == watched:
                    add(sub.lineno, "5-qobject-key", f"Qt object '{watched}' used as a set/dict key inside eventFilter")
    unique = {(f.line, f.group, f.message): f for f in out}
    return sorted(unique.values(), key=lambda f: (f.line, f.group))


# ---------------------------------------------------------------- file sources

def _allowed(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    return not rel.startswith(FORBIDDEN_PREFIXES) and not rel.startswith(SELF_PATHS) and rel.endswith(".py")


def files_from_tree(root: Path, paths) -> dict[str, str]:
    out = {}
    for name in paths:
        base = root / name
        if base.is_file():
            candidates = [base]
        elif base.is_dir():
            candidates = sorted(base.rglob("*.py"))
        else:
            continue
        for p in candidates:
            rel = p.relative_to(root).as_posix()
            if _allowed(rel) and "/__pycache__/" not in f"/{rel}":
                out[rel] = p.read_text(encoding="utf-8")
    return out


def files_from_ref(ref: str, paths, repo: Path) -> dict[str, str]:
    names = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "--name-only", ref, "--", *paths],
                           check=True, capture_output=True, text=True).stdout.splitlines()
    out = {}
    for rel in names:
        if _allowed(rel):
            blob = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{rel}"], check=True, capture_output=True)
            out[rel] = blob.stdout.decode("utf-8")
    return out


# ---------------------------------------------------------------- commands

def cmd_check(files: dict[str, str], as_json: bool) -> dict:
    rows, total = {}, Counts()
    for rel, text in sorted(files.items()):
        c = count(text)
        if c.any():
            rows[rel] = c
            for k in vars(total):
                setattr(total, k, getattr(total, k) + getattr(c, k))
    importing = sum(1 for c in rows.values() if c.imports)
    summary = {"files_mentioning": len(rows), "files_importing": importing, **vars(total)}
    if as_json:
        print(json.dumps({"summary": summary, "files": {k: vars(v) for k, v in rows.items()}}, ensure_ascii=False, indent=1))
    else:
        print(f"{'file':<62} {'imp':>4} {'sig':>4} {'slot':>4} {'prop':>4} {'sip':>4} {'prose':>5} {'chg':>4}")
        for rel, c in rows.items():
            print(f"{rel:<62} {c.imports:>4} {c.signal:>4} {c.slot:>4} {c.prop:>4} {c.sip:>4} {c.prose:>5} {c.changes:>4}")
        print("summary: " + ", ".join(f"{k}={v}" for k, v in summary.items()))
    return summary


def cmd_apply(root: Path, paths) -> dict:
    root = root.resolve()
    if (root / ".git").exists() and not (root / ".qt_port_scratch").exists():
        raise SystemExit(f"refusing to rewrite a git checkout ({root}); copy it to a scratch folder first "
                         "(or create an empty .qt_port_scratch file there to confirm it is a scratch copy)")
    stats: dict[str, int] = {}
    changed = 0
    for rel, text in files_from_tree(root, paths).items():
        new, changes = rewrite(text)
        if new != text:
            (root / rel).write_text(new, encoding="utf-8")
            changed += 1
        for ch in changes:
            stats[ch.kind] = stats.get(ch.kind, 0) + 1
    stats["files changed"] = changed
    print("apply: " + ", ".join(f"{k}={v}" for k, v in sorted(stats.items())))
    return stats


def cmd_lint(files: dict[str, str], as_json: bool) -> list[Finding]:
    findings = [f for rel, text in sorted(files.items()) for f in lint(text, rel)]
    if as_json:
        print(json.dumps([vars(f) for f in findings], ensure_ascii=False, indent=1))
    else:
        for f in findings:
            print(f"{f.path}:{f.line}: [{f.group}] {f.message}")
        groups: dict[str, int] = {}
        for f in findings:
            groups[f.group] = groups.get(f.group, 0) + 1
        print(f"lint: {len(findings)} findings; " + ", ".join(f"{k}={v}" for k, v in sorted(groups.items())))
    return findings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", metavar="DIR")
    mode.add_argument("--lint", action="store_true")
    ap.add_argument("paths", nargs="*", help=f"paths relative to the root (default: {' '.join(DEFAULT_PATHS)})")
    ap.add_argument("--root", default=".", help="tree to read for --check/--lint (default: current folder)")
    ap.add_argument("--ref", help="read files from this git ref instead of the working tree")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    paths = tuple(PurePosixPath(p).as_posix().rstrip("/") for p in args.paths) or DEFAULT_PATHS
    if any(p.startswith(FORBIDDEN_PREFIXES) or p in ("docs", ".") for p in paths):
        ap.error("name source folders explicitly; docs/ and the protected cache folder are not read")
    if args.apply:
        cmd_apply(Path(args.apply), paths)
        return 0
    root = Path(args.root)
    files = files_from_ref(args.ref, paths, root) if args.ref else files_from_tree(root, paths)
    if args.check:
        cmd_check(files, args.json)
    else:
        cmd_lint(files, args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
