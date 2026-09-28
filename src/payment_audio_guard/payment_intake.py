"""Typed HTTP boundary for payment-call review."""

from typing import Protocol

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .fintech_transcriber import FintechTranscriber
from .payment_guard import AuditNotification, PaymentEvent, decide_payment


class Transcriber(Protocol):
    def transcribe(self, audio_base64: str, audio_format: str) -> str:
        """Return spoken text from encoded audio."""


class PaymentCallRequest(BaseModel):
    payment: PaymentEvent
    audio_base64: str = Field(min_length=1)
    audio_format: str = Field(pattern=r"^(wav|mp3)$")


def create_service(transcriber: Transcriber | None = None) -> FastAPI:
    service = FastAPI(title="Payment audio guard")

    @service.post("/payment-events/review", response_model=AuditNotification)
    def review_payment(request: PaymentCallRequest) -> AuditNotification:
        active_transcriber = transcriber or FintechTranscriber()
        transcript = active_transcriber.transcribe(
            request.audio_base64, request.audio_format
        )
        return decide_payment(request.payment, transcript)

    return service


app = create_service()
