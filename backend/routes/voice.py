# routes/voice.py — STT, TTS, and full voice command handler
from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from schemas import TranscribeResponse, SpeakRequest, VoiceCommandResponse
from services import voice as voice_svc
from services import llm as llm_svc
import prompts

router = APIRouter()


@router.post("/voice/transcribe", response_model=TranscribeResponse)
async def transcribe(audio: UploadFile = File(...)) -> TranscribeResponse:
    audio_bytes = await audio.read()
    try:
        text = voice_svc.transcribe(audio_bytes, filename=audio.filename or "audio.webm")
        return TranscribeResponse(text=text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")


@router.post("/voice/speak")
async def speak(req: SpeakRequest) -> Response:
    audio_bytes = voice_svc.speak(req.text)
    if audio_bytes is None:
        # Signal browser to use Web Speech API fallback
        raise HTTPException(status_code=503, detail="TTS_PROVIDER=browser — use browser speechSynthesis")
    return Response(content=audio_bytes, media_type="audio/wav")


@router.post("/voice/command", response_model=VoiceCommandResponse)
async def voice_command(
    audio: UploadFile = File(...),
    engineer: str = Form(default=""),
) -> VoiceCommandResponse:
    # 1. Transcribe
    audio_bytes = await audio.read()
    try:
        transcript = voice_svc.transcribe(audio_bytes, filename=audio.filename or "audio.webm")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

    if not transcript or not transcript.strip():
        return VoiceCommandResponse(
            transcript="",
            intent="none",
            result={},
            spoken_summary="I didn't quite catch that."
        )

    # 2. Classify intent
    intent_data = llm_svc.call_llm(
        system=prompts.VOICE_INTENT_SYSTEM,
        user=prompts.VOICE_INTENT_USER.format(transcript=transcript),
        schema_keys=["intent", "payload"],
    )
    intent = intent_data.get("intent", "question")
    payload = intent_data.get("payload", {})

    # 3. Route to the appropriate handler
    result: dict = {}
    spoken_summary = ""

    if intent == "triage":
        from routes.triage import triage
        from schemas import TriageRequest
        triage_req = TriageRequest(
            alert_text=payload.get("alert_text", transcript),
            use_memory=True,
            engineer=engineer or None,
        )
        triage_resp = await triage(triage_req)
        result = triage_resp.model_dump()
        spoken_summary = triage_resp.spoken_summary

    elif intent == "resolve":
        from routes.resolve import resolve
        from schemas import ResolveRequest
        resolve_req = ResolveRequest(
            alert_text=transcript,
            worked=payload.get("worked", transcript),
            failed=payload.get("failed"),
            notes=payload.get("notes"),
            engineer=engineer or None,
        )
        resolve_resp = await resolve(resolve_req)
        result = resolve_resp.model_dump()
        spoken_summary = "Resolution saved to memory. Look at Incident Console for more info."

    elif intent == "preference":
        from routes.resolve import resolve
        from schemas import ResolveRequest
        # Store preference as a resolution-style note
        pref_text = payload.get("preference", transcript)
        if engineer:
            from services.memory import remember
            from datetime import datetime, timezone
            await remember(
                content=f"Engineer {engineer} preference: {pref_text}",
                context="engineer preference",
                when=datetime.now(timezone.utc),
                doc_id=f"pref-{engineer}-voice",
                meta={"kind": "preference", "engineer": engineer},
            )
        result = {"preference_saved": pref_text}
        spoken_summary = "Got it, I'll remember that preference. Look at Incident Console for more info."

    else:  # question
        from services.memory import recall, format_memories_for_prompt
        from services.llm import call_llm
        question = payload.get("question", transcript)
        memories = await recall(question, budget="mid")
        mems_fmt = format_memories_for_prompt(memories)
        answer_data = call_llm(
            system="You are an incident memory assistant. Answer the engineer's question using the memory provided. The spoken_summary MUST be 2-3 sentences and the last sentence MUST be exactly 'Look at Incident Console for more info.'. Return JSON: {\"answer\": \"string\", \"spoken_summary\": \"string\"}",
            user=f"Question: {question}\n\nMemory:\n{mems_fmt}",
            schema_keys=["answer", "spoken_summary"],
        )
        result = answer_data
        spoken_summary = answer_data.get("spoken_summary", answer_data.get("answer", ""))

    return VoiceCommandResponse(
        transcript=transcript,
        intent=intent,
        result=result,
        spoken_summary=spoken_summary,
    )
