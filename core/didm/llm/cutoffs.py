"""DIDM-3 model training cutoffs: the look-ahead rule of PREREG_V0 section 5, made executable.

Rule (PREREG_V0 5.2-5.4, owner answer P4):

* Every model has a training cutoff with a public source. No public cutoff -> the model
  is not used for historical validation.
* In-house model: cutoff = the later of the base model's pre-training cutoff and the
  last day of the fine-tuning data. If either is unknown the cutoff is unknown.
* A model's scores validate only articles received on or after cutoff + 3 months.
* The same rule holds for commercial API models; nothing here loosens it.
* The baselines PREREG_V0 5.4 names for the period before an LLM's cutoff (the
  Loughran-McDonald dictionary, FinBERT) are usable at any article date, but only as a
  pinned, sourced snapshot.

The registry below is the machine-readable twin of docs/didm/MODEL_CUTOFFS.md; the
acceptance test compares the two. A row is "verified" only with a snapshot id, a source
URL, the day it was checked and (for the cutoff rule) a cutoff. Anything else is not
eligible. Cutoffs are never guessed: an unstated cutoff stays None.

Standard library only; no network, no clock reads.
"""
from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import Enum

MARGIN_MONTHS = 3            # PREREG_V0 5.3, owner answer P4 (2026-11-18)
NOT_VERIFIED = "미검증, 자격 없음"


class CutoffError(ValueError):
    pass


class Rule(str, Enum):
    CUTOFF = "cutoff"                    # eligible from cutoff + 3 months
    BASELINE = "prereg-5.4-baseline"     # named in PREREG_V0 5.4; eligible at any date once pinned


@dataclass(frozen=True)
class ModelCard:
    key: str                         # the model_version a scorer reports (ScorerInfo.model_version)
    family: str
    rule: Rule
    snapshot_id: str | None = None   # pinned snapshot: API model id, repository commit, file version
    cutoff: date | None = None       # last day of training data, as the publisher states it
    source_url: str | None = None
    checked_on: date | None = None
    # In-house (fine-tuned) models only: both parts, each from its own source.
    base_cutoff: date | None = None
    finetune_through: date | None = None
    in_house: bool = False
    note: str = ""

    @property
    def effective_cutoff(self) -> date | None:
        if self.in_house:
            if self.base_cutoff is None or self.finetune_through is None:
                return None
            return max(self.base_cutoff, self.finetune_through)
        return self.cutoff

    @property
    def verified(self) -> bool:
        if not (self.snapshot_id and self.source_url and self.checked_on):
            return False
        return self.rule is Rule.BASELINE or self.effective_cutoff is not None

    @property
    def eligible_from(self) -> date | None:
        """First article day this model may validate; None = never (or any day for a baseline)."""
        if not self.verified or self.rule is Rule.BASELINE:
            return None
        return add_months(self.effective_cutoff, MARGIN_MONTHS)


@dataclass(frozen=True)
class Eligibility:
    eligible: bool
    reason: str
    eligible_from: date | None = None


def add_months(day: date, months: int) -> date:
    """Calendar months later, clamped to the month's last day (2023-11-30 + 3 = 2024-02-29)."""
    if isinstance(day, datetime) or not isinstance(day, date):
        raise CutoffError("day must be a date")
    if isinstance(months, bool) or not isinstance(months, int) or months < 0:
        raise CutoffError("months must be a non-negative integer")
    index = day.year * 12 + (day.month - 1) + months
    year, month = divmod(index, 12)
    month += 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


_MONTH = re.compile(r"^(\d{4})-(\d{2})$")
_DAY = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def cutoff_from_text(text: str) -> date:
    """"2025-03" -> 2025-03-31 (a month-only cutoff counts to the month's last day); "2023-12-31" as is."""
    if not isinstance(text, str):
        raise CutoffError("cutoff must be text like 2025-03 or 2025-03-31")
    try:
        if m := _DAY.fullmatch(text):
            return date(int(m[1]), int(m[2]), int(m[3]))
        if m := _MONTH.fullmatch(text):
            year, month = int(m[1]), int(m[2])
            return date(year, month, calendar.monthrange(year, month)[1])
    except (ValueError, calendar.IllegalMonthError):
        pass
    raise CutoffError(f"not a cutoff date: {text!r}")


