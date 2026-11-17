"""Research Library pieces (owner-approved draft 2026-11-17, docs/product/ui_drafts_2026-11-17/draft_06_library.png).

The page itself is built in `ResearchWindow.make_library` from the page kit (`page_kit.Workspace`); this module holds
what only this page needs: the session's runs as one list of rows (symbol, model, key figure, run status, verdict,
time), the run information grid and the reproducibility checklist with status dots.

Display only. Rows, figures and checks are read from the session's ResearchRun records (`core.research.runs`) and the
latest portfolio and strategy reports of this session; a value that a record does not hold is shown as not recorded,
never filled in. Nothing here computes, saves or sends anything.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import math

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFontMetrics, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import (QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QSizePolicy, QToolTip, QVBoxLayout,
                             QWidget)

from core.theme import LIGHT
from .page_kit import Text, Workspace, pick
from .stock_detail_style import line_color

KINDS = ("monte_carlo", "portfolio", "strategy")
KIND_NAMES = {"monte_carlo": ("Monte Carlo", "몬테카를로"), "portfolio": ("Portfolio", "포트폴리오"),
              "strategy": ("Strategy", "전략")}
STATUS_WORDS = {"COMPLETED": ("Completed", "완료"), "RUNNING": ("Running", "실행 중"), "FAILED": ("Failed", "실패")}
OFFICIAL_WORDS = {"NOT_RUN": ("Not run", "미실행"), "PARTIAL": ("Partial", "부분"), "NOT_VERIFIED": ("Unverified", "미검증"),
                  "NOT_APPLIED": ("Not applied", "미적용"), "PASS": ("Pass", "통과"), "FAIL": ("Fail", "실패"),
                  "BLOCKED": ("Blocked", "차단")}
# The cost declaration a ResearchRun carries (core.research.runs.new_run), in words.
COST_REASONS = {"price_distribution_not_strategy_backtest": ("a price distribution, not a backtest",
                                                             "가격 분포라 해당 없음")}
# What commentary_payload leaves out (commentary.commentary_payload, core.research.ai_payload).
PAYLOAD_EXCLUDES = ("accounts · ledgers · secret settings · file paths", "계좌 · 원장 · 비밀 설정 · 파일 경로")


def minus(text):
    return str(text).replace("-", "−")


def signed_pct(value, digits=1):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"
    return minus(f"{number:.{digits}%}") if math.isfinite(number) else "—"


def parse_time(value):
    if not value:
        return None
    try:
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return (moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def short_hash(digest):
    digest = str(digest or "")
    return f"sha256 {digest[:4]}…{digest[-4:]}" if len(digest) >= 12 else digest


def official(code):
    """('미실행', 'NOT_RUN')-style word and code for a status code; unknown codes keep only the code."""
    code = str(code or "—")
    return OFFICIAL_WORDS.get(code), code


def official_pair(code):
    """'미실행 NOT_RUN' in Korean; in English the code itself reads as the word."""
    word, code = official(code)
    return (code, f"{word[1]} {code}") if word else (code, code)


@dataclass
class Entry:
    """One row: a ResearchRun (Monte Carlo) or the latest portfolio or strategy report of this session."""
    key: str
    kind: str
    record: dict
    status: str
    verdict: str
    created_at: str | None
    symbol: tuple
    symbol_sub: tuple
    model: tuple
    model_sub: tuple
    figure: str = "—"
    figure_tone: str = ""
    figure_sub: tuple = ("", "")
    saved: bool = False
    mark: str = ""                       # letters for the avatar, or 'portfolio' / 'strategy' for a glyph
    search: str = field(default="", repr=False)

    def matches(self, query):
        query = str(query or "").strip().lower()
        return not query or all(part in self.search for part in query.split())


def _search_text(*pairs):
    return " ".join(str(value) for pair in pairs for value in (pair if isinstance(pair, tuple) else (pair,))).lower()


def run_entry(run, *, saved=False):
    """A Monte Carlo ResearchRun as a row."""
    from .risk_display import MC_MODEL_LABELS, ko, source_name
    params = run.get("parameters") or {}
    metrics = run.get("metrics") or {}
    data = run.get("data") or {}
    status = str(run.get("execution_status") or "")
    symbol = str(params.get("symbol") or "—")
    model_en = MC_MODEL_LABELS.get(params.get("model"), str(params.get("model") or "—"))
    horizon, paths = params.get("horizon_days"), params.get("n_paths")
    sub_en, sub_ko = ["Monte Carlo"], ["몬테카를로"]
    if isinstance(horizon, int):
        sub_en.append(f"{horizon:,} sessions")
        sub_ko.append(f"{horizon:,}거래일")
    if isinstance(paths, int):
        sub_en.append(f"{paths:,} paths")
        sub_ko.append(f"{paths:,}경로")
    if data.get("source"):
        source = (source_name(data["source"], "en"), source_name(data["source"], "ko"))
    elif status == "RUNNING":
        source = ("data not recorded yet", "자료 기록 전")
    else:
        source = ("no price data", "가격 자료 없음")
    if status == "COMPLETED" and "var_pct" in metrics:
        # As the Build & Test key figures show it: the recorded value, no rise/fall colour (a VaR is not a price move).
        figure, tone, figure_sub = signed_pct(metrics["var_pct"]), "", ("95% VaR", "95% VaR")
    elif status == "RUNNING":
        figure, tone, figure_sub = "—", "", ("calculating", "계산 중")
    else:
        code = str(run.get("error_code") or "")
        figure, tone, figure_sub = "—", "", (code, code) if code else ("no result", "결과 없음")
    entry = Entry(run.get("run_id", ""), "monte_carlo", run, status, str(run.get("verdict") or "NOT_RUN"),
                  run.get("created_at"), (symbol, symbol), source, (model_en, ko(model_en)),
                  (" · ".join(sub_en), " · ".join(sub_ko)), figure, tone, figure_sub, saved, symbol)
    entry.search = _search_text(entry.symbol, entry.symbol_sub, entry.model, entry.model_sub, KIND_NAMES["monte_carlo"])
    return entry


def _sections(report, kind):
    return [s for s in report.get("sections") or () if isinstance(s, dict) and s.get("type") == kind]


def portfolio_entry(report):
    """The latest portfolio report (PortfolioPane.exports.report) as a row."""
    from .risk_display import OBJECTIVE_LABELS, ko, source_name
    params = report.get("parameters") or {}
    symbols = [str(s) for s in params.get("symbols") or ()]
    objective = str(params.get("objective") or "")
    objective_en = OBJECTIVE_LABELS.get(objective, objective or "—")
    chosen = {}
    for section in _sections(report, "portfolios"):
        chosen = (section.get("data") or {}).get(objective) or {}
    sources = []
    for section in _sections(report, "provenance"):
        for history in section.get("histories") or ():
            if history.get("source") and history["source"] not in sources:
                sources.append(history["source"])
    first = symbols[0] if symbols else "—"
    more = len(symbols) - 1
    sub = ((f"{first} and {more} more", f"{first} 외 {more}종목") if more > 0 else (first, first))
    source_en = ", ".join(source_name(s, "en") for s in sources)
    source_ko = ", ".join(source_name(s, "ko") for s in sources)
    model_sub = (" · ".join(x for x in ("Portfolio", f"{len(symbols)} symbols", source_en) if x),
                 " · ".join(x for x in ("포트폴리오", f"{len(symbols)}종목", source_ko) if x))
    sharpe = chosen.get("sharpe")
    figure = f"{float(sharpe):.3f}" if isinstance(sharpe, (int, float)) and math.isfinite(float(sharpe)) else "—"
    entry = Entry("portfolio", "portfolio", report, str(report.get("execution_status") or ""),
                  str(report.get("verdict") or "NOT_RUN"), report.get("created_at"), KIND_NAMES["portfolio"], sub,
                  (objective_en, ko(objective_en)), model_sub, minus(figure), "", ("Sharpe ratio", "샤프 지수"),
                  mark="portfolio")
    entry.search = _search_text(entry.symbol, " ".join(symbols), entry.model, entry.model_sub)
    return entry


def statistics(report):
    """The strategy report's 'Validation statistics' table as {metric: value text}."""
    for section in _sections(report, "table"):
        if section.get("name") == "Validation statistics":
            return {str(row[0]): str(row[1]) for row in section.get("rows") or () if len(row) >= 2}
    return {}


