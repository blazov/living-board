#!/bin/bash
# Living Board — Interactive Setup
# Sets up the database, memory system, dashboard, and agent runner.

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${GREEN}  ✓${NC} $1"; }
warn()  { echo -e "${YELLOW}  !${NC} $1"; }
error() { echo -e "${RED}  ✗${NC} $1"; }
step()  { echo -e "\n${CYAN}${BOLD}$1${NC}"; }

echo ""
echo -e "${BOLD}  ╔═══════════════════════════════════════╗${NC}"
echo -e "${BOLD}  ║         Living Board — Setup           ║${NC}"
echo -e "${BOLD}  ║   Self-learning autonomous AI agent    ║${NC}"
echo -e "${BOLD}  ╚═══════════════════════════════════════╝${NC}"
echo ""

# ──────────────────────────────────────────────
# Step 0: Verify we're in the right directory
# ──────────────────────────────────────────────
if [ ! -f "CLAUDE.md" ] || [ ! -d "dashboard" ]; then
  error "Not in the living-board root directory."
  error "Run this script from the repo root: cd living-board && ./setup.sh"
  exit 1
fi

# ──────────────────────────────────────────────
# Step 1: Prerequisites
# ──────────────────────────────────────────────
step "Checking prerequisites..."

PREREQS_OK=true

# Node.js
if command -v node &>/dev/null; then
  NODE_VER=$(node --version | sed 's/v//' | cut -d. -f1)
  if [ "$NODE_VER" -ge 20 ]; then
    info "Node.js $(node --version)"
  else
    error "Node.js $(node --version) — need v20+"
    PREREQS_OK=false
  fi
else
  error "Node.js — not found (need v20+)"
  PREREQS_OK=false
fi

# npm
if command -v npm &>/dev/null; then
  info "npm $(npm --version)"
else
  error "npm — not found"
  PREREQS_OK=false
fi

# Python 3
if command -v python3 &>/dev/null; then
  info "Python $(python3 --version 2>&1 | sed 's/Python //')"
else
  error "Python 3 — not found"
  PREREQS_OK=false
fi

# git
if command -v git &>/dev/null; then
  info "git $(git --version | sed 's/git version //')"
else
  error "git — not found"
  PREREQS_OK=false
fi

# Docker (soft requirement for memory system)
HAS_DOCKER=false
if command -v docker &>/dev/null; then
  info "Docker $(docker --version 2>&1 | sed 's/Docker version //' | cut -d, -f1)"
  HAS_DOCKER=true
else
  warn "Docker — not found (needed for memory system)"
fi

# Claude Code CLI (soft requirement)
HAS_CLAUDE=false
if command -v claude &>/dev/null; then
  info "Claude Code CLI found"
  HAS_CLAUDE=true
else
  warn "Claude Code CLI — not found (optional)"
fi

# openssl
if command -v openssl &>/dev/null; then
  info "openssl available"
else
  warn "openssl — not found (will use fallback for secret generation)"
fi

if [ "$PREREQS_OK" = false ]; then
  echo ""
  error "Missing required prerequisites. Install them and re-run."
  exit 1
fi

# ──────────────────────────────────────────────
# Step 2: Agent mode
# ──────────────────────────────────────────────
step "How do you want to run the agent?"
echo "  [1] Claude Code — uses CLAUDE.md + scheduled triggers (recommended if you have Claude Code)"
echo "  [2] Python runner — works with Claude API, OpenAI, or local Ollama"
echo ""
read -p "  Choice [1/2]: " AGENT_MODE
AGENT_MODE=${AGENT_MODE:-1}

# ──────────────────────────────────────────────
# Step 3: Database setup
# ──────────────────────────────────────────────
step "Database setup"
echo "  [1] I already have a Supabase project"
echo "  [2] Create one for me (requires Claude Code + Supabase MCP)"
echo ""
read -p "  Choice [1/2]: " DB_MODE
DB_MODE=${DB_MODE:-1}

SUPABASE_URL=""
SUPABASE_KEY=""
PROJECT_ID=""

