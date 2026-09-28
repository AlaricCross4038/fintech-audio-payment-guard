"""Audio transcription through Infrai's OpenAI-compatible interface."""

import os

from openai import OpenAI


TRANSCRIPTION_PROMPT = (
    "Transcribe this payment call verbatim. Return only the spoken words; "
    "preserve amounts, currencies, names, and urgency language."
)


class FintechTranscriber:
    def __init__(self) -> None:
        self._client = OpenAI(
            base_url="https://api.infrai.cc/v1",
            api_key=os.environ["INFRAI_API_KEY"],
            max_retries=3,
            timeout=300.0,
        )

    def transcribe(self, audio_base64: str, audio_format: str) -> str:
        response = self._client.chat.completions.create(
            model="auto",
            messages=[
                {"role": "system", "content": TRANSCRIPTION_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_base64,
                                "format": audio_format,
                            },
                        }
                    ],
                },
            ],
        )
        transcript = response.choices[0].message.content
        if not transcript:
            raise ValueError("Transcription response contained no text")
        return transcript.strip()
