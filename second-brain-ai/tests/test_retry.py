"""
Unit tests for retry logic and input validation utilities.
"""
import pytest
from src.utils.retry import (
    retry_with_backoff,
    validate_api_key,
    validate_file_upload,
    validate_youtube_url,
)


class TestRetryWithBackoff:

    def test_succeeds_on_first_try(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def always_succeeds():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = always_succeeds()
        assert result == "ok"
        assert call_count == 1

    def test_retries_on_failure_then_succeeds(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("temporary failure")
            return "ok"

        result = fails_twice()
        assert result == "ok"
        assert call_count == 3

    def test_raises_after_max_retries(self):
        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def always_fails():
            raise ConnectionError("always fails")

        with pytest.raises(ConnectionError):
            always_fails()

    def test_does_not_retry_on_auth_error(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def auth_error():
            nonlocal call_count
            call_count += 1
            raise Exception("Invalid API key provided")

        with pytest.raises(Exception, match="Invalid API key"):
            auth_error()
        assert call_count == 1  # Should NOT retry

    def test_preserves_function_name(self):
        @retry_with_backoff()
        def my_function():
            return "hello"

        assert my_function.__name__ == "my_function"


class TestValidateApiKey:

    def test_empty_key_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_api_key("", "groq")

    def test_whitespace_key_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_api_key("   ", "groq")

    def test_key_with_spaces_raises(self):
        with pytest.raises(ValueError, match="spaces"):
            validate_api_key("abc def ghi", "groq")

    def test_too_short_key_raises(self):
        with pytest.raises(ValueError, match="too short"):
            validate_api_key("short", "groq")

    def test_valid_key_passes(self):
        # Should not raise
        validate_api_key("a" * 50, "groq")

    def test_unknown_provider_uses_default_min_length(self):
        # Should not raise with long enough key
        validate_api_key("a" * 25, "unknown_provider")


class TestValidateFileUpload:

    def test_valid_pdf_passes(self):
        validate_file_upload("notes.pdf", 1024 * 1024)  # 1MB

    def test_valid_pptx_passes(self):
        validate_file_upload("slides.pptx", 500 * 1024)

    def test_valid_txt_passes(self):
        validate_file_upload("notes.txt", 10 * 1024)

    def test_invalid_extension_raises(self):
        with pytest.raises(ValueError, match="unsupported type"):
            validate_file_upload("notes.docx", 1024)

    def test_file_too_large_raises(self):
        with pytest.raises(ValueError, match="too large"):
            validate_file_upload("notes.pdf", 100 * 1024 * 1024)  # 100MB

    def test_custom_max_size(self):
        with pytest.raises(ValueError, match="too large"):
            validate_file_upload("notes.pdf", 2 * 1024 * 1024, max_mb=1)


class TestValidateYoutubeUrl:

    def test_valid_full_url(self):
        validate_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_valid_short_url(self):
        validate_youtube_url("https://youtu.be/dQw4w9WgXcQ")

    def test_empty_url_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_youtube_url("")

    def test_non_youtube_url_raises(self):
        with pytest.raises(ValueError, match="valid YouTube URL"):
            validate_youtube_url("https://vimeo.com/123456")

    def test_invalid_url_raises(self):
        with pytest.raises(ValueError, match="valid YouTube URL"):
            validate_youtube_url("not a url at all")
