from unittest.mock import patch

from gitscribe.commands import (
    _data_generate_commit_message,
    _data_generate_pr_description,
    _data_review_diff,
    _data_suggest_branch_name,
    _data_summarize_changes,
)


def _diff_result(diff="diff content", truncated=False):
    return {"diff": diff, "truncated": truncated}


# ---------------------------------------------------------------------------
# generate_commit_message
# ---------------------------------------------------------------------------


class TestDataGenerateCommitMessage:
    def test_success(self):
        with (
            patch("gitscribe.commands._get_diff", return_value=_diff_result()),
            patch("gitscribe.commands.generate", return_value="feat: add thing"),
        ):
            r = _data_generate_commit_message("/repo")
        assert r == {"status": "ok", "message": "feat: add thing", "truncated": False}

    def test_empty_diff(self):
        with patch("gitscribe.commands._get_diff", return_value=_diff_result(diff="  ")):
            r = _data_generate_commit_message("/repo")
        assert "error" in r

    def test_git_error(self):
        with patch("gitscribe.commands._get_diff", return_value={"error": "Git error: bad"}):
            r = _data_generate_commit_message("/repo")
        assert "error" in r

    def test_backend_error(self):
        with (
            patch("gitscribe.commands._get_diff", return_value=_diff_result()),
            patch("gitscribe.commands.generate", side_effect=RuntimeError("no backend")),
        ):
            r = _data_generate_commit_message("/repo")
        assert "error" in r
        assert "no backend" in r["error"]

    def test_truncated_flag_passed_through(self):
        with (
            patch("gitscribe.commands._get_diff", return_value=_diff_result(truncated=True)),
            patch("gitscribe.commands.generate", return_value="feat: x"),
        ):
            r = _data_generate_commit_message("/repo")
        assert r["truncated"] is True


# ---------------------------------------------------------------------------
# generate_pr_description
# ---------------------------------------------------------------------------


class TestDataGeneratePrDescription:
    def _mock_run(self, diff="diff content", branch="feature/x"):
        from unittest.mock import MagicMock

        def side(cmd, **kwargs):
            m = MagicMock()
            m.returncode = 0
            if "rev-parse" in cmd:
                m.stdout = f"{branch}\n"
            else:
                lines = diff.splitlines()
                m.stdout = "\n".join(lines)
            return m

        return side

    def test_success(self):
        with (
            patch("gitscribe.commands.subprocess.run", side_effect=self._mock_run()),
            patch(
                "gitscribe.commands.generate",
                return_value="PR title\n\nPR body here",
            ),
        ):
            r = _data_generate_pr_description("/repo", "main")
        assert r["status"] == "ok"
        assert r["title"] == "PR title"
        assert "body" in r

    def test_empty_diff(self):
        with patch("gitscribe.commands.subprocess.run", side_effect=self._mock_run(diff="")):
            r = _data_generate_pr_description("/repo", "main")
        assert "error" in r

    def test_git_error(self):
        from unittest.mock import MagicMock

        m = MagicMock()
        m.returncode = 1
        m.stderr = "unknown revision"
        with patch("gitscribe.commands.subprocess.run", return_value=m):
            r = _data_generate_pr_description("/repo", "main")
        assert "error" in r

    def test_backend_error(self):
        with (
            patch("gitscribe.commands.subprocess.run", side_effect=self._mock_run()),
            patch("gitscribe.commands.generate", side_effect=RuntimeError("no backend")),
        ):
            r = _data_generate_pr_description("/repo", "main")
        assert "error" in r


# ---------------------------------------------------------------------------
# review_diff
# ---------------------------------------------------------------------------


class TestDataReviewDiff:
    def test_success(self):
        with (
            patch("gitscribe.commands._get_diff", return_value=_diff_result()),
            patch("gitscribe.commands.generate", return_value="Looks good."),
        ):
            r = _data_review_diff("/repo")
        assert r == {"status": "ok", "review": "Looks good.", "truncated": False}

    def test_empty_diff(self):
        with patch("gitscribe.commands._get_diff", return_value=_diff_result(diff="")):
            r = _data_review_diff("/repo")
        assert "error" in r

    def test_git_error(self):
        with patch("gitscribe.commands._get_diff", return_value={"error": "Git error: bad"}):
            r = _data_review_diff("/repo")
        assert "error" in r

    def test_backend_error(self):
        with (
            patch("gitscribe.commands._get_diff", return_value=_diff_result()),
            patch("gitscribe.commands.generate", side_effect=RuntimeError("fail")),
        ):
            r = _data_review_diff("/repo")
        assert "error" in r


# ---------------------------------------------------------------------------
# suggest_branch_name
# ---------------------------------------------------------------------------


class TestDataSuggestBranchName:
    def test_success(self):
        with patch("gitscribe.commands.generate", return_value="feat/add-user-login"):
            r = _data_suggest_branch_name("add user login feature")
        assert r == {"status": "ok", "branch_name": "feat/add-user-login"}

    def test_empty_description(self):
        r = _data_suggest_branch_name("")
        assert "error" in r

    def test_whitespace_description(self):
        r = _data_suggest_branch_name("   ")
        assert "error" in r

    def test_backend_error(self):
        with patch("gitscribe.commands.generate", side_effect=RuntimeError("fail")):
            r = _data_suggest_branch_name("some task")
        assert "error" in r


# ---------------------------------------------------------------------------
# summarize_changes
# ---------------------------------------------------------------------------


class TestDataSummarizeChanges:
    def test_success(self):
        with (
            patch("gitscribe.commands._get_diff", return_value=_diff_result()),
            patch("gitscribe.commands.generate", return_value="A function was added."),
        ):
            r = _data_summarize_changes("/repo")
        assert r == {"status": "ok", "summary": "A function was added.", "truncated": False}

    def test_empty_diff(self):
        with patch("gitscribe.commands._get_diff", return_value=_diff_result(diff="")):
            r = _data_summarize_changes("/repo")
        assert "error" in r

    def test_git_error(self):
        with patch("gitscribe.commands._get_diff", return_value={"error": "Git error: bad"}):
            r = _data_summarize_changes("/repo")
        assert "error" in r

    def test_backend_error(self):
        with (
            patch("gitscribe.commands._get_diff", return_value=_diff_result()),
            patch("gitscribe.commands.generate", side_effect=RuntimeError("fail")),
        ):
            r = _data_summarize_changes("/repo")
        assert "error" in r