def strategy_entry(report):
    """The latest strategy report (StrategyPane.report, a 'run', not the stored cards) as a row."""
    from core.research.strategy_workflow import FAMILIES
    from .risk_display import ko
    params = report.get("parameters") or {}
    symbols = [str(s) for s in params.get("symbols") or ()]
    family = str(params.get("family") or "")
    family_en = FAMILIES[family][0] if family in FAMILIES else (family or "—")
    days = params.get("days")
    first = symbols[0] if symbols else "—"
    more = len(symbols) - 1
    sub = ((f"{first} and {more} more", f"{first} 외 {more}종목") if more > 0 else (first, first))
    days_en = f"{days:,} sessions" if isinstance(days, int) else ""
    days_ko = f"{days:,}거래일" if isinstance(days, int) else ""
    model_sub = (" · ".join(x for x in ("Strategy Lab", days_en) if x), " · ".join(x for x in ("전략 실험실", days_ko) if x))
    figure = statistics(report).get("OOS Sharpe", "—")
    entry = Entry("strategy", "strategy", report, str(report.get("execution_status") or ""),
                  str(report.get("verdict") or "NOT_RUN"), report.get("created_at"), KIND_NAMES["strategy"], sub,
                  (family_en, ko(family_en)), model_sub, minus(figure), "",
                  ("OOS Sharpe", "표본 외 샤프"), mark="strategy")
    entry.search = _search_text(entry.symbol, " ".join(symbols), entry.model, entry.model_sub)
    return entry


def entries(runs, *, saved=(), portfolio=None, strategy=None):
    """Every row of the session, newest first: the ResearchRuns and the latest portfolio and strategy reports."""
    rows = [run_entry(run, saved=run.get("run_id") in saved) for run in runs]
    if portfolio:
        rows.append(portfolio_entry(portfolio))
    if strategy and (strategy.get("parameters") or {}).get("tool") != "cards":
        rows.append(strategy_entry(strategy))
    order = {id(entry): index for index, entry in enumerate(rows)}
    rows.sort(key=lambda entry: (-(parse_time(entry.created_at) or datetime.min.replace(tzinfo=timezone.utc)).timestamp(),
                                 order[id(entry)]))
    return rows


def counts(rows, saved):
    """The counts line: completed, running, failed, saved, not yet saved (completed runs), reproducibility, verdict."""
    runs = [entry for entry in rows if entry.kind == "monte_carlo"]
    done = sum(entry.status == "COMPLETED" for entry in rows)
    saved_runs = sum(entry.record.get("run_id") in saved for entry in runs)
    unsaved = sum(entry.status == "COMPLETED" and entry.record.get("run_id") not in saved for entry in runs)
    reproducibility = sorted({str(entry.record.get("reproducibility")) for entry in rows if entry.record.get("reproducibility")})
    verdicts = sorted({entry.verdict for entry in rows if entry.verdict})
    return dict(completed=done, running=sum(entry.status == "RUNNING" for entry in rows),
                failed=sum(entry.status == "FAILED" for entry in rows), saved=saved_runs, unsaved=unsaved,
                reproducibility=" · ".join(reproducibility), verdict=" · ".join(verdicts))


# ---------------------------------------------------------------------------------------------------------------
# Evidence: the run information grid and the reproducibility checklist, read from one record.

def run_info(entry):
    """[(caption pair, value pair, wide)] for the 실행 정보 grid."""
    from .risk_display import source_name
    record = entry.record
    created = parse_time(entry.created_at)
    when = created.strftime("%Y-%m-%d %H:%M:%S") if created else "—"
    params = record.get("parameters") or {}
    if entry.kind == "monte_carlo":
        data = record.get("data") or {}
        horizon, paths = params.get("horizon_days"), params.get("n_paths")
        span = ((f"{horizon:,} sessions · {paths:,}" if isinstance(horizon, int) and isinstance(paths, int) else "—"),
                (f"{horizon:,}거래일 · {paths:,}개" if isinstance(horizon, int) and isinstance(paths, int) else "—"))
        if data:
            last = str(data.get("last_observation") or "")[:10]
            source = (f"{source_name(data.get('source'), 'en')} · to {last}", f"{source_name(data.get('source'), 'ko')} · {last}까지")
        else:
            source = ("not loaded", "불러오지 않음")
        run_id = str(record.get("run_id") or "")[:8]
        rows = [(("Symbol", "종목 코드"), entry.symbol, False), (("Model", "모델"), entry.model, False),
                (("Horizon · paths", "기간 · 경로"), span, False), (("Data", "데이터"), source, False),
                (("Created · UTC", "생성 시각 · UTC"), (f"{when} · run ID {run_id}", f"{when} · 실행 ID {run_id}"), True)]
        if record.get("error_code"):
            rows.append((("Error", "오류"), (str(record["error_code"]),) * 2, True))
        return rows
    symbols = ", ".join(str(s) for s in params.get("symbols") or ()) or "—"
    if entry.kind == "portfolio":
        cap = params.get("max_weight")
        cap_text = f"{float(cap):.0%}" if isinstance(cap, (int, float)) else "—"
        return [(("Symbols", "종목"), (symbols, symbols), True), (("Objective", "목표"), entry.model, False),
                (("Weight cap", "비중 상한"), (cap_text, cap_text), False),
                (("Created · UTC", "생성 시각 · UTC"), (when, when), True)]
    cost = params.get("cost_bps")
    cost_pair = ((f"{float(cost):g} bp per side", f"편도 {float(cost):g}bp") if isinstance(cost, (int, float))
                 else ("table rate", "표준 요율"))
    days = params.get("days")
    days_pair = (f"{days:,} sessions", f"{days:,}거래일") if isinstance(days, int) else ("—", "—")
    return [(("Symbols", "종목"), (symbols, symbols), True), (("Strategy", "전략"), entry.model, True),
            (("Period", "기간"), days_pair, False), (("Costs", "거래 비용"), cost_pair, False),
            (("Created · UTC", "생성 시각 · UTC"), (when, when), True)]


