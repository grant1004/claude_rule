#!/bin/sh
# claude_rule guard: PreToolUse hook for Edit|Write|NotebookEdit.
#
# The main conversation dispatches edits to a worker; it does not make them.
# This hook blocks an edit to a project file when the call comes from the
# main conversation, and lets every call made inside a subagent through.
#
# The script always exits 0. To block a call it prints a PreToolUse "deny"
# decision as JSON on stdout; printing nothing lets the call go ahead. A crash,
# a missing file or a damaged copy of this script therefore prints no decision
# and blocks nothing, so a problem in the guard can never stop work. (Exit
# code 2 would also block, but a shell syntax error exits with 2 as well.)
#
# Set CR_GUARD=off in the environment of a session that is meant to edit files
# itself.

[ "${CR_GUARD:-on}" = "off" ] && exit 0

input=$(cat)

# A tool call made inside a subagent or teammate carries a top-level agent_id.
# Text inside a JSON string has its quotes escaped (\"), so file content that
# merely mentions agent_id cannot match these patterns.
case "$input" in
  *'"agent_id":"'[!\"]*|*'"agent_id": "'[!\"]*) exit 0 ;;
esac

# Plan mode only lets Claude write its own plan file.
case "$input" in
  *'"permission_mode":"plan"'*|*'"permission_mode": "plan"'*) exit 0 ;;
esac

# The file being edited: the first real file_path or notebook_path key.
pair=$(printf '%s' "$input" | grep -oE '"(file_path|notebook_path)"[[:space:]]*:[[:space:]]*"([^"\\]|\\.)*"' | head -n 1)
[ -z "$pair" ] && exit 0

# Drop the key, undo JSON escaping of \ and /, and compare in lower case with
# forward slashes so Windows and POSIX paths are handled the same way.
path=$(printf '%s' "$pair" \
  | sed -E -e 's/^"[a-z_]+"[[:space:]]*:[[:space:]]*"//' -e 's/"$//' -e 's|\\\\|/|g' -e 's|\\/|/|g' \
  | tr 'A-Z' 'a-z')
[ -z "$path" ] && exit 0

case "$path" in
  */.claude/worktrees/*) ;;      # a worker's worktree is not the main conversation's to edit
  */.claude/*) exit 0 ;;         # Claude Code's own files: plans, memory, settings, rules
esac

case "$path" in
  wip.md|*/wip.md) exit 0 ;;                                  # the task ledger
  claude.md|*/claude.md|claude.local.md|*/claude.local.md) exit 0 ;;
  docs/*.md|*/docs/*.md) exit 0 ;;                            # plans, kickoff notes, analyses
  */info/exclude) exit 0 ;;                                   # git's local exclude file
esac

cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"claude_rule guard: the main conversation must not edit project files itself. Write a dispatch brief and hand this change to the cr-worker agent (use cr-worker-isolated when another worker is using the working directory), update WIP.md, then end the turn. Do not work around this with Bash or PowerShell. The main conversation may write only WIP.md, CLAUDE.md and Markdown files under docs/."}}
EOF
exit 0
