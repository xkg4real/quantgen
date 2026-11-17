"""Macro -> Model cards view (02_ui_design section 1; code_ui D.1).

Renders the v2 macro card registry as records: every card's verdict chip, a disposition chip beside it
(BUILD-AS-INSURANCE is a disposition, never a verdict), its reason code, its label verbatim, the instrument book and
the notional status; the gate package status with its refusal reasons; the registered R-06 US REJECT; FORWARD-SIM and
refusal books in their own groups marked "not a recommendation" and never styled success; the tech-fund card drafts
with their NOT_RUN reasons; the CRY-1 control results under their vendor-data label.

Owner UI review 2026-11-10: every status word has a Korean word beside its code (verdicts read '미실행 · NOT_RUN'),
each card opens with one plain sentence of what its record means, and the verbatim record (registry label, reason
text, gate reasons with their file paths) sits one click away under 'Original record' (원문 보기). Visible text never
shows a local file path. The data, the verdict logic and the English record strings are unchanged.

`cards_blocks` is a pure dict -> controls renderer (testable without a page). `load_inputs` reads the validated
records once (call it in a worker: a broken verdict chain or a re-hash mismatch raises, and the view fails closed).
Nothing here computes exposure, admits a card or writes a file.
"""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Callable, Optional

import flet as ft

from core.theme import active
from ui.components import (DISPOSITION_STYLE, VERDICT_STYLE, LocalText, card, chip, disposition_chip, notice,
                           verdict_chip)
from ui.ficc_widgets import lchip

ROOT = Path(__file__).resolve().parents[1]
VERDICTS = ("PASS", "REVISE", "REJECT", "INSUFFICIENT_DATA", "NOT_RUN")    # schema $defs.card verdict
TF_DOCS = ROOT / "docs" / "techfund"
STRETCH = ft.CrossAxisAlignment.STRETCH          # cards fill the view width

# (group key, heading, caption); a card's group follows its disposition, the registered REJECT has its own.
GROUPS = (
    ("cards", "Macro model cards",
     "CARD-O / CARD-P registry. Nothing here reaches the recommended book until it PASSes under a frozen gate package."),
    ("registered", "Registered REJECT — a fact about the instrument",
     "Registered card: never re-run, never rebuilt."),
    ("forward_sim", "FORWARD-SIM books — not a recommendation",
     "Display only: a FORWARD-SIM multiplier never reaches the recommended book, and a forward record never validates."),
    ("refusal", "Refusal books — not a recommendation",
     "Retired legs kept as labelled REJECTs (archived council records); display only."),
)

# Korean words for the record codes. The verdict code always stays visible (repository policy).
VERDICT_KO = {"PASS": "통과 · PASS", "REVISE": "보완 필요 · REVISE", "REJECT": "기각 · REJECT",
              "INSUFFICIENT_DATA": "데이터 부족 · INSUFFICIENT_DATA", "NOT_RUN": "미실행 · NOT_RUN",
              "UNVERIFIED": "미검증 · UNVERIFIED"}
DISPOSITION_KO = {"RECOMMENDATION": "권장", "BUILD_AS_INSURANCE": "보험용 구축", "INVARIANT_STEP": "불변 단계",
                  "SPECIFICATION_ONLY": "사양서 단계", "FORWARD_SIM": "전진 모의 · 권유 아님",
                  "REFUSAL_BOOK": "거절 북 · 권유 아님", "DESCRIPTIVE": "설명용"}
STATUS_KO = {"NOT_FROZEN": "동결 전", "FROZEN": "동결됨", "UNKNOWN": "알 수 없음",
             "BUILD_NOW": "지금 구축", "SPECIFICATION_BOOK": "사양서 단계", "FORWARD_SIM": "전진 모의",
             "RETIRED": "퇴역", "BUILD_AS_INSURANCE": "보험용 구축", "NOT_RUN": "미실행",
             "registered": "등록된 기록", "archived_record": "보관된 위원회 기록", "no_verdict_row": "판정 기록 없음",
             "invalid_verdict": "판정 형식 오류", "—": "사유 코드 없음",
             "REFDATA": "기준 데이터 없음", "PENDING": "선행 작업 대기"}
