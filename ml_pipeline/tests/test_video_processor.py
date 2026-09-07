"""
Unit tests for ml_pipeline/video_processor.py
"""
import os
import tempfile
from unittest.mock import MagicMock, patch
import pytest

from ml_pipeline.video_processor import (
    AUDIO_EXTENSIONS,
    FFmpegNotFoundError,
    MediaProcessingError,
    SUPPORTED_MEDIA_EXTENSIONS,
    VIDEO_EXTENSIONS,
    YouTubeProcessingError,
    download_youtube_audio,
    extract_audio_from_video,
    extract_youtube_video_id,
    fetch_youtube_captions,
    is_youtube_url,
    process_audio,
    process_media,
    process_video,
    process_youtube_url,
    transcribe_audio,
)


def test_supported_extensions():
    assert ".mp4" in VIDEO_EXTENSIONS
    assert ".webm" in VIDEO_EXTENSIONS
    assert ".mp3" in AUDIO_EXTENSIONS
    assert ".wav" in AUDIO_EXTENSIONS
    assert VIDEO_EXTENSIONS.issubset(SUPPORTED_MEDIA_EXTENSIONS)
    assert AUDIO_EXTENSIONS.issubset(SUPPORTED_MEDIA_EXTENSIONS)


def test_unsupported_format_raises():
    with tempfile.NamedTemporaryFile(suffix=".txt") as f:
        with pytest.raises(ValueError, match="Unsupported media format"):
            process_media(f.name)


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        process_media("non_existent_file_path.mp4")


def test_extract_audio_ffmpeg_not_found():
    with tempfile.NamedTemporaryFile(suffix=".mp4") as f:
        with patch("shutil.which", return_value=None):
            with pytest.raises(FFmpegNotFoundError):
                extract_audio_from_video(f.name)


