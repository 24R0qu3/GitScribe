def build_commit_message_prompt(diff: str) -> str:
    return f"""\
Generate a conventional commit message for the following git diff.

Rules:
- type must be one of: feat, fix, refactor, docs, test, chore, style, perf
- use imperative mood ("add", not "added" or "adds")
- title must be 72 characters or fewer
- no markdown formatting
- return only the commit message, nothing else

Git diff:
{diff}
"""


def build_pr_description_prompt(diff: str, base_branch: str, head_branch: str) -> str:
    return f"""\
Generate a pull request title and description for the following git diff.

Context:
- Base branch: {base_branch}
- Head branch: {head_branch}

Rules:
- Return exactly two sections separated by a blank line:
  1. First line: the PR title (max 72 characters, no prefix)
  2. Rest: the PR body in markdown (bullet points, what changed and why)
- No extra commentary, just title and body

Git diff:
{diff}
"""


def build_review_diff_prompt(diff: str) -> str:
    return f"""\
Review the following git diff and provide concise, actionable feedback.

Structure your response as:
1. **Summary** — one sentence describing what changed
2. **Issues** — list any bugs, security concerns, or logic errors (skip if none)
3. **Suggestions** — list improvements for readability, performance, or style (skip if none)

Be specific and brief. No praise, no filler.

Git diff:
{diff}
"""


def build_suggest_branch_name_prompt(description: str) -> str:
    return f"""\
Generate a git branch name for the following task description.

Rules:
- Use kebab-case (lowercase, hyphens only)
- Prefix with a type: feat/, fix/, refactor/, docs/, chore/
- Max 50 characters total
- No special characters except hyphens and forward slash
- Return only the branch name, nothing else

Task description:
{description}
"""


def build_summarize_changes_prompt(diff: str) -> str:
    return f"""\
Summarize the following git diff in plain English.

Rules:
- Write 2-4 sentences maximum
- Focus on what changed and why it matters, not how
- No bullet points, no markdown, just prose
- Return only the summary, nothing else

Git diff:
{diff}
"""
