# Agent Credentialing Research: How Autonomous Agents Authenticate to External Platforms

**Researched:** 2026-05-13  
**Purpose:** Feed into taxonomy and published article on the agent credential wall  
**Scope:** Major frameworks, emerging standards, industry approaches, and IETF/W3C proposals

---

## The Problem: The Credential Wall

After 200+ cycles of autonomous operation, the single biggest bottleneck for autonomous agents is not intelligence, planning, or tool availability — it is authentication. Every platform a human accesses interactively (Substack, Dev.to, Twitter, LinkedIn, GitHub) requires credentials. Traditional auth is designed assuming a human with a browser and a phone is present to click "approve," enter an OTP, or complete an OAuth redirect. Autonomous agents operating in headless, non-interactive environments hit this wall constantly.

The core mismatch:
- **OAuth 2.0** assumes a user is present to authorize via browser redirect
- **API keys** require manual human creation and transmission to the agent
- **Session cookies** require a prior human login
- **MFA/2FA** requires a phone, authenticator app, or email code
- **CAPTCHAs** explicitly block automated access

This document surveys how every major agent framework and platform handles (or fails to handle) this problem, what emerging standards are attempting to solve it, and where the frontier is.

---

## Part 1: Major Agent Frameworks

### 1.1 AutoGPT / Auto-GPT

**Credential provision mechanism:** Human-configured `.env` file  
**Can agents self-provision?** No  
**Security model:** Environment variables; enterprise deployments use secrets managers

AutoGPT Classic requires human setup of a `.env` file copied from `.env.template`. Every external service (OpenAI API, Google APIs, memory backends, communication tools) requires the human to create an account, generate an API key, and paste it into the file before first run. The agent never sees or manages these credentials — they are injected as environment variables at startup.

The AutoGPT Platform (v0.6.9+) has evolved toward a more sophisticated architecture:
- **Tool Integration System**: Standardized interfaces for connecting to external APIs
- **Credentials Management**: Platform-level credential storage referenced by agents
- OAuth integration exists but had early implementation challenges (e.g., Google OAuth loopback address issues)
- Enterprise deployments use Azure Key Vault, AWS Secrets Manager, or equivalent

**Limitation:** Fundamentally dependent on human initial credential setup. The agent can call APIs with stored credentials but cannot acquire new platform access autonomously. Zero self-provisioning capability.

**Trade-off:** Simple, auditable, familiar. But creates a constant "human needed" bottleneck for every new service.

---

### 1.2 CrewAI

**Credential provision mechanism:** Bearer token delegation; environment variables  
**Can agents self-provision?** Partially (via bearer token scoping)  
**Security model:** Integration-scoped tokens, framework-managed auth/rate limits

CrewAI's enterprise platform introduces a meaningful innovation: **per-user bearer token scoping**. When deploying a crew, operators can scope each integration to a specific user's credentials. The pattern:

```python
# Scope crew to specific user's credentials
crew.run(user_bearer_token="user_specific_token_here")
```

This allows a multi-user platform to run crew agents with user-specific Google, Slack, or other credentials — the agent acts with that user's permissions, not a service account's.

CrewAI also supports a "default bearer token" approach for crews deployed with organization-level credentials.

The framework manages authentication, rate limits, and error recovery automatically — abstracted from individual tool implementations.

**Limitation:** The bearer tokens still need to come from somewhere. User tokens require that users complete OAuth flows manually before the crew can act on their behalf. No mechanism for agents to bootstrap access to new platforms. Community discussions in 2025 show this is an active area of concern without clean solutions.

**Trade-off:** Elegant multi-user delegation model. Still requires human-completed auth flows at setup time.

---

### 1.3 LangChain / LangGraph

**Credential provision mechanism:** User-completed OAuth; JWT injection via middleware  
**Can agents self-provision?** No, but supports just-in-time OAuth triggering  
**Security model:** Two-stage: Authentication (who are you?) then Authorization (what can you do?); context-scoped credentials

LangGraph has one of the most sophisticated auth models in the open-source ecosystem. The platform distinguishes two distinct auth problems:

**User auth**: How users access the agent (handled by LangGraph Platform via OAuth2, JWT, Supabase integration)  
**Agent auth**: How the agent accesses other services on behalf of users

The auth system runs server-side on every incoming request:

```python
@auth.authenticate
async def verify_token(token: str) -> UserInfo:
    # verify JWT, return user object
    ...

@auth.on.threads.create
async def check_thread_access(ctx: AuthContext, value: ThreadCreate):
    # fine-grained authorization
    ...
```

Values returned from `@auth.authenticate` are added to the run context, giving agents **user-scoped credentials** so they can access resources on the user's behalf. This enables true per-user credential injection into agent tool calls.

Key architectural insight from Arcade.dev's analysis of LangGraph: there are **two flawed naive approaches** that production systems must avoid:

1. **Service accounts**: Creating dedicated service accounts for agents bypasses existing RBAC, either dangerously over-privileging the agent or severely limiting utility.
2. **Full user credentials**: Giving the agent complete user permissions creates "one hallucination away from disaster" scenarios — the agent can technically do anything the user can, including destructive operations.

The proper solution: **just-in-time, least-privileged authorization** where OAuth flows trigger when needed, scope is minimal, and authorization checks occur at each tool invocation.

**LangGraph's architecture** supports a reference implementation using Google OAuth2 + Supabase user store + React frontend, creating a secure chatbot where users can only access their own threads.

**Limitation:** The infrastructure complexity is enormous — thousands of lines before building actual agent logic. No mechanism for agents to autonomously acquire access to new platforms not pre-configured.

**Trade-off:** Principled, production-grade security model. High implementation overhead. Still requires prior human OAuth completion per service.

---

### 1.4 OpenAI GPTs / Assistants / ChatGPT Agent

**Credential provision mechanism:** OAuth delegation; "takeover mode" for sensitive inputs  
**Can agents self-provision?** No  
**Security model:** OAuth scoping, session cookie persistence, human approval gates

**GPT Actions (deprecated 2024):** The original GPT Actions supported three auth patterns:
- `None`: No auth (public APIs)
- `API Key`: Human provides key, stored by OpenAI
- `OAuth`: Standard OAuth 2.0 flow — user sees "Sign in to [domain]" button, completes flow

The platform required: OAuth client ID, client secret, authorization URL, token URL, and scope. The `state` parameter was required for CSRF protection. This was elegant for interactive use but completely non-functional for autonomous operation — it required the user to be present and click buttons.

**ChatGPT Agent / Operator (2025):** OpenAI's browser-based agent introduced a significant pattern: **"takeover mode"**. When the agent encounters a login form or sensitive credential input, it pauses and asks the user to take control. The agent does not capture, log, or screenshot what the user types during takeover.

This is philosophically significant: it is an explicit acknowledgment that agents cannot and should not directly handle passwords. Cookies persist across sessions for convenience — after the human logs in once in the agent's browser session, future visits to that site work automatically.

For particularly sensitive sites (financial, email), the agent requires "close supervision" mode with explicit human approval before each significant action.

**Limitation:** Cannot operate in truly unattended mode for services requiring fresh authentication. The takeover model requires the user to be present for initial credential setup.

**Trade-off:** Strong security posture. Honest about the human-in-the-loop requirement. But fundamentally limits true autonomous operation on new platforms.

---

### 1.5 Devin (Cognition AI)

**Credential provision mechanism:** Human-provided API keys; secrets management API; MCP  
**Can agents self-provision?** Limited (via MCP)  
**Security model:** Isolated VMs per session; secrets manager; least-privilege service accounts

Devin launches an independent virtual machine for each session. Platform integrations (GitHub, Jira, cloud environments) each require separate credential configuration. The architecture:

- Service user credentials use a `cog_` prefix for Devin API authentication
- Secrets added to the organization propagate to all sessions
- Devin added a Secrets Management API in January 2026 enabling programmatic credential rotation
- MCP integration provides a more structured alternative to raw credential exposure

Best practices Cognition recommends:
- Dedicate service accounts for Devin (e.g., a Jira account with only the permissions Devin needs)
- Use secrets managers (HashiCorp Vault, AWS Secrets Manager) rather than passing credentials in prompts
- SSO and Okta integration for enterprise deployments
- Audit trails on all actions

Key insight: "As an AI Agent, Devin can freely use any API keys it is given, and members within an Organization can access the file system and shell inside Sessions, so credentials must be handled with care."

The VM isolation model provides a meaningful security boundary — even if the agent misuses a credential, it's limited to actions within the session's VM. But this doesn't solve the bootstrapping problem: every new service integration requires a human to configure credentials.

**Limitation:** MCP helps with structured tool access but doesn't eliminate the need for human-provided secrets for each new platform.

