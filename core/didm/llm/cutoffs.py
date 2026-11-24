"""DIDM-3 model training cutoffs: the look-ahead rule of PREREG_V0 section 5, made executable.

Rule (PREREG_V0 5.2-5.4, owner answer P4):

* Every model has a training cutoff with a public source. No public cutoff -> the model
  is not used for historical validation.
* In-house model: cutoff = the later of the base model's pre-training cutoff and the
  last day of the fine-tuning data. If either is unknown the cutoff is unknown.
* A model's scores validate only articles dated on or after cutoff + 3 months. The article's
  date is the EARLIER of the day it was published and the day we received it: an old article
  fetched today has a received_at of today (PREREG_V0 5.1), but the model may have been trained
  on it, so the publication day decides.
* The same rule holds for commercial API models; nothing here loosens it.
* The baselines PREREG_V0 5.4 names for the period before an LLM's cutoff (the
  Loughran-McDonald dictionary, FinBERT) are usable at any article date, but only as a
  pinned, sourced snapshot, and only under the keys in BASELINE_KEYS: labelling some other
  model a baseline does not exempt it.

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
# The only models PREREG_V0 5.4 names as usable before an LLM's cutoff without a cutoff of their own.
BASELINE_KEYS = frozenset({"loughran-mcdonald", "ProsusAI/finbert"})


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

    def __post_init__(self) -> None:
        if self.rule is Rule.BASELINE and (self.cutoff is not None or self.in_house
                                           or self.base_cutoff is not None or self.finetune_through is not None):
            raise CutoffError("a baseline card carries no cutoff; a model with a cutoff follows the cutoff rule")

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
        if self.rule is Rule.BASELINE:
            return self.key in BASELINE_KEYS
        return self.effective_cutoff is not None

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


def _utc_day(value: date | datetime, name: str) -> date:
    """The UTC calendar day of a timestamp. A datetime must carry a timezone."""
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise CutoffError(f"{name} must carry a timezone")
        return value.astimezone(timezone.utc).date()
    if isinstance(value, date):
        return value
    raise CutoffError(f"{name} must be a date or a timezone-aware datetime")


def article_day(published_at: date | datetime, received_at: date | datetime) -> date:
    """The day the cutoff rule compares: the earlier of the publication day and the receipt day (UTC)."""
    return min(_utc_day(published_at, "published_at"), _utc_day(received_at, "received_at"))


def eligibility(card: ModelCard | None, *, published_at: date | datetime,
                received_at: date | datetime) -> Eligibility:
    """May this model's score validate this article? Fails closed.

    Both timestamps are required and the earlier day decides, so a backfilled article (published
    before the model's cutoff, received today) is not eligible.
    """
    day = article_day(published_at, received_at)
    if card is None:
        return Eligibility(False, "model is not in the cutoff registry")
    if not card.verified:
        return Eligibility(False, "no verified public cutoff: not used for historical validation")
    if card.rule is Rule.BASELINE:
        return Eligibility(True, "baseline named in PREREG_V0 5.4")
    first = card.eligible_from
    if day >= first:
        return Eligibility(True, f"published and received on or after cutoff + {MARGIN_MONTHS} months", first)
    return Eligibility(False, f"published or received before cutoff + {MARGIN_MONTHS} months ({first.isoformat()})",
                       first)


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

    def eligibility(self, model_version: str, *, published_at: date | datetime,
                    received_at: date | datetime) -> Eligibility:
        return eligibility(self.get(model_version), published_at=published_at, received_at=received_at)

    def with_card(self, card: ModelCard) -> "Registry":
        return Registry((*self._cards.values(), card))


# --- the registry (twin of docs/didm/MODEL_CUTOFFS.md) ---

_ANTHROPIC_URL = "https://platform.claude.com/docs/en/about-claude/models/overview"
_CHRONO_PAPER = "https://arxiv.org/abs/2502.21206"
_CHECKED = date(2026, 11, 24)

# ChronoGPT vintage year -> commit of huggingface.co/manelalab/chrono-gpt-v1-<year>1231 (read 2026-11-24).
_CHRONO_COMMITS = {
    1999: "45d6568340081add5c5b1444feb17a94b8f8199d", 2000: "aab8e7f10ffc8a63b557d47ceeca0712ddc0fdfa",
    2001: "84f4d197fc931bb3cc39d1a071e8436304890921", 2002: "4b48afa531ff3d530b0273e5c64b8ad1381016e4",
    2003: "6aba09104ca8ccb8febb2a29d2e4c8bb99526638", 2004: "f446364b14657b8f77d864bd305e7caea5e5e209",
    2005: "64a190a1eba9d0bd4a320225284ceb8376634cda", 2006: "a0a130d03014401d9f7370c50537f49c128da78d",
    2007: "ca382535273b9f3a6d5ff476f565246b8c90fa07", 2008: "020fcd3af211e574905941a369f9635bca53a8d6",
    2009: "0c7124691ed3fb527af12dab7013eac1ae56fec7", 2010: "4fb687ab4b3029e5d364423434e6f20019b1b222",
    2011: "ea5aaed9f362885f367514b067a36cc4faa0ce5e", 2012: "67a896b02f6cdcd2e99d62866a2d334eeaeb99b5",
    2013: "6f2e595689458b1809d5c6efb9a6095257347ca2", 2014: "4fba07f4ef563b3addf2b05f385d0b347bf1cc0d",
    2015: "aacd4c4e8020dd0ad686d36f18bcf34cd8003bc3", 2016: "20d93dc9b103644b212db413db4ab1207063d010",
    2017: "4cc4334a2c2d38ae35deb0bb7fcae642d3f73a10", 2018: "17d7de7945199ff03be989ca84d00c0f59a975af",
    2019: "7e62517f31b11fad179c79ce79a465aa00c7ee4d", 2020: "c0d2acbd2a378ac79d8a5ae79a9447d23145eb8a",
    2021: "a070953708ee809e630e4d9652e9c753d7b6782e", 2022: "993711fdf078740fe1c837a3687528e2173443d2",
    2023: "8ac22e54d37df8bb8037622680414118239fbe53", 2024: "1d9f1b8ff50bb45a6fe1402280e617af4c2d805c",
}


def _claude(key: str) -> ModelCard:
    # The page gives the training data cutoff as a month ("Jun 2026"); a month counts to its last day.
    return ModelCard(key=key, family="Claude (API)", rule=Rule.CUTOFF, snapshot_id=key,
                     cutoff=cutoff_from_text("2026-06"), source_url=_ANTHROPIC_URL, checked_on=_CHECKED,
                     note="출처 표의 Training data cutoff = Jun 2026; 모델 ID가 곧 고정 스냅샷")


def _chrono(year: int, commit: str) -> ModelCard:
    # Paper Table 1 gives "December, 1999" ... "December, 2024"; one checkpoint per year in between.
    return ModelCard(key=f"manelalab/chrono-gpt-v1-{year}1231", family="ChronoGPT 빈티지", rule=Rule.CUTOFF,
                     snapshot_id=commit, cutoff=cutoff_from_text(f"{year}-12"), source_url=_CHRONO_PAPER,
                     checked_on=_CHECKED, note="논문 표 1의 Knowledge Cutoff = December, <연도>")


REGISTRY = Registry((
    ModelCard(key="loughran-mcdonald", family="Loughran-McDonald 사전", rule=Rule.BASELINE,
              snapshot_id="Loughran-McDonald_MasterDictionary_1993-2025.csv (Updated: March, 2026)",
              source_url="https://sraf.nd.edu/loughranmcdonald-master-dictionary/", checked_on=_CHECKED,
              note="사전 판 1993-2025; 학술 연구는 무료, 상업 이용은 별도 허가"),
    ModelCard(key="ProsusAI/finbert", family="FinBERT", rule=Rule.BASELINE,
              snapshot_id="0bc2ac10dda6929bcb1f77ccc43c7ec5c424f031",
              source_url="https://huggingface.co/ProsusAI/finbert", checked_on=_CHECKED,
              note="모델 카드에 마감일 문구 없음; 가중치 라이선스 CC BY-NC-SA 4.0 (비상업)"),
    *(_chrono(year, commit) for year, commit in _CHRONO_COMMITS.items()),
    ModelCard(key="qwen3-candidates", family="Qwen3 후보", rule=Rule.CUTOFF,
              note="모델 카드(Qwen/Qwen3-8B)와 기술 보고서(arXiv 2505.09388)에 학습 마감일 문구 없음"),
    _claude("claude-fable-5-2"),
    _claude("claude-opus-5-5"),
    _claude("claude-sonnet-5-5"),
    _claude("claude-haiku-5-5"),
    ModelCard(key="quantgpt-in-house", family="자체 LLM", rule=Rule.CUTOFF, in_house=True,
              note="기반 모델과 미세조정 자료가 아직 정해지지 않음 (QUANTGPT 세션)"),
))