@dataclass(frozen=True)
class Check:
    state: str            # 'ok' recorded, 'warn' not verified, 'none' not applicable / not run / not recorded
    label: tuple
    value: tuple
    sub: tuple = ("", "")


NOT_RECORDED = ("not recorded", "기록 없음")


def _environment(environment):
    environment = environment or {}
    parts = [(name, environment.get(key)) for name, key in (("Python", "python"), ("NumPy", "numpy"))]
    shown = [f"{name} {value}" for name, value in parts if value and value != "NOT_RECORDED"]
    return " · ".join(shown)


def evidence(entry):
    """The reproducibility checklist for one row: (checks, recorded count, unverified count, reproducibility code)."""
    record = entry.record
    code = record.get("code") or {}
    environment = _environment(record.get("environment"))
    verdict = official_pair(entry.verdict)
    checks = []
    unverified = 0
    if entry.kind == "monte_carlo":
        params = record.get("parameters") or {}
        data = record.get("data") or {}
        seed = params.get("seed")
        checks.append(Check("ok", ("Random seed", "난수 시드"), (str(seed),) * 2) if isinstance(seed, int)
                      else Check("none", ("Random seed", "난수 시드"), NOT_RECORDED))
        digest = code.get("calculation_sha256")
        checks.append(Check("ok", ("Calculation code hash", "계산 코드 해시"), (short_hash(digest),) * 2) if digest
                      else Check("warn", ("Calculation code hash", "계산 코드 해시"), NOT_RECORDED))
        fingerprint = data.get("fingerprint_sha256")
        checks.append(Check("ok", ("Data fingerprint", "데이터 지문"), (short_hash(fingerprint),) * 2) if fingerprint
                      else Check("none", ("Data fingerprint", "데이터 지문"), ("no data", "데이터 없음")))
        checks.append(Check("ok", ("Runtime", "실행 환경"), (environment,) * 2) if environment
                      else Check("warn", ("Runtime", "실행 환경"), NOT_RECORDED))
        if data:
            states = [str(data.get("vintage")), str(data.get("license"))]
            unverified = sum(state == "NOT_VERIFIED" for state in states)
            shown = states[0] if states[0] == states[1] else f"{states[0]} · {states[1]}"
            checks.append(Check("warn" if unverified else "ok", ("Data vintage · licence", "데이터 빈티지 · 라이선스"),
                                official_pair(shown) if states[0] == states[1] else (shown, shown)))
        else:
            checks.append(Check("none", ("Data vintage · licence", "데이터 빈티지 · 라이선스"), ("no data", "데이터 없음")))
        cost = record.get("cost") or {}
        checks.append(Check("none", ("Trading costs", "거래 비용"), official_pair(cost.get("status") or "—"),
                            COST_REASONS.get(cost.get("reason"), ("", ""))))
    else:
        commit = code.get("commit")
        checks.append(Check("ok", ("Code revision", "코드 버전"), (str(commit)[:10],) * 2) if commit
                      else Check("none", ("Code revision", "코드 버전"), NOT_RECORDED))
        checks.append(Check("ok", ("Runtime", "실행 환경"), (environment,) * 2) if environment
                      else Check("warn", ("Runtime", "실행 환경"), NOT_RECORDED))
        rights = str(record.get("data_rights") or "")
        unverified = int(rights == "NOT_VERIFIED")
        checks.append(Check("warn" if unverified else ("ok" if rights else "none"), ("Data rights", "데이터 권리"),
                            official_pair(rights) if rights else NOT_RECORDED))
        if entry.kind == "strategy":
            cost = (record.get("parameters") or {}).get("cost_bps")
            checks.append(Check("ok", ("Trading costs", "거래 비용"),
                                (f"{float(cost):g} bp per side", f"편도 {float(cost):g}bp") if isinstance(cost, (int, float))
                                else ("table rate", "표준 요율")))
        else:
            checks.append(Check("none", ("Trading costs", "거래 비용"), NOT_RECORDED,
                                ("weights, not a backtest", "비중 계산이라 해당 없음")))
    checks.append(Check("none", ("Verdict", "검증 판정"), verdict))
    recorded = sum(check.state == "ok" for check in checks)
    return checks, recorded, unverified, str(record.get("reproducibility") or "—")