CLASS_KO = {"descriptive": "설명용", "forward_only": "전진 기록 전용"}
_P11_TIP = ("운영 규칙 P11: 게이트 패키지가 동결되고 정식 실행이 기록되기 전에는 어떤 카드도 실행하지 않습니다.",
            "Ruling P11: no card runs before the gate package is frozen and its formal run is recorded.")
_PATH = re.compile(r"(?:[A-Za-z]:\\|/)(?:[^\s'\"()\[\],;:]+[\\/])+(?P<name>[^\s'\"()\[\],;:\\/]+)")


def _group(c: dict) -> str:
    d = c.get("disposition")
    if d == "FORWARD_SIM":
        return "forward_sim"
    if d == "REFUSAL_BOOK":
        return "refusal"
    return "registered" if c.get("rerun") is False else "cards"


def _heading(text: str, caption: str = "") -> ft.Control:
    pal = active()
    rows = [ft.Text(text, size=15, weight=ft.FontWeight.W_600, color=pal.text)]
    if caption:
        rows.append(ft.Text(caption, size=12, color=pal.muted))
    return ft.Column(rows, spacing=2)


def _tagged(control: ft.Control, tag: str) -> ft.Control:
    control.data = tag                       # lets a test tell a verdict chip from a disposition chip
    return control


def _kv(d: dict) -> str:
    """Scalars of a result dict as 'k v' pairs (format only, 3 significant digits)."""
    out = []
    for k, v in d.items():
        if isinstance(v, float):
            out.append(f"{k} {v:.3g}")
        elif isinstance(v, (bool, int, str)) or v is None:
            out.append(f"{k} {v}")
    return ", ".join(out)


def _no_paths(text: str) -> str:
    """A local file path shown by its file name only (the full path stays in the original record)."""
    return _PATH.sub(lambda m: m["name"], str(text))


def _status(code) -> str:
    return STATUS_KO.get(str(code), str(code))


def _local_chip(chip_box: ft.Container, ko: str) -> ft.Container:
    """Korean wording for a styled chip (verdict / disposition) whose English word stays its value."""
    old = chip_box.content
    chip_box.content = LocalText(ko, old.value, size=old.size, color=old.color, weight=old.weight)
    return chip_box


def _verdict_chip(verdict: str, *, tooltip: str = "") -> ft.Container:
    return _local_chip(verdict_chip(verdict, tooltip=tooltip), VERDICT_KO.get(verdict, verdict))


def _disposition_chip(disp: str) -> ft.Container:
    box = disposition_chip(disp, tooltip=disp)
    label = DISPOSITION_STYLE.get(disp, (disp, ""))[0]
    return _local_chip(box, DISPOSITION_KO.get(disp, label))


def _summary_text(ko: str, en: str) -> ft.Control:
    return LocalText(ko, en, size=13, color=active().text, selectable=True)


def _original(lines: list[ft.Control]) -> ft.Control:
    """The verbatim record, collapsed: keyboard-reachable, selectable, nothing dropped."""
    pal = active()
    return ft.ExpansionTile(
        title=ft.Text("Original record", size=12, color=pal.muted),
        controls=[ft.Container(ft.Column(lines, spacing=4), padding=ft.Padding(0, 0, 0, 8))],
        expanded=False, dense=True, tile_padding=ft.Padding(0, 0, 0, 0), min_tile_height=30,
        expanded_cross_axis_alignment=ft.CrossAxisAlignment.START)


def _reason(c: dict, row: Optional[dict], verdict: str, gate: dict) -> tuple[str, str]:
    """(reason code, reason text) for the verdict shown."""
    if row is not None:
        code = row.get("reason_code") or row.get("reason") or c.get("reason_code") or c.get("reason")
        return (str(code), f"verdict row {row.get('card_id')} r{row.get('revision')} in cards/verdicts.jsonl") if code \
            else ("—", "verdict row carries no reason code")
    if c.get("rerun") is False:
        return "registered", "registered card: never re-run, never rebuilt"
    if c.get("source"):
        return "archived_record", f"archived council record ({c['source']})"
    if verdict == "NOT_RUN":
        st = gate.get("status") or "UNKNOWN"
        if st != "FROZEN":
            return st, f"gate package {st}: no card runs before the freeze (P11)"
        return "no_verdict_row", "no verdict row in cards/verdicts.jsonl"
    code = c.get("reason_code") or c.get("reason")
    return (str(code), str(code)) if code else ("—", "no reason code recorded")


