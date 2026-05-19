"""Unit tests for Ollama client — all network calls mocked."""
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
    def test_returns_true_when_up(self):
        mock = MagicMock()
        mock.status = 200
        mock.__enter__ = lambda s: s
        mock.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock):
            assert is_ollama_running() is True

    def test_returns_false_on_error(self):
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
            assert is_ollama_running() is False


class TestGetInstalledModels:
    def _mock(self, data):
        mock = MagicMock()
        mock.read.return_value = json.dumps(data).encode()
        mock.__enter__ = lambda s: s
        mock.__exit__ = MagicMock(return_value=False)
        return mock

    def test_returns_model_names(self):
        data = {"models": [{"name": "llama3.2:latest"}, {"name": "mistral:latest"}]}
        with patch("urllib.request.urlopen", return_value=self._mock(data)):
            models = get_installed_models()
        assert "llama3.2" in models and "mistral" in models

    def test_strips_tag(self):
        data = {"models": [{"name": "llama3.2:latest"}]}
        with patch("urllib.request.urlopen", return_value=self._mock(data)):
            assert get_installed_models() == ["llama3.2"]

    def test_empty_on_error(self):
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
            assert get_installed_models() == []


class TestGetBestAvailableModel:
    def test_returns_recommended(self):
        with patch("src.llm.ollama_client.get_installed_models", return_value=["llama3.2", "mistral"]):
            assert get_best_available_model() == "llama3.2"

    def test_returns_first_installed_if_none_recommended(self):
        with patch("src.llm.ollama_client.get_installed_models", return_value=["custom-model"]):
            assert get_best_available_model() == "custom-model"

    def test_returns_none_when_empty(self):
        with patch("src.llm.ollama_client.get_installed_models", return_value=[]):
            assert get_best_available_model() is None


class TestRecommendedModels:
    def test_required_fields(self):
        for name, info in RECOMMENDED_MODELS.items():
            for field in ("size", "speed", "quality", "desc"):
                assert field in info, f"{name} missing {field}"

    def test_llama32_included(self):
        assert "llama3.2" in RECOMMENDED_MODELS


class TestInstallInstructions:
    def test_returns_string(self):
        assert isinstance(get_install_instructions(), str)

    def test_contains_ollama_url(self):
        assert "ollama.com" in get_install_instructions()

    def test_contains_pull_command(self):
        assert "ollama pull" in get_install_instructions()
