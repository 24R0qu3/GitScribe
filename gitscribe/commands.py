import subprocess

from .backend import generate
from .config import DIFF_MAX_LINES, REPO_PATH
from .prompts import (
    build_commit_message_prompt,
    build_pr_description_prompt,
    build_review_diff_prompt,
    build_suggest_branch_name_prompt,
    build_summarize_changes_prompt,
)

_GIT_TIMEOUT = 10


def _get_diff(
    repo_path: str,
    staged: bool = False,
    paths: list[str] | None = None,
    max_lines: int = DIFF_MAX_LINES,
) -> dict:
    cmd = ["git", "diff"]
    if staged:
        cmd.append("--staged")
    if paths:
        cmd += ["--"] + paths
    try:
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            timeout=_GIT_TIMEOUT,
        )
    except OSError as e:
        return {"error": f"Git error: {e}"}
    if result.returncode != 0:
        return {"error": f"Git error: {result.stderr.strip()}"}
    lines = result.stdout.splitlines()
    truncated = len(lines) > max_lines
    return {"diff": "\n".join(lines[:max_lines]), "truncated": truncated}


def _err(msg: str) -> dict:
    return {"error": msg}


def _ok(**kwargs) -> dict:
    return {"status": "ok", **kwargs}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def _data_generate_commit_message(repo_path: str = REPO_PATH, staged_only: bool = True) -> dict:
    diff_result = _get_diff(repo_path, staged=staged_only)
    if "error" in diff_result:
        return diff_result
    if not diff_result["diff"].strip():
        return _err("No changes found to generate a commit message from.")
    try:
        message = generate(build_commit_message_prompt(diff_result["diff"]))
    except RuntimeError as e:
        return _err(str(e))
    return _ok(message=message, truncated=diff_result["truncated"])


def _data_generate_pr_description(
    repo_path: str = REPO_PATH, base_branch: str = "main"
) -> dict:
    try:
        result = subprocess.run(
            ["git", "diff", f"{base_branch}...HEAD"],
            cwd=repo_path,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            timeout=_GIT_TIMEOUT,
        )
    except OSError as e:
        return _err(f"Git error: {e}")
    if result.returncode != 0:
        return _err(f"Git error: {result.stderr.strip()}")

    lines = result.stdout.splitlines()
    truncated = len(lines) > DIFF_MAX_LINES
    diff = "\n".join(lines[:DIFF_MAX_LINES])

    if not diff.strip():
        return _err(f"No diff found between '{base_branch}' and HEAD.")

    try:
        head_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            timeout=_GIT_TIMEOUT,
        )
        head_branch = head_result.stdout.strip() if head_result.returncode == 0 else "HEAD"
    except OSError:
        head_branch = "HEAD"

    try:
        raw = generate(build_pr_description_prompt(diff, base_branch, head_branch))
    except RuntimeError as e:
        return _err(str(e))

    lines_out = raw.strip().splitlines()
    title = lines_out[0].strip() if lines_out else ""
    body = "\n".join(lines_out[1:]).strip() if len(lines_out) > 1 else ""
    return _ok(title=title, body=body, truncated=truncated)


def _data_review_diff(
    repo_path: str = REPO_PATH,
    staged: bool = False,
    paths: list[str] | None = None,
) -> dict:
    diff_result = _get_diff(repo_path, staged=staged, paths=paths)
    if "error" in diff_result:
        return diff_result
    if not diff_result["diff"].strip():
        return _err("No changes found to review.")
    try:
        review = generate(build_review_diff_prompt(diff_result["diff"]))
    except RuntimeError as e:
        return _err(str(e))
    return _ok(review=review, truncated=diff_result["truncated"])


def _data_suggest_branch_name(description: str = "") -> dict:
    if not description.strip():
        return _err("description is required.")
    try:
        branch_name = generate(build_suggest_branch_name_prompt(description))
    except RuntimeError as e:
        return _err(str(e))
    return _ok(branch_name=branch_name.strip())


def _data_summarize_changes(
    repo_path: str = REPO_PATH,
    staged: bool = False,
    paths: list[str] | None = None,
) -> dict:
    diff_result = _get_diff(repo_path, staged=staged, paths=paths)
    if "error" in diff_result:
        return diff_result
    if not diff_result["diff"].strip():
        return _err("No changes found to summarize.")
    try:
        summary = generate(build_summarize_changes_prompt(diff_result["diff"]))
    except RuntimeError as e:
        return _err(str(e))
    return _ok(summary=summary, truncated=diff_result["truncated"])