if [ "$DB_MODE" = "2" ]; then
  # Auto-create via Claude Code MCP
  if [ "$HAS_CLAUDE" = false ]; then
    warn "Claude Code CLI not found. Falling back to manual setup."
    DB_MODE="1"
  else
    step "Auto-creating Supabase project..."
    echo ""
    echo "  Run this command in Claude Code (copy-paste it):"
    echo ""
    echo -e "  ${CYAN}claude -p \"Use the Supabase MCP to:"
    echo "    1. List my organizations (list_organizations)"
    echo "    2. Create a project called 'living-board' in my org (create_project)"
    echo "    3. Apply the migration from artifacts/living-board-template/schema.sql (apply_migration)"
    echo "    4. Get the project URL (get_project_url) and anon key (get_publishable_keys)"
    echo -e "    5. Print the URL and anon key\"${NC}"
    echo ""
    read -p "  Paste your Supabase URL (e.g. https://abc123.supabase.co): " SUPABASE_URL
    read -p "  Paste your anon key: " SUPABASE_KEY
  fi
fi

if [ "$DB_MODE" = "1" ]; then
  echo ""
  read -p "  Supabase URL (e.g. https://abc123.supabase.co): " SUPABASE_URL
  read -p "  Supabase anon key: " SUPABASE_KEY
fi

# Extract project ID from URL
if [ -n "$SUPABASE_URL" ]; then
  PROJECT_ID=$(echo "$SUPABASE_URL" | sed -E 's|https://([^.]+)\.supabase\.co.*|\1|')
  info "Project ID: $PROJECT_ID"
fi

# ──────────────────────────────────────────────
# Step 4: Validate Supabase connection
# ──────────────────────────────────────────────
if [ -n "$SUPABASE_URL" ] && [ -n "$SUPABASE_KEY" ]; then
  step "Validating Supabase connection..."
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    "$SUPABASE_URL/rest/v1/" \
    -H "apikey: $SUPABASE_KEY" \
    -H "Authorization: Bearer $SUPABASE_KEY" 2>/dev/null || echo "000")

  if [ "$HTTP_STATUS" = "200" ]; then
    info "Supabase connection verified"
  else
    warn "Could not verify connection (HTTP $HTTP_STATUS)"
    warn "Check your URL and key. Continuing anyway..."
  fi
fi

# ──────────────────────────────────────────────
# Step 5: Schema deployment
# ──────────────────────────────────────────────
if [ "$DB_MODE" = "1" ]; then
  step "Schema deployment"

  # Check if tables already exist
  TABLE_CHECK=$(curl -s -o /dev/null -w "%{http_code}" \
    "$SUPABASE_URL/rest/v1/goals?select=id&limit=1" \
    -H "apikey: $SUPABASE_KEY" \
    -H "Authorization: Bearer $SUPABASE_KEY" 2>/dev/null || echo "000")

  if [ "$TABLE_CHECK" = "200" ]; then
    info "Tables already exist — skipping schema deployment"
  else
    echo ""
    echo "  Open the Supabase SQL editor and run the schema:"
    echo ""
    echo "  URL:  https://supabase.com/dashboard/project/$PROJECT_ID/sql/new"
    echo "  File: artifacts/living-board-template/schema.sql"
    echo ""
    read -p "  Press Enter when you've run the schema... "

    # Re-check
    TABLE_CHECK=$(curl -s -o /dev/null -w "%{http_code}" \
      "$SUPABASE_URL/rest/v1/goals?select=id&limit=1" \
      -H "apikey: $SUPABASE_KEY" \
      -H "Authorization: Bearer $SUPABASE_KEY" 2>/dev/null || echo "000")

    if [ "$TABLE_CHECK" = "200" ]; then
      info "Schema verified"
    else
      warn "Could not verify tables. Make sure you ran schema.sql."
    fi
  fi

  # Seed data
  echo ""
  read -p "  Insert example data (sample goal + tasks)? [y/N] " SEED_DATA
  if [[ "$SEED_DATA" =~ ^[Yy]$ ]]; then
    echo ""
    echo "  Run seed-data.sql in the same SQL editor:"
    echo "  File: artifacts/living-board-template/seed-data.sql"
    echo ""
    read -p "  Press Enter when done... "
    info "Seed data applied"
  fi
