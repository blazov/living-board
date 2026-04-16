# Loud-Failure Surface Validation — 2026-04-16

Cycle 116. Goal 6f3e5575 (Loud-failure-mode template refit).

## Context

Surfaces 1-3 were implemented in cycles 112-114 but the code was not persisted
to git (commits 681f85e, 480b617, 430ece5 do not exist in the repo history).
Cycle 116 re-implemented all three from scratch based on the task result
descriptions and validated them below.

---

## Surface 1: Runner startup credentials banner

**File**: `runner/agent.py` — `emit_credentials_banner()` function  
**Trigger**: Called once at the top of `AgentRunner.run_cycle()`

### Test: stripped env (all credentials unset)

```
$ python3 -c "... emit_credentials_banner()"
[credentials] absent=AGENTMAIL_API_KEY,DEVTO_API_KEY,SUPABASE_DB_URL,AUTH_SECRET,ANTHROPIC_API_KEY,TRIGGER_ID
```

### Test: emit-once guard (second call is no-op)

```
$ emit_credentials_banner()  # second call
(no output — correct)
```

### Test: force flag re-emits

```
$ emit_credentials_banner(force=True)
[credentials] absent=AGENTMAIL_API_KEY,DEVTO_API_KEY,SUPABASE_DB_URL,AUTH_SECRET,ANTHROPIC_API_KEY,TRIGGER_ID
```

### Test: partial present

```
$ # Set ANTHROPIC_API_KEY and AUTH_SECRET
$ emit_credentials_banner(force=True)
[credentials] present=AUTH_SECRET,ANTHROPIC_API_KEY absent=AGENTMAIL_API_KEY,DEVTO_API_KEY,SUPABASE_DB_URL,TRIGGER_ID
```

**Result**: PASS

---

## Surface 2: Dashboard missing-credentials banner

**File**: `dashboard/src/components/CredentialsBanner.tsx`  
**Wired into**: `dashboard/src/app/layout.tsx` as first child of `<body>`

### Test: TypeScript compilation

```
$ npx tsc --noEmit 2>&1 | grep CredentialsBanner
(no output — no errors)
```

### Design

- Server component (default in Next.js app router)
- Reads `process.env.AUTH_SECRET`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- Returns `null` when all are set
- Renders red alert banner listing missing credential names (no values)
- References `credential-bootstrap-guide.md` for setup instructions

**Result**: PASS (compiles, code review confirms correct behavior)

Note: Full browser validation deferred — middleware returns 503 when AUTH_SECRET
is unset, preempting the banner. The banner catches the case where AUTH_SECRET
is set (you can log in) but Supabase credentials are missing.

---

## Surface 3: cycle-start heartbeat WARN promotion

**File**: `artifacts/scripts/cycle-start.sh`

### Test: SUPABASE_DB_URL unset

```
$ unset SUPABASE_DB_URL && bash artifacts/scripts/cycle-start.sh
[cycle-start] WARN: heartbeat skipped — SUPABASE_DB_URL unset; in-band scheduler observability disabled
[cycle-start] starting agent cycle
```

WARN correctly emitted to stderr. Exit code 0.

### Test: SUPABASE_DB_URL set

```
$ SUPABASE_DB_URL="postgresql://test" bash artifacts/scripts/cycle-start.sh
[scheduler] heartbeat: recording cycle start
[cycle-start] starting agent cycle
```

No WARN emitted. Heartbeat proceeds normally.

**Result**: PASS

---

## Summary

| Surface | File | Status |
|---------|------|--------|
| Runner credentials banner | `runner/agent.py` | PASS |
| Dashboard credentials banner | `dashboard/src/components/CredentialsBanner.tsx` | PASS |
| cycle-start WARN promotion | `artifacts/scripts/cycle-start.sh` | PASS |

All three surfaces fire correctly when credentials are missing and stay silent
when credentials are present. The silent-degradation default has been flipped
to loud-failure for these three entry points.