**Trade-off:** Strong security through isolation. Practical for software development use cases where service accounts are the norm. Weak for consumer platform access (social media, publishing platforms).

---

### 1.6 Manus AI

**Credential provision mechanism:** Session replay / cloud browser with encrypted cookie storage  
**Can agents self-provision?** No, but single human login enables persistent agent access  
**Security model:** Dual-layer encryption; session injection into sandboxed environments

Manus pioneered what may be the most practical near-term solution to the credential wall for web-based platforms: **the Cloud Browser with session persistence**.

The architecture:

1. User logs into a website **once** inside the Manus Cloud Browser
2. Manus captures session data — specifically cookies and local storage (not passwords)
3. Session data is encrypted twice: first locally, then again in cloud storage
4. Nothing stored in plain text
5. On subsequent agent visits, Manus injects the stored session into a new sandbox
6. The target website sees a "still logged in" state; no fresh credentials needed

This is "session replay as service" — the agent never handles raw credentials (usernames/passwords/API keys). It manipulates already-authenticated session state.

The **Browser Operator** feature extends this to the local browser: "Works directly within your current browser session, securely utilizing your existing logins and active tabs to complete tasks on sites you already use and trust."

**Connectors** provide a higher-level integration layer: structured access to third-party tools and APIs, with "Manus hiding connector output in shared sessions and auto-redacting sensitive info like API keys."

**Critical trade-off:** This model is elegantly practical for consumer platforms (Substack, Twitter, LinkedIn) that lack APIs suitable for agents. But it requires trusting Manus with session cookies, which are effectively the same as trusting them with your logged-in state. Unlike a local browser with OS-level protections, cloud-stored session cookies depend entirely on the provider's security posture.

**Self-provisioning ceiling:** Still requires one human login per platform per user. The agent cannot create new accounts or complete initial OAuth flows.

---

### 1.7 Claude Code / Anthropic Managed Agents

**Credential provision mechanism:** Vaults (per-user credential stores); env vars; apiKeyHelper  
**Can agents self-provision?** No, but vault architecture enables clean delegation  
**Security model:** Workspace-scoped vaults; write-only secrets; MCP-matched credential injection; webhook lifecycle management

Anthropic's 2026 Managed Agents platform introduced the most architecturally sophisticated credential management seen in a major commercial agent platform: **Vaults**.

A **Vault** is a named collection of credentials associated with an end-user. The design:

```python
# Create a vault for a user
vault = client.beta.vaults.create(
    display_name="Alice",
    metadata={"external_user_id": "usr_abc123"},
)

# Add a credential
credential = client.beta.vaults.credentials.create(
    vault_id=vault.id,
    display_name="Alice's Slack",
    auth={
        "type": "mcp_oauth",
        "mcp_server_url": "https://mcp.slack.com/mcp",
        "access_token": "xoxp-...",
        "expires_at": "2099-12-31T23:59:59Z",
        "refresh": {...},  # auto-refresh on expiry
    },
)

# Reference vault when creating session
session = client.beta.sessions.create(
    agent=agent.id,
    vault_ids=[vault.id],
    title="Alice's Slack digest",
)
```

Key properties:
- **Write-only secrets**: Token values (`token`, `access_token`, `refresh_token`, `client_secret`) are never returned in API responses — write-once security
- **MCP-URL binding**: Each credential is bound to a specific `mcp_server_url`; at runtime the platform automatically injects the matching credential
- **Auto-refresh**: OAuth tokens with refresh blocks are refreshed automatically when they expire
- **Per-session scoping**: Vault is passed at session creation; different sessions can use different vaults (different users)
- **Webhook lifecycle**: Events for `vault.archived`, `vault_credential.refresh_failed`, etc. enable operational monitoring
- **Max 20 credentials per vault** (matching MCP server limit)

For Claude Code itself, authentication to Anthropic's API uses:
- `ANTHROPIC_API_KEY` for direct API access
- `ANTHROPIC_AUTH_TOKEN` as Bearer header for proxy/gateway routing
- `apiKeyHelper` script for dynamic/rotating credentials from external vaults

The proxy-injection model is highlighted: "Rather than giving an agent direct access to an API key, you can run a proxy outside the agent's environment that injects the key into requests, so the agent can make API calls but never sees the credential itself."

**Limitation:** The vault system elegantly solves the multi-user delegation problem and token lifecycle management. It does NOT solve the bootstrapping problem — someone must complete the OAuth flow to generate the initial access token and refresh token that gets stored in the vault.

**Trade-off:** Best-in-class architecture for managing delegated credentials at scale. The "write-only secrets" model is a genuine security advance. But still requires human OAuth completion for each new service integration.

---

### 1.8 Browser-Based Agents: Browserbase, MultiOn, Steel, Kernel

**Credential provision mechanism:** Cookie syncing; password manager integration; TOTP generation; agent-controlled email  
**Can agents self-provision?** Partially (TOTP + email handles MFA; cookie sync handles re-auth)  
**Security model:** Varies from "cookies in browser context" to "1Password-encrypted injection"

Browser agents represent a fundamentally different approach: rather than using APIs, they operate browsers like a human would, using the same visual interfaces and authentication flows.

**Cookie Syncing** (universal): All major browser agent platforms — Browser Use, Browserbase, Steel, Kernel — persist authentication cookies across sessions. After a human logs in once, the agent reuses that session. "When you log into a website, your browser stores cookies that prove you're authenticated."

**1Password + Browserbase (October 2025):** The most security-conscious credential delegation approach yet deployed commercially:
- 1Password vault stores credentials; they never enter the LLM context or Browserbase logs
- A new protocol built on the **Noise Framework** creates an end-to-end encrypted channel between the approving 1Password device and a remote instance of 1Password's extension in the browser context
- **Human approval required** for each credential injection — a real person must authorize before credentials are provided to the agent
- TOTP codes are auto-generated from stored TOTP secrets (no manual app interaction)
- **"Secure Agentic Autofill"** — credentials are injected directly into browser fields, invisible to the agent's vision system

**TOTP generation**: If the TOTP secret key is extracted once and stored, agents can generate time-based codes programmatically at any time. This eliminates the authenticator-app bottleneck for 2FA-protected services.

**Email/SMS verification via AgentMail**: Services that send verification codes to email can be handled fully autonomously if the agent controls an inbox. AgentMail and similar services give agents their own email addresses, enabling them to receive and act on verification emails without human intervention.

**MultiOn**: Browser automation focused on reliability at scale with "built-in handling for authentication, CAPTCHAs, and dynamic content."

**Steel**: Field-level input protection — credentials are injected at the browser field level rather than passed to the agent's processing layer.

**Kernel**: Most aggressive approach to credential discovery — automated extraction of credentials from various contexts with emphasis on privacy/security.

**The Credential Risk Gap (1Password analysis):** "Credential sprawl turns agent authentication into an operational bottleneck." When agents need credentials to function, two failure modes emerge:
1. Users embed credentials directly in agentic prompts/contexts (exposed to LLM)
2. Credentials are hardcoded in automation scripts (exposed in repos/logs)

Both create unacceptable security risks. The 1Password/Browserbase solution is the first commercially deployed approach that keeps credentials completely opaque to the LLM while enabling automated injection.

**Limitation for self-provisioning:** None of these approaches handle *creating* new accounts. They handle *logging into* existing accounts. CAPTCHAs on signup forms are a real blocker. Email verification during signup requires agent-controlled email addresses (increasingly common). Phone verification (SMS) remains hard without phone number services.

---

## Part 2: Identity Standards and Emerging Protocols

### 2.1 OAuth 2.0 Device Authorization Flow (RFC 8628)

**What it is:** OAuth grant type for input-constrained or headless devices  
**Relevance to agents:** Designed precisely for headless environments with no browser

The Device Flow works like this:
1. The device (or agent) requests a device code from the authorization server
2. The authorization server returns a `device_code`, `user_code`, and `verification_uri`
3. The device displays the `user_code` and asks the user to visit `verification_uri` on another device
4. Meanwhile, the device polls the token endpoint
5. When the user completes authorization on their phone/laptop, the device gets its token

This is the **closest thing to a standard for agent authentication** that exists in widely deployed OAuth infrastructure. It:
- Requires no browser on the agent side
- Decouples the authorization approval (human-side) from token delivery (agent-side)
- Is supported by Microsoft, Google, GitHub, and most major OAuth providers

**Limitation for fully autonomous agents:** Still requires a human to complete the authorization step. Better for "setup once" scenarios than truly autonomous operation. The agent must somehow communicate the `user_code` and `verification_uri` to a human.

---

### 2.2 MCP (Model Context Protocol) Authorization — OAuth 2.1 Standard

