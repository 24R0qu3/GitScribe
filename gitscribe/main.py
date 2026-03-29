import argparse
import asyncio
import json
import sys
from pathlib import Path

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
    result = _data_generate_commit_message(repo_path=args.repo, staged_only=not args.unstaged)
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


def _patch_claude_json(app_name: str, remove: bool) -> None:
    claude_json = Path.home() / ".claude.json"
    exe = str(Path(sys.argv[0]).resolve())

    data: dict = {}
    if claude_json.exists():
        try:
            data = json.loads(claude_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            _fail("~/.claude.json contains invalid JSON.")

    servers: dict = data.setdefault("mcpServers", {})

    if remove:
        if app_name in servers:
            del servers[app_name]
            claude_json.write_text(json.dumps(data, indent=2), encoding="utf-8")
            console.print(f"[green]Removed[/green] {app_name} from ~/.claude.json")
        else:
            console.print(f"[dim]{app_name} not registered — nothing to remove.[/dim]")
        return

    servers[app_name] = {"type": "stdio", "command": exe, "args": ["mcp"], "env": {}}
    claude_json.write_text(json.dumps(data, indent=2), encoding="utf-8")
    console.print(f"[green]Registered[/green] {app_name} → [cyan]{exe}[/cyan]")
    console.print("[dim]Restart Claude Code to activate.[/dim]")


def cmd_patch_claude(args: argparse.Namespace) -> None:
    _patch_claude_json("gitscribe", remove=args.remove)


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
        description="AI-powered git assistant — commit messages, PR descriptions, reviews, and more.",  # noqa: E501
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

    # patch-claude
    p = sub.add_parser("patch-claude", help="Register/unregister in ~/.claude.json.")
    p.add_argument("--remove", action="store_true", help="Remove from ~/.claude.json.")
    p.set_defaults(func=cmd_patch_claude)

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
