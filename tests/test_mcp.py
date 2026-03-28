import json
from unittest.mock import patch

import pytest
from mcp.types import TextContent


def _ok(**kw):
    return {"status": "ok", **kw}


async def _call(name: str, args: dict) -> dict:
    from gitscribe.server import call_tool

    result = await call_tool(name, args)
    assert isinstance(result[0], TextContent)
    return json.loads(result[0].text)


# ---------------------------------------------------------------------------
# list_tools
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_tools_returns_all_5():
    from gitscribe.server import list_tools

    tools = await list_tools()
    names = {t.name for t in tools}
    assert names == {
        "generate_commit_message",
        "generate_pr_description",
        "review_diff",
        "suggest_branch_name",
        "summarize_changes",
    }


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_commit_message():
    with patch(
        "gitscribe.server._data_generate_commit_message",
        return_value=_ok(message="feat: x", truncated=False),
    ):
        data = await _call("generate_commit_message", {})
    assert data["message"] == "feat: x"


@pytest.mark.asyncio
async def test_generate_pr_description():
    with patch(
        "gitscribe.server._data_generate_pr_description",
        return_value=_ok(title="My PR", body="## Changes", truncated=False),
    ):
        data = await _call("generate_pr_description", {"base_branch": "main"})
    assert data["title"] == "My PR"


@pytest.mark.asyncio
async def test_review_diff():
    with patch(
        "gitscribe.server._data_review_diff",
        return_value=_ok(review="Looks good.", truncated=False),
    ):
        data = await _call("review_diff", {})
    assert data["review"] == "Looks good."


@pytest.mark.asyncio
async def test_suggest_branch_name():
    with patch(
        "gitscribe.server._data_suggest_branch_name",
        return_value=_ok(branch_name="feat/add-login"),
    ):
        data = await _call("suggest_branch_name", {"description": "add login"})
    assert data["branch_name"] == "feat/add-login"


@pytest.mark.asyncio
async def test_summarize_changes():
    with patch(
        "gitscribe.server._data_summarize_changes",
        return_value=_ok(summary="Added a login function.", truncated=False),
    ):
        data = await _call("summarize_changes", {})
    assert data["summary"] == "Added a login function."


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_tool_returns_error():
    data = await _call("no_such_tool", {})
    assert "error" in data


@pytest.mark.asyncio
async def test_exception_returns_error():
    with patch(
        "gitscribe.server._data_generate_commit_message",
        side_effect=RuntimeError("boom"),
    ):
        data = await _call("generate_commit_message", {})
    assert "error" in data
    assert "boom" in data["error"]


@pytest.mark.asyncio
async def test_error_dict_passthrough():
    with patch(
        "gitscribe.server._data_generate_commit_message",
        return_value={"error": "No staged changes."},
    ):
        data = await _call("generate_commit_message", {})
    assert data == {"error": "No staged changes."}
