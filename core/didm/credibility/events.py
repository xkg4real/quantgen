"""Which reports are about the same claim: the event key of the credibility state (DIDM-9, choice C9).

Decision (main session, 2026-11-24; owner question 14 in docs/didm/PREREG_V0_1_PROPOSAL_2026-11-24.md):

    event = target + event type + first-report window

A report joins the open event of its target and event type if it is received within EVENT_WINDOW of
that event's FIRST report; otherwise it starts a new event. The origin cluster is not part of the key:
independent outlets reporting the same claim must add up in the credibility state, and the origin
cluster is used inside an event only to stop re-publications from counting twice.

Online and point-in-time: reports are taken in order of receipt, so a report's event never depends on
anything received after it. No model, no network, no clock.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Sequence

EVENT_WINDOW = timedelta(days=7)          # same value as the clustering look-back (ENTITIES_V0 E2); not registered


class EventError(ValueError):
    pass


@dataclass(frozen=True)
class EventKeyConfig:
    """The reading of "same claim" (choice C9). The default is the decision above; the other two are the
    alternatives put to the owner (question 14) and exist so that the difference can be shown and tested.

    first_report_window : target + event type, within ``window`` of the event's first report (default)
    calendar_day        : target + event type + UTC calendar day of receipt
    with_origin         : target + event type + origin cluster, within ``window`` (independent outlets
                          never add up)
    """
    mode: str = "first_report_window"
    window: timedelta = timedelta(days=7)

    def __post_init__(self) -> None:
        if self.mode not in ("first_report_window", "calendar_day", "with_origin"):
            raise EventError("mode is first_report_window, calendar_day or with_origin")
        if self.window <= timedelta(0):
            raise EventError("window must be positive")


@dataclass(frozen=True)
class Mention:
    article_id: str
    entity_id: str
    event_type: str
    received_at: datetime
    origin_cluster_id: str = ""        # only read by the with_origin alternative


def event_id(entity_id: str, event_type: str, first_article_id: str) -> str:
    digest = hashlib.sha256(f"{entity_id}|{event_type}|{first_article_id}".encode("utf-8")).hexdigest()
    return "ev-" + digest[:20]


def assign(mentions: Sequence[Mention], *, config: EventKeyConfig | None = None) -> dict[tuple[str, str], str]:
    """(article_id, entity_id) -> event id."""
    config = config or EventKeyConfig(window=EVENT_WINDOW)
    window = config.window
    keys = [(m.article_id, m.entity_id) for m in mentions]
    if len(set(keys)) != len(keys):
        raise EventError("an article mentions the same target twice")
    for m in mentions:
        if not isinstance(m.received_at, datetime) or m.received_at.tzinfo is None:
            raise EventError("received_at must be a timezone-aware datetime")
    open_event: dict[tuple, tuple[datetime, str]] = {}                # slot -> (first report time, event id)
    out: dict[tuple[str, str], str] = {}
    for m in sorted(mentions, key=lambda m: (m.received_at.astimezone(timezone.utc), m.article_id, m.entity_id)):
        when = m.received_at.astimezone(timezone.utc)
        if config.mode == "calendar_day":
            slot = (m.entity_id, m.event_type, when.date().isoformat())
        elif config.mode == "with_origin":
            slot = (m.entity_id, m.event_type, m.origin_cluster_id)
        else:
            slot = (m.entity_id, m.event_type)
        current = open_event.get(slot)
        if current is None or m.received_at - current[0] > window:
            current = (m.received_at, event_id(m.entity_id, m.event_type, m.article_id))
            open_event[slot] = current
        out[(m.article_id, m.entity_id)] = current[1]
    return out
