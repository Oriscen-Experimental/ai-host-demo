"""
语音转文字服务 (Speech-to-Text)
使用 OpenAI Whisper API
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
    将base64编码的音频转换为文字

    Args:
        audio_base64: base64编码的音频数据 (可带或不带data URL前缀)
        mime_type: 音频MIME类型

    Returns:
        转录的文字
    """
    if not audio_base64:
        return ""

    try:
        # 移除 data URL 前缀 (如 "data:audio/webm;base64,")
        if "," in audio_base64:
            audio_base64 = audio_base64.split(",", 1)[1]

        # 解码 base64
        audio_bytes = base64.b64decode(audio_base64)

        # 根据 MIME 类型确定文件扩展名
        ext_map = {
            "audio/webm": ".webm",
            "audio/ogg": ".ogg",
            "audio/mp4": ".m4a",
            "audio/mpeg": ".mp3",
            "audio/wav": ".wav",
        }
        ext = ext_map.get(mime_type, ".webm")

        # 写入临时文件
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            # 在线程池中调用同步的 Whisper API
            def _sync_transcribe():
                client = _get_openai_client()
                with open(tmp_path, "rb") as audio_file:
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="zh",  # 默认中文
                        response_format="text",
                    )
                return response

            text = await asyncio.get_event_loop().run_in_executor(None, _sync_transcribe)
            return text.strip() if text else ""

        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        print(f"[STT] Transcription error: {e}")
        return ""