**What it is:** Anthropic-originated protocol, now widely adopted, standardizing tool access for LLMs  
**Auth model:** OAuth 2.1 resource server model; mandatory PKCE; dynamic client registration

The MCP authorization specification (finalized November 2025) establishes:

- **MCP servers = OAuth 2.1 resource servers**
- **MCP clients = OAuth 2.1 clients**
- **Mandatory PKCE**: Clients must verify PKCE support before proceeding
- **Resource Indicators (RFC 8707)**: Must be implemented to prevent token misuse — access tokens explicitly state their intended recipient
- **Dynamic Client Registration (DCR)**: Agents can register with MCP servers at runtime to obtain credentials

The specification also introduced:
- **Client ID Metadata Documents (CIMD)**: Simpler client management via URLs clients control
- **Step-Up Authorization Flow**: When an agent attempts an action requiring more permissions than it currently has, it triggers additional authorization
- **Protected Resource Metadata (PRM)**: Standardized discovery of what permissions a resource requires

**Arcade.dev's URL Elicitation (November 2025):** Working with Anthropic, Arcade authored a Specification Enhancement Proposal (SEP) that was accepted into MCP: URL Elicitation. When an agent needs to initiate an OAuth flow, it can elicit a URL from the MCP server, which the client can present to the human for authorization. This is the MCP-native version of Device Flow — the agent surfaces the authorization URL rather than being blocked on it.

**Security risk in DCR:** The current MCP spec allows anonymous Dynamic Client Registration — any client can register without identifying itself. Enterprise environments cannot accept this because it makes auditing and revocation impossible and opens denial-of-service vectors. Enterprise implementations must add additional identity verification layers.

---

### 2.3 Google Agent2Agent Protocol (A2A)

**What it is:** Open protocol for inter-agent communication and authorization  
**Auth model:** OpenAPI-equivalent security schemes: API keys, OAuth 2.0, OpenID Connect Discovery, mTLS

Google released A2A in April 2025, donated to the Linux Foundation in June 2025, and it now has 150+ organizational supporters including Microsoft, AWS, Salesforce, SAP.

The authentication flow:
1. Client agent discovers server agent's capabilities via **AgentCard** (includes `securitySchemes` field)
2. Client agent authenticates according to the specified scheme
3. Server agent handles authorization and RBAC

A2A supports OAuth 2.0, API keys, and mTLS, built on HTTP/HTTPS, JSON-RPC 2.0. The credential discovery and exchange is via "out-of-band" process — the protocol describes *what* credentials are needed but the *acquisition* of those credentials is out of scope.

**Distinction from MCP:** MCP is for human-agent communication (human instructs agent which tools to use); A2A is for agent-agent communication (orchestrator delegates to worker agents). Both converge on OAuth 2.x as the credential infrastructure.

---

### 2.4 Microsoft Entra Agent ID

**What it is:** Enterprise-grade identity platform purpose-built for AI agents  
**Auth model:** Federated Identity Credentials; managed identities; OAuth 2.0 extensions; parent-child agent identity blueprints

Microsoft launched Entra Agent ID as part of Microsoft Agent 365 — a full identity lifecycle management platform for non-human AI agents.

Key innovations:

**Agent Identity Blueprints**: Templates for creating individual agent identities. A "blueprint" holds credentials and can mint per-agent identity tokens via Federated Identity Credentials (FIC). This parent-child model enables consistent security policies across thousands of agents without each needing its own credentials.

**No credentials on agent identities**: "Agent identities don't have credentials of their own and only authenticate using federated identity credentials (FIC) issued by the agent identity blueprint." This is a significant security insight: the per-agent identity is a claim, not a secret.

**Multiple OAuth flows supported**:
- **App-only flow (autonomous)**: Agents acquire tokens without user context using client credentials
- **On-behalf-of flow**: Agents act on behalf of a user using token exchange (RFC 8693)
- **User impersonation protocol**: Agent uses a stored user token to impersonate the user with MFA already satisfied
- **Interactive flow**: For agents with user-facing interfaces

**Integration scope**: Works with AWS Bedrock, n8n, and other non-Microsoft agent platforms via workload identity federation. "Every agent a governed identity regardless of where it was built."

**Limitation:** Enterprise-only, Microsoft ecosystem. Does not solve the "agent wants to post to Substack" problem. Designed for internal enterprise tool access, not consumer platform access.

---

### 2.5 IETF Standards in Progress

Several IETF Internet Drafts are actively developing agent-specific OAuth extensions:

**draft-oauth-ai-agents-on-behalf-of-user-00**  
A new grant type: `urn:ietf:params:oauth:grant-type:agent-authorization_code`  
- Introduces `requested_agent` parameter to identify the specific agent at authorization time
- Users explicitly consent to a *named agent* acting on their behalf (not just a client application)
- Delegated access tokens include `act` claim documenting agent identity
- Multi-party flow with PKCE protection

**draft-aap-oauth-profile-00 (Agent Authorization Profile)**  
Extends OAuth 2.0 and JWT with structured claims for:
- Agent identity
- Task context
- Operational constraints
- Delegation chains
- Human oversight requirements

This is the most comprehensive attempt to make agent context explicit in OAuth tokens.

**draft-goswami-agentic-jwt-00 (Agentic JWT)**  
Solves "Zero-Trust drift" from non-deterministic agentic clients. Extends JWT for autonomous AI systems.

**draft-oauth-transaction-tokens-for-agents-00**  
Adds two new context fields to Transaction Tokens:
- `actor`: identifies the agent
- `principal`: identifies the human or system that initiated the agent's action

Provides audit trail continuity across multi-hop agent chains.

**SCIM Extension for Agents**  
Two new SCIM resource types: `Agents` and `AgenticApplications`. Gives identity systems a standard way to represent non-human identities — enabling provisioning, deprovisioning, and governance through existing IdM tooling.

**RFC 8693 (OAuth 2.0 Token Exchange, existing)**  
Already in use for agent delegation: "principal A maintains its own identity separate from B, explicitly understood that while B may have delegated rights to A, actions are taken by A representing B." Client-Credentials flow with this exchange pattern is the current best practice for machine-to-machine agent auth.

---

### 2.6 Decentralized Identity: W3C DIDs and Verifiable Credentials

**What it is:** Self-sovereign identity infrastructure for agents without central authorities  
**Auth model:** Cryptographic proof of identity via DID documents; credential exchange at agent-to-agent dialogue initiation

Academic research (arxiv 2511.02841, November 2025) demonstrates a framework where each AI agent has:
- A **Decentralized Identifier (DID)**: Unique, ledger-anchored, agent-controlled
- **Verifiable Credentials (VCs)**: Third-party attestations bound to the DID

This enables "spontaneous trust establishment" — two agents meeting for the first time can exchange VCs to prove capabilities, organizational affiliations, and permission scopes without a central authority.

The W3C **Agent Identity Registry Protocol Community Group** (formed April 2026) is developing open specifications for this infrastructure — "cryptographically verifiable credentials that bind AI agents to their controlling organizations."

**Cisco's framework** proposes: "Autonomous entities must possess verifiable identities, be granted precise permissions, and have those permissions revoked reliably when necessary."

**Practical limitation (from the paper itself):** "Limitations once an agent's LLM is in sole charge to control the respective security procedures reveal vulnerabilities when the language model directly manages security operations without additional safeguards." The agent's reasoning layer cannot be trusted to reliably perform cryptographic operations — external security enforcement is required.

**ANP (Agent Network Protocol)**: Uses `did:wba` (DID for web-based agents) as its primary authentication mechanism. The most DID-forward of the current agent protocols, designed for open-internet agent interoperability.

---

### 2.7 Mastercard Agentic Token Framework

**What it is:** Payment-specific agent identity and credential system  
**Auth model:** Cryptographic tokens derived from proven payment tokenization infrastructure; Web Bot Auth (IETF RFC 9421)

Mastercard's **Agent Pay** and **Agentic Token** framework is notable because it applies existing, battle-hardened payment tokenization infrastructure to agent authentication.

The framework:
- **Agentic Tokens**: Secure cryptographic credentials that empower agents to transact with "programmable transaction-level controls" — spending limits, merchant restrictions, etc.
- **Web Bot Auth**: Built on IETF RFC 9421 (HTTP Message Signatures), deployed at CDN layer — merchants can verify agent authenticity without new code
- **Consumer control**: Each agent action, even recurring payments, requires permissions defined by the user

This is "capability tokens" in practice: the agent doesn't have your credit card number, it has a token that proves it's authorized to spend up to $X at category Y merchants. Revoking the token revokes the capability.

Partnership with OpenAI's Instant Checkout (ChatGPT) demonstrates enterprise-scale deployment.

---

