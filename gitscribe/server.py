import asyncio
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from rich.console import Console

from .commands import (
    _data_generate_commit_message,
    _data_generate_pr_description,
    _data_review_diff,
    _data_suggest_branch_name,
    _data_summarize_changes,
)
from .config import REPO_PATH

console = Console(stderr=True)

server = Server("gitscribe")

_REPO = {
    "type": "string",
    "description": "Absolute path to the git repository.",
    "default": REPO_PATH,
}

_TOOLS = [
    Tool(
        name="generate_commit_message",
        description=(
            "Generate a conventional commit message from staged (or unstaged) git changes. "
            "Uses a local Ollama model if running, otherwise falls back to the Claude API."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "repo_path": _REPO,
                "staged_only": {
                    "type": "boolean",
                    "description": "Use only staged diff (default). Set false to include unstaged.",
                    "default": True,
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="generate_pr_description",
        description=(
            "Generate a pull request title and markdown body by diffing the current branch "
            "against a base branch."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "repo_path": _REPO,
                "base_branch": {
                    "type": "string",
                    "description": "Branch to diff against.",
                    "default": "main",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="review_diff",
        description="Review a diff and return a structured summary, issues, and suggestions.",
        inputSchema={
            "type": "object",
            "properties": {
                "repo_path": _REPO,
                "staged": {
                    "type": "boolean",
                    "description": "Review staged diff instead of unstaged.",
                    "default": False,
                },
                "paths": {
                    "type": ["array", "null"],
                    "items": {"type": "string"},
                    "description": "Limit review to these paths. Omit for full diff.",
                    "default": None,
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="suggest_branch_name",
        description="Suggest a git branch name slug from a plain-English task description.",
        inputSchema={
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Plain-English description of the task or feature.",
                },
            },
            "required": ["description"],
        },
    ),
    Tool(
        name="summarize_changes",
        description="Summarize git changes in plain English prose.",
        inputSchema={
            "type": "object",
            "properties": {
                "repo_path": _REPO,
                "staged": {
                    "type": "boolean",
                    "description": "Summarize staged diff instead of unstaged.",
                    "default": False,
                },
                "paths": {
                    "type": ["array", "null"],
                    "items": {"type": "string"},
                    "description": "Limit summary to these paths. Omit for full diff.",
                    "default": None,
                },
            },
            "required": [],
        },
    ),
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    return _TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    r = arguments.get("repo_path", REPO_PATH)

    try:
        match name:
            case "generate_commit_message":
                result = await asyncio.to_thread(
                    _data_generate_commit_message,
                    r,
                    arguments.get("staged_only", True),
                )
            case "generate_pr_description":
                result = await asyncio.to_thread(
                    _data_generate_pr_description,
                    r,
                    arguments.get("base_branch", "main"),
                )
            case "review_diff":
                result = await asyncio.to_thread(
                    _data_review_diff,
                    r,
                    arguments.get("staged", False),
                    arguments.get("paths") or None,
                )
            case "suggest_branch_name":
                result = await asyncio.to_thread(
                    _data_suggest_branch_name,
                    arguments.get("description", ""),
                )
            case "summarize_changes":
                result = await asyncio.to_thread(
                    _data_summarize_changes,
                    r,
                    arguments.get("staged", False),
                    arguments.get("paths") or None,
                )
            case _:
                result = {"error": f"Unknown tool: {name}"}

    except Exception as e:
        result = {"error": str(e)}

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]


async def main() -> None:
    console.print("[dim]Starting gitscribe MCP server...[/dim]")
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
