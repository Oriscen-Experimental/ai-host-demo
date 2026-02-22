"""
Speech-to-Text Service
Using OpenAI Whisper API
"""
import base64
import tempfile
import asyncio
import os
import app.config as config


_openai_client = None


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _openai_client


async def transcribe_audio(audio_base64: str, mime_type: str = "audio/webm") -> str:
    """
    Convert base64-encoded audio to text

    Args:
        audio_base64: base64-encoded audio data (with or without data URL prefix)
        mime_type: audio MIME type

    Returns:
        Transcribed text
    """
    if not audio_base64:
        return ""

    try:
        # Remove data URL prefix (e.g. "data:audio/webm;base64,")
        if "," in audio_base64:
            audio_base64 = audio_base64.split(",", 1)[1]

        # Decode base64
        audio_bytes = base64.b64decode(audio_base64)

        # Determine file extension based on MIME type
        ext_map = {
            "audio/webm": ".webm",
            "audio/ogg": ".ogg",
            "audio/mp4": ".m4a",
            "audio/mpeg": ".mp3",
            "audio/wav": ".wav",
        }
        ext = ext_map.get(mime_type, ".webm")

        # Write to temporary file
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            # Call synchronous Whisper API in thread pool
            def _sync_transcribe():
                client = _get_openai_client()
                with open(tmp_path, "rb") as audio_file:
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="en",  # Default English
                        response_format="text",
                    )
                return response

            text = await asyncio.get_event_loop().run_in_executor(None, _sync_transcribe)
            return text.strip() if text else ""

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        print(f"[STT] Transcription error: {e}")
        return ""
