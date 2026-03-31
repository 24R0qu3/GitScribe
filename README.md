# GitScribe

AI-powered git assistant — generates commit messages, PR descriptions, diff reviews, and branch names using Ollama or the Claude API.

## Tools (5 MCP)

| Tool | Description |
|---|---|
| `generate_commit_message` | Conventional commit from staged diff |
| `generate_pr_description` | Title + markdown body from branch diff |
| `review_diff` | Summary, issues, and suggestions for a diff |
| `suggest_branch_name` | kebab-case branch name from a description |
| `summarize_changes` | 2–4 sentence plain-prose summary |

## Backends

| Backend | When used |
|---|---|
| `ollama` | Always use local Ollama |
| `claude` | Always use Claude API |
| `auto` _(default)_ | Ollama if running or startable, Claude API otherwise |

## Installation

### 1. Clone and set up the virtual environment

```bash
git clone https://github.com/24R0qu3/GitScribe.git
cd GitScribe
python -m venv .venv
```

### 2. Activate and install

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -e .
```

This registers the `gitscribe` executable inside the venv.

### 3. Register with Claude Code

Add the following to `~/.claude.json` under `mcpServers`:

```json
"gitscribe": {
  "type": "stdio",
  "command": "/absolute/path/to/GitScribe/.venv/Scripts/gitscribe.exe",
  "args": ["mcp"],
  "env": {}
}
```

> **macOS / Linux:** the executable is `.venv/bin/gitscribe` (no `.exe`).

Restart Claude Code — the 5 tools will appear automatically.

### 4. Configure backend

Create `~/.config/gitscribe/config.toml`:

```toml
backend = "auto"          # auto | ollama | claude
ollama_model = "qwen3:1.7b"
ollama_url = "http://localhost:11434/api/generate"
diff_max_lines = 200
```

For the Claude backend, set your API key:

```bash
# Windows
set ANTHROPIC_API_KEY=sk-ant-...

# macOS / Linux
export ANTHROPIC_API_KEY=sk-ant-...
```

## CLI

```bash
gitscribe commit-msg                    # generate commit message from staged diff
gitscribe commit-msg --no-staged        # use unstaged diff instead
gitscribe pr-desc --base main           # PR description vs main
gitscribe review                        # review staged diff
gitscribe branch-name "add dark mode"   # suggest a branch name
gitscribe summarize                     # summarize staged changes
```

## Companion

[GitMCP](https://github.com/24R0qu3/GitMCP) — pure git operations MCP server (22 tools). GitScribe uses git directly and works standalone, but pairs naturally with GitMCP for full git workflow coverage.