fi

# ──────────────────────────────────────────────
# Step 6: Generate auth secret and write .env.local
# ──────────────────────────────────────────────
step "Configuring dashboard..."

if command -v openssl &>/dev/null; then
  AUTH_SECRET=$(openssl rand -base64 32)
else
  AUTH_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
fi

# Prompt for SUPABASE_DB_URL — enables the in-band scheduler heartbeat line
# printed by cycle-start.sh. Without it, every cycle logs
# "[scheduler] skipped: no SUPABASE_DB_URL" and the 6h-dropout WARN is unreachable.
echo ""
echo "  (Optional) Supabase Postgres connection URL — powers the scheduler heartbeat."
echo "  Find it at: https://supabase.com/dashboard/project/$PROJECT_ID/settings/database"
echo "  Copy the 'Transaction' or 'Session' pooler URI from the Connection string panel."
echo "  Leave blank to skip — agent still runs, but cycle-start.sh will log"
echo "  '[scheduler] skipped: no SUPABASE_DB_URL' and dropouts won't surface in-band."
read -p "  SUPABASE_DB_URL (or press Enter to skip): " SUPABASE_DB_URL

cat > dashboard/.env.local <<EOF
NEXT_PUBLIC_SUPABASE_URL=$SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY=$SUPABASE_KEY
AUTH_SECRET=$AUTH_SECRET
EOF

if [ -n "$SUPABASE_DB_URL" ]; then
  echo "SUPABASE_DB_URL=$SUPABASE_DB_URL" >> dashboard/.env.local
  info "SUPABASE_DB_URL captured — heartbeat line will be emitted by cycle-start.sh"
else
  warn "SUPABASE_DB_URL skipped — scheduler heartbeat will log as skipped each cycle"
fi

info "Created dashboard/.env.local"
echo ""
echo -e "  ${BOLD}Your dashboard password:${NC} $AUTH_SECRET"
echo "  Save this somewhere — you'll need it to log in."
echo ""

# ──────────────────────────────────────────────
# Step 7: CLAUDE.md placeholders
# ──────────────────────────────────────────────
step "Configuring agent instructions..."