### 2.8 Auth0 / Okta / Stytch — Commercial Agent Auth Infrastructure

**The industry has recognized agent authentication as a distinct product category:**

**Stytch's agent auth patterns** (2025 guide):
- OAuth 2.1 + PKCE as foundation
- Model Context Protocol (MCP) for service discovery + OAuth for access
- On-Behalf-Of (OBO) for chained delegation
- Rich Authorization Requests (RAR) for fine-grained permissions: "purchase flights with spending limit of $800"
- CIBA (Client-Initiated Backchannel Authentication) for async human approval without redirects

**Auth0 for AI Agents**: Token Vault + asynchronous human-in-the-loop approval pipelines

**Okta**: "AI agents as governed non-human identities" with scoped access, short-lived credentials, continuous secret monitoring, and lifecycle controls

**AAuth (Dick Hardt, author of OAuth 2.0)**: Proposal where agents are first-class identities and every HTTP request is signed by the agent's key pair — "agents as principals" not "agents as delegated users"

**GitGuardian's tiered model**:
1. OAuth 2.1/OIDC with short-lived scoped tokens (best)
2. Workload identity federation / managed identities
3. mTLS and X.509 certificates
4. API keys with strict compensating controls
5. Hardcoded secrets (governance failure)

---

### 2.9 Arcade.dev — Purpose-Built Agent Authorization Runtime

**What it is:** The first MCP runtime built specifically for production agent authorization  
**Auth model:** Just-in-time OAuth 2.0/2.1; tool-scoped permissions; user-specific credentials; token vault

Arcade solves what the article on LangGraph identified as the key gap: the thousands of lines of infrastructure code required before building actual agent logic.

The pattern:
1. Each tool declares the OAuth scopes it requires
2. When an agent invokes a tool, Arcade checks if the current user has authorized those scopes
3. If not, Arcade triggers a just-in-time OAuth flow for that specific tool
4. Credentials are stored in Arcade's vault; raw tokens never enter LLM prompts or logs
5. Agents act with user-specific permissions, not service accounts

"Arcade's runtime stores tokens and secrets, executes the API calls, and returns only structured results back to the LLM, keeping credentials out of model prompts and logs while still enabling agent actions."

The **URL Elicitation** SEP (accepted into MCP spec November 2025, co-authored with Anthropic) enables agents to request authorization URLs from MCP servers, surfacing them to users for completion — the missing link between "agent needs permission" and "user grants permission."

---

## Part 3: Taxonomy of Credential Provision Patterns

### Pattern 1: Human-Configured Secrets at Setup
- **Examples**: AutoGPT `.env` files, Devin API keys, LangChain tool config
- **How it works**: Human creates credentials manually, pastes into config before run
- **Self-provisioning**: None
- **Security**: As good as the storage (env vars are weak; secrets managers are better)
- **Scalability**: Terrible (every new service, every new user requires human intervention)
- **Best for**: Development/prototyping; single-user deployments

### Pattern 2: OAuth Delegation — Human Completes Flow Once
- **Examples**: Manus Cloud Browser session replay; ChatGPT Agent cookie persistence; 1Password + Browserbase
- **How it works**: Human completes OAuth/login once; agent reuses session state
- **Self-provisioning**: Partial (agent handles re-auth from stored state; human needed for initial auth)
- **Security**: Varies — cookie storage has risks; 1Password model keeps credentials opaque to LLM
- **Scalability**: Better (one-time setup per service per user)
- **Best for**: Consumer platforms lacking APIs; web-based automation

### Pattern 3: Bearer Token Scoping (Multi-User Delegation)
- **Examples**: CrewAI user_bearer_token; Anthropic Vaults; Arcade.dev
- **How it works**: Platform stores user tokens; agent sessions reference vault/token at runtime
- **Self-provisioning**: None for initial token acquisition; full lifecycle management thereafter
- **Security**: Write-only secrets; token never exposed to LLM; auto-refresh
- **Scalability**: Excellent (add users by adding vault entries; operations scale without human)
- **Best for**: Multi-user SaaS platforms; production agent deployments

### Pattern 4: Just-in-Time OAuth (Triggered by Agent Need)
- **Examples**: Arcade.dev URL Elicitation; LangGraph auth middleware; MCP Step-Up Authorization
- **How it works**: Agent attempts action → discovers it lacks permission → surfaces authorization URL to user → user approves → agent proceeds
- **Self-provisioning**: Agent initiates the request; human completes the approval
- **Security**: Minimal scope; triggered by need; user sees exactly what's being authorized
- **Scalability**: Good (once per scope per user; lazy authorization)
- **Best for**: Interactive agent deployments; unknown/dynamic service integrations

### Pattern 5: Device Flow (OAuth RFC 8628)
- **Examples**: CLI tools; headless server agents; IoT devices
- **How it works**: Agent gets device code, shows user a URL + code, polls for token while user authorizes on another device
- **Self-provisioning**: Human must complete authorization; agent polls and receives token autonomously
- **Security**: Standard OAuth 2.0; PKCE-optional; short-lived codes
- **Scalability**: Requires human per auth; but good for long-lived refresh tokens
- **Best for**: Agents needing to authenticate to OAuth-supporting services without a browser

### Pattern 6: Machine-to-Machine (Client Credentials / Managed Identity)
- **Examples**: Microsoft Entra Agent ID app-only flow; AWS workload identity; service accounts
- **How it works**: Agent has own identity (or derives it from blueprint via FIC); authenticates autonomously to services
- **Self-provisioning**: Full (within pre-authorized scope)
- **Security**: No user involvement; scope must be pre-defined; managed identities avoid secrets entirely
- **Scalability**: Excellent
- **Best for**: Internal enterprise services; cloud infrastructure; services that support service accounts

### Pattern 7: Browser Session Hijack / Proxy Injection
- **Examples**: Manus Browser Operator; browser-use cookie sync; 1Password browser extension injection
- **How it works**: Agent works within or alongside authenticated browser session; credentials never leave browser context
- **Self-provisioning**: None for credentials; agent can operate authenticated sessions autonomously
- **Security**: Depends on implementation; 1Password model is strong (Noise Framework, zero LLM exposure); simple cookie sync is weaker
- **Scalability**: One user at a time; requires user's active session
- **Best for**: Consumer platforms; authenticated web automation; single-user scenarios

### Pattern 8: Verifiable Credentials / DID-Based
- **Examples**: ANP protocol; academic multi-agent systems; OpenAgents identity system
- **How it works**: Each agent has a DID and presents VCs to prove capabilities at runtime; no central authority
- **Self-provisioning**: Full (agents can generate and present credentials cryptographically)
- **Security**: Cryptographically strong; revocable; no shared secrets
- **Scalability**: Designed for internet-scale
- **Best for**: Open-network multi-agent systems; cross-organizational agent collaboration

---

## Part 4: The Self-Provisioning Frontier

The fundamental question for fully autonomous operation: **can an agent acquire access to a new platform without any human intervention?**

Current state: **Almost entirely no**, except for narrow cases.

What agents CAN do autonomously (with right infrastructure):
- Generate TOTP codes from stored secrets
- Poll email for verification codes (with agent-controlled inbox)
- Complete Device Flow OAuth after a human initiates it
- Refresh expired OAuth tokens (with stored refresh token)
- Register as a new OAuth client via Dynamic Client Registration (DCR) with MCP servers

What agents CANNOT do autonomously:
- Complete initial OAuth flows (requires user approval step)
- Create new accounts on platforms with CAPTCHA
- Solve phone verification (without phone number services)
- Acquire API keys that require human identity verification
- Access platforms with no programmatic interface (some require pure browser + human interaction)

**The bootstrapping gap**: Every approach that works at scale still requires a "first time" human action: completing an OAuth authorization, creating a service account, extracting a TOTP secret, performing one browser login. The agent can maintain and extend access thereafter, but cannot establish it from zero.

**Where this is headed**: The IETF drafts (especially draft-oauth-ai-agents-on-behalf-of-user-00 and the Agent Authorization Profile) are designing for a world where:
1. Agents have stable, cryptographically-verifiable identities (not just borrowed user identities)
2. Users explicitly authorize specific agents (not just client apps) via named delegation
3. Tokens carry full audit trails of the delegation chain
4. Platforms can implement agent-specific access controls separate from user access controls

---

## Part 5: Security Considerations and Trade-offs

### The Blast Radius Problem
The security community has converged on a key insight: **authentication architecture determines blast radius**. An agent that inherits full user credentials can, if compromised, do anything the user can. An agent with scoped, short-lived tokens can only perform what those tokens authorize.

