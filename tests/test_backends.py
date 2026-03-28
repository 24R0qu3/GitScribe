import os
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Ollama backend
# ---------------------------------------------------------------------------


class TestOllamaBackend:
    def test_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"response": "feat: add thing"}
        mock_resp.raise_for_status = MagicMock()
        with patch("gitscribe.ollama_backend.requests.post", return_value=mock_resp):
            from gitscribe.ollama_backend import generate

            result = generate("prompt")
        assert result == "feat: add thing"

    def test_timeout_raises(self):
        import requests

        with patch(
            "gitscribe.ollama_backend.requests.post",
            side_effect=requests.exceptions.Timeout,
        ):
            from gitscribe.ollama_backend import generate

            with pytest.raises(RuntimeError, match="timed out"):
                generate("prompt")

    def test_connection_error_raises(self):
        import requests

        with patch(
            "gitscribe.ollama_backend.requests.post",
            side_effect=requests.exceptions.ConnectionError("refused"),
        ):
            from gitscribe.ollama_backend import generate

            with pytest.raises(RuntimeError, match="connect"):
                generate("prompt")

    def test_http_error_raises(self):
        import requests

        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError("404")
        with patch("gitscribe.ollama_backend.requests.post", return_value=mock_resp):
            from gitscribe.ollama_backend import generate

            with pytest.raises(RuntimeError, match="HTTP"):
                generate("prompt")


# ---------------------------------------------------------------------------
# Claude backend
# ---------------------------------------------------------------------------


class TestClaudeBackend:
    def test_success(self):
        mock_content = MagicMock()
        mock_content.text = "feat: add thing"
        mock_message = MagicMock()
        mock_message.content = [mock_content]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("gitscribe.claude_backend.anthropic.Anthropic", return_value=mock_client):
                from gitscribe.claude_backend import generate

                result = generate("prompt")
        assert result == "feat: add thing"

    def test_missing_api_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            from gitscribe.claude_backend import generate

            with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
                generate("prompt")

    def test_api_error_raises(self):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API error")
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("gitscribe.claude_backend.anthropic.Anthropic", return_value=mock_client):
                from gitscribe.claude_backend import generate

                with pytest.raises(Exception, match="API error"):
                    generate("prompt")


# ---------------------------------------------------------------------------
# Auto-detection
# ---------------------------------------------------------------------------


class TestBackendAutoDetection:
    def test_auto_uses_ollama_when_reachable(self):
        from gitscribe import backend

        with patch.object(backend, "BACKEND", "auto"):
            with patch.object(backend, "_ollama_reachable", return_value=True):
                with patch("gitscribe.ollama_backend.requests.post") as mock_post:
                    mock_resp = MagicMock()
                    mock_resp.json.return_value = {"response": "from ollama"}
                    mock_resp.raise_for_status = MagicMock()
                    mock_post.return_value = mock_resp
                    result = backend.generate("prompt")
        assert result == "from ollama"

    def test_auto_falls_back_to_claude_when_ollama_unreachable(self):
        from gitscribe import backend

        mock_content = MagicMock()
        mock_content.text = "from claude"
        mock_message = MagicMock()
        mock_message.content = [mock_content]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch.object(backend, "_ollama_reachable", return_value=False):
            with patch.object(backend, "BACKEND", "auto"):
                with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "key"}):
                    with patch(
                        "gitscribe.claude_backend.anthropic.Anthropic",
                        return_value=mock_client,
                    ):
                        result = backend.generate("prompt")
        assert result == "from claude"

    def test_unknown_backend_raises(self):
        from gitscribe import backend

        with patch.object(backend, "BACKEND", "unknown"):
            with pytest.raises(RuntimeError, match="Unknown backend"):
                backend.generate("prompt")

    def test_forced_ollama(self):
        from gitscribe import backend

        with patch.object(backend, "BACKEND", "ollama"):
            with patch("gitscribe.ollama_backend.requests.post") as mock_post:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {"response": "ollama result"}
                mock_resp.raise_for_status = MagicMock()
                mock_post.return_value = mock_resp
                result = backend.generate("prompt")
        assert result == "ollama result"

    def test_forced_claude(self):
        from gitscribe import backend

        mock_content = MagicMock()
        mock_content.text = "claude result"
        mock_message = MagicMock()
        mock_message.content = [mock_content]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message

        with patch.object(backend, "BACKEND", "claude"):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "key"}):
                with patch(
                    "gitscribe.claude_backend.anthropic.Anthropic",
                    return_value=mock_client,
                ):
                    result = backend.generate("prompt")
        assert result == "claude result"


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


class TestPrompts:
    def test_commit_message_prompt_contains_diff(self):
        from gitscribe.prompts import build_commit_message_prompt

        p = build_commit_message_prompt("diff content")
        assert "diff content" in p
        assert "conventional" in p.lower()

    def test_pr_description_prompt_contains_branches(self):
        from gitscribe.prompts import build_pr_description_prompt

        p = build_pr_description_prompt("diff", "main", "feature/x")
        assert "main" in p
        assert "feature/x" in p

    def test_review_diff_prompt_contains_diff(self):
        from gitscribe.prompts import build_review_diff_prompt

        p = build_review_diff_prompt("diff content")
        assert "diff content" in p
        assert "issues" in p.lower() or "review" in p.lower()

    def test_suggest_branch_name_prompt_contains_description(self):
        from gitscribe.prompts import build_suggest_branch_name_prompt

        p = build_suggest_branch_name_prompt("add user login")
        assert "add user login" in p
        assert "kebab" in p.lower() or "branch" in p.lower()

    def test_summarize_changes_prompt_contains_diff(self):
        from gitscribe.prompts import build_summarize_changes_prompt

        p = build_summarize_changes_prompt("diff content")
        assert "diff content" in p
        assert "summar" in p.lower()