def test_extract_audio_calls_ffmpeg_correctly():
    with tempfile.NamedTemporaryFile(suffix=".mp4") as f:
        with patch("shutil.which", return_value="/usr/local/bin/ffmpeg"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            out_path = extract_audio_from_video(f.name)
            assert out_path.endswith(".wav")
            assert mock_run.called
            cmd = mock_run.call_args[0][0]
            assert cmd[0] == "ffmpeg"
            assert "-i" in cmd
            assert f.name in cmd
            if os.path.exists(out_path):
                os.remove(out_path)


def test_transcribe_audio_mocked_whisper():
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        f.write(b"RIFF dummy audio content")
        f.flush()

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "In official statistics, stratified random sampling ensures adequate subgroup representation."
        mock_response.segments = [
            {"start": 0.0, "end": 4.5, "text": "In official statistics, stratified random sampling ensures adequate subgroup representation."}
        ]
        mock_response.duration = 4.5
        mock_response.language = "en"
        mock_client.audio.transcriptions.create.return_value = mock_response

        with patch("ml_pipeline.video_processor._get_client", return_value=mock_client):
            result = transcribe_audio(f.name, language="en")
            assert "stratified random sampling" in result["raw_text"]
            assert result["duration"] == 4.5
            assert result["language"] == "en"
            assert len(result["segments"]) == 1


def test_process_media_audio_end_to_end():
    with tempfile.NamedTemporaryFile(suffix=".mp3") as f:
        f.write(b"ID3 dummy mp3 content")
        f.flush()

        sample_transcript = (
            "The Consumer Price Index measures changes over time in general price level. "
            "It is compiled monthly using representative basket of goods and services. "
            "Base year weighting is determined through nationwide consumer expenditure surveys."
        )

        with patch("ml_pipeline.video_processor.transcribe_audio") as mock_transcribe:
            mock_transcribe.return_value = {
                "raw_text": sample_transcript,
                "segments": [],
                "duration": 12.0,
                "language": "en",
            }

            doc = process_audio(f.name, chunk=True, chunk_size=100, overlap=20)
            assert doc["source_type"] == "audio"
            assert doc["raw_text"] == sample_transcript
            assert doc["duration"] == 12.0
            assert len(doc["chunks"]) > 0
            assert doc["chunks"][0]["source_id"] == os.path.basename(f.name)


def test_temp_audio_cleanup_on_video():
    with tempfile.NamedTemporaryFile(suffix=".mp4") as f:
        dummy_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        dummy_wav_name = dummy_wav.name
        dummy_wav.close()

        with patch("ml_pipeline.video_processor.extract_audio_from_video", return_value=dummy_wav_name), \
             patch("ml_pipeline.video_processor.transcribe_audio") as mock_transcribe:
            mock_transcribe.return_value = {"raw_text": "Sample text", "duration": 5.0}
            doc = process_video(f.name)
            assert doc["source_type"] == "video"
            # Temp file must be cleaned up
            assert not os.path.exists(dummy_wav_name)


def test_extract_youtube_video_id():
    # Standard watch URL
    assert extract_youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # Query parameters
    assert extract_youtube_video_id("https://youtube.com/watch?app=desktop&v=dQw4w9WgXcQ&t=10s") == "dQw4w9WgXcQ"
    # Shortened youtu.be URL
    assert extract_youtube_video_id("https://youtu.be/dQw4w9WgXcQ?t=42") == "dQw4w9WgXcQ"
    # Shorts URL
    assert extract_youtube_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # Embed URL
    assert extract_youtube_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # Raw 11-char ID
    assert extract_youtube_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    # Non-YouTube URL or local file
    assert extract_youtube_video_id("https://example.com/video.mp4") is None
    assert extract_youtube_video_id("/local/file/lecture.mp4") is None
    assert extract_youtube_video_id("") is None


def test_is_youtube_url():
    assert is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True
    assert is_youtube_url("https://youtu.be/dQw4w9WgXcQ") is True
    assert is_youtube_url("https://youtube.com/shorts/dQw4w9WgXcQ") is True
    assert is_youtube_url("https://example.com/video.mp4") is False
    assert is_youtube_url("local_recording.mp4") is False


def test_fetch_youtube_captions_success():
    mock_raw_snippets = [
        {"start": 0.0, "duration": 3.5, "text": "Welcome to the official statistics workshop."},
        {"start": 3.5, "duration": 4.0, "text": "Today we cover consumer price index calculation."},
    ]

    mock_transcript = MagicMock()
    mock_transcript.language_code = "en"
    mock_transcript.fetch.return_value = mock_raw_snippets

    mock_transcript_list = MagicMock()
    mock_transcript_list.find_manually_created_transcript.return_value = mock_transcript

    mock_api_instance = MagicMock()
    mock_api_instance.list.return_value = mock_transcript_list

    with patch("youtube_transcript_api.YouTubeTranscriptApi", return_value=mock_api_instance):
        result = fetch_youtube_captions("dQw4w9WgXcQ", language="en")
        assert result is not None
        assert "official statistics workshop" in result["raw_text"]
        assert "consumer price index" in result["raw_text"]
        assert result["duration"] == 7.5
        assert result["method"] == "youtube_captions"
        assert len(result["segments"]) == 2


def test_download_youtube_audio_mocked():
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_output_file = os.path.join(tmpdir, "audio.wav")
        with open(mock_output_file, "wb") as f:
            f.write(b"RIFF dummy wav audio")

        mock_ydl = MagicMock()
        mock_ydl.__enter__.return_value = mock_ydl

        with patch("yt_dlp.YoutubeDL", return_value=mock_ydl), \
             patch("tempfile.mkdtemp", return_value=tmpdir):
            out_file = download_youtube_audio("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            assert os.path.exists(out_file)
            assert mock_ydl.download.called


def test_process_youtube_url_tier1_captions():
    mock_caption_result = {
        "raw_text": "National Statistical Systems provide critical indicators for economic development planning.",
        "segments": [{"start": 0.0, "end": 6.0, "text": "National Statistical Systems provide critical indicators."}],
        "duration": 6.0,
        "language": "en",
        "method": "youtube_captions",
    }

    with patch("ml_pipeline.video_processor.fetch_youtube_captions", return_value=mock_caption_result), \
         patch("ml_pipeline.video_processor.download_youtube_audio") as mock_dl:
        doc = process_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ", chunk=True)
        # Verify Tier 1 was used and audio download was NOT triggered
        assert mock_dl.called is False
        assert doc["source_type"] == "youtube"
        assert doc["video_id"] == "dQw4w9WgXcQ"
        assert doc["method"] == "youtube_captions"
        assert "National Statistical Systems" in doc["raw_text"]
        assert len(doc["chunks"]) > 0
        assert doc["chunks"][0]["source_id"] == "youtube_dQw4w9WgXcQ"


def test_process_youtube_url_tier2_whisper_fallback():
    mock_whisper_result = {
        "raw_text": "Field enumeration procedures require comprehensive address verification before surveys.",
        "segments": [{"start": 0.0, "end": 5.0, "text": "Field enumeration procedures require comprehensive address verification."}],
        "duration": 5.0,
        "language": "en",
    }

    dummy_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    dummy_audio.write(b"dummy")
    dummy_audio.close()

    # Captions return None (missing captions), forcing Tier 2
    with patch("ml_pipeline.video_processor.fetch_youtube_captions", return_value=None), \
         patch("ml_pipeline.video_processor.download_youtube_audio", return_value=dummy_audio.name), \
         patch("ml_pipeline.video_processor.transcribe_audio", return_value=mock_whisper_result):
        doc = process_youtube_url("https://youtu.be/dQw4w9WgXcQ")
        assert doc["source_type"] == "youtube"
        assert doc["method"] == "yt_dlp_whisper"
        assert "Field enumeration procedures" in doc["raw_text"]
        assert doc["duration"] == 5.0


def test_process_media_routes_youtube_url():
    sample_doc = {
        "filename": "youtube_dQw4w9WgXcQ",
        "file_path": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "source_type": "youtube",
        "video_id": "dQw4w9WgXcQ",
        "raw_text": "Sample lecture",
        "chunks": [],
    }

    with patch("ml_pipeline.video_processor.process_youtube_url", return_value=sample_doc) as mock_yt_proc:
        res = process_media("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert mock_yt_proc.called
        assert res["source_type"] == "youtube"
        assert res["video_id"] == "dQw4w9WgXcQ"


def test_invalid_youtube_url_raises():
    with pytest.raises(YouTubeProcessingError, match="Invalid or unrecognized YouTube URL"):
        process_youtube_url("https://www.youtube.com/watch?v=invalid")