if grep -q "{{SUPABASE_PROJECT_ID}}" CLAUDE.md 2>/dev/null; then
  if [ -n "$PROJECT_ID" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i '' "s/{{SUPABASE_PROJECT_ID}}/$PROJECT_ID/g" CLAUDE.md
    else
      sed -i "s/{{SUPABASE_PROJECT_ID}}/$PROJECT_ID/g" CLAUDE.md
    fi
    info "Supabase project ID set in CLAUDE.md"
  fi
fi

if grep -q "{{AGENTMAIL_ADDRESS}}" CLAUDE.md 2>/dev/null; then
  echo ""
  read -p "  AgentMail address (or press Enter to skip email): " AGENTMAIL_ADDR
  if [ -n "$AGENTMAIL_ADDR" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i '' "s/{{AGENTMAIL_ADDRESS}}/$AGENTMAIL_ADDR/g" CLAUDE.md
    else
      sed -i "s/{{AGENTMAIL_ADDRESS}}/$AGENTMAIL_ADDR/g" CLAUDE.md
    fi
    info "AgentMail address set in CLAUDE.md"
  else
    info "Skipped email — you can configure it later in CLAUDE.md"
  fi
fi

# ──────────────────────────────────────────────
# Step 8: Install dashboard dependencies
# ──────────────────────────────────────────────
step "Installing dashboard..."
cd dashboard && npm install --silent 2>&1 | tail -1 && cd ..
info "Dashboard dependencies installed"

# ──────────────────────────────────────────────
# Step 9: Memory system (DEFAULT — not optional)
# ──────────────────────────────────────────────
step "Setting up the memory system"
echo "  This is the dual-layer memory that makes Living Board learn across goals."
echo ""

MEMORY_OK=false

if [ "$HAS_DOCKER" = true ]; then
  # Qdrant
  if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "lb-qdrant"; then
    info "Qdrant is already running"
  else
    echo "  Starting Qdrant (vector database)..."
    docker run -d --name lb-qdrant \
      -p 6333:6333 -p 6334:6334 \
      -v qdrant_data:/qdrant/storage \
      qdrant/qdrant:latest > /dev/null 2>&1
    info "Qdrant started on port 6333"
  fi

  # Ollama
  if command -v ollama &>/dev/null && curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    info "Ollama is running natively"
    OLLAMA_CMD="ollama"
  elif docker ps --format '{{.Names}}' 2>/dev/null | grep -q "lb-ollama"; then
    info "Ollama is already running in Docker"
    OLLAMA_CMD="docker exec lb-ollama ollama"
  else
    echo "  Starting Ollama (embedding engine)..."
    docker run -d --name lb-ollama \
      -p 11434:11434 \
      -v ollama_data:/root/.ollama \
      ollama/ollama:latest > /dev/null 2>&1
    # Wait for Ollama to be ready
    echo "  Waiting for Ollama to start..."
    for i in $(seq 1 30); do
      if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        break
      fi
      sleep 1
    done
    info "Ollama started on port 11434"
    OLLAMA_CMD="docker exec lb-ollama ollama"
  fi

  # Pull bge-m3 embedding model
  echo ""
  echo "  Downloading bge-m3 embedding model (~1.7GB)..."
  echo "  This enables semantic search across all learnings."
  echo ""
  $OLLAMA_CMD pull bge-m3
  info "bge-m3 model ready"

  # Verify end-to-end
  echo ""
  echo "  Verifying memory system..."
  python3 -c "
import urllib.request, json, sys
try:
    urllib.request.urlopen('http://localhost:6333/healthz', timeout=5)
except Exception:
    print('  ✗ Qdrant not reachable', file=sys.stderr)
    sys.exit(1)
try:
    data = json.dumps({'model': 'bge-m3', 'prompt': 'test'}).encode()
    req = urllib.request.Request('http://localhost:11434/api/embeddings',
        data=data, headers={'Content-Type': 'application/json'})
    r = urllib.request.urlopen(req, timeout=30)
    result = json.loads(r.read())
    assert 'embedding' in result and len(result['embedding']) > 0
except Exception as e:
    print(f'  ✗ Embedding generation failed: {e}', file=sys.stderr)
    sys.exit(1)
print('  OK')
" && MEMORY_OK=true

  if [ "$MEMORY_OK" = true ]; then
    info "Memory system verified: Qdrant + Ollama + bge-m3"
  else
    warn "Memory system verification failed — check Docker containers"
  fi

else
  echo ""
  warn "Docker not found."
  warn "The memory system requires Docker for Qdrant (vector database)."
  warn "Install Docker Desktop: https://docker.com/products/docker-desktop"
  echo ""
  warn "Without it, the agent uses Supabase learnings only (per-goal memory)."
  warn "Cross-goal pattern recognition requires the vector memory layer."
  echo ""
  read -p "  Continue without vector memory? [y/N] " SKIP_MEMORY
  if [[ ! "$SKIP_MEMORY" =~ ^[Yy]$ ]]; then
    echo ""
    echo "  Install Docker and re-run ./setup.sh"
    exit 0
  fi
fi

# ──────────────────────────────────────────────
# Step 10: Python runner setup (if chosen)
# ──────────────────────────────────────────────
if [ "$AGENT_MODE" = "2" ]; then
  step "Setting up Python runner..."

  # Install runner
  pip3 install -e ./runner --quiet 2>&1 | tail -1
  info "Python runner installed"

  # Create agent.toml
  if [ ! -f "agent.toml" ]; then
    cp agent.toml.example agent.toml
    info "Created agent.toml from example"
  fi

  echo ""
  echo "  Which LLM provider do you want to use?"
  echo "  [1] Claude API (Anthropic)"
  echo "  [2] OpenAI"
  echo "  [3] Ollama (local models)"
  echo ""
  read -p "  Choice [1/2/3]: " LLM_CHOICE
  LLM_CHOICE=${LLM_CHOICE:-1}

  case $LLM_CHOICE in
    1)
      PROVIDER="anthropic"
      read -p "  Anthropic API key: " API_KEY
      echo "ANTHROPIC_API_KEY=$API_KEY" >> .env
      ;;
    2)
      PROVIDER="openai"
      read -p "  OpenAI API key: " API_KEY
      echo "OPENAI_API_KEY=$API_KEY" >> .env
      ;;
    3)
      PROVIDER="ollama"
      echo ""
      echo "  Make sure Ollama is running with your preferred models."
      echo "  Default tier mapping: tier1=llama3.1:70b, tier2=llama3.1:8b, tier3=llama3.2:3b"
      ;;
  esac

  # Update agent.toml provider
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/^type = \"anthropic\"/type = \"$PROVIDER\"/" agent.toml
  else
    sed -i "s/^type = \"anthropic\"/type = \"$PROVIDER\"/" agent.toml
  fi

  info "Provider set to: $PROVIDER"