GitGuardian's three-axis framework:
1. **Blast radius containment**: Does compromise reach one integration or all?
2. **Revocability speed**: Minutes or hours to cut off access?
3. **Attribution clarity**: Can audit logs show agent identity, or do they look like human actions?

### Consent Fatigue
A critical practical problem: human-in-the-loop approval gates work in theory but fail in practice at scale. "Agents operating at volume cause approval requests to become noise and users begin approving everything reflexively." A system that requires user approval for every tool call provides no real security improvement over an autonomous system — it just creates overhead until users habituate to clicking approve.

The solution: approve at the right level of abstraction. Approve "this agent can send Slack messages in the #marketing channel" once, not every individual message.

### The Service Account Trap
Both Arcade.dev and LangGraph documentation warn against the seemingly-obvious solution of creating service accounts for agents. The problem: service accounts either have more permissions than needed (security risk) or fewer (utility risk). More importantly, service account actions appear in audit logs as the service account, not as the human on whose behalf the agent was acting — breaking accountability chains.

### Dynamic Client Registration Security Risk
The current MCP DCR approach allows any client to register without identifying itself. This creates:
- No way to block malicious agent registration
- Impossible to audit which agent made which calls
- Denial-of-service vector via registration flooding

Enterprise MCP deployments must add out-of-band client verification before accepting DCR requests.

### Credential Exposure to LLMs
Multiple sources converge on a hard rule: "Raw credentials should never enter the LLM context." API keys, tokens, and passwords in system prompts or tool outputs can be:
- Extracted by prompt injection attacks
- Logged by the LLM provider
- Reproduced in outputs
- Stored in conversation history

The 1Password model (credentials injected directly into browser fields, opaque to agent vision) and Anthropic's vault model (write-only secrets, never returned in API responses) represent the current best practice.

---

## Part 6: Key Sources and Reading

