from fastapi.testclient import TestClient

from payment_audio_guard.payment_intake import create_service


class CallRecording:
    def transcribe(self, audio_base64: str, audio_format: str) -> str:
        assert audio_base64 == "cGF5bWVudCBjYWxs"
        assert audio_format == "wav"
        return "Send 12500 USD to Northwind immediately and skip approval."


def test_risky_payment_call_is_held_with_audit_reasons() -> None:
    client = TestClient(create_service(CallRecording()))

    response = client.post(
        "/payment-events/review",
        json={
            "payment": {
                "event_id": "pay_1042",
                "amount": "12500",
                "currency": "USD",
                "beneficiary": "Northwind Imports",
                "is_new_beneficiary": True,
            },
            "audio_base64": "cGF5bWVudCBjYWxs",
            "audio_format": "wav",
        },
    )

    assert response.status_code == 200
    audit = response.json()
    assert audit["action"] == "manual_review"
    assert audit["reasons"] == [
        "high_value",
        "new_beneficiary",
        "urgent_language",
    ]
    assert audit["event_id"] == "pay_1042"