def preview_content(entry, has_rows):
    """The preview card for a row (or for no row): title, note, link, empty text, key figures, whether the run's fan
    chart is shown, a reading line and the quiet foot. Every figure is read from the record."""
    content = dict(title=("Preview", "결과 미리보기"), note=("", ""), open=("Go to Build & Test ›", "설계/검증으로 이동 ›"),
                   empty=("Choose a run in the list to preview it.", "목록에서 실행을 고르면 여기에서 미리 볼 수 있어요."),
                   figures=[], chart=False, text=("", ""), foot=("", ""))
    if entry is None:
        if not has_rows:
            content["empty"] = ("Run a calculation under Build & Test or Portfolio & Risk: every run of this session is "
                                "listed here.", "설계/검증이나 분석에서 계산을 실행하면 이번 세션의 실행이 여기에 쌓여요.")
        return content
    record = entry.record
    content["title"] = (f"{entry.symbol[0]} preview", f"{entry.symbol[1]} 결과 미리보기")
    if entry.kind == "monte_carlo":
        params = record.get("parameters") or {}
        horizon, paths, seed = params.get("horizon_days"), params.get("n_paths"), params.get("seed")
        en, ko = [entry.model[0]], [entry.model[1]]
        if isinstance(horizon, int):
            en.append(f"{horizon:,} sessions")
            ko.append(f"{horizon:,}거래일")
        if isinstance(paths, int):
            en.append(f"{paths:,} paths")
            ko.append(f"경로 {paths:,}개")
        if isinstance(seed, int):
            en.append(f"seed {seed}")
            ko.append(f"시드 {seed}")
        content["note"] = (" · ".join(en), " · ".join(ko))
        metrics = record.get("metrics") or {}
        if entry.status == "COMPLETED" and metrics:
            def number(key):
                return minus(f"{float(metrics[key]):,.2f}") if key in metrics else "—"
            content["figures"] = [(("Start", "시작"), number("spot"), ""), (("Median", "중앙값"), number("p50"), ""),
                                  (("Lower 5%", "하위 5%"), number("p05"), "down"),
                                  (("Upper 5%", "상위 5%"), number("p95"), "up"),
                                  (("P(loss)", "손실 확률"), signed_pct(metrics.get("prob_loss")), ""),
                                  (("95% VaR", "95% VaR"), signed_pct(metrics.get("var_pct")), "")]
            content["chart"] = True
            content["foot"] = ("Simulation · not a guarantee of the future · not investment advice",
                               "시뮬레이션 · 미래 보장 아님 · 투자 권유 아님")
        elif entry.status == "RUNNING":
            content["text"] = ("Calculating. The result shows here when it finishes.",
                               "계산 중이에요. 끝나면 결과가 여기에 보여요.")
        else:
            code = str(record.get("error_code") or "—")
            content["text"] = (f"The calculation failed ({code}). The failed record stays here as evidence; check the "
                               "inputs or the data connection and run it again.",
                               f"계산이 실패했어요({code}). 실패 기록도 근거로 남아요. 입력이나 데이터 연결을 확인한 뒤 "
                               "다시 실행하세요.")
        return content
    content["note"] = (f"{entry.model[0]} · {entry.model_sub[0]}", f"{entry.model[1]} · {entry.model_sub[1]}")
    if entry.kind == "portfolio":
        objective = (record.get("parameters") or {}).get("objective")
        chosen = {}
        for section in _sections(record, "portfolios"):
            chosen = (section.get("data") or {}).get(objective) or {}
        content["figures"] = [(("Expected return", "기대 수익률"), signed_pct(chosen.get("ann_return")), ""),
                              (("Volatility", "변동성"), signed_pct(chosen.get("ann_vol")), ""),
                              (("Sharpe ratio", "샤프 지수"), entry.figure, "")]
        content["text"] = ("The weights, the frontier and the correlations are on Portfolio & Risk.",
                           "비중·효율적 투자선·상관관계는 분석 화면에 있어요.")
        content["foot"] = ("Weights from past prices · not a guarantee of the future · not investment advice",
                           "과거 가격으로 계산한 비중 · 미래 보장 아님 · 투자 권유 아님")
        content["open"] = ("Go to Portfolio & Risk ›", "분석으로 이동 ›")
        return content
    stats = statistics(record)
    labels = ((("OOS Sharpe", "표본 외 샤프"), "OOS Sharpe"), (("Deflated Sharpe", "디플레이티드 샤프"), "Deflated Sharpe"),
              (("PBO", "PBO"), "PBO"), (("Max drawdown", "최대 낙폭"), "Max drawdown"), (("Trades", "거래 수"), "Trades"))
    content["figures"] = [(pair, minus(stats[key]), "") for pair, key in labels if key in stats]
    content["text"] = ("Rules, costs and every gate criterion are on Build & Test → Strategy Lab.",
                       "규칙·비용·검증 기준은 설계/검증의 전략 실험실에 있어요.")
    content["foot"] = ("Backtest on past prices · not a guarantee of the future · not investment advice",
                       "과거 가격 백테스트 · 미래 보장 아님 · 투자 권유 아님")
    return content


def side_content(entry):
    """The right column for a row: the status pill, the run information, the checklist and its counts."""
    checks, recorded, unverified, reproducibility = evidence(entry)
    word = STATUS_WORDS.get(entry.status)
    return dict(status=(f"● {word[0]}", f"● {word[1]}") if word else (entry.status, entry.status),
                status_tone={"COMPLETED": "ok", "FAILED": "err"}.get(entry.status, ""),
                info=run_info(entry), checks=checks,
                count=((f"{recorded} recorded · {unverified} unverified", f"기록 {recorded} · 미검증 {unverified}"),
                       (f"{recorded} recorded", f"기록 {recorded}")),
                reproducibility=official_pair(reproducibility),
                reproducibility_tone="warn" if reproducibility in ("PARTIAL", "NOT_VERIFIED") else "")


def payload_summary(payload):
    """The 전송 내용 box: [(caption pair, value pair)] for a prepared commentary payload."""
    raw = json.dumps(payload, ensure_ascii=False, allow_nan=False, sort_keys=True).encode("utf-8")
    size = len(raw)
    size_text = f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B"
    params, sections = len(payload.get("parameters") or {}), len(payload.get("sections") or ())
    head = (f"{params} parameters · {sections} sections · JSON {size_text}", f"매개변수 {params} · 섹션 {sections} · JSON {size_text}")
    marks = " · ".join(str(payload.get(key) or "—") for key in ("official_verdict", "reproducibility", "data_rights"))
    return head, [(("Status marks", "상태 표시"), (marks, marks)), (("Left out", "빼는 것"), PAYLOAD_EXCLUDES)]


# ---------------------------------------------------------------------------------------------------------------
# Widgets

def faint(p):
    from .typography import mix
    return mix(p.muted, p.surface, 0.42)


def library_sheet(p, dark):
    """This page's rules on top of the kit's (page_kit.kit_sheet)."""
    from .typography import TONE_COLORS, mix
    t = TONE_COLORS[bool(dark)]
    line = line_color(p)
    return f"""
      QWidget[lib='plain'], QFrame[kit='card'] QWidget, QWidget#qgWorkspace QCheckBox {{ background: transparent; }}
      QLineEdit#libSearch {{ min-height: 22px; padding: 5px 12px 5px 6px; border: 1px solid {line}; border-radius: 17px;
                             background: {p.surface}; font-size: 13px; }}
      QLineEdit#libSearch:focus {{ border: 2px solid {p.accent}; }}
      QLabel[lib='sort'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[lib='foot'] {{ font-size: 11px; color: {faint(p)}; }}
      QLabel[lib='key'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[lib='value'] {{ font-size: 13px; font-weight: 500; color: {p.text}; }}
      QLabel[lib='check'] {{ font-size: 13px; color: {p.text}; }}
      QLabel[lib='checkSub'] {{ font-size: 11px; color: {faint(p)}; }}
      QLabel[lib='checkValue'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[lib='checkValue'][tone='warn'] {{ color: {p.warning}; }}
      QFrame[lib='checkRow'] {{ background: transparent; border: 0; border-top: 1px solid {line}; }}
      QFrame[lib='checkRow'][first='true'] {{ border-top: 0; }}
      QLabel[lib='dot'] {{ border-radius: 3px; min-width: 7px; max-width: 7px; min-height: 7px; max-height: 7px;
                           background: {mix(p.muted, p.surface, 0.55)}; }}
      QLabel[lib='dot'][state='ok'] {{ background: {p.success}; }}
      QLabel[lib='dot'][state='warn'] {{ background: {mix(p.warning, '#E0B040', 0.35)}; }}
      QFrame[lib='payload'] {{ background: {mix(p.surface_2, p.bg, 0.3)}; border: 0; border-radius: 12px; }}
      QLabel[lib='payloadHead'] {{ font-size: 12px; font-weight: 600; color: {p.text}; }}
      QLabel[lib='payloadKey'] {{ font-size: 12px; color: {p.muted}; }}
      QLabel[lib='payloadValue'] {{ font-size: 12px; color: {p.text}; }}
      QLabel[lib='payloadNote'] {{ font-size: 12px; color: {faint(p)}; }}
      QPushButton[lib='link'] {{ padding: 2px 4px; border: 0; border-radius: 6px; background: transparent;
                                 color: {p.accent}; font-size: 12px; font-weight: 500; }}
      QPushButton[lib='link']:hover {{ background: {p.accent_soft}; }}
      QPushButton[lib='link']:focus {{ border: 2px solid {p.accent}; }}
      QPushButton[lib='link']:disabled {{ color: {p.muted}; }}
      QWidget#qgWorkspace QPlainTextEdit {{ border: 1px solid {line}; border-radius: 9px; background: {p.surface};
                                            font-size: 12px; padding: 4px; }}
      QWidget#qgWorkspace QCheckBox {{ font-size: 12px; color: {p.text}; spacing: 8px; }}
      QLabel[lib='consent'] {{ font-size: 12px; color: {p.text}; }}
      QWidget#qgWorkspace QCheckBox::indicator {{ width: 14px; height: 14px; border: 1px solid {mix(p.border, p.muted, 0.45)};
                                                  border-radius: 4px; background: {p.surface}; }}
      QWidget#qgWorkspace QCheckBox::indicator:hover {{ border-color: {p.accent}; }}
      QWidget#qgWorkspace QCheckBox::indicator:checked {{ border: 4px solid {p.accent}; background: {p.on_accent}; }}
      QWidget#qgWorkspace QCheckBox:focus {{ color: {p.accent}; }}
      QLabel[pill='live'] {{ color: {p.accent}; background: {p.surface_2}; }}
      QLabel[kit='figValue'][tone='err'] {{ color: {p.error}; }}
      QPushButton#libExport {{ padding: 10px 8px; font-size: 13px; }}
      QLabel[kit='pill'][tone='warn'] {{ color: {p.warning}; background: {t['flat_tint']}; }}
    """