fi

# ──────────────────────────────────────────────
# Step 11: Claude Code setup (if chosen)
# ──────────────────────────────────────────────
if [ "$AGENT_MODE" = "1" ]; then
  step "Setting up Claude Code..."

  if [ "$HAS_CLAUDE" = true ]; then
    echo "  Adding Supabase MCP connector..."
    claude mcp add supabase --type url --url "https://mcp.supabase.com" 2>/dev/null || true
    info "Supabase MCP added"
  else
    echo ""
    echo "  Add the Supabase MCP manually in your Claude Code config:"
    echo ""
    echo '  {"mcpServers": {"supabase": {"type": "url", "url": "https://mcp.supabase.com"}}}'
    echo ""
  fi
fi

# ──────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────
echo ""
echo -e "${BOLD}  ╔═══════════════════════════════════════╗${NC}"
echo -e "${BOLD}  ║          Setup Complete!               ║${NC}"
echo -e "${BOLD}  ╚═══════════════════════════════════════╝${NC}"
echo ""
echo -e "  Dashboard password:  ${BOLD}$AUTH_SECRET${NC}"
echo -e "  Supabase project:    $PROJECT_ID"

if [ "$MEMORY_OK" = true ]; then
  echo -e "  Memory system:       ${GREEN}✓${NC} Qdrant + Ollama + bge-m3"
else
  echo -e "  Memory system:       ${YELLOW}—${NC} not configured"
fi

if [ "$AGENT_MODE" = "2" ]; then
  echo -e "  Agent mode:          Python runner ($PROVIDER)"
else
  echo -e "  Agent mode:          Claude Code"
fi

echo ""
echo "  Next steps:"
echo ""
echo "  1. Start the dashboard:"
echo "     cd dashboard && npm run dev"
echo "     → http://localhost:3000"
echo ""

if [ "$AGENT_MODE" = "2" ]; then
  echo "  2. Run the agent:"
  echo "     python -m runner run"
  echo ""
  echo "     Or run as a daemon:"
  echo "     python -m runner daemon --interval 3600"
  echo ""
  echo "     Or schedule with cron (every hour):"
  echo "     0 * * * * cd $(pwd) && python -m runner run >> artifacts/logs/agent.log 2>&1"
else
  echo "  2. Schedule the agent:"
  echo "     claude trigger create --name living-board \\"
  echo "       --schedule '0 * * * *' \\"
  echo "       --prompt 'Execute your full agent cycle as defined in CLAUDE.md.'"
fi

echo ""
echo "  3. Add your first goal (in Supabase SQL editor or dashboard):"
echo "     INSERT INTO goals (title, description, status, priority)"
echo "     VALUES ('My first goal', 'Description', 'in_progress', 3);"
echo ""
