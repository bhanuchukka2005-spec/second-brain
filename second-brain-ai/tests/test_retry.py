"""Unit tests for retry and validation utilities."""
from src.utils.retry import (
    retry_with_backoff, validate_api_key, validate_file_upload, validate_youtube_url
)


class TestRetryWithBackoff:
    def test_succeeds_first_try(self):
        count = [0]
        @retry_with_backoff(max_retries=3, base_delay=0.001)
        def fn():
            count[0] += 1
            return "ok"
        assert fn() == "ok" and count[0] == 1

    def test_retries_then_succeeds(self):
        count = [0]
        @retry_with_backoff(max_retries=3, base_delay=0.001)
        def fn():
            count[0] += 1
            if count[0] < 3:
                raise ConnectionError("tmp")
            return "ok"
        assert fn() == "ok" and count[0] == 3

    def test_raises_after_max(self):
        @retry_with_backoff(max_retries=2, base_delay=0.001)
        def fn():
            raise ConnectionError("always fails")
        try:
            fn()
            assert False
        except ConnectionError:
            pass

    def test_no_retry_on_auth(self):
        count = [0]
        @retry_with_backoff(max_retries=3, base_delay=0.001)
        def fn():
            count[0] += 1
            raise Exception("Invalid API key provided")
        try:
            fn()
        except Exception:
            pass
        assert count[0] == 1

    def test_preserves_name(self):
        @retry_with_backoff()
        def my_fn(): return "ok"
        assert my_fn.__name__ == "my_fn"


class TestValidateApiKey:
    def test_empty_raises(self):
        try: validate_api_key("", "groq"); assert False
        except ValueError as e: assert "empty" in str(e).lower()

    def test_spaces_raises(self):
        try: validate_api_key("abc def ghi", "groq"); assert False
        except ValueError as e: assert "spaces" in str(e).lower()

    def test_short_raises(self):
        try: validate_api_key("short", "groq"); assert False
        except ValueError: pass

    def test_valid_passes(self):
        validate_api_key("a" * 25, "groq")


class TestValidateFileUpload:
    def test_valid_pdf(self): validate_file_upload("notes.pdf", 1024 * 1024)
    def test_valid_pptx(self): validate_file_upload("slides.pptx", 500 * 1024)
    def test_valid_txt(self): validate_file_upload("notes.txt", 10 * 1024)

    def test_bad_ext(self):
        try: validate_file_upload("notes.docx", 1024); assert False
        except ValueError: pass

    def test_too_large(self):
        try: validate_file_upload("notes.pdf", 100 * 1024 * 1024); assert False
        except ValueError: pass


class TestValidateYoutubeUrl:
    def test_valid_full(self): validate_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    def test_valid_short(self): validate_youtube_url("https://youtu.be/dQw4w9WgXcQ")

    def test_empty_raises(self):
        try: validate_youtube_url(""); assert False
        except ValueError: pass

    def test_non_youtube_raises(self):
        try: validate_youtube_url("https://vimeo.com/123456"); assert False
        except ValueError: pass