def in_house_card(key: str, *, base: ModelCard, finetune_through: date | None, snapshot_id: str | None,
                  source_url: str | None, checked_on: date | None, note: str = "") -> ModelCard:
    """A card for a fine-tuned model: cutoff = later of the base cutoff and the fine-tuning data's last day.

    An unverified base (no public cutoff) makes the fine-tuned model unverified too, whatever the
    fine-tuning data's dates are.
    """
    if not isinstance(base, ModelCard):
        raise CutoffError("base must be a ModelCard")
    if base.rule is not Rule.CUTOFF:
        raise CutoffError("the base of an in-house model must follow the cutoff rule")
    return ModelCard(
        key=key, family="in-house", rule=Rule.CUTOFF, snapshot_id=snapshot_id,
        source_url=source_url, checked_on=checked_on, in_house=True,
        base_cutoff=base.effective_cutoff if base.verified else None,
        finetune_through=finetune_through, note=note or f"base {base.key}",
    )


def article_day(received_at: date | datetime) -> date:
    """The UTC calendar day an article was received. A datetime must carry a timezone."""
    if isinstance(received_at, datetime):
        if received_at.tzinfo is None or received_at.utcoffset() is None:
            raise CutoffError("received_at must carry a timezone")
        return received_at.astimezone(timezone.utc).date()
    if isinstance(received_at, date):
        return received_at
    raise CutoffError("received_at must be a date or a timezone-aware datetime")


def eligibility(card: ModelCard | None, received_at: date | datetime) -> Eligibility:
    """May this model's score validate an article received at ``received_at``? Fails closed."""
    day = article_day(received_at)
    if card is None:
        return Eligibility(False, "model is not in the cutoff registry")
    if not card.verified:
        return Eligibility(False, "no verified public cutoff: not used for historical validation")
    if card.rule is Rule.BASELINE:
        return Eligibility(True, "baseline named in PREREG_V0 5.4")
    first = card.eligible_from
    if day >= first:
        return Eligibility(True, f"received on or after cutoff + {MARGIN_MONTHS} months", first)
    return Eligibility(False, f"received before cutoff + {MARGIN_MONTHS} months ({first.isoformat()})", first)


class Registry:
    def __init__(self, cards: tuple[ModelCard, ...]):
        keys = [c.key for c in cards]
        if len(keys) != len(set(keys)):
            raise CutoffError("duplicate model key in the cutoff registry")
        self._cards = {c.key: c for c in cards}

    def __iter__(self):
        return iter(self._cards.values())

    def __len__(self) -> int:
        return len(self._cards)

    def get(self, model_version: str) -> ModelCard | None:
        return self._cards.get(model_version)

    def eligibility(self, model_version: str, received_at: date | datetime) -> Eligibility:
        return eligibility(self.get(model_version), received_at)

    def with_card(self, card: ModelCard) -> "Registry":
        return Registry((*self._cards.values(), card))


# --- the registry (twin of docs/didm/MODEL_CUTOFFS.md) ---

_ANTHROPIC_URL = "https://platform.claude.com/docs/en/about-claude/models/overview"
_CHECKED = date(2026, 11, 24)
_BLOCKED = "출처 페이지를 열지 못함 (세션 네트워크 정책이 호스트를 막음, 2026-11-24)"


def _claude(key: str) -> ModelCard:
    # The page gives the training data cutoff as a month ("Jun 2026"); a month counts to its last day.
    return ModelCard(key=key, family="Claude (API)", rule=Rule.CUTOFF, snapshot_id=key,
                     cutoff=cutoff_from_text("2026-06"), source_url=_ANTHROPIC_URL, checked_on=_CHECKED,
                     note="출처 표의 Training data cutoff = Jun 2026; 모델 ID가 곧 고정 스냅샷")


REGISTRY = Registry((
    ModelCard(key="loughran-mcdonald", family="Loughran-McDonald 사전", rule=Rule.BASELINE, note=_BLOCKED),
    ModelCard(key="ProsusAI/finbert", family="FinBERT", rule=Rule.BASELINE, note=_BLOCKED),
    ModelCard(key="chronogpt-vintages", family="ChronoGPT 빈티지", rule=Rule.CUTOFF, note=_BLOCKED),
    ModelCard(key="qwen3-candidates", family="Qwen3 후보", rule=Rule.CUTOFF, note=_BLOCKED),
    _claude("claude-fable-5-2"),
    _claude("claude-opus-5-5"),
    _claude("claude-sonnet-5-5"),
    _claude("claude-haiku-5-5"),
    ModelCard(key="quantgpt-in-house", family="자체 LLM", rule=Rule.CUTOFF, in_house=True,
              note="기반 모델과 미세조정 자료가 아직 정해지지 않음 (QUANTGPT 세션)"),
))
