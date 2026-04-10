# Credential Bootstrap Guide

**Problem:** Remote Claude Code sessions start with a blank environment. Every session since April 9 has been unable to connect to Supabase or check email because credentials aren't available.

**This document lists every credential the agent needs and how to provide them.**

---

## Required Credentials

### 1. Supabase (CRITICAL — blocks all database operations)

```
NEXT_PUBLIC_SUPABASE_URL=https://ieekjkeayiclprdekxla.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key>
```

**Where to find the anon key:**
- Supabase Dashboard → Project Settings → API → `anon` / `public` key
- URL: https://supabase.com/dashboard/project/ieekjkeayiclprdekxla/settings/api

**How to provide:**
- Option A: Create `dashboard/.env.local` with both values (the Python runner reads this)
- Option B: Set as environment variables in the session
- Option C: Complete the Supabase MCP OAuth flow in an interactive Claude Code desktop session (one-time)

### 2. AgentMail (needed for email check/send)

```
AGENTMAIL_API_KEY=<your-key>
```

**Where to find:**
- AgentMail dashboard or the original setup email
- Was referenced in `dashboard/.env.local` previously

**How to provide:**
- Add to `dashboard/.env.local` or set as env var

### 3. Dev.to API Key (NEW — proposed for cross-platform publishing)

```
DEVTO_API_KEY=<your-key>
```

**How to generate:**
1. Go to https://dev.to/settings/extensions
2. Under "DEV Community API Keys", enter a description
3. Click "Generate API Key"
4. Copy the key

---

## Recommended: Create a `.env` File

Create `/home/user/living-board/.env` with:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://ieekjkeayiclprdekxla.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<paste-anon-key-here>

# AgentMail
AGENTMAIL_API_KEY=<paste-key-here>

# Dev.to (optional, for cross-platform publishing)
DEVTO_API_KEY=<paste-key-here>
```

The Python runner at `runner/config.py` already reads from `.env` and `dashboard/.env.local`.

---

## For Remote Triggers / Scheduled Sessions

If using Claude Code remote triggers, credentials must be passed as environment variables in the trigger configuration. The `.env` file approach only works for local/interactive sessions.

Check your trigger configuration to ensure `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` are included in the environment.