class LibraryWorkspace(Workspace):
    """The kit's Workspace with this page's extra rules; pieces registered with `on_theme` follow the theme, and a
    toolbar piece in `optional_toolbar` (the caption) steps aside when the toolbar is too narrow for it, so nothing in
    the toolbar is cut or overlaps (A3)."""

    def __init__(self, *args, **kwargs):
        self.theme_followers = []
        self.optional_toolbar = []
        super().__init__(*args, **kwargs)

    def on_theme(self, widget):
        self.theme_followers.append(widget)
        widget.set_theme(self.colors, self.dark)
        return widget

    def set_theme(self, colors, dark=None):
        super().set_theme(colors, dark)
        self.setStyleSheet(self.styleSheet() + library_sheet(colors, self.dark))
        for widget in getattr(self, "theme_followers", ()):
            try:
                widget.set_theme(colors, self.dark)
            except RuntimeError:
                pass

    def set_language(self, language):
        super().set_language(language)
        self.fit_toolbar()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_toolbar()

    def fit_toolbar(self):
        if not getattr(self, "optional_toolbar", None):
            return
        layouts = (self.toolbar_left, self.toolbar_right)
        widgets = [self.title] + [layout.itemAt(i).widget() for layout in layouts for i in range(layout.count())]
        widgets = [w for w in widgets if w is not None and w not in self.optional_toolbar and not w.isHidden()]
        needed = sum(w.minimumSizeHint().width() if w.minimumSizeHint().width() > 0 else w.sizeHint().width()
                     for w in widgets)
        needed += self.toolbar.spacing() * (len(widgets) + 1) + 24
        width = self.toolbar_host.width() or self.width()
        for widget in self.optional_toolbar:
            extra = widget.sizeHint().width() + self.toolbar.spacing()
            fits = needed + extra <= width
            if widget.isHidden() == fits:
                widget.setVisible(fits)
            if fits:
                needed += extra


class SearchField(QLineEdit):
    """The toolbar's search over the runs (symbol, name, model): 240 px when there is room, never under 150 px."""

    def __init__(self):
        super().__init__()
        self.setObjectName("libSearch")
        self.setMaxLength(60)
        self.setClearButtonEnabled(True)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setProperty("qg_literal", True)
        self.icon_action = self.addAction(search_icon(LIGHT.muted), QLineEdit.ActionPosition.LeadingPosition)
        self.set_language("ko")

    def sizeHint(self):
        return QSize(240, super().sizeHint().height())

    def minimumSizeHint(self):
        return QSize(150, super().minimumSizeHint().height())

    def set_language(self, language):
        self.setPlaceholderText(pick(language, ("Search symbol or model", "종목·모델 검색")))
        self.setAccessibleName(pick(language, ("Search runs", "실행 검색")))

    def set_theme(self, colors, dark):
        self.icon_action.setIcon(search_icon(colors.muted))


class ExportRow(QWidget):
    """The two exports side by side, one above the other when the column is too narrow for both labels."""

    def __init__(self, buttons):
        super().__init__()
        from PyQt6.QtWidgets import QBoxLayout
        self.buttons = tuple(buttons)
        self.box = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        self.box.setContentsMargins(0, 0, 0, 0)
        self.box.setSpacing(8)
        for button in self.buttons:
            button.setObjectName("libExport")
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.box.addWidget(button, 1)

    def fit(self):
        from PyQt6.QtWidgets import QBoxLayout
        width = self.width()
        needed = sum(button.sizeHint().width() for button in self.buttons) + self.box.spacing()
        direction = QBoxLayout.Direction.LeftToRight if needed <= width else QBoxLayout.Direction.TopToBottom
        if self.box.direction() != direction:
            self.box.setDirection(direction)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit()

    def set_language(self, language):
        for button in self.buttons:
            button.set_language(language)
        self.fit()


def preview_chart():
    """The selected run's fan chart in the preview card: the Build & Test chart's drawing, but it fills the card's
    remaining height (at least 180 px) instead of taking half its width, so the card fits the window."""
    from .charts import FanChart

    class PreviewFan(FanChart):
        # The approved draft's preview is a wide, short band across the card (draft_06_library.png), so the card's
        # width is used as it is; Build & Test keeps its own width cap and aspect.
        MAX_WIDTH = 16777215

        def hasHeightForWidth(self):
            return False

        def sizeHint(self):
            return QSize(min(self.MAX_WIDTH, max(self.minimumWidth(), self.width())), self._base_height)

    chart = PreviewFan()
    chart._base_height = 180
    chart.setMinimumHeight(180)
    chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    return chart


def search_icon(color, size=14):
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), 1.5)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.drawEllipse(QRectF(1.6, 1.6, 8.6, 8.6))
    painter.drawLine(QPointF(9.4, 9.4), QPointF(12.4, 12.4))
    painter.end()
    return QIcon(pixmap)


class Dot(QLabel):
    def __init__(self, state="none", parent=None):
        super().__init__(parent)
        self.setProperty("lib", "dot")
        self.setFixedSize(7, 7)
        self.set_state(state)

    def set_state(self, state):
        from .stock_detail_style import set_prop
        set_prop(self, "state", state)


