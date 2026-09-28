# services/voice.py — Groq Whisper STT + Orpheus TTS with browser fallback hint
from __future__ import annotations
import io
import logging
from typing import Optional

from groq import Groq

from config import settings

logger = logging.getLogger(__name__)

_client: Optional[Groq] = None

# Jargon hint for Whisper — improves accuracy for domain-specific terms
WHISPER_PROMPT = (
    "payments-service, checkout-api, auth-service, search-service, "
    "notification-worker, HikariCP, HikariPool, Redis, Kafka, Postgres, "
    "INC, DEP, SEV1, SEV2, rollback, deploy, canary, p99, RDS"
)

TTS_VOICE = "tara"  # Orpheus voices: tara, leah, leo, etc.


def _get_groq() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    Transcribe audio using Groq Whisper large-v3-turbo.
    Returns transcribed text.
    """
    client = _get_groq()
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename

    transcription = client.audio.transcriptions.create(
        file=(filename, audio_bytes),
        model="whisper-large-v3-turbo",
        prompt=WHISPER_PROMPT,
        response_format="text",
        language="en",
    )
    return str(transcription).strip()


def speak(text: str) -> Optional[bytes]:
    """
    Synthesize speech using Groq Orpheus TTS.
    Returns raw audio bytes (wav), or None if TTS_PROVIDER is 'browser'
    or if Orpheus is unavailable (Preview API).
    """
    if settings.TTS_PROVIDER != "groq":
        return None

    try:
        client = _get_groq()
        response = client.audio.speech.create(
            model="canopylabs/orpheus-v1-english",
            voice=TTS_VOICE,
            input=text,
            response_format="wav",
        )
        # response.content is raw audio bytes
        return response.content
    except Exception as e:
        # Orpheus is Preview — gracefully fall back to browser TTS
        logger.warning("Orpheus TTS failed (likely Preview limitation): %s", e)
        return None