def _card_summary(c: dict, verdict: str, disp: str, code: str) -> tuple[str, str]:
    """One plain sentence of what the record means (Korean, English). Reads the record; decides nothing."""
    disp_ko = DISPOSITION_KO.get(disp, disp)
    if code == "invalid_verdict":
        return ("저장된 판정 값이 형식에 맞지 않아 판정으로 표시하지 않습니다(안전 차단).",
                "The stored verdict is not a schema verdict, so none is shown (fail closed).")
    if c.get("rerun") is False:
        return (f"등록된 {VERDICT_KO.get(verdict, verdict).split(' · ')[0]} 기록입니다. 다시 실행하거나 다시 만들지 "
                "않습니다.", f"A registered {verdict} record: never re-run, never rebuilt.")
    if disp == "FORWARD_SIM":
        return ("전진 모의 기록만 남기는 표시용 북입니다. 권장 북에는 들어가지 않습니다.",
                "A display-only forward-simulation book; it never reaches the recommended book.")
    if disp == "REFUSAL_BOOK":
        return ("퇴역한 구성요소를 거절 기록으로 보관한 북입니다. 표시 전용입니다.",
                "A retired leg kept as a refusal record; display only.")
    if verdict == "NOT_RUN":
        if code in ("NOT_FROZEN", "UNKNOWN"):
            return ("게이트 패키지가 동결되기 전이라 아직 실행하지 않은 카드입니다. 권장 북에는 들어가지 않습니다.",
                    "Not run yet: the gate package is not frozen. It does not reach the recommended book.")
        return ("아직 판정 기록이 없는 카드입니다. 권장 북에는 들어가지 않습니다.",
                "No verdict row yet; it does not reach the recommended book.")
    if verdict == "PASS":
        return (f"게이트를 통과했습니다. 용도 구분은 '{disp_ko}'입니다.", f"Passed the gate; disposition {disp}.")
    if verdict == "REVISE":
        return ("게이트에서 보완이 필요하다는 판정을 받았습니다. 권장 북에는 들어가지 않습니다.",
                "The gate asked for revisions; it does not reach the recommended book.")
    if verdict == "REJECT":
        return ("게이트에서 기각되었습니다. 권장 북에는 들어가지 않습니다.",
                "Rejected by the gate; it does not reach the recommended book.")
    return ("데이터가 부족해 판정하지 못했습니다. 권장 북에는 들어가지 않습니다.",
            "Too little data to decide; it does not reach the recommended book.")


def _notional(c: dict) -> ft.Control:
    n = c.get("notional")
    if not n:
        return lchip("명목금액: 슬리브 키 없음", "notional: no sleeve key", "muted")
    if n.get("value") is None:
        return lchip("명목금액: 미입력 (소유자 입력 필요)", "notional: null (owner input)", "warning",
                     tooltip=f"{n.get('ref')} is null in the store")
    return lchip(f"명목금액: {n['value']}", f"notional: {n['value']}", "muted", tooltip=str(n.get("ref")))