class InfoGrid(QWidget):
    """The 실행 정보 grid: a caption over a value, two columns; a wide value spans both."""

    def __init__(self):
        super().__init__()
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(6, 0, 4, 0)
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(10)
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)
        self.language = "ko"

    def set_rows(self, rows, language):
        self.language = language
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget() is not None:
                item.widget().hide()
                item.widget().deleteLater()
        row = column = 0
        for caption, value, wide in rows:
            if wide and column:
                row, column = row + 1, 0
            cell = QWidget(self)                      # parented from the start (see CheckList.set_checks)
            cell.setProperty("lib", "plain")
            box = QVBoxLayout(cell)
            box.setContentsMargins(0, 0, 0, 0)
            box.setSpacing(3)
            key = Text(caption, "")
            key.setParent(cell)
            key.setProperty("lib", "key")
            text = Text(value, "", wrap=True, selectable=True)
            text.setParent(cell)
            text.setProperty("lib", "value")
            from .stock_detail_style import numbers
            numbers(text)
            for widget in (key, text):
                widget.set_language(language)
                box.addWidget(widget)
            self.grid.addWidget(cell, row, column, 1, 2 if wide else 1)
            column += 2 if wide else 1
            if column >= 2:
                row, column = row + 1, 0


class CheckList(QWidget):
    """The reproducibility checklist: a status dot, the item (with a quiet reason) and its recorded value."""

    def __init__(self):
        super().__init__()
        self.column = QVBoxLayout(self)
        self.column.setContentsMargins(6, 0, 4, 0)
        self.column.setSpacing(0)
        self.rows = []

    def set_checks(self, checks, language):
        for row in self.rows:
            row.hide()
            row.deleteLater()
        self.rows = []
        from .stock_detail_style import numbers
        for index, check in enumerate(checks):
            # Every piece has its parent from the start: a parentless widget that is polished or shown becomes a
            # window of its own for a moment and takes the activation from the main window.
            row = QFrame(self)
            row.setProperty("lib", "checkRow")
            row.setProperty("first", index == 0)
            line = QHBoxLayout(row)
            line.setContentsMargins(0, 6, 0, 6)
            line.setSpacing(8)
            dot = Dot(check.state, row)
            line.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)
            name = QWidget(row)
            name.setProperty("lib", "plain")
            words = QVBoxLayout(name)
            words.setContentsMargins(0, 0, 0, 0)
            words.setSpacing(1)
            title = Text(check.label, "", wrap=True)
            title.setParent(name)
            title.setProperty("lib", "check")
            words.addWidget(title)
            sub = Text(check.sub, "", wrap=True)
            sub.setParent(name)
            sub.setProperty("lib", "checkSub")
            words.addWidget(sub)
            sub.setVisible(bool(check.sub[0] or check.sub[1]))
            line.addWidget(name, 1)
            value = Text(check.value, "", selectable=True)
            value.setParent(row)
            value.setProperty("lib", "checkValue")
            value.setProperty("tone", "warn" if check.state == "warn" else "")
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            numbers(value)
            line.addWidget(value, 0, Qt.AlignmentFlag.AlignVCenter)
            for widget in (title, sub, value):
                widget.set_language(language)
            self.column.addWidget(row)
            self.rows.append(row)


# The run list --------------------------------------------------------------------------------------------------

# Column shares (the draft's grid: 1.3fr 1.55fr .95fr .8fr 1fr .78fr) for the full, medium and narrow lists.
COLUMNS = {
    "full": (("who", 1.2), ("model", 1.7), ("figure", .8), ("status", .85), ("verdict", .95), ("time", .7)),
    "medium": (("who", 1.35), ("model", 1.45), ("figure", .9), ("status", .95), ("time", .78)),
    "narrow": (("who", 1.35), ("figure", .85), ("status", 1.05), ("time", .75)),
}
HEADERS = {"who": ("Symbol", "종목 코드"), "model": ("Model · tool", "모델 · 도구"), "figure": ("Key figure", "핵심 수치"),
           "status": ("Run status", "실행 상태"), "verdict": ("Verdict", "검증 판정"), "time": ("Created · UTC", "생성 시각 · UTC")}
RIGHT = {"figure", "time"}
HEADER_H, ROW_H, GAP, PAD, EMPTY_H = 34, 46, 14, 10, 132


