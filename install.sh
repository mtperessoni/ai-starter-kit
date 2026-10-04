#!/usr/bin/env bash
# Installs the /ai-kit skill for this user and the global CLAUDE.md block.
# Run once per machine, and again after pulling the kit to refresh both.
# Usage: ./install.sh [--no-global-block]
set -euo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_HOME="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
SKILL_DIR="$CLAUDE_HOME/skills/ai-kit"
GLOBAL_MD="$CLAUDE_HOME/CLAUDE.md"
START="<!-- ai-kit:start"
END="<!-- ai-kit:end -->"

mkdir -p "$SKILL_DIR"
rm -rf "$SKILL_DIR/reference"
cp -R "$KIT/installer/ai-kit/." "$SKILL_DIR/"
printf '%s\n' "$KIT" > "$SKILL_DIR/kit-path"
echo "skill: $SKILL_DIR (kit at $KIT)"

if [ "${1:-}" != "--no-global-block" ]; then
    touch "$GLOBAL_MD"
    tmp="$(mktemp)"
    awk -v start="$START" -v end="$END" '
        index($0, start) == 1 { skip = 1; next }
        skip && index($0, end) == 1 { skip = 0; next }
        !skip { print }
    ' "$GLOBAL_MD" > "$tmp"
    { cat "$tmp"; [ -s "$tmp" ] && echo; cat "$KIT/global/CLAUDE.md"; } > "$GLOBAL_MD"
    rm -f "$tmp"
    echo "global block: $GLOBAL_MD"
fi

echo "done. In a project, open Claude Code and run: /ai-kit install"
