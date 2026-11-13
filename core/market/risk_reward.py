"""User-authored price scenarios. No signal, fill prediction, position sizing or order path."""
from dataclasses import dataclass, replace
import math


@dataclass(frozen=True)
class RiskRewardPlan:
    direction: str
    entry: float
    stop: float
    target: float

    @property
    def error(self):
        if self.direction not in ("long", "short"):
            return "direction"
        if not all(math.isfinite(v) and v > 0 for v in (self.entry, self.stop, self.target)):
            return "price"
        if self.direction == "long" and not self.stop < self.entry < self.target:
            return "long_order"
        if self.direction == "short" and not self.target < self.entry < self.stop:
            return "short_order"
        return ""

    @property
    def metrics(self):
        if self.error:
            return None
        risk, reward = abs(self.entry - self.stop), abs(self.target - self.entry)
        return {"risk": risk, "reward": reward, "ratio": reward / risk,
                "risk_pct": risk / self.entry * 100, "reward_pct": reward / self.entry * 100}

    def moved(self, field, price):
        if field == "entry":
            shift = price - self.entry
            return replace(self, entry=price, stop=self.stop + shift, target=self.target + shift)
        if field not in ("stop", "target"):
            raise ValueError("Unknown price level")
        return replace(self, **{field: price})
