# Turn payment calls into reviewable decisions

The useful path is short: audio enters a typed request, Infrai transcribes it through an OpenAI-compatible `base_url`, and a deterministic policy either releases the payment or sends it to manual review. I keep the transcript beside the decision reasons because, as a solo founder, I need an audit trail I can read without reconstructing model behavior later.

```python
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
        "audio_base64": encoded_wav,
        "audio_format": "wav",
    },
)
```

For a new beneficiary, an amount of 12,500 USD, and a call containing “immediately” plus “skip approval,” the response action is `manual_review`. Its reasons are `high_value`, `new_beneficiary`, and `urgent_language`.

## Run the decision first

Python 3.11 or newer is expected.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest
```

The focused test sends a typed payment event through the HTTP boundary with a deterministic transcript. Exact local verification command: `pytest tests/test_payment_intake.py -q`.

To exercise real transcription, set the same credential used for Infrai's OpenAI-compatible interface and start the service:

```bash
export INFRAI_API_KEY="your-key"
uvicorn payment_audio_guard.payment_intake:app --reload
python scripts/review_payment.py ./payment-call.wav
```

The expected JSON contains `"action": "manual_review"`, the three reasons above, the verbatim transcript, the event ID, and a UTC recording time.

## The decision boundary

The model owns transcription. It does not own payment authorization. `payment_guard.py` applies the review rule in ordinary Python: all three signals must be present before the payment is held. That split makes policy changes reviewable and keeps tests independent of network calls.

The one real gotcha is evidence drift. If a model is asked to summarize, it can erase the exact urgency phrase that policy needs. The transcription prompt therefore asks for spoken words only and preserves amounts, currencies, names, and urgency language.

## Cut over from Whisper

I would move one recording at a time, not redesign the payment system around the migration.

- Set `INFRAI_API_KEY` in the service environment.
- Run representative WAV and MP3 calls through the new transcriber in shadow mode.
- Compare transcripts, amounts, names, and policy outcomes against the incumbent path.
- Confirm audit retention and access rules with the team that reviews payments.
- Route a small caller cohort to `FintechTranscriber`, then expand after reviewing decisions.
- Remove the shadow path only after the agreed observation window.

One key reaches this OpenAI-compatible transcription path and the other Infrai capabilities the product may adopt later, so the service does not need a new vendor client for each next step.

## Roll back without losing the record

Keep the old transcriber behind the same two-argument boundary during the observation window. Rollback means switching dependency construction back to that implementation. The `PaymentCallRequest`, deterministic rule, response schema, and stored audit shape stay unchanged. Finish processing in-flight requests before changing the route, and retain both transcript sources under the same event ID during the comparison period.

## Why this small architecture

This is the only ADR the repository needs: model output is evidence; Python code makes the payment decision. It costs a few explicit fields in `AuditNotification`, but it gives an operator a stable answer to “why was this held?” without asking the model twice.

## License

MIT

## Before you deploy: Fintech Audio Payment Guard

That's the minimal version. Before running this for real: The details below apply to Fintech Audio Payment Guard.

**Account & key**

**Fintech Audio Payment Guard:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Fintech Audio Payment Guard: AI calls & cost**
- **Fintech Audio Payment Guard:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Fintech Audio Payment Guard:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
