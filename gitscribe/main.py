import argparse
import asyncio
import json
import sys

from rich.console import Console

from .commands import (
    _data_generate_commit_message,
    _data_generate_pr_description,
    _data_review_diff,
    _data_suggest_branch_name,
    _data_summarize_changes,
)
from .config import REPO_PATH

console = Console()


def _fail(msg: str) -> None:
    console.print(f"[red]Error:[/red] {msg}")
    raise SystemExit(1)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_commit_msg(args: argparse.Namespace) -> None:
    result = _data_generate_commit_message(
        repo_path=args.repo, staged_only=not args.unstaged
    )
    if "error" in result:
        _fail(result["error"])
    if result.get("truncated"):
        console.print("[yellow]Warning:[/yellow] diff was truncated.")
    console.print(f"[cyan]{result['message']}[/cyan]")


def cmd_pr_desc(args: argparse.Namespace) -> None:
    result = _data_generate_pr_description(repo_path=args.repo, base_branch=args.base)
    if "error" in result:
        _fail(result["error"])
    if result.get("truncated"):
        console.print("[yellow]Warning:[/yellow] diff was truncated.")
    console.print(f"[bold]{result['title']}[/bold]")
    if result["body"]:
        console.print()
        console.print(result["body"])


def cmd_review(args: argparse.Namespace) -> None:
    paths = args.paths if args.paths else None
    result = _data_review_diff(repo_path=args.repo, staged=args.staged, paths=paths)
    if "error" in result:
        _fail(result["error"])
    if result.get("truncated"):
        console.print("[yellow]Warning:[/yellow] diff was truncated.")
    console.print(result["review"])


def cmd_branch_name(args: argparse.Namespace) -> None:
    result = _data_suggest_branch_name(description=args.description)
    if "error" in result:
        _fail(result["error"])
    console.print(f"[cyan]{result['branch_name']}[/cyan]")


def cmd_summarize(args: argparse.Namespace) -> None:
    paths = args.paths if args.paths else None
    result = _data_summarize_changes(repo_path=args.repo, staged=args.staged, paths=paths)
    if "error" in result:
        _fail(result["error"])
    if result.get("truncated"):
        console.print("[yellow]Warning:[/yellow] diff was truncated.")
    console.print(result["summary"])


def cmd_mcp(args: argparse.Namespace) -> None:
    if args.print_config:
        venv_exe = sys.executable.replace("python.exe", "gitscribe.exe")
        cfg = {"mcpServers": {"gitscribe": {"command": venv_exe, "args": ["mcp"]}}}
        console.print(json.dumps(cfg, indent=2))
        return

    from .server import main as server_main

    asyncio.run(server_main())


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gitscribe",
        description="AI-powered git assistant — commit messages, PR descriptions, reviews, and more.",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    _repo = dict(default=REPO_PATH, metavar="PATH", help="Path to git repository.")

    # commit-msg
    p = sub.add_parser("commit-msg", help="Generate a conventional commit message.")
    p.add_argument("--unstaged", action="store_true", help="Use unstaged diff instead of staged.")
    p.add_argument("--repo", **_repo)
    p.set_defaults(func=cmd_commit_msg)

    # pr-desc
    p = sub.add_parser("pr-desc", help="Generate a PR title and description.")
    p.add_argument("base", metavar="BASE_BRANCH", help="Branch to diff against.")
    p.add_argument("--repo", **_repo)
    p.set_defaults(func=cmd_pr_desc)

    # review
    p = sub.add_parser("review", help="Review a diff for issues and suggestions.")
    p.add_argument("--staged", action="store_true", help="Review staged diff.")
    p.add_argument("paths", nargs="*", help="Limit to specific paths.")
    p.add_argument("--repo", **_repo)
    p.set_defaults(func=cmd_review)

    # branch-name
    p = sub.add_parser("branch-name", help="Suggest a branch name from a task description.")
    p.add_argument("description", help="Plain-English task description.")
    p.set_defaults(func=cmd_branch_name)

    # summarize
    p = sub.add_parser("summarize", help="Summarize changes in plain English.")
    p.add_argument("--staged", action="store_true", help="Summarize staged diff.")
    p.add_argument("paths", nargs="*", help="Limit to specific paths.")
    p.add_argument("--repo", **_repo)
    p.set_defaults(func=cmd_summarize)

    # mcp
    p = sub.add_parser("mcp", help="Start the MCP stdio server.")
    p.add_argument(
        "--print-config",
        action="store_true",
        help="Print Claude Code MCP config snippet and exit.",
    )
    p.set_defaults(func=cmd_mcp)

    return parser


def run() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    run()
