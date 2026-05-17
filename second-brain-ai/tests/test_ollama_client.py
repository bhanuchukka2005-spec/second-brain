"""
Unit tests for Ollama client utilities.
All network calls are mocked — tests run without Ollama installed.
"""
import json
from unittest.mock import patch, MagicMock
from src.llm.ollama_client import (
    is_ollama_running,
    get_installed_models,
    get_best_available_model,
    get_install_instructions,
    RECOMMENDED_MODELS,
)


class TestIsOllamaRunning:

    def test_returns_true_when_server_responds(self):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            assert is_ollama_running() is True

    def test_returns_false_when_connection_refused(self):
        import urllib.error
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused")
        ):
            assert is_ollama_running() is False

    def test_returns_false_on_any_exception(self):
        with patch("urllib.request.urlopen", side_effect=Exception("unexpected")):
            assert is_ollama_running() is False


class TestGetInstalledModels:

    def _make_mock_response(self, models_data: dict):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(models_data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    def test_returns_model_names(self):
        data = {"models": [{"name": "llama3.2:latest"}, {"name": "mistral:latest"}]}
        with patch("urllib.request.urlopen", return_value=self._make_mock_response(data)):
            models = get_installed_models()
        assert "llama3.2" in models
        assert "mistral" in models

    def test_strips_tag_from_model_name(self):
        data = {"models": [{"name": "llama3.2:latest"}]}
        with patch("urllib.request.urlopen", return_value=self._make_mock_response(data)):
            models = get_installed_models()
        assert models == ["llama3.2"]

    def test_returns_empty_list_when_no_models(self):
        data = {"models": []}
        with patch("urllib.request.urlopen", return_value=self._make_mock_response(data)):
            models = get_installed_models()
        assert models == []

    def test_returns_empty_list_on_connection_error(self):
        import urllib.error
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("refused")
        ):
            assert get_installed_models() == []


class TestGetBestAvailableModel:

    def test_returns_recommended_model_when_installed(self):
        with patch(
            "src.llm.ollama_client.get_installed_models",
            return_value=["llama3.2", "mistral"]
        ):
            model = get_best_available_model()
        # llama3.2 is first in RECOMMENDED_MODELS
        assert model == "llama3.2"

    def test_returns_first_installed_when_none_recommended(self):
        with patch(
            "src.llm.ollama_client.get_installed_models",
            return_value=["some-custom-model"]
        ):
            model = get_best_available_model()
        assert model == "some-custom-model"

    def test_returns_none_when_no_models_installed(self):
        with patch(
            "src.llm.ollama_client.get_installed_models",
            return_value=[]
        ):
            assert get_best_available_model() is None

    def test_prefers_higher_priority_model(self):
        # llama3.2 comes before mistral in RECOMMENDED_MODELS
        with patch(
            "src.llm.ollama_client.get_installed_models",
            return_value=["mistral", "llama3.2"]
        ):
            model = get_best_available_model()
        assert model == "llama3.2"


class TestRecommendedModels:

    def test_all_models_have_required_fields(self):
        required = {"size", "speed", "quality", "desc"}
        for model_name, info in RECOMMENDED_MODELS.items():
            missing = required - set(info.keys())
            assert not missing, f"Model '{model_name}' missing fields: {missing}"

    def test_model_count(self):
        assert len(RECOMMENDED_MODELS) >= 5

    def test_llama32_is_included(self):
        assert "llama3.2" in RECOMMENDED_MODELS


class TestStreamOllama:

    def _make_stream_response(self, tokens):
        """Build mock streaming response with JSON lines."""
        lines = [
            json.dumps({"response": t, "done": False}).encode() + b"\n"
            for t in tokens
        ]
        lines.append(json.dumps({"response": "", "done": True}).encode() + b"\n")

        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.__iter__ = lambda s: iter(lines)
        return mock_resp

    def test_stream_yields_tokens(self):
        from src.llm.ollama_client import stream_ollama
        mock_resp = self._make_stream_response(["Hello", " world", "!"])
        with patch("urllib.request.urlopen", return_value=mock_resp):
            tokens = list(stream_ollama("llama3.2", "test prompt"))
        assert tokens == ["Hello", " world", "!"]

    def test_stream_assembles_to_full_response(self):
        from src.llm.ollama_client import stream_ollama
        mock_resp = self._make_stream_response(["This", " is", " a", " test"])
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = "".join(stream_ollama("llama3.2", "test"))
        assert result == "This is a test"

    def test_call_ollama_returns_string(self):
        from src.llm.ollama_client import call_ollama
        mock_resp = self._make_stream_response(["Answer", " here"])
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = call_ollama("llama3.2", "test prompt")
        assert result == "Answer here"

    def test_stream_raises_on_connection_error(self):
        import urllib.error
        from src.llm.ollama_client import stream_ollama
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("refused")
        ):
            with __import__("pytest").raises(ConnectionError):
                list(stream_ollama("llama3.2", "test"))


class TestGetInstallInstructions:

    def test_returns_string(self):
        assert isinstance(get_install_instructions(), str)

    def test_contains_ollama_url(self):
        instructions = get_install_instructions()
        assert "ollama.com" in instructions

    def test_contains_pull_command(self):
        instructions = get_install_instructions()
        assert "ollama pull" in instructions

    def test_contains_serve_command(self):
        instructions = get_install_instructions()
        assert "ollama serve" in instructions
