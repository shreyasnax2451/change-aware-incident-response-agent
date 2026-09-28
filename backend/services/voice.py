# services/voice.py — Deepgram STT/TTS (with Groq Orpheus fallback)
from __future__ import annotations
import io
import logging
from typing import Optional
import httpx

from groq import Groq
from config import settings

logger = logging.getLogger(__name__)

_client: Optional[Groq] = None

# Jargon hint for Whisper — improves accuracy for domain-specific terms (used if we fall back)
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
    Transcribe audio using Deepgram.
    Returns transcribed text.
    """
    if not settings.DEEPGRAM_API_KEY:
        logger.warning("No DEEPGRAM_API_KEY, falling back to Groq Whisper.")
        client = _get_groq()
        transcription = client.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model="whisper-large-v3-turbo",
            prompt=WHISPER_PROMPT,
            response_format="text",
            language="en",
        )
        return str(transcription).strip()

    # Use Deepgram STT
    url = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true"
    headers = {
        "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
        "Content-Type": "audio/webm",
    }
    with httpx.Client() as client:
        response = client.post(url, headers=headers, content=audio_bytes, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        return data["results"]["channels"][0]["alternatives"][0]["transcript"]


def speak(text: str) -> Optional[bytes]:
    """
    Synthesize speech using Deepgram TTS or Groq Orpheus.
    Returns raw audio bytes (wav), or None if TTS_PROVIDER is 'browser'.
    """
    if settings.TTS_PROVIDER == "elevenlabs" and settings.ELEVENLABS_API_KEY:
        url = "https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL"  # Rachel voice
        headers = {
            "xi-api-key": settings.ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg"
        }
        json_data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
        }
        try:
            with httpx.Client() as client:
                response = client.post(url, headers=headers, json=json_data, timeout=30.0)
                if response.status_code == 200:
                    return response.content
                logger.warning("ElevenLabs TTS failed: %s", response.text)
        except Exception as e:
            logger.warning("ElevenLabs TTS error: %s", e)
        return None

    if settings.TTS_PROVIDER == "deepgram" and settings.DEEPGRAM_API_KEY:
        url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en&container=wav&encoding=linear16"
        headers = {
            "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client() as client:
                response = client.post(url, headers=headers, json={"text": text}, timeout=30.0)
                if response.status_code == 200:
                    return response.content
                logger.warning("Deepgram TTS failed: %s", response.text)
        except Exception as e:
            logger.warning("Deepgram TTS error: %s", e)
        return None

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
        return response.content
    except Exception as e:
        logger.warning("Orpheus TTS failed (likely Preview limitation): %s", e)
        return None