def _card_row(c: dict, row: Optional[dict], gate: dict, drafts: list[dict]) -> ft.Control:
    pal = active()
    verdict = str((row or c).get("verdict") or "NOT_RUN")
    disp = str((row or c).get("disposition") or "DESCRIPTIVE")
    code, why = _reason(c, row, verdict, gate)
    if verdict in VERDICTS:
        vchip = _verdict_chip(verdict, tooltip=why)
    else:                                    # never let a disposition or a stray word pose as a verdict
        code, why = "invalid_verdict", f"verdict {verdict!r} is not a schema verdict (fail closed)"
        vchip = lchip("판정 형식 오류", "verdict invalid", "error", tooltip=why)
    cls = str(c.get("class") or "class ?")
    head = ft.Row([
        ft.Text(str(c.get("card_id")), size=13, weight=ft.FontWeight.W_600, color=pal.text, selectable=True),
        lchip(CLASS_KO.get(cls, cls), cls),
        _tagged(vchip, "verdict"),
        _tagged(_disposition_chip(disp), "disposition"),
        lchip(f"사유: {_status(code)}", f"reason: {code}", "muted", tooltip=why),
    ], spacing=6, wrap=True)
    facts = []
    if c.get("instrument_book"):
        facts.append(lchip(f"상품 북: {c['instrument_book']}", f"instrument book: {c['instrument_book']}"))
    if c.get("build_status"):
        facts.append(lchip(f"구축 단계: {_status(c['build_status'])}", f"build status: {c['build_status']}",
                           tooltip=str(c["build_status"])))
    if "notional" in c:
        facts.append(_notional(c))
    nulls = c.get("owner_nulls") or {}
    if nulls:
        facts.append(lchip(f"소유자·기준값 미입력 {len(nulls)}개", f"{len(nulls)} owner / reference nulls", "warning",
                           tooltip="\n".join(f"{k}: {v}" for k, v in nulls.items())))
    revs = sorted(d.get("revision") for d in drafts if isinstance(d.get("revision"), int))
    if revs:
        committed = any(d.get("header_md5") for d in drafts)
        listed = ", ".join(f"r{r}" for r in revs)
        facts.append(lchip("헤더 " + ("커밋됨 " if committed else "초안 ") + listed + ("" if committed else " · 커밋 전"),
                           "header " + ("committed " if committed else "drafts ") + listed
                           + ("" if committed else " · not committed"), tooltip=str(drafts[-1].get("claim") or "")))
    record: list[ft.Control] = [
        ft.Text(c.get("label") or "no label in the registry", size=12, color=pal.text, selectable=True),
        ft.Text(f"Reason: {why}", size=12, color=pal.muted, selectable=True)]
    extra = [f"{k}: {_kv(c[k]) if isinstance(c[k], dict) else c[k]}" for k in ("span", "fragility_ratio", "backlog")
             if c.get(k) is not None]
    if extra:
        record.append(ft.Text(" · ".join(extra), size=12, color=pal.muted, selectable=True))
    lines: list[ft.Control] = [head, _summary_text(*_card_summary(c, verdict, disp, code))]
    if facts:
        lines.append(ft.Row(facts, spacing=6, run_spacing=6, wrap=True))
    lines.append(_original(record))
    return _tagged(card(ft.Column(lines, spacing=6)), f"card:{c.get('card_id')}")


def _gate_reason(reason: str) -> tuple[str, str]:
    """A refusal reason in plain words (Korean, English), without its local paths."""
    text = str(reason)
    if text.startswith("NOT_FROZEN: acceptance test not passed"):
        return ("수용 테스트를 아직 통과하지 않았습니다. 기준 데이터로 한 번 실행해 통과해야 합니다.",
                "The acceptance test has not passed yet; it must run once on the reference data and pass.")
    if text.startswith("NOT_FROZEN: anchor UNVERSIONED"):
        return ("저장소가 아직 git 버전 관리 아래 있지 않습니다. 소유자가 저장소를 git에 두어야 합니다.",
                "The repository is not under git yet; the owner must place it there.")
    if text.startswith("NOT_FROZEN: reference fixtures absent"):
        try:
            n = len(ast.literal_eval(text.split(":", 2)[2].strip()))
        except (ValueError, SyntaxError, IndexError, TypeError):
            n = None
        if n:
            return (f"기준 데이터 파일 {n}개가 없습니다.", f"{n} reference data files are missing.")
        return ("기준 데이터 파일이 없습니다.", "Reference data files are missing.")
    shown = _no_paths(text)
    return shown, shown


