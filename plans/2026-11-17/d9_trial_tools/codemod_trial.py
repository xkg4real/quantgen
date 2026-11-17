"""Trial PyQt6 -> PySide6 codemod for a scratch copy (not the real tool). Usage: codemod_trial.py <root>"""
import re, sys, pathlib
root = pathlib.Path(sys.argv[1])
stats = {}
def bump(k, n):
    stats[k] = stats.get(k, 0) + n
for path in list(root.rglob("*.py")):
    text = path.read_text(encoding="utf-8")
    new = text
    n = len(re.findall(r"^(\s*)from PyQt6 import sip\s*$", new, flags=re.M)); bump("sip import", n)
    new = re.sub(r"^(\s*)from PyQt6 import sip\s*$",
                 r"\1import shiboken6 as _shb; from types import SimpleNamespace as _NS; sip = _NS(isdeleted=lambda o: not _shb.isValid(o), delete=_shb.delete)",
                 new, flags=re.M)
    for a, b in (("pyqtSignal", "Signal"), ("pyqtSlot", "Slot"), ("pyqtProperty", "Property")):
        k = len(re.findall(rf"\b{a}\b", new)); bump(a, k); new = re.sub(rf"\b{a}\b", b, new)
    k = len(re.findall(r"\bPyQt6\b", new)); bump("PyQt6 word", k); new = re.sub(r"\bPyQt6\b", "PySide6", new)
    if new != text:
        bump("files changed", 1)
        path.write_text(new, encoding="utf-8")
print(stats)
