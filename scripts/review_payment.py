"""Submit one local audio file to the running review service."""

import argparse
import base64

import httpx


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("audio", help="Path to a WAV or MP3 payment call")
    args = parser.parse_args()
    audio_format = args.audio.rsplit(".", 1)[-1].lower()
    with open(args.audio, "rb") as recording:
        encoded = base64.b64encode(recording.read()).decode("ascii")

    response = httpx.post(
        "http://127.0.0.1:8000/payment-events/review",
        json={
            "payment": {
                "event_id": "pay_1042",
                "amount": "12500",
                "currency": "USD",
                "beneficiary": "Northwind Imports",
                "is_new_beneficiary": True,
            },
            "audio_base64": encoded,
            "audio_format": audio_format,
        },
        timeout=1200.0,
    )
    response.raise_for_status()
    print(response.json())


if __name__ == "__main__":
    main()
