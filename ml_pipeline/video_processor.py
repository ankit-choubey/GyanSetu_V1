"""
ml_pipeline/video_processor.py — Video and Audio ASR Content Ingestion Engine.
GyanSetu - Phase 5.1

Extracts audio from lecture recordings and webinars using ffmpeg,
transcribes speech via Groq Whisper API (whisper-large-v3),
and pipes text into semantic chunking for RAG and MCQ generation.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from openai import OpenAI

from ml_pipeline.chunker import DEFAULT_RAG_CHUNK_SIZE, DEFAULT_RAG_OVERLAP, chunk_text
from ml_pipeline.config import GROQ_API_KEY, GROQ_BASE_URL

VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
SUPPORTED_MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

WHISPER_MODEL = "whisper-large-v3"
_client: Optional[OpenAI] = None

YOUTUBE_REGEX = re.compile(
    r'(?:https?:\/\/)?'
    r'(?:(?:www\.|m\.)?youtube\.com\/(?:watch\?.*?v=|embed\/|shorts\/|v\/)|youtu\.be\/)'
    r'([a-zA-Z0-9_-]{11})',
    re.IGNORECASE,
)


class MediaProcessingError(Exception):
    """Raised when video extraction or transcription fails."""
    pass


class FFmpegNotFoundError(MediaProcessingError):
    """Raised when ffmpeg binary is not available on system."""
    pass


class YouTubeProcessingError(MediaProcessingError):
    """Raised when YouTube video processing fails."""
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


def extract_youtube_video_id(url_or_id: str) -> Optional[str]:
    """
    Extracts the 11-character YouTube video ID from various YouTube URL formats or raw ID.

    Supports:
        - Standard watch URLs: https://www.youtube.com/watch?v=VIDEO_ID
        - Shortened URLs: https://youtu.be/VIDEO_ID
        - Embed URLs: https://www.youtube.com/embed/VIDEO_ID
        - Shorts URLs: https://www.youtube.com/shorts/VIDEO_ID
        - Direct 11-character video IDs
    """
    if not url_or_id or not isinstance(url_or_id, str):
        return None

    cleaned = url_or_id.strip()

    # Raw 11-character alphanumeric video ID
    if len(cleaned) == 11 and re.match(r"^[a-zA-Z0-9_-]{11}$", cleaned):
        return cleaned

    try:
        parsed = urlparse(cleaned if "://" in cleaned else f"https://{cleaned}")
        netloc = (parsed.netloc or "").lower()

        is_yt_domain = (
            netloc == "youtube.com"
            or netloc.endswith(".youtube.com")
            or netloc == "youtu.be"
            or netloc.endswith(".youtu.be")
        )

        if is_yt_domain:
            if "youtu.be" in netloc:
                parts = [p for p in parsed.path.split("/") if p]
                if parts and len(parts[0]) == 11:
                    return parts[0]

            if "youtube.com" in netloc:
                if parsed.path == "/watch":
                    qs = parse_qs(parsed.query)
                    vids = qs.get("v")
                    if vids and len(vids[0]) == 11:
                        return vids[0]
                elif any(parsed.path.startswith(prefix) for prefix in ("/embed/", "/shorts/", "/v/")):
                    parts = [p for p in parsed.path.split("/") if p]
                    if len(parts) >= 2 and len(parts[1]) == 11:
                        return parts[1]
    except Exception:
        pass

    m = YOUTUBE_REGEX.search(cleaned)
    if m:
        start = m.start()
        prefix = cleaned[:start]
        if not prefix or prefix.endswith(("://", " ", "\t", "\n")):
            return m.group(1)

    return None


def is_youtube_url(url_or_path: str) -> bool:
    """
    Returns True if the given string represents a YouTube URL.
    """
    if not url_or_path or not isinstance(url_or_path, str):
        return False
    clean = url_or_path.strip().lower()
    if not (clean.startswith(("http://", "https://", "www.")) or "youtube.com" in clean or "youtu.be" in clean):
        return False
    return extract_youtube_video_id(url_or_path) is not None


def fetch_youtube_captions(
    video_id: str,
    *,
    language: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Attempts to fetch existing transcripts/subtitles for a YouTube video via youtube-transcript-api.

    Prioritizes the requested language, then English ('en'), Hindi ('hi'), or any available subtitle track.
    Returns None if transcripts are disabled or cannot be retrieved.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None

    lang_candidates = []
    if language:
        lang_candidates.append(language)
    for l in ("en", "hi", "en-US", "en-GB", "es", "fr"):
        if l not in lang_candidates:
            lang_candidates.append(l)

    raw_snippets = None
    detected_lang = language or "en"

    # Strategy 1: Using TranscriptList API
    try:
        api = YouTubeTranscriptApi() if hasattr(YouTubeTranscriptApi, "fetch") else YouTubeTranscriptApi
        if hasattr(api, "list"):
            try:
                transcript_list = api.list(video_id)
                transcript = None
                try:
                    transcript = transcript_list.find_manually_created_transcript(lang_candidates)
                except Exception:
                    pass
                if transcript is None:
                    try:
                        transcript = transcript_list.find_generated_transcript(lang_candidates)
                    except Exception:
                        pass
                if transcript is None:
                    for t in transcript_list:
                        transcript = t
                        break

                if transcript is not None:
                    detected_lang = getattr(transcript, "language_code", detected_lang)
                    fetched = transcript.fetch()
                    if hasattr(fetched, "to_raw_data"):
                        raw_snippets = fetched.to_raw_data()
                    elif isinstance(fetched, list):
                        raw_snippets = fetched
                    else:
                        raw_snippets = [{"text": s.text, "start": s.start, "duration": s.duration} for s in fetched]
            except Exception:
                pass
    except Exception:
        pass

    # Strategy 2: Direct fetch / get_transcript fallback
    if raw_snippets is None:
        try:
            api = YouTubeTranscriptApi() if hasattr(YouTubeTranscriptApi, "fetch") else YouTubeTranscriptApi
            if hasattr(api, "fetch"):
                try:
                    fetched = api.fetch(video_id, languages=lang_candidates)
                    if hasattr(fetched, "to_raw_data"):
                        raw_snippets = fetched.to_raw_data()
                    elif isinstance(fetched, list):
                        raw_snippets = fetched
                    else:
                        raw_snippets = [{"text": s.text, "start": s.start, "duration": s.duration} for s in fetched]
                except TypeError:
                    fetched = YouTubeTranscriptApi.fetch(video_id, languages=lang_candidates)
                    if hasattr(fetched, "to_raw_data"):
                        raw_snippets = fetched.to_raw_data()
                    elif isinstance(fetched, list):
                        raw_snippets = fetched
                    else:
                        raw_snippets = [{"text": s.text, "start": s.start, "duration": s.duration} for s in fetched]
            elif hasattr(api, "get_transcript"):
                raw_snippets = api.get_transcript(video_id, languages=lang_candidates)
        except Exception:
            return None

    if not raw_snippets:
        return None

    segments = []
    text_parts = []
    total_duration = 0.0

    for item in raw_snippets:
        if isinstance(item, dict):
            txt = (item.get("text") or "").strip()
            start = float(item.get("start") or 0.0)
            dur = float(item.get("duration") or 0.0)
        else:
            txt = getattr(item, "text", "").strip()
            start = float(getattr(item, "start", 0.0))
            dur = float(getattr(item, "duration", 0.0))

        if txt:
            text_parts.append(txt)
            segments.append({
                "start": round(start, 2),
                "end": round(start + dur, 2),
                "text": txt,
            })
            total_duration = max(total_duration, start + dur)

    raw_text = " ".join(text_parts).strip()
    if not raw_text:
        return None

    return {
        "raw_text": raw_text,
        "segments": segments,
        "duration": round(total_duration, 2),
        "language": detected_lang,
        "method": "youtube_captions",
    }


def download_youtube_audio(url: str, output_path: Optional[str] = None) -> str:
    """
    Downloads the audio track of a YouTube video using yt-dlp.

    Args:
        url: YouTube video URL or ID.
        output_path: Optional destination path. If not provided, creates a temporary file.

    Returns:
        Path to the downloaded audio file (.wav or original audio format).
    """
    try:
        import yt_dlp
    except ImportError as err:
        raise YouTubeProcessingError(
            "yt-dlp package is not installed. Install with `pip install yt-dlp` to download YouTube audio."
        ) from err

    temp_dir = tempfile.mkdtemp(prefix="gyansetu_yt_audio_")
    out_template = os.path.join(temp_dir, "audio.%(ext)s")

    ydl_opts: Dict[str, Any] = {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    if shutil.which("ffmpeg"):
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "192",
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        downloaded_files = [
            os.path.join(temp_dir, f)
            for f in os.listdir(temp_dir)
            if not f.startswith(".")
        ]
        if not downloaded_files:
            raise YouTubeProcessingError(f"yt-dlp finished but produced no audio file for {url}")

        source_file = downloaded_files[0]
        if output_path:
            shutil.move(source_file, output_path)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return output_path

        return source_file
    except Exception as err:
        shutil.rmtree(temp_dir, ignore_errors=True)
        if isinstance(err, MediaProcessingError):
            raise
        raise YouTubeProcessingError(f"Failed to download YouTube audio: {err}") from err


def process_youtube_url(
    url: str,
    *,
    language: Optional[str] = None,
    chunk: bool = True,
    chunk_size: int = DEFAULT_RAG_CHUNK_SIZE,
    overlap: int = DEFAULT_RAG_OVERLAP,
    prefer_captions: bool = True,
    prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """
    End-to-end ingestion of a YouTube video into structured transcripts and semantic chunks:
    1. Extracts YouTube video ID.
    2. (Tier 1) Attempts instant subtitle/caption extraction via youtube-transcript-api.
    3. (Tier 2) If captions are unavailable, downloads audio via yt-dlp and transcribes via Groq Whisper.
    4. Pipes transcript into semantic chunker for RAG and MCQ generation.

    Args:
        url: YouTube video URL or ID.
        language: Language hint (e.g. 'en', 'hi').
        chunk: Whether to chunk the resulting transcript.
        chunk_size: Character size for semantic chunks.
        overlap: Overlap for chunks.
        prefer_captions: If True, attempts zero-cost caption retrieval before running Whisper ASR.
        prompt: Context or glossary prompt for Whisper ASR.

    Returns:
        Structured media dictionary matching document_processor conventions.
    """
    video_id = extract_youtube_video_id(url)
    if not video_id:
        raise YouTubeProcessingError(f"Invalid or unrecognized YouTube URL: {url}")

    canonical_url = f"https://www.youtube.com/watch?v={video_id}"
    transcription: Optional[Dict[str, Any]] = None

    # Tier 1: Try instant caption extraction
    if prefer_captions:
        try:
            transcription = fetch_youtube_captions(video_id, language=language)
        except Exception:
            transcription = None

    # Tier 2: Fallback to yt-dlp audio download + Groq Whisper
    temp_audio_path: Optional[str] = None
    if not transcription or not transcription.get("raw_text"):
        try:
            temp_audio_path = download_youtube_audio(canonical_url)
            whisper_result = transcribe_audio(temp_audio_path, language=language, prompt=prompt)
            transcription = {
                "raw_text": whisper_result["raw_text"],
                "segments": whisper_result.get("segments", []),
                "duration": whisper_result.get("duration"),
                "language": whisper_result.get("language") or language,
                "method": "yt_dlp_whisper",
            }
        except Exception as err:
            raise YouTubeProcessingError(
                f"Failed to process YouTube video {url} via captions and Whisper: {err}"
            ) from err
        finally:
            if temp_audio_path:
                temp_parent = os.path.dirname(temp_audio_path)
                if os.path.exists(temp_audio_path):
                    try:
                        os.remove(temp_audio_path)
                    except OSError:
                        pass
                if "gyansetu_yt_audio_" in temp_parent and os.path.exists(temp_parent):
                    shutil.rmtree(temp_parent, ignore_errors=True)

    raw_text = transcription.get("raw_text", "")
    chunks = []
    if chunk and raw_text:
        chunks = chunk_text(
            raw_text,
            chunk_size=chunk_size,
            overlap=overlap,
            source_id=f"youtube_{video_id}",
        )

    return {
        "filename": f"youtube_{video_id}",
        "file_path": canonical_url,
        "source_type": "youtube",
        "video_id": video_id,
        "text": raw_text,
        "transcript": raw_text,
        "raw_text": raw_text,
        "language": transcription.get("language") or language,
        "duration": transcription.get("duration"),
        "segments": transcription.get("segments", []),
        "method": transcription.get("method", "youtube_captions"),
        "chunks": chunks,
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
    End-to-end processing of audio, video, or YouTube content into structured plain text and semantic chunks.

    Args:
        file_path: Path to the media file or a YouTube URL.
        language: Language hint (e.g. 'en', 'hi').
        chunk: Whether to chunk the resulting transcript.
        chunk_size: Target character size for semantic chunks.
        overlap: Character overlap for chunks.
        prompt: Domain terms or context for Whisper transcription.

    Returns:
        Structured media dictionary matching document_processor conventions.
    """
    if is_youtube_url(file_path):
        return process_youtube_url(
            file_path,
            language=language,
            chunk=chunk,
            chunk_size=chunk_size,
            overlap=overlap,
            prompt=prompt,
        )

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
