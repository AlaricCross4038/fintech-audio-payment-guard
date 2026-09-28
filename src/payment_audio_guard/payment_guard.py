"""Deterministic payment policy and audit record construction."""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class PaymentEvent(BaseModel):
    event_id: str = Field(min_length=1)
    amount: Decimal = Field(gt=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    beneficiary: str = Field(min_length=1)
    is_new_beneficiary: bool


class Action(str, Enum):
    RELEASE = "release"
    MANUAL_REVIEW = "manual_review"


class AuditNotification(BaseModel):
    event_id: str
    action: Action
    reasons: list[str]
    transcript: str
    recorded_at: datetime


URGENT_PAYMENT_TERMS = ("urgent", "immediately", "today only", "skip approval")
HIGH_VALUE = Decimal("10000")


def decide_payment(event: PaymentEvent, transcript: str) -> AuditNotification:
    """Return the visible state transition and the evidence that caused it."""
    normalized = transcript.casefold()
    reasons: list[str] = []

    if event.amount >= HIGH_VALUE:
        reasons.append("high_value")
    if event.is_new_beneficiary:
        reasons.append("new_beneficiary")
    if any(term in normalized for term in URGENT_PAYMENT_TERMS):
        reasons.append("urgent_language")

    action = (
        Action.MANUAL_REVIEW
        if {"high_value", "new_beneficiary", "urgent_language"}.issubset(reasons)
        else Action.RELEASE
    )
    return AuditNotification(
        event_id=event.event_id,
        action=action,
        reasons=reasons,
        transcript=transcript,
        recorded_at=datetime.now(timezone.utc),
    )
