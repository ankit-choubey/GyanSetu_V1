"""
ml_pipeline/video_processor.py — Video and Audio ASR Content Ingestion Engine.
GyanSetu - Phase 5.1

Extracts audio from lecture recordings and webinars using ffmpeg,
transcribes speech via Groq Whisper API (whisper-large-v3),
and pipes text into semantic chunking for RAG and MCQ generation.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

from openai import OpenAI

from ml_pipeline.chunker import DEFAULT_RAG_CHUNK_SIZE, DEFAULT_RAG_OVERLAP, chunk_text
from ml_pipeline.config import GROQ_API_KEY, GROQ_BASE_URL

VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
SUPPORTED_MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

WHISPER_MODEL = "whisper-large-v3"
_client: Optional[OpenAI] = None


class MediaProcessingError(Exception):
    """Raised when video extraction or transcription fails."""
    pass


class FFmpegNotFoundError(MediaProcessingError):
    """Raised when ffmpeg binary is not available on system."""
    pass


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not configured; cannot transcribe media.")
        _client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url=GROQ_BASE_URL,
        )
    return _client


def extract_audio_from_video(video_path: str, output_audio_path: Optional[str] = None) -> str:
    """
    Extracts audio track from a video file using ffmpeg as a 16kHz mono WAV.

    Args:
        video_path: Path to the input video file.
        output_audio_path: Optional destination path. If None, creates a temp file.

    Returns:
        Path to the extracted WAV audio file.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Input video file not found: {video_path}")

    ext = os.path.splitext(video_path)[1].lower()
    if ext not in VIDEO_EXTENSIONS:
        raise ValueError(f"Unsupported video extension '{ext}'. Supported: {sorted(VIDEO_EXTENSIONS)}")

    if not shutil.which("ffmpeg"):
        raise FFmpegNotFoundError(
            "ffmpeg executable was not found on system PATH. "
            "Install ffmpeg (e.g. `brew install ffmpeg`) to process video files."
        )

    if output_audio_path is None:
        fd, output_audio_path = tempfile.mkstemp(suffix=".wav", prefix="gyansetu_audio_")
        os.close(fd)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        output_audio_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except subprocess.CalledProcessError as err:
        stderr_msg = err.stderr.decode("utf-8", errors="replace")
        raise MediaProcessingError(f"ffmpeg audio extraction failed: {stderr_msg}") from err

    return output_audio_path


def transcribe_audio(
    audio_path: str,
    *,
    language: Optional[str] = None,
    prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Transcribes an audio file using Groq Whisper endpoint.

    Args:
        audio_path: Path to the audio file.
        language: Optional 2-letter ISO language code (e.g. 'en', 'hi').
        prompt: Optional glossary/context prompt for Whisper domain vocabulary.

    Returns:
        Dictionary with raw_text, segments, language, duration.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    ext = os.path.splitext(audio_path)[1].lower()
    if ext not in SUPPORTED_MEDIA_EXTENSIONS:
        raise ValueError(f"Unsupported audio format '{ext}'. Supported: {sorted(SUPPORTED_MEDIA_EXTENSIONS)}")

    client = _get_client()

    with open(audio_path, "rb") as f:
        kwargs: Dict[str, Any] = {
            "file": f,
            "model": WHISPER_MODEL,
            "response_format": "verbose_json",
        }
        if language:
            kwargs["language"] = language
        if prompt:
            kwargs["prompt"] = prompt

        response = client.audio.transcriptions.create(**kwargs)

    # Verbose JSON responses provide text, duration, segments, language
    if isinstance(response, dict):
        raw_text = response.get("text", "")
        segments = response.get("segments", [])
        duration = response.get("duration", 0.0)
        detected_lang = response.get("language", language)
    else:
        raw_text = getattr(response, "text", str(response))
        segments = getattr(response, "segments", [])
        duration = getattr(response, "duration", 0.0)
        detected_lang = getattr(response, "language", language)

    return {
        "raw_text": raw_text.strip(),
        "segments": segments,
        "duration": duration,
        "language": detected_lang,
    }


def process_media(
    file_path: str,
    *,
    language: Optional[str] = None,
    chunk: bool = True,
    chunk_size: int = DEFAULT_RAG_CHUNK_SIZE,
    overlap: int = DEFAULT_RAG_OVERLAP,
    prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """
    End-to-end processing of audio or video content into structured plain text and semantic chunks.

    Args:
        file_path: Path to the media file.
        language: Language hint (e.g. 'en', 'hi').
        chunk: Whether to chunk the resulting transcript.
        chunk_size: Target character size for semantic chunks.
        overlap: Character overlap for chunks.
        prompt: Domain terms or context for Whisper transcription.

    Returns:
        Structured media dictionary matching document_processor conventions.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Media file not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_MEDIA_EXTENSIONS:
        raise ValueError(f"Unsupported media format '{ext}'. Supported: {sorted(SUPPORTED_MEDIA_EXTENSIONS)}")

    is_video = ext in VIDEO_EXTENSIONS
    temp_audio_path: Optional[str] = None

    try:
        if is_video:
            source_type = "video"
            temp_audio_path = extract_audio_from_video(file_path)
            transcription = transcribe_audio(temp_audio_path, language=language, prompt=prompt)
        else:
            source_type = "audio"
            transcription = transcribe_audio(file_path, language=language, prompt=prompt)

        raw_text = transcription["raw_text"]
        chunks = []
        if chunk and raw_text:
            chunks = chunk_text(
                raw_text,
                chunk_size=chunk_size,
                overlap=overlap,
                source_id=os.path.basename(file_path),
            )

        return {
            "filename": os.path.basename(file_path),
            "file_path": file_path,
            "source_type": source_type,
            "raw_text": raw_text,
            "language": transcription.get("language") or language,
            "duration": transcription.get("duration"),
            "segments": transcription.get("segments", []),
            "chunks": chunks,
        }
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except OSError:
                pass


def process_video(file_path: str, **kwargs) -> Dict[str, Any]:
    """Convenience wrapper for video files."""
    return process_media(file_path, **kwargs)


def process_audio(file_path: str, **kwargs) -> Dict[str, Any]:
    """Convenience wrapper for audio files."""
    return process_media(file_path, **kwargs)
