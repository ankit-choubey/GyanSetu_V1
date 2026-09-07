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
    extract_audio_from_video,
    process_audio,
    process_media,
    process_video,
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