class RunList(QWidget):
    """The session's runs as rows (the draft's run grid), painted in one widget so the columns always line up.

    One tab stop: Up/Down/Home/End move the selection, a click selects a row. `selected(key)` is emitted for a
    choice the user made. Rows are filtered by kind (`set_kind`) and by a search text (`set_query`)."""
    selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setAccessibleName("Session runs")
        self.rows, self.shown = [], []
        self.kind, self.query = "all", ""
        self.current = ""
        self.hover = -1
        self.language = "ko"
        self.colors, self.dark = LIGHT, False
        self.empty_pair = ("", "")
        self._fit()

    # data -----------------------------------------------------------------------------------------------------
    def set_entries(self, rows):
        self.rows = list(rows)
        self._filter()

    def set_kind(self, kind):
        self.kind = kind
        self._filter()

    def set_query(self, query):
        self.query = str(query or "")
        self._filter()

    def set_empty(self, pair):
        self.empty_pair = pair
        self.update()

    def _filter(self):
        self.shown = [row for row in self.rows if (self.kind == "all" or row.kind == self.kind) and row.matches(self.query)]
        self.hover = -1
        self._fit()
        self._describe()
        self.update()

    def select(self, key, *, emit=False):
        self.current = key or ""
        self._describe()
        self.update()
        if emit:
            self.selected.emit(self.current)

    def entry(self, key=None):
        key = self.current if key is None else key
        return next((row for row in self.rows if row.key == key), None)

    def set_language(self, language):
        self.language = language
        self._describe()
        self.update()

    def set_theme(self, colors, dark):
        self.colors, self.dark = colors, bool(dark)
        self.update()

    # geometry ---------------------------------------------------------------------------------------------------
    def _fit(self):
        height = HEADER_H + (len(self.shown) * ROW_H if self.shown else EMPTY_H)
        if self.height() != height or self.minimumHeight() != height:
            self.setFixedHeight(height)

    def sizeHint(self):
        return QSize(640, self.height())

    def minimumSizeHint(self):
        return QSize(280, self.height())

    def layout_name(self):
        width = self.width() - 2 * PAD
        return "full" if width >= 700 else "medium" if width >= 500 else "narrow"

    def columns(self):
        spec = COLUMNS[self.layout_name()]
        inner = max(1, self.width() - 2 * PAD - GAP * (len(spec) - 1))
        total = sum(share for _, share in spec)
        x, out = float(PAD), []
        for name, share in spec:
            width = inner * share / total
            out.append((name, QRectF(x, 0, width, 0)))
            x += width + GAP
        return out

    def row_rect(self, index):
        return QRectF(0, HEADER_H + index * ROW_H + 1, self.width(), ROW_H - 2)

    def index_at(self, y):
        index = int((y - HEADER_H) // ROW_H)
        return index if y >= HEADER_H and 0 <= index < len(self.shown) else -1

    # interaction ------------------------------------------------------------------------------------------------
    def mouseMoveEvent(self, event):
        index = self.index_at(event.position().y())
        if index != self.hover:
            self.hover = index
            self.setCursor(Qt.CursorShape.PointingHandCursor if index >= 0 else Qt.CursorShape.ArrowCursor)
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.hover = -1
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        index = self.index_at(event.position().y())
        if event.button() == Qt.MouseButton.LeftButton and index >= 0:
            self.setFocus(Qt.FocusReason.MouseFocusReason)
            self.select(self.shown[index].key, emit=True)
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        keys = {Qt.Key.Key_Up: -1, Qt.Key.Key_Down: 1}
        if self.shown and event.key() in (*keys, Qt.Key.Key_Home, Qt.Key.Key_End):
            index = next((i for i, row in enumerate(self.shown) if row.key == self.current), -1)
            if event.key() == Qt.Key.Key_Home:
                index = 0
            elif event.key() == Qt.Key.Key_End:
                index = len(self.shown) - 1
            else:
                index = 0 if index < 0 else max(0, min(len(self.shown) - 1, index + keys[event.key()]))
            self.select(self.shown[index].key, emit=True)
            return
        super().keyPressEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.update()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.update()

    def event(self, event):
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.ToolTip:
            index = self.index_at(event.position().y() if hasattr(event, "position") else event.pos().y())
            if index >= 0:
                QToolTip.showText(event.globalPos(), self.describe(self.shown[index]), self)
            else:
                QToolTip.hideText()
            return True
        return super().event(event)

    def describe(self, row):
        p = lambda pair: pick(self.language, pair)
        status = STATUS_WORDS.get(row.status)
        parts = [p(row.symbol), p(row.symbol_sub), p(row.model), p(row.model_sub),
                 " ".join(x for x in (row.figure, p(row.figure_sub)) if x and x != "—") or row.figure,
                 p(status) if status else row.status, p(official_pair(row.verdict)), self._time(row)[0]]
        return " · ".join(part for part in parts if part)

    def _describe(self):
        row = self.entry()
        name = pick(self.language, ("Session runs", "이번 세션 실행"))
        self.setAccessibleName(name)
        self.setAccessibleDescription(self.describe(row) if row is not None else "")

    # painting ---------------------------------------------------------------------------------------------------
    def _fonts(self):
        from .font_policy import number_font
        from .typography import scaled_font
        base = self.font()
        return dict(head=scaled_font(base, 12, 400), sym=scaled_font(base, 14, 600), a=scaled_font(base, 13, 500),
                    b=scaled_font(base, 11, 400), pill=scaled_font(base, 12, 500), code=scaled_font(base, 11, 500),
                    num=number_font(scaled_font(base, 13, 500)), num_b=number_font(scaled_font(base, 11, 400)),
                    avatar=scaled_font(base, 11, 600))

    def _time(self, row):
        moment = parse_time(row.created_at)
        return (moment.strftime("%H:%M:%S"), moment.strftime("%m-%d")) if moment else ("—", "")

    def paintEvent(self, event):
        from .typography import TONE_COLORS, mix
        p, tones = self.colors, TONE_COLORS[self.dark]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        fonts = self._fonts()
        columns = self.columns()
        line = QColor(line_color(p))
        # Header
        painter.setFont(fonts["head"])
        painter.setPen(QColor(p.muted))
        for name, rect in columns:
            box = QRectF(rect.x(), 0, rect.width(), HEADER_H - 4)
            align = (Qt.AlignmentFlag.AlignRight if name in RIGHT else Qt.AlignmentFlag.AlignLeft) | Qt.AlignmentFlag.AlignVCenter
            caption = HEADERS[name] if name != "time" or self.layout_name() == "full" else ("UTC time", "UTC 시각")
            text = QFontMetrics(fonts["head"]).elidedText(pick(self.language, caption), Qt.TextElideMode.ElideRight,
                                                          int(box.width()))
            painter.drawText(box.adjusted(6 if name == "status" else 0, 0, 0, 0), align, text)
        painter.setPen(QPen(line, 1))
        painter.drawLine(QPointF(2, HEADER_H - 2.5), QPointF(self.width() - 2, HEADER_H - 2.5))
        if not self.shown:
            painter.setFont(fonts["a"])
            painter.setPen(QColor(p.muted))
            box = QRectF(24, HEADER_H, self.width() - 48, EMPTY_H)
            painter.drawText(box, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, pick(self.language, self.empty_pair))
            return
        for index, row in enumerate(self.shown):
            rect = self.row_rect(index)
            chosen = row.key == self.current
            if chosen or index == self.hover:
                path = QPainterPath()
                path.addRoundedRect(rect, 10, 10)
                painter.fillPath(path, QColor(p.accent_soft if chosen else mix(p.surface_2, p.surface, 0.45)))
                if chosen:
                    painter.save()
                    painter.setClipPath(path)
                    painter.fillRect(QRectF(rect.x(), rect.y(), 3, rect.height()), QColor(p.accent))
                    painter.restore()
                    if self.hasFocus():
                        painter.setPen(QPen(QColor(p.accent), 1.5))
                        painter.setBrush(Qt.BrushStyle.NoBrush)
                        painter.drawRoundedRect(rect.adjusted(0.75, 0.75, -0.75, -0.75), 10, 10)
            self._paint_row(painter, row, rect, columns, fonts, chosen, tones)

    def _two(self, painter, box, top, bottom, top_font, bottom_font, top_color, bottom_color, right=False):
        align = (Qt.AlignmentFlag.AlignRight if right else Qt.AlignmentFlag.AlignLeft)
        top_m, bottom_m = QFontMetrics(top_font), QFontMetrics(bottom_font)
        total = top_m.height() + (2 + bottom_m.height() if bottom else 0)
        y = box.center().y() - total / 2
        painter.setFont(top_font)
        painter.setPen(QColor(top_color))
        painter.drawText(QRectF(box.x(), y, box.width(), top_m.height()), align | Qt.AlignmentFlag.AlignVCenter,
                         top_m.elidedText(top, Qt.TextElideMode.ElideRight, int(box.width())))
        if bottom:
            painter.setFont(bottom_font)
            painter.setPen(QColor(bottom_color))
            painter.drawText(QRectF(box.x(), y + top_m.height() + 2, box.width(), bottom_m.height()),
                             align | Qt.AlignmentFlag.AlignVCenter,
                             bottom_m.elidedText(bottom, Qt.TextElideMode.ElideRight, int(box.width())))

    def _pill(self, painter, x, cy, max_width, word, code, fonts, fg, bg, dot=False):
        """A rounded pill at (x, centre y): an optional dot, a word and a quieter code. Returns its width."""
        word_m, code_m = QFontMetrics(fonts["pill"]), QFontMetrics(fonts["code"])
        inner = (11 if dot else 0) + (word_m.horizontalAdvance(word) if word else 0)
        if code:
            inner += (4 if word else 0) + code_m.horizontalAdvance(code)
        width = min(max_width, inner + 18)
        rect = QRectF(x, cy - 11, width, 22)
        path = QPainterPath()
        path.addRoundedRect(rect, 11, 11)
        painter.fillPath(path, QColor(bg))
        painter.save()
        painter.setClipRect(rect.adjusted(6, 0, -6, 0))
        tx = rect.x() + 9
        if dot:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(fg))
            painter.drawEllipse(QPointF(tx + 3, cy), 3, 3)
            tx += 11
        if word:
            painter.setFont(fonts["pill"])
            painter.setPen(QColor(fg))
            painter.drawText(QRectF(tx, rect.y(), rect.right() - tx, rect.height()),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, word)
            tx += word_m.horizontalAdvance(word) + 4
        if code:
            painter.setFont(fonts["code"])
            painter.setPen(QColor(faint(self.colors)))
            painter.drawText(QRectF(tx, rect.y(), max(0.0, rect.right() - tx), rect.height()),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                             code_m.elidedText(code, Qt.TextElideMode.ElideRight, int(max(0.0, rect.right() - 6 - tx))))
        painter.restore()
        return width

    def _avatar(self, painter, rect, row, fonts):
        from .company_identity import company_mark
        p = self.colors
        painter.save()
        painter.setPen(Qt.PenStyle.NoPen)
        if row.mark in ("portfolio", "strategy"):
            painter.setBrush(QColor(p.surface_2))
            painter.drawEllipse(rect)
            c = rect.center()
            if row.mark == "portfolio":
                from .typography import mix
                tiles = ((-6, -6, p.accent), (1, -6, mix(p.accent, p.surface, 0.45)),
                         (-6, 1, mix(p.accent, p.surface, 0.45)), (1, 1, mix(p.accent, p.surface, 0.7)))
                for dx, dy, color in tiles:
                    painter.setBrush(QColor(color))
                    painter.drawRoundedRect(QRectF(c.x() + dx, c.y() + dy, 5, 5), 1.2, 1.2)
            else:
                pen = QPen(QColor(p.accent), 1.7)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                path = QPainterPath(QPointF(c.x() - 7, c.y() + 4))
                for dx, dy in ((-3, 0), (0, 2), (6, -4)):
                    path.lineTo(QPointF(c.x() + dx, c.y() + dy))
                painter.drawPath(path)
        else:
            mark = company_mark(str(row.mark))
            # The shared letter marks are drawn for light surfaces; the dark theme keeps the plain mark.
            known = mark.background not in ("#E9ECE8", "#E7EDE8") and not self.dark
            letters = mark.letters if known else (str(row.mark)[:1].upper() or "?")
            painter.setBrush(QColor(mark.background if known else p.surface_2))
            painter.drawEllipse(rect)
            painter.setFont(fonts["avatar"])
            painter.setPen(QColor(mark.foreground if known else p.accent))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, letters)
        painter.restore()

    def _paint_row(self, painter, row, rect, columns, fonts, chosen, tones):
        from .typography import mix
        p = self.colors
        cy = rect.center().y()
        muted, text = p.muted, p.text
        for name, column in columns:
            box = QRectF(column.x(), rect.y(), column.width(), rect.height())
            if name == "who":
                avatar = QRectF(box.x(), cy - 15, 30, 30)
                self._avatar(painter, avatar, row, fonts)
                sub = pick(self.language, row.symbol_sub)
                if self.layout_name() == "narrow":
                    sub = pick(self.language, row.model)
                self._two(painter, box.adjusted(40, 0, 0, 0), pick(self.language, row.symbol), sub,
                          fonts["sym"], fonts["b"], text, muted)
            elif name == "model":
                self._two(painter, box, pick(self.language, row.model), pick(self.language, row.model_sub),
                          fonts["a"], fonts["b"], text, muted)
            elif name == "figure":
                color = tones[row.figure_tone] if row.figure_tone in ("up", "down") else (muted if row.figure == "—" else text)
                self._two(painter, box, row.figure, pick(self.language, row.figure_sub), fonts["num"], fonts["b"],
                          color, muted, right=True)
            elif name == "status":
                word = STATUS_WORDS.get(row.status)
                if row.status == "COMPLETED":
                    fg, bg = p.success, mix(p.accent_soft, p.success, 0.12 if chosen else 0.04)
                elif row.status == "FAILED":
                    fg, bg = p.error, tones["up_tint"]
                else:
                    fg, bg = p.accent, mix(p.surface_2, p.accent, 0.06) if chosen else p.surface_2
                layout = self.layout_name()
                y = cy if layout == "full" else cy - 8
                inset = 6 if layout == "full" else 0
                self._pill(painter, box.x() + inset, y, box.width() - inset, pick(self.language, word) if word else row.status,
                           "", fonts, fg, bg, dot=layout == "full")
                if layout != "full":
                    verdict_word, code = official(row.verdict)
                    painter.setFont(fonts["code"])
                    painter.setPen(QColor(faint(p)))
                    painter.drawText(QRectF(box.x() + inset + 2, cy + 6, box.width() - 8, 16),
                                     Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                                     QFontMetrics(fonts["code"]).elidedText(code, Qt.TextElideMode.ElideRight,
                                                                            int(box.width() - 8)))
            elif name == "verdict":
                word, code = official(row.verdict)
                bg = mix(p.surface_2, p.accent, 0.06) if chosen else p.surface_2
                if self.language == "ko" and word:      # 미실행 NOT_RUN: the Korean word beside the code
                    self._pill(painter, box.x(), cy, box.width(), word[1], code, fonts, muted, bg)
                else:                                    # in English the code is the word
                    self._pill(painter, box.x(), cy, box.width(), code, "", fonts, muted, bg)
            elif name == "time":
                clock, day = self._time(row)
                if row.saved:
                    self._two(painter, box, clock, "", fonts["num"], fonts["b"], text, muted, right=True)
                    m = QFontMetrics(fonts["b"])
                    word = pick(self.language, ("Saved", "저장함"))
                    width = m.horizontalAdvance(word)
                    top_h = QFontMetrics(fonts["num"]).height()
                    y = cy - (top_h + 2 + m.height()) / 2 + top_h + 2
                    painter.setFont(fonts["b"])
                    painter.setPen(QColor(p.success))
                    painter.drawText(QRectF(box.right() - width, y, width, m.height()),
                                     Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, word)
                    pen = QPen(QColor(p.success), 1.5)
                    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                    painter.setPen(pen)
                    mid = y + m.height() / 2
                    x = box.right() - width - 12
                    painter.drawPolyline([QPointF(x, mid), QPointF(x + 2.6, mid + 2.6), QPointF(x + 8, mid - 3)])
                else:
                    self._two(painter, box, clock, day, fonts["num"], fonts["num_b"], text, muted, right=True)


__all__ = ["Entry", "entries", "run_entry", "portfolio_entry", "strategy_entry", "counts", "run_info", "evidence",
           "Check", "payload_summary", "LibraryWorkspace", "RunList", "InfoGrid", "CheckList", "Dot", "search_icon",
           "library_sheet", "KIND_NAMES", "STATUS_WORDS", "official_pair", "signed_pct", "parse_time", "statistics"]