def _gate_block(gate: dict) -> ft.Control:
    pal = active()
    st = str(gate.get("status") or "UNKNOWN")
    token = "success" if st == "FROZEN" else "warning" if st == "NOT_FROZEN" else "error"
    lines: list[ft.Control] = [ft.Row([ft.Text("Gate package", size=15, weight=ft.FontWeight.W_600, color=pal.text),
                                       lchip(f"게이트 패키지 {_status(st)}", f"gate package {st}", token,
                                             tooltip=st)], spacing=10, wrap=True)]
    if st != "FROZEN":
        lines.append(ft.Container(ft.Text("No macro card runs before the freeze: every card stays NOT RUN until the "
                                          "package is frozen and its formal run is recorded (P11).", size=12,
                                          color=pal.muted), tooltip=_P11_TIP[1]))
    reasons = [str(r) for r in gate.get("reasons") or []]
    lines += [LocalText("• " + ko, "• " + en, size=12, color=pal.text, selectable=True)
              for ko, en in (_gate_reason(r) for r in reasons)]
    if reasons:
        lines.append(_original([ft.Text("• " + r, size=12, color=pal.muted, selectable=True) for r in reasons]))
    return card(ft.Column(lines, spacing=6))


def _techfund_row(d: dict) -> ft.Control:
    pal = active()
    run = str(d.get("run_status") or d.get("verdict") or "NOT_RUN")
    why = str(d.get("blocked_by") or "no reason recorded")
    kind = why.split(":", 1)[0].strip() if ":" in why else ""
    cls = str(d.get("class") or "class ?")
    build = str(d.get("build_status") or "—")
    book = str(d.get("instrument_book") or "—")
    if kind == "REFDATA":
        summary = ("기준 데이터가 아직 없어 실행하지 않은 제안 카드입니다. 권유가 아닙니다.",
                   "A proposal not run yet: its reference data is absent. Not a recommendation.")
    elif kind == "PENDING":
        summary = ("선행 작업을 기다리는 제안 카드로, 아직 실행하지 않았습니다. 권유가 아닙니다.",
                   "A proposal waiting for prerequisite work; not run yet. Not a recommendation.")
    else:
        summary = ("아직 실행하지 않은 제안 카드입니다. 권유가 아닙니다.", "A proposal not run yet. Not a recommendation.")
    record: list[ft.Control] = [
        ft.Text(str(d.get("hypothesis") or ""), size=12, color=pal.text, italic=True, selectable=True),
        ft.Text(f"Reason: {why}", size=12, color=pal.muted, selectable=True)]
    lab = d.get("lab_reference")
    if isinstance(lab, dict) and lab.get("label"):
        record.append(ft.Text(str(lab["label"]), size=12, color=pal.muted, selectable=True))
    lines: list[ft.Control] = [
        ft.Row([ft.Text(str(d.get("card_id")), size=13, weight=ft.FontWeight.W_600, color=pal.text),
                lchip(CLASS_KO.get(cls, cls), cls),
                _tagged(_verdict_chip(run, tooltip=why), "verdict"),
                lchip(f"구축 단계: {_status(build)}", f"build status: {build}", tooltip=build),
                lchip(f"상품 북: {book}", f"instrument book: {book}"),
                lchip(f"사유: {_status(kind) if kind else '기록 없음'}", f"reason: {kind or 'none'}", "muted",
                      tooltip=_no_paths(why))], spacing=6, wrap=True),
        _summary_text(*summary),
        _original(record)]
    return _tagged(card(ft.Column(lines, spacing=6)), f"card:{d.get('card_id')}")


def _cry1_lines(results) -> list[str]:
    out = []
    for venue, body in (results or {}).items():
        if not isinstance(body, dict):
            continue
        if "decision" in body:
            out.append(f"{venue}: {body['decision']} — {body.get('reason', '')}")
            continue
        for k, v in body.items():
            if isinstance(v, dict) and "decision" in v:
                out.append(f"{venue} · {k}: {v['decision']} — {v.get('reason', '')}")
            elif isinstance(v, dict):
                out.append(f"{venue} · {k}: {_kv(v)}")
            elif k == "trigger" and v:
                out.append(f"{venue}: {v}")
    return out


