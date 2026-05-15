#!/usr/bin/env bash
set -euo pipefail

# Writes Claude Code settings with Supabase MCP configuration.
# Expected env vars: SUPABASE_PROJECT_ID, SUPABASE_SERVICE_KEY, ALLOWED_TOOLS

if [ -z "${SUPABASE_PROJECT_ID:-}" ]; then
  echo "::error::supabase_project_id input is required"
  exit 1
fi

if [ -z "${SUPABASE_SERVICE_KEY:-}" ]; then
  echo "::error::supabase_service_key input is required"
  exit 1
fi

# Build the allow list from comma-separated input
IFS=',' read -ra TOOLS <<< "${ALLOWED_TOOLS:-Bash,Read,Write,Edit}"
ALLOW_JSON=$(printf '%s\n' "${TOOLS[@]}" | sed 's/^ *//;s/ *$//' | jq -R . | jq -s .)

mkdir -p ~/.claude

# Write settings — MCP server config + permissions
cat > ~/.claude/settings.json << SETTINGS
{
  "permissions": {
    "allow": ${ALLOW_JSON}
  },
  "mcpServers": {
    "Supabase": {
      "command": "npx",
      "args": [
        "-y",
        "@anthropic-ai/claude-mcp-server-supabase",
        "--access-token", "${SUPABASE_SERVICE_KEY}",
        "--project-id", "${SUPABASE_PROJECT_ID}"
      ]
    }
  }
}
SETTINGS

echo "Claude Code configured with Supabase MCP (project: ${SUPABASE_PROJECT_ID})"
echo "Allowed tools: ${ALLOWED_TOOLS}"