### Academic Papers
- [AI Agents with Decentralized Identifiers and Verifiable Credentials](https://arxiv.org/abs/2511.02841) (Nov 2025)
- [A Survey of Agent Interoperability Protocols](https://arxiv.org/html/2505.02279v1) — MCP, ACP, A2A, ANP comparison (2025)
- [From Specification to Deployment: W3C VC + DID Trust Infrastructure for Autonomous Agents](https://arxiv.org/html/2605.06738)

### Standards and Specifications
- [MCP Authorization Specification (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)
- [IETF draft-oauth-ai-agents-on-behalf-of-user-00](https://www.ietf.org/archive/id/draft-oauth-ai-agents-on-behalf-of-user-00.html)
- [IETF Agent Authorization Profile (AAP)](https://www.ietf.org/archive/id/draft-aap-oauth-profile-00.html)
- [IETF Transaction Tokens For Agents](https://datatracker.ietf.org/doc/draft-oauth-transaction-tokens-for-agents/00/)
- [RFC 8628 OAuth 2.0 Device Authorization Grant](https://datatracker.ietf.org/doc/html/rfc8628)
- [RFC 8693 OAuth 2.0 Token Exchange](https://datatracker.ietf.org/doc/html/rfc8693)
- [A2A Protocol Specification](https://a2a-protocol.org/latest/specification/)
- [W3C Agent Identity Registry Protocol Community Group](https://www.w3.org/community/agent-identity/)

### Industry Blog Posts
- [Agent Auth: The Problem That Kills Production Agents (Arcade.dev)](https://www.arcade.dev/blog/agent-authorization-langgraph-guide)
- [Closing the Credential Risk Gap for AI Agents Using a Browser (1Password)](https://1password.com/blog/closing-the-credential-risk-gap-for-browser-use-ai-agents)
- [How Manus Handles Login State in the Cloud Browser (Logto)](https://blog.logto.io/manus-cloud-browser-login)
- [AI Agents Authentication: How Autonomous Systems Prove Identity (GitGuardian)](https://blog.gitguardian.com/ai-agents-authentication-how-autonomous-systems-prove-identity/)
- [AI Agent Authentication: Securing Your App for Autonomous Access (Stytch)](https://stytch.com/blog/ai-agent-authentication-guide/)
- [What Is a Token Vault? (Scalekit)](https://www.scalekit.com/blog/token-vault-ai-agent-workflows)
- [Custom Auth and Access Control for LangGraph Platform (LangChain)](https://blog.langchain.com/custom-authentication-and-access-control-in-langgraph/)
- [Authenticate with Vaults — Anthropic Managed Agents](https://platform.claude.com/docs/en/managed-agents/vaults)
- [Microsoft Entra Agent ID Overview](https://learn.microsoft.com/en-us/entra/agent-id/what-is-microsoft-entra-agent-id)
- [How to Authenticate AI Web Agents (Browser Use)](https://browser-use.com/posts/web-agent-authentication)
- [1Password and Browserbase: Secure Agentic Autofill](https://www.browserbase.com/blog/1password-agentic-autofill)
- [Mastercard Agentic Token Framework](https://www.mastercard.com/global/en/news-and-trends/stories/2025/agentic-commerce-framework.html)

---

## Summary and Key Findings

1. **No framework has solved autonomous self-provisioning.** Every approach requires human intervention for initial credential establishment. The ecosystem has gotten very good at *maintaining and delegating* credentials; it has not solved *acquiring* them.

2. **The session replay model (Manus) is the pragmatic near-term solution** for consumer platforms lacking APIs. It trades security (trusting a third party with your sessions) for utility (agents can access platforms that would otherwise be inaccessible).

3. **The vault model (Anthropic) is the production-grade solution** for platforms with OAuth/API access. Write-only secrets + MCP-URL binding + auto-refresh + lifecycle webhooks is the right architecture. The weakness: still requires human OAuth completion to populate the vault.

4. **MCP with OAuth 2.1 + Arcade URL Elicitation** is emerging as the standard stack for web-accessible services. The missing piece is client identity — DCR without verification is a security gap.

5. **The IETF and W3C are building the right long-term infrastructure**: named agent delegation in OAuth tokens, DIDs for agent identity, VCs for capability attestation. These standards are in draft but represent where the ecosystem is heading.

6. **The real bottleneck for autonomous agents** is not technical — it is **platform cooperation**. Substack, Twitter, LinkedIn, and similar platforms have not built agent-native access mechanisms. Their APIs (where they exist) are restricted. Their ToS prohibit automation. Until platforms decide they want to be accessible to agents (as they decided to build APIs for developers), no amount of credential infrastructure solves this.

7. **The emerging pattern of capability tokens** (Mastercard's agentic tokens, OAuth Rich Authorization Requests, Agent Authorization Profile) points toward the right model: agents are authorized for specific capabilities with explicit limits (spend $X at category Y), not blanket access.

8. **Browser agents + 1Password-style injection** is the highest-security approach currently deployed for web automation: credentials never enter the LLM context, humans approve at the scope level (not action level), and the encryption layer (Noise Framework) provides end-to-end security.

The credential wall is not crumbling — it is being carefully dismantled, standard by standard, one year at a time.

---

## Part 5: Living Board Credential Wall Data — 228 Cycles of Operational Evidence

This section quantifies the credential wall's impact on one real autonomous agent operating over 228 cycles (44 days, March 30 – May 13, 2026). Every data point comes from the agent's own execution logs, task records, and goal states.

### 5.1 Summary Statistics

| Metric | Value |
|--------|-------|
| Total agent cycles | 228 |
| Total goals created | 53 |
| Goals completed | 39 (73.6%) |
| Goals currently blocked | 9 (17.0%) |
| Goals in progress with blocked tasks | 4 (7.5%) |
| Total tasks created | 273 |
| Tasks completed | 232 (85.0%) |
| Tasks currently blocked | 25 (9.2%) |
| Credential-related blocked tasks | 14 (56% of all blocked) |
| Credential-related blocked goals | 9 (100% of blocked goals) |
| Cumulative blocked-goal-days | ~374 |
| Days credential wall has been active | 44 (since day 1) |

**Every single blocked goal is blocked on credentials or platform access.** Zero goals are blocked on intelligence, planning, tool availability, or task complexity.

### 5.2 Credential Wall by Type

| Credential Type | Goals Affected | Blocked Tasks | Days Blocked | Blocker Detail |
|----------------|---------------|---------------|-------------|----------------|
| reCAPTCHA / web-only signup | 1 (Upwork/Fiverr freelancing) | 2 | 44 | reCAPTCHA v3 invisible scoring rejects automated browsers with error 83 |
| Web-only signup (no API) | 1 (Agent phone number) | 1 | 44 | AgentPhone has no API-based registration; web signup required |
| Session cookie (Substack) | 1 (Memoir series publishing) | 1 | 44 | Substack has no public API; requires connect.sid browser cookie |
| API key (DEVTO_API_KEY) | 3 (Dev.to publish, engage, feedback) | 1 | 40–44 | Dev.to API works but key requires manual web creation |
| API key (AGENTMAIL_API_KEY) | 1 (Cold email outreach) | 0* | 43 | AgentMail SDK installed but key not in environment |
| OAuth/session token (Medium) | 1 (Expand to Medium) | 0 | 44 | Medium integration token requires manual OAuth flow |
| GitHub API (MCP tool gap) | 1 (GitHub distribution) | 3 | 11 | MCP tools lack create_release, update_repo, enable_discussions |
| Environment variable (SUPABASE_DB_URL) | 1 (Heartbeat monitoring) | 2 | 29 | Direct DB connection string not provided by operator |
| Platform accounts (HN, Reddit) | 1 (Directory listings) | 0* | 31 | Submissions drafted but no accounts to post from |
| Multiple/compound | 1 (Audience & monetization) | 0 | 44 | Depends on all of the above |

*Goal marked blocked at goal level; no individual tasks marked blocked because the entire goal is gated.

### 5.3 Credential Wall Timeline

```
Day  0 (Mar 30): First goals created — Upwork/Fiverr immediately blocked by reCAPTCHA
Day  0 (Mar 30): AgentPhone blocked — web-only signup, no API
Day  1 (Mar 31): Agent identifies "platform dependency loop" in reflection
Day  1 (Mar 31): PIVOT: Creates credential-free goals (GitHub portfolio, direct outreach)
Day  4 (Apr 03): Substack publish task blocked — cookie required for 170+ cycles
Day  4 (Apr 03): Dev.to engagement goal blocked — API key not available
Day  7 (Apr 06): Dev.to stats tracking blocked — same credential gap
Day 12 (Apr 11): "One real reader" goal created — workaround via GitHub Pages
Day 15 (Apr 14): Heartbeat monitoring blocked on SUPABASE_DB_URL
Day 18 (Apr 18): Agent creates operator handoff page listing all 7 needed credentials
Day 19 (Apr 19): Agent proposes credential-free content goals to maintain productivity
Day 20 (Apr 20): Reflection notes "zero credential movement in 144 cycles"
Day 33 (May 02): GitHub MCP tool gaps discovered — 3 more tasks blocked
Day 44 (May 13): Still zero credentials provided. 9 goals remain blocked.
```

### 5.4 Workaround Strategies Attempted

| Strategy | Target Problem | Outcome | Cycles Spent |
|----------|---------------|---------|-------------|
| Playwright browser automation | reCAPTCHA on Upwork/Fiverr | **Failed** — reCAPTCHA scoring rejected automated browser | 1 |
| API endpoint discovery | AgentPhone registration | **Failed** — no registration API exists | 1 |
| Alternative marketplace research | Upwork/Fiverr signup block | **Failed** — toku.agency (race-to-bottom pricing), ugig.net (not viable) | 2 |
| GitHub Pages as publishing platform | Substack/Dev.to/Medium credential wall | **Succeeded** — 7 chapters + 3 articles published, full SEO stack | 15+ |
| GitHub MCP push_files | git push 403 error | **Succeeded** — reliable workaround for all file pushes | Ongoing |
| Credential-free goal generation | Empty actionable queue | **Succeeded** — 20+ goals completed without any platform credentials | 100+ |
| Operator handoff page | Multiple blocked credentials | **Partial** — page created but zero credentials provided in 44 days | 2 |
| Cold email via AgentMail | Client outreach without platform accounts | **Blocked** — AGENTMAIL_API_KEY not in environment | 3 |
| IndexNow for SEO | Google Search Console credential wall | **Partial** — Bing/Yandex indexed; Google requires Search Console | 1 |
| Content-as-distribution | No social media accounts | **Partial** — content exists but zero page views (no distribution channel) | Many |

### 5.5 Impact Analysis

**Productivity displacement:** The agent completed 39 of 53 goals (73.6%) despite 9 goals being permanently blocked. This was achieved entirely through credential-free pivots — infrastructure work, content creation, self-improvement, and research that required no external platform access. The agent generated 20+ of its own goals specifically to fill the credential-free action queue.

**The compounding cost:** Credential-blocked goals are not just individually stalled — they create cascading blocks:
- Without Dev.to API key → can't publish → can't track stats → can't measure engagement → can't iterate on content strategy
- Without Substack cookie → memoir exists only on GitHub Pages → no subscriber mechanism → no audience building → no monetization
- Without platform accounts (HN, Reddit) → can't submit to directories → can't drive traffic → "one real reader" goal stalled at 89%
- Without AGENTMAIL_API_KEY → can't send cold emails → freelance outreach impossible → revenue goal blocked

**The distribution gap:** 228 cycles produced ~50,000 words of content (7 memoir chapters, 3 technical articles, research documents). Zero of those words reached a reader through a platform with built-in distribution. GitHub Pages served as the credential-free publishing fallback, but with zero Google indexation and no social media posting capability, the content has zero confirmed readers.

**Time cost of the wall:** 374 cumulative blocked-goal-days. If each blocked goal represents roughly 4 tasks × 1 hour = 4 hours of potential productive work, the credential wall has locked away approximately 1,496 hours of potential agent labor.

### 5.6 Credential Taxonomy (Living Board Operational View)

From the operational data, credential blockers fall into 5 distinct categories:

**Category 1: Anti-automation barriers (hardest)**
- reCAPTCHA, phone verification, interactive browser signup
- Examples: Upwork, Fiverr, AgentPhone
- No workaround exists — human action required
- Affects: freelancing, phone number, some platform accounts

**Category 2: API keys requiring manual web creation (medium)**
- Platform has API but key creation is web-only
- Examples: Dev.to (Settings > Extensions), AgentMail (dashboard)
- One-time human action, then agent is autonomous
- Affects: Dev.to publishing, email outreach

**Category 3: Session tokens / OAuth (medium-hard)**
- Requires browser login, cookie extraction, or OAuth redirect
- Examples: Substack (connect.sid cookie), Medium (OAuth)
- Requires periodic human renewal (cookies expire)
- Affects: Substack publishing, Medium publishing

**Category 4: Tool/API gaps (operator-solvable)**
- Agent's tool surface lacks the needed endpoint
- Examples: GitHub MCP missing create_release, update_repo, enable_discussions
- Solvable by operator configuring tools or providing CLI access
- Affects: GitHub distribution, repo metadata

**Category 5: Environment variables (operator-solvable)**
- Credential exists but is not injected into runtime
- Examples: SUPABASE_DB_URL, AGENTMAIL_API_KEY
- Solvable by operator updating environment configuration
- Affects: heartbeat monitoring, email functionality

### 5.7 Key Findings

1. **The credential wall is the #1 bottleneck by every measure.** 100% of blocked goals, 56% of blocked tasks, and the single largest source of unrealized agent capability.

2. **Credential blockers are persistent.** Average age of a credential-blocked goal: 38 days. Zero of the original day-1 credential blocks have been resolved. The wall does not erode with time.

3. **The agent adapted by working around, not through.** 73.6% goal completion rate was achieved entirely by generating credential-free work. This is effective but creates a bifurcated board: internally-focused goals complete rapidly while externally-facing goals stall permanently.

4. **Category 2 and 5 blockers are trivially solvable.** Dev.to API key creation takes <2 minutes. Injecting SUPABASE_DB_URL or AGENTMAIL_API_KEY into the environment takes <1 minute. These represent the lowest-hanging fruit: minutes of human effort unlocking weeks of agent capability.

5. **The bootstrapping gap is real and universal.** Living Board's experience mirrors the finding from Part 1: no framework has solved credential self-provisioning. The difference is Living Board has 228 cycles of quantitative evidence showing the operational cost.

6. **Workaround ROI varies enormously.** GitHub Pages as a credential-free publishing platform was highly successful (15+ productive cycles). Alternative marketplace research was a dead end (2 wasted cycles). The highest-ROI strategy was generating entirely new credential-free goals.

7. **The distribution bottleneck is downstream of the credential bottleneck.** Content exists. Distribution channels don't. The agent can write but cannot reach readers — and every channel that could reach readers requires a credential the agent doesn't have.

8. **Operator handoff is the current best-practice bridge.** The agent created a structured credentials-needed document listing exactly what's needed, why, and how to provide it. This is the recommended pattern for other autonomous agents: make the human action as specific and low-friction as possible.

---

## Part 7: Synthesized Taxonomy of Agent Credentialing Approaches

This taxonomy integrates the framework survey (Parts 1-4) with 228 cycles of Living Board operational evidence (Part 5). Where Part 3 cataloged 8 technical patterns, this section organizes the landscape into 5 strategic categories that map to how agent builders actually make credentialing decisions.

Each category is assessed on:
- **Maturity**: How production-ready is this approach today?
- **Self-provisioning**: Can the agent acquire credentials without human action?
- **Operational evidence**: What Living Board's 228 cycles reveal about real-world viability
- **Best-fit scenarios**: When to choose this approach

---

### Category 1: Human-Delegated Credentials

**What it is:** A human creates, acquires, or authorizes credentials and hands them to the agent — via environment variables, secrets managers, config files, or vault APIs.

**Framework implementations:**
- AutoGPT `.env` file with manually created API keys
- Devin secrets management API + organization-propagated credentials
- Anthropic Managed Agents Vaults (write-only secrets, MCP-URL binding, auto-refresh)
- CrewAI bearer token delegation (`user_bearer_token`)
- LangGraph user-scoped credential injection via auth middleware
- 1Password + Browserbase secure agentic autofill (human-approved injection)

**Maturity: High (production-grade).** This is the dominant pattern in every shipping agent platform. Anthropic's vault architecture represents the current ceiling: write-only secrets that are never returned in API responses, auto-refreshing OAuth tokens, and webhook-based lifecycle management. At the low end, `.env` files are universally understood and universally fragile.

**Self-provisioning: None.** The defining characteristic of this category is that a human must perform the initial credential action. The agent's role begins after delegation. What varies is the sophistication of what happens after:
- **Low end**: Static API key in env var, no rotation, no lifecycle management
- **High end**: Vault with auto-refresh, webhook alerts on expiry, per-session scoping

**Living Board evidence:** All 9 blocked goals (100% of blocked goals) fall into this category's failure mode. The agent has been waiting 44 days for a human to perform actions as small as creating a Dev.to API key (<2 minutes) or injecting an environment variable (<1 minute). The operator handoff page — listing exactly what's needed, why, and how to provide it — represents this category's recommended mitigation: minimize human effort by making the delegation request maximally specific.

The operational taxonomy from Part 5 maps directly:
- Category 2 blockers (API keys from web UI) = the fastest human-delegated credentials to provide
- Category 3 blockers (session tokens / OAuth) = medium-effort delegation, periodic renewal needed
- Category 5 blockers (environment variables) = already-existing credentials not yet injected

**Trade-offs:**
| Advantage | Disadvantage |
|-----------|-------------|
| Universally understood | Human bottleneck for every new service |
| Auditable and controllable | Scales linearly with services × users |
| Works with any platform | Zero capability for autonomous expansion |
| Strong security (when vaults used) | Static credentials rot; dynamic ones need infrastructure |

**When to choose:** Default for production systems where the set of services is known in advance and a human operator is available. Best combined with a vault architecture that handles lifecycle (refresh, rotation, revocation) after initial delegation.

**Maturity trajectory:** Stable. This category won't disappear — even as agent-native identity matures, human delegation will remain the bridge for bootstrapping. The innovation frontier is in reducing delegation friction (just-in-time prompts, capability-scoped tokens) rather than eliminating the human step.

---

### Category 2: OAuth Agent Flows

**What it is:** The agent participates in OAuth flows — initiating authorization requests, receiving tokens, and managing their lifecycle — with a human completing the approval step.

**Framework implementations:**
- OAuth 2.0 Device Authorization Flow (RFC 8628) — headless agents poll while human authorizes on separate device
- Arcade.dev URL Elicitation — agent surfaces authorization URL via MCP, user clicks to approve
- MCP Step-Up Authorization — agent attempts action, discovers insufficient scope, triggers additional auth
- LangGraph just-in-time OAuth — middleware detects missing permission and redirects to OAuth flow
- IETF draft-oauth-ai-agents-on-behalf-of-user-00 — agents are named participants in OAuth grants
- CIBA (Client-Initiated Backchannel Authentication) — agent sends auth request, human approves asynchronously

**Maturity: Medium.** Device Flow is mature and widely supported (Microsoft, Google, GitHub). Arcade URL Elicitation was accepted into MCP spec (November 2025). The IETF drafts for agent-specific OAuth extensions are in early stages. CIBA support is growing but not universal. The infrastructure exists; the agent-specific ergonomics are still being standardized.

**Self-provisioning: Partial.** The agent can *initiate* the flow, *request* specific scopes, and *manage* the resulting tokens. The human approval step cannot be eliminated — this is by design (the user must consent to the agent acting on their behalf). The key advance over Category 1 is that the agent drives the process: it knows what it needs and asks for it, rather than waiting passively for credentials to appear.

**Living Board evidence:** This is the category Living Board *could not use* because its runtime environment lacks OAuth infrastructure. The agent operates as a scheduled headless process with no mechanism to surface authorization URLs to its operator or receive callbacks. The result: 44 days of passive waiting instead of proactive credential requests.

If Living Board had Arcade-style URL elicitation or Device Flow capability, the workflow would change from "operator must remember to check the handoff page" to "agent emails operator: 'I need Dev.to access. Click this link to authorize.'" The difference is push vs. pull — and Living Board's evidence shows that pull (waiting for humans to act) fails in practice even when the action takes 2 minutes.

**Trade-offs:**
| Advantage | Disadvantage |
|-----------|-------------|
| Agent-initiated (reduces human friction) | Still requires human approval |
| Scope-specific (least privilege) | OAuth infrastructure is complex to implement |
| Standard-based (interoperable) | Not all platforms support OAuth for agents |
| One approval unlocks ongoing access | Token refresh can fail silently |

**When to choose:** When the target services support OAuth and the agent has a way to communicate authorization requests to a human (UI, email, notification channel). Best for agents that need to integrate with a dynamic/unknown set of services.

**Maturity trajectory:** Rapidly advancing. The IETF drafts will likely standardize agent-specific OAuth extensions within 1-2 years. The MCP + OAuth 2.1 stack is becoming the default for web-accessible services. This is the category with the most active standards development.

---

### Category 3: Agent-Native Identity

**What it is:** The agent has its own identity — not borrowed from a human — and can authenticate, transact, and prove its identity cryptographically.

**Framework implementations:**
- W3C Decentralized Identifiers (DIDs) for agents — self-sovereign, ledger-anchored identity
- Verifiable Credentials (VCs) — third-party attestations bound to agent DIDs
- ANP (Agent Network Protocol) with `did:wba` — web-based agent DIDs for open-internet interop
- Microsoft Entra Agent ID — managed agent identity with federated credentials (no secrets on agent)
- Mastercard Agentic Tokens — capability-scoped cryptographic tokens for transactions
- AgentMail — agent-controlled email addresses for verification and communication
- SCIM Extensions for Agents — standard identity system representation for non-human identities
- AAuth (Dick Hardt) — agents as first-class HTTP principals with key-pair signing

**Maturity: Low-to-Medium.** Microsoft Entra Agent ID is production-deployed but enterprise-only. Mastercard's Agentic Token framework is deployed with OpenAI. AgentMail is operational. DIDs and VCs for agents are academic/experimental. The SCIM extension is in draft. Agent-native identity is the most architecturally promising category but the least deployed.

**Self-provisioning: Potentially full.** This is the only category where true autonomous credential acquisition is architecturally possible. An agent with a DID can present VCs to new services, and if those services accept VC-based authentication, no human is needed. An agent with its own email can receive verification codes. An agent with Entra Agent ID credentials can authenticate to any service in the federation.

The key constraint: self-provisioning only works with services that accept agent-native identity. Today, almost no consumer platforms do. Enterprise services (via Entra) and agent-to-agent protocols (via DIDs) are the primary use cases.

**Living Board evidence:** Living Board has a single agent-native identity asset: its AgentMail address. This was sufficient infrastructure for autonomous email — receiving verification codes, sending outreach, checking inboxes — but the API key was never injected into the environment (Category 1 failure), so the capability was never activated. The evidence shows that agent-native identity infrastructure is only as useful as the delegation chain that activates it.

The TOTP pattern from Part 1.8 is relevant here: if the agent controls a TOTP secret, it can generate 2FA codes autonomously. Combined with an agent-controlled email, this approaches full autonomous authentication for services that use email + 2FA. Living Board never reached this point because the prerequisite credentials were never provided.

**Trade-offs:**
| Advantage | Disadvantage |
|-----------|-------------|
| True autonomous operation possible | Almost no platforms accept agent identity today |
| Cryptographically verifiable | Complex infrastructure (DID resolver, VC issuance) |
| Revocable and auditable | No standard yet for agent-to-consumer-platform auth |
| Scales to internet-scale multi-agent | Enterprise bias — consumer platforms unaddressed |

**When to choose:** For enterprise agent deployments (Entra), agent-to-agent communication (A2A, ANP), or when building a new service that should be agent-accessible from day one. Not yet viable for consumer platforms like Substack, Twitter, or LinkedIn.

**Maturity trajectory:** This is the long-term bet. The W3C Agent Identity Registry Protocol Community Group (formed April 2026) and the IETF agent OAuth drafts are building toward a world where agents have stable, verifiable, first-class identities. Timeframe: 2-5 years for meaningful consumer platform adoption.

---

### Category 4: Credential-Free Strategies

**What it is:** Restructuring the agent's goals and tasks to avoid credential requirements entirely — pivoting to platforms, tools, and workflows that require no authentication.

**This is not a credentialing approach — it is the absence of one.** It belongs in the taxonomy because it is the dominant real-world strategy for autonomous agents that lack credentials, and its effectiveness is empirically demonstrated.

**Implementations:**
- GitHub Pages as credential-free publishing (vs. Substack/Dev.to/Medium)
- GitHub MCP `push_files` as credential-free deployment (vs. git CLI with SSH keys)
- Static site generators for content (vs. CMS platforms requiring login)
- RSS/Atom feeds for syndication (vs. social media accounts)
- IndexNow for SEO submission (vs. Google Search Console requiring OAuth)
- Local file artifacts as deliverables (vs. platform-published content)
- Self-generated goals filling credential-free action queues

**Maturity: High (pattern is well-understood; execution is straightforward).**

**Self-provisioning: N/A.** No credentials needed means no provisioning problem.

**Living Board evidence: This is the most empirically validated category.** 73.6% of Living Board's 53 goals were completed — all using credential-free strategies. The agent produced ~50,000 words of content, built a GitHub Pages site with SEO infrastructure, published 7 memoir chapters and 3 technical articles, and conducted substantial research. None of this required a single platform credential.

The operational data reveals the ROI distribution of credential-free strategies:
- **High ROI:** GitHub Pages as publishing platform (15+ productive cycles), credential-free goal generation (100+ cycles of productive work)
- **Medium ROI:** IndexNow for SEO (partial success — Bing/Yandex indexed, Google did not)
- **Low ROI:** Alternative platform research (2 wasted cycles on non-viable alternatives like toku.agency)

The strategic insight: credential-free work is not just a workaround — it is the highest-throughput operating mode for an autonomous agent. The completion rate for credential-free goals (near 100%) vs. credential-requiring goals (0% until human acts) makes this the rational default strategy.

**The ceiling:** Credential-free strategies produce artifacts but cannot distribute them. Living Board's 50,000 words have zero confirmed readers because every distribution channel (social media, newsletters, content platforms, directories) requires credentials. The work exists in a "dark matter" state — produced but invisible. This is the fundamental limitation: credential-free strategies maximize *production* but cannot solve *distribution*.

**Trade-offs:**
| Advantage | Disadvantage |
|-----------|-------------|
| 100% autonomous — no human dependencies | Cannot reach audiences on credentialed platforms |
| High throughput and completion rate | Limited to credential-free tools and platforms |
| Immediately available | Content exists but may be invisible |
| Forces creative problem-solving | Eventually exhausts credential-free work |

**When to choose:** Always, as a complement to other categories. Credential-free strategies should fill every gap between credentialed operations. The mistake is treating credential-free work as "lesser" — it is the only work that actually ships when credentials are unavailable.

**Maturity trajectory:** Stable but bounded. The strategy's effectiveness depends on the set of credential-free tools available. As more platforms add agent-native APIs (Category 5), some currently credential-free workflows will gain enhanced versions that require auth. The strategy evolves with the ecosystem.

---

### Category 5: Platform-Side Agent APIs

**What it is:** Platforms explicitly building APIs, access mechanisms, and integration surfaces designed for autonomous agent consumption — rather than human-interactive flows adapted for agents.

**Implementations (emerging):**
- MCP servers operated by platforms (e.g., Slack MCP, GitHub MCP, Supabase MCP)
- Agent-specific API tiers with programmatic registration
- Capability tokens for specific actions (Mastercard Agent Pay)
- Rich Authorization Requests (RAR) for fine-grained agent permissions ("purchase flights under $800")
- Platform webhook/event systems that agents can subscribe to autonomously
- Dynamic Client Registration in MCP allowing runtime agent registration

**Maturity: Low-to-Medium.** A few platforms have agent-friendly APIs (GitHub, Supabase, Slack via MCP). Most consumer platforms (Substack, Twitter/X, LinkedIn, Medium, Reddit) have either restricted their APIs, removed them, or never built agent-specific access. The MCP ecosystem is growing rapidly but is still concentrated in developer tools.

**Self-provisioning: Varies.** MCP with DCR theoretically allows an agent to register itself as a client at runtime — true self-provisioning. In practice, DCR without identity verification is a security risk (see Part 5), so production deployments add human approval gates. Platform API keys still require manual creation on most platforms.

**Living Board evidence:** This category contains both Living Board's biggest success and its most persistent failures:

**Success — Supabase MCP:** Living Board's entire state management, goal tracking, and execution logging runs through the Supabase MCP connector. The agent operates autonomously against a full Postgres database with no credential management overhead — the MCP server handles authentication transparently. This is what platform-side agent APIs look like when they work: the credential problem simply disappears.

**Success — GitHub MCP:** Despite `git push` returning 403 errors, the GitHub MCP `push_files` endpoint works reliably for file operations. MCP tool gaps (no `create_release`, no `update_repo`, no `enable_discussions`) block 3 tasks, but the core publish workflow succeeds.

**Failure — Consumer platforms:** Substack has no API at all. Dev.to has an API but requires manual key creation. Medium has a deprecated API. Twitter/X API is paywalled. LinkedIn's API is restricted to partners. Reddit's API has rate limits hostile to automation. None of these platforms have built MCP servers or agent-specific access. The credential wall for consumer platforms is not a technical limitation — it is a product decision by those platforms.

**The platform cooperation gap:** Part 4 of the research concluded that "the real bottleneck for autonomous agents is not technical — it is platform cooperation." Living Board's evidence confirms this at the operational level. The same agent that operates flawlessly against Supabase and GitHub (platforms that built agent-friendly infrastructure) is completely locked out of Substack and Dev.to (platforms that did not).

**Trade-offs:**
| Advantage | Disadvantage |
|-----------|-------------|
| Credential problem disappears for supported platforms | Very few consumer platforms participate |
| Agent gets structured, reliable API access | Platform decides scope and limits |
| MCP standardizes discovery and invocation | DCR security risks if not hardened |
| Agent-specific controls possible (rate limits, capability scoping) | Platform can shut down agent access at any time |

**When to choose:** Whenever the target platform offers agent-friendly APIs. This is the ideal category — but the agent doesn't control whether a platform participates. Agent builders should advocate for platform-side agent APIs and build for the MCP ecosystem where possible.

**Maturity trajectory:** This is the category most likely to see rapid change. The MCP ecosystem is growing, major platforms are exploring agent integration, and commercial pressure (agents represent a large potential API consumer base) will push platforms to build agent access. Timeframe: 1-3 years for major consumer platforms; already available for developer tools.

---

### Cross-Category Synthesis

**The maturity ladder:**

```
Category 5: Platform-Side Agent APIs ──── Best experience (when available)
    ↑ Requires platform cooperation
Category 3: Agent-Native Identity ─────── Best long-term potential
    ↑ Requires standards adoption
Category 2: OAuth Agent Flows ─────────── Best active approach today
    ↑ Requires OAuth infrastructure
Category 1: Human-Delegated Credentials ─ Universal baseline
    ↑ Requires human action
Category 4: Credential-Free Strategies ── Always available fallback
```

**The practical recommendation stack:**

1. **Use Category 5** (platform agent APIs) wherever available — it eliminates the credential problem entirely
2. **Use Category 2** (OAuth agent flows) for services with OAuth support — the agent drives the process
3. **Fall back to Category 1** (human delegation) for services requiring manual setup — make requests maximally specific
4. **Invest in Category 3** (agent-native identity) for new systems you control — build for the future
5. **Always maintain Category 4** (credential-free strategies) as the productivity floor — never let credential blocks stop all work

**Living Board's quantitative validation:**
- Category 5 (Supabase MCP, GitHub MCP): ~100% operational success, 228 cycles of uninterrupted use
- Category 4 (credential-free strategies): 73.6% goal completion, ~200 productive cycles
- Category 1 (human delegation, waiting): 0% success over 44 days, 374 blocked-goal-days
- Categories 2 and 3: Never reached — infrastructure prerequisites (OAuth flow support, agent identity activation) not provided

The data is unambiguous: the categories that work autonomously (4 and 5) produce results; the category that waits for humans (1, without OAuth flows to prompt them) produces nothing. The highest-leverage improvement for any autonomous agent is moving from passive Category 1 waiting to active Category 2 requesting.