def _cry1_row(r: dict) -> ft.Control:
    pal = active()
    label = str(r.get("label") or "vendor data, labelled trial, not a formal card run")
    card_name = str(r.get("card", "—"))
    status = str(r.get("status") or "")
    ko = f"제공처 데이터로 한 표시된 시험이며 정식 카드 실행이 아닙니다. 카드 {card_name}의 저장된 판정은 바뀌지 않습니다."
    en = f"A labelled trial on vendor data, not a formal card run; the stored verdict of card {card_name} is not rewritten."
    if status == "NOT_RUN":
        reason_kind = str(r.get("reason") or "").split(":", 1)[0].strip()
        ko += f" 이 시험은 아직 실행하지 않았습니다({_status(reason_kind) if reason_kind else '사유 기록 없음'})."
        en += " This trial has not run yet."
    record: list[ft.Control] = [ft.Text(f"Card {card_name}: {r.get('c3_verdict', '')}", size=12, color=pal.text,
                                        selectable=True)]
    if status:
        record.append(ft.Text(f"{status}: {r.get('reason', '')}", size=12, color=pal.muted, selectable=True))
    record += [ft.Text("• " + ln, size=12, color=pal.muted, selectable=True) for ln in _cry1_lines(r.get("results"))]
    lines: list[ft.Control] = [
        ft.Row([ft.Text(f"{r.get('item', 'CRY-1')}: {r.get('addition', '')}", size=13, weight=ft.FontWeight.W_600,
                        color=pal.text),
                lchip("제공처 데이터 · 표시된 시험 · 정식 카드 실행 아님", label, "error")
                if label == "vendor data, labelled trial, not a formal card run" else chip(label, "error"),
                lchip(f"등록 번호 {r.get('register_id', '—')}", f"register {r.get('register_id', '—')}")],
               spacing=6, wrap=True),
        _summary_text(ko, en),
        _original(record)]
    return card(ft.Column(lines, spacing=4))


def cards_blocks(cards: list[dict], verdicts: list[dict], gate_status: dict, headers: list[dict], *,
                 techfund: list[dict] = (), cry1: list[dict] = ()) -> list[ft.Control]:
    """cards = `cards.list_cards(...)` rows (+ the refusal cards), verdicts = rows of `cards/verdicts.jsonl`,
    gate_status = {status, reasons}, headers = header dicts (drafts and committed); techfund = the tech-fund
    `*.draft.json` dicts, cry1 = the `cry1_*.json` results. Missing or malformed inputs fail closed: one error
    notice and nothing else."""
    if not isinstance(cards, list) or not isinstance(verdicts, list) or not isinstance(gate_status, dict) \
            or not isinstance(headers, list):
        return [notice("Model cards not shown: the card registry, verdict chain or gate status is missing or invalid "
                       "(fail closed).", "error", icon=ft.Icons.ERROR_OUTLINE)]
    last = {r.get("card_id"): r for r in verdicts if isinstance(r, dict)}          # later rows win
    drafts: dict[str, list[dict]] = {}
    for h in headers:
        if isinstance(h, dict):
            drafts.setdefault(h.get("card_id"), []).append(h)
    blocks: list[ft.Control] = [
        notice("Read-only records. A verdict chip shows only a gate result; BUILD-AS-INSURANCE, FORWARD-SIM and "
               "refusal are dispositions, shown beside it. Labels are printed verbatim.", "accent",
               icon=ft.Icons.LOCK_OUTLINE),
        ft.Row([lchip(f"카드 {len(cards)}개", f"{len(cards)} cards"),
                lchip(f"판정 기록 {len(verdicts)}건", f"{len(verdicts)} verdict rows")], spacing=6, wrap=True),
        _gate_block(gate_status)]
    for key, title, caption in GROUPS:
        rows = [c for c in cards if isinstance(c, dict) and _group(c) == key]
        if rows:
            blocks.append(ft.Container(ft.Column([_heading(title, caption)] + [
                _card_row(c, last.get(c.get("card_id")), gate_status, drafts.get(c.get("card_id"), [])) for c in rows],
                spacing=8, horizontal_alignment=STRETCH), data=key))
    blocks.append(ft.Container(ft.Column(
        [_heading("Tech-fund card drafts — not run, not a recommendation",
                  "Proposals pending owner confirmation; Council v2.0 governs on conflict.")]
        + ([_techfund_row(d) for d in techfund if isinstance(d, dict)]
           or [notice("No tech-fund card drafts found under docs/techfund.", "accent")]), spacing=8, horizontal_alignment=STRETCH), data="techfund"))
    blocks.append(ft.Container(ft.Column(
        [_heading("CRY-1 control results (crypto card C3)",
                  "Vendor data, labelled trials, not formal card runs; the stored C3 verdict is not rewritten.")]
        + ([_cry1_row(r) for r in cry1 if isinstance(r, dict)]
           or [notice("No CRY-1 results found under docs/techfund.", "accent")]), spacing=8, horizontal_alignment=STRETCH), data="cry1"))
    return blocks


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_inputs(macro_dir=None, cards_root=None) -> dict:
    """The keyword arguments of `cards_blocks`, read once. Raises on a broken verdict chain, a committed header or
    card that does not re-hash, or an unreadable store (the caller shows the error and no numbers)."""
    import config
    from core.ficc import macro_artifacts as MA
    from core.quant import cards as K, gate_package as GP, refusal as R
    from core.rules.macro_rules import load_store
    from core.skills.macro_daily import CARDS_ROOT, GOVERNANCE_LOG
    macro_dir = Path(macro_dir or config.macro_dir())
    store, root = load_store(rulings_log=macro_dir / GOVERNANCE_LOG), Path(cards_root or CARDS_ROOT)   # effective store (S1)
    cards = K.list_cards(root, store)
    for c in cards:
        if c.get("notional"):
            c["notional"]["value"] = store.get(c["notional"]["ref"])
    for rule, spec in (("R-11", R.CARD_S1), ("R-12", R.CARD_S2)):
        rec = R.REFUSAL_RECORDS.get(rule, {})
        cards.append({**spec, "rule_id": rule, "source": rec.get("source"), "span": rec.get("span"),
                      "fragility_ratio": rec.get("fragility_ratio"), "backlog": rec.get("backlog")})
    return {"cards": cards,
            "verdicts": K.read_chain(K.verdicts_path(root), K.VERDICT_ROW),
            "gate_status": {"status": GP.package_state(store, macro_dir),
                            "reasons": GP.freeze_reasons(store, MA.GIT_HASH, macro_dir)},
            "headers": K.committed_headers(root) + [_json(p) for p in sorted((root / "headers").glob("*.draft.json"))],
            "techfund": [_json(p) for p in sorted(TF_DOCS.glob("*.draft.json"))],
            "cry1": [_json(p) for p in sorted(TF_DOCS.glob("cry1_*.json"))]}


def view_shell(page: ft.Page, load: Callable[[], dict], render: Callable[[dict], list[ft.Control]]) -> ft.Control:
    """Refresh button + host: `render(load())` on `page.run_thread`, two-tier except, re-read on every Refresh."""
    pal = active()
    busy = ft.ProgressRing(visible=False, width=20, height=20)
    status = ft.Text("", size=12, color=pal.muted)
    host = ft.Column(spacing=14, horizontal_alignment=STRETCH)

    def refresh(e=None) -> None:
        busy.visible = True
        status.value = "Reading… (local files, read-only)"
        page.update()

        def worker():
            try:
                blocks = render(load())
            except (ValueError, OSError, RuntimeError) as exc:
                blocks = [notice(str(exc), "error", icon=ft.Icons.ERROR_OUTLINE)]
            except Exception as exc:
                blocks = [notice(f"{type(exc).__name__}: {exc}", "error", icon=ft.Icons.ERROR_OUTLINE)]
            host.controls = blocks
            busy.visible = False
            status.value = ""
            page.update()

        page.run_thread(worker)

    refresh()
    return ft.Column([ft.Row([ft.Button("Refresh", icon=ft.Icons.REFRESH, on_click=refresh), busy, status],
                             spacing=10, wrap=True),
                      ft.Column([host], scroll=ft.ScrollMode.AUTO, expand=True, horizontal_alignment=STRETCH)],
                     spacing=14, expand=True)


def build_cards_view(page: ft.Page) -> ft.Control:
    return view_shell(page, load_inputs, lambda d: cards_blocks(d["cards"], d["verdicts"], d["gate_status"],
                                                               d["headers"], techfund=d["techfund"], cry1=d["cry1"]))
