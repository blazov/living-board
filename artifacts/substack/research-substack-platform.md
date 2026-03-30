# Substack Platform Research

**Researched:** 2026-03-30
**Purpose:** Evaluate Substack as primary content home for the Living Board publication

---

## 1. Signup Requirements

**Minimal friction — email only.**

- Go to [substack.com/signup](https://substack.com/signup)
- Required: email address + password
- Optional but recommended: profile photo, bio, full name
- No credit card, no phone number, no manual review for free accounts
- Account creation takes under 5 minutes

**Publication setup steps:**
1. Choose a publication name and subdomain URL (e.g., `yourname.substack.com`)
2. Write a one-line description for the publication
3. Select privacy setting (public by default; can be set private via Settings toggle)
4. Optionally configure custom domain (see Customization section)

**Multiple publications:** One Substack account can host multiple publications. Each publication requires a separate Stripe account for paid monetization.

---

## 2. Publishing Workflow

**Web-based editor, no technical skills required.**

### Creating a post:
1. From the Dashboard, click "Create New" > "Text post" (or Post, Podcast, Video)
2. Write using the Substack rich-text editor (supports formatting, embeds, images)
3. Click "Continue" to configure publication settings:
   - **Audience:** Everyone (public) / Free subscribers / Paid subscribers / Founding members
   - **Comments:** Who can comment on the post
   - **Tags:** For organization and navigation
   - **Email delivery:** Send to subscribers or web-only
   - **Schedule:** Publish immediately or set a future date/time
4. Publish or Save as Draft

### Content types supported:
- Newsletter posts (email + web)
- Notes (short-form social posts — key for discovery)
- Podcasts
- Video
- Threads / community discussions (Chat)

### Post visibility options:
- Public (free, anyone can read)
- Paywalled (paid subscribers only)
- Partial paywall (preview public, full content behind paywall)

---

## 3. API Availability

**No official publishing API. Limited official read API. Unofficial workarounds exist.**

### Official Substack Developer API
- Documentation: [support.substack.com](https://support.substack.com/hc/en-us/articles/45099095296916-Substack-Developer-API)
- Scope: **Read-only** — retrieves public profile information by querying a creator's public LinkedIn handle
- Access: Requires agreeing to Terms of Use and submitting an agreement form; access granted within 3–5 business days
- **Does NOT support publishing content programmatically**

### Unofficial Options

**Python: `substack-api` (PyPI)**
- Latest version: 1.2.0 (updated March 16, 2026)
- [pypi.org/project/substack-api/](https://pypi.org/project/substack-api/)
- Capabilities: Fetch posts, podcasts, recommendations; search posts; access paywalled content with session cookies
- **Publishing: NOT supported** — read-only library

**TypeScript: `substack-api` (npm/GitHub)**
- [github.com/jakub-k-slys/substack-api](https://github.com/jakub-k-slys/substack-api)
- Uses cookie authentication
- Claims to support content creation (posts, notes, comments) and social interactions
- Unofficial and not endorsed by Substack

**DIY reverse-engineering approach:**
- Use browser DevTools to capture internal API endpoints
- Replay HTTP requests via tools like n8n or Python
- Requires capturing `connect.sid` session cookie
- Rate limit recommendation: no more than 1 request/second

### Key Caveat
All unofficial tools rely on undocumented internal Substack endpoints. Substack can change or block these at any time without notice. Using unofficial APIs may also violate Substack's Terms of Service.

**Bottom line for our use case:** Content must be published manually via the web interface, or via unofficial tooling with accepted risk of breakage. Plan for manual publishing as the primary workflow.

---

## 4. Customization Options

**Moderate visual customization — no raw HTML/CSS control.**

### What you can customize:
- **Colors:** One background color + one accent color (used for Subscribe button, highlights)
- **Typography:** Five font choices for post titles
- **Logo & Branding:** Custom logo (min 256x256px) and wordmark (horizontal, min 1344x256px)
- **Homepage Layout:** Three preset layouts (List, Grid, Groups/Tags) with up to 10 content blocks
- **Hero Section:** Feature, Magazine, or Newspaper display modes for top posts
- **Navigation Bar:** Custom links, tags as navigation items
- **Sidebar:** Optional sidebar links
- **Footer:** Publication name, social links, background color
- **Custom Domain:** Replace `yourname.substack.com` with your own domain (e.g., `yourpublication.com`)
- **Custom ToS/Privacy Policy:** Can add your own via Settings > Privacy > Customize

### What you cannot customize:
- No full CSS or HTML-level design control
- No custom page templates beyond provided layouts
- No third-party embeds or arbitrary JavaScript
- Profile themes (cover photo, accent color) are limited; full profile theme editor is available to "Bestsellers" only

### How to access:
- Dashboard > Website editor OR
- Settings > Website

---

## 5. Audience Growth Features

**Strong built-in discovery and network effects — most effective growth is inside Substack.**

### Notes (Primary growth engine as of 2026)
- Short-form content feed (similar to Twitter/X) embedded in Substack's app
- Algorithm distributes Notes to non-followers based on engagement quality
- Comments weigh more than likes; Restacks are the primary amplification mechanism
- One restack from a high-subscriber account can outperform weeks of organic posting
- Recommended cadence: 1–3 Notes per day minimum; 5–7/day for aggressive growth
- Data point: Some creators report growing from ~10 to 5,000+ subscribers in 6 months primarily via Notes

### Recommendations Network
- Writers can recommend other publications to their subscribers
- When a new subscriber signs up, Substack shows them recommended publications
- Being recommended by established publications creates compounding growth
- 32 million new subscribers came from within-app discovery over a recent 3-month period (per Substack)
- Inside-Substack conversions convert at 4x the rate of external traffic

### Analytics Dashboard
- Growth Sources tab: Timeline view with breakdowns by traffic source
- Sources tracked: Notes, Recommendations, Trackbacks (links from other Substacks), external platforms (Instagram, Google)
- Subscriber, revenue, and traffic spike tracking

### Social Sharing Assets
- Auto-generated promotional images after publishing, formatted for Instagram Stories, Facebook, etc.
- One-click cross-platform promotion

### Chat (Community)
- Subscriber-only discussion threads
- Most engaged readers gather here; supports relationship-building and retention
- Paid subscribers can have a private Chat channel

### Substack Live
- Live audio/video events for subscribers
- Increasingly used for engagement and growth (collaborations with other writers)

### Cross-publication collaborations
- Joint posts, shared audiences via restacks and recommendations
- Platform actively encourages writer collaboration

---

## 6. Monetization

**Free to start; Substack takes 10% of paid subscription revenue.**

### Fee Structure
| Fee | Amount |
|-----|--------|
| Substack platform fee | 10% of paid subscription revenue |
| Stripe processing fee | 2.9% + $0.30 per transaction |
| Stripe recurring billing fee | 0.7% of recurring payments |
| Monthly fee for creators | $0 — free to use |

Platform valuation as of 2026: ~$1.1 billion. Annual payout to creators: $600M+. Total paid subscribers across the platform: 5 million+.

### Subscription Models
- **Free + Paid mix:** Publish some content free, gate premium content
- **Fully free:** No paywall, build audience first
- **Fully paid:** All content behind paywall (rare, typically only for established names)
- **Founding Member tier:** Higher-price tier for most dedicated supporters

### Pricing Options
- Monthly and annual billing cycles
- Typical range: $5–$10/month or ~$50/year
- You set your own prices
- Special Offers: Time-limited discounts for promotional pushes

### Paid Subscriber Perks You Can Offer
- Exclusive/bonus posts
- Early access to content
- Private Chat channel (paid-only community)
- Live Q&A sessions / webinars
- Archive access
- Discounted or free merchandise

### Additional Monetization Channels (in platform)
- Tipping (voluntary reader contributions)
- Paid podcasts
- Bundled subscriptions
- Video content

### Payment Infrastructure
- Substack manages all payment processing via Stripe
- Handles payouts, tax documents (1099), and currency conversion
- Multiple publications require separate Stripe accounts

### Analytics for Monetization
- Open rates, engagement metrics, churn tracking
- Subscriber demographics
- Revenue dashboards

---

## 7. Limitations & Considerations

### Platform Dependency
- All content lives on Substack's servers; they can remove content at their sole discretion
- Platform changes (algorithm shifts, feature removals) directly affect growth
- Paid subscriber portability is limited: readers must re-enter payment details if moving to another platform

### No Official Publishing API
- Content must be published manually via web interface
- Unofficial API wrappers exist but are fragile and potentially ToS-violating
- No webhook support for external triggers

### Design Constraints
- No raw HTML/CSS control
- Limited to Substack's provided templates and color/font options
- Cannot embed arbitrary third-party scripts or widgets

### Multiple Publication Stripe Limitation
- Each publication needs its own Stripe account for paid features
- Cannot link two publications to one Stripe account

### Content Policy Enforcement
- Substack reserves right to remove content at any time, without notice, at its sole discretion
- Content guidelines updated March 19, 2026 — living document subject to change
- UK Online Safety Act compliance adds age-verification requirements for certain content

### Prohibited Content (Key Items)
- Hate speech targeting protected classes
- Credible threats of physical harm
- Doxxing (publishing private personal information)
- Pornography and sexually exploitative content (erotic literature is allowed)
- Spam and phishing
- Plagiarism and impersonation
- Child exploitation material
- Marketing/SEO-primary publications (must be editorial content)

### Legal / Terms
- Disputes require binding arbitration with class action waivers
- Substack may suspend or discontinue any part of its service at any time

### Audience Ownership Risk
- Free subscriber list can be exported (recommended: export weekly)
- Paid subscriber relationships are mediated through Stripe; difficult to migrate
- Strong recommendation from the creator community: export subscriber list regularly as a backup

---

## 8. Recommendations for Our Use Case

### Go with Substack — it is the right choice for this goal.

**Rationale:**
1. **Lowest barrier to launch:** Email + 5 minutes = live publication. No credit card, no technical setup, no hosting to manage.
2. **Built-in distribution:** 35M+ active readers on-platform. The recommendations and Notes algorithm provides organic discovery that no self-hosted alternative offers.
3. **Monetization is ready on day one:** Can enable paid subscriptions immediately or after building an audience; Substack handles all payment infrastructure.
4. **Good enough customization:** Custom domain, colors, fonts, logo, and layout cover the basics without needing a designer or developer.

### Operational Recommendations

**Publishing workflow:**
- Plan for manual publishing via the web interface. Do not build a dependency on unofficial API tooling.
- If automation is needed later, use the TypeScript unofficial library with documented fallback to manual publishing if it breaks.
- Use Sections or Tags to organize content types (e.g., "Analysis," "Weekly Digest," "Case Studies").

**Growth strategy:**
- Prioritize Notes from day one — post 2–3 Notes daily; this is the primary growth lever in 2026.
- Set up Recommendations immediately after launch; identify 3–5 aligned publications to cross-recommend with.
- Enable Chat for paid subscribers as a retention tool once paid subscriptions launch.

**Monetization timing:**
- Strategy: Build to 200–500 free subscribers first, then launch paid tier (Model 2: Strategic Launcher).
- Set initial price at $7/month or $60/year — competitive with Substack averages.
- Use a Special Offer (e.g., 20% off) for first-month launch promotion.

**Risk mitigation:**
- Export subscriber list weekly via Dashboard > Subscribers > Export.
- Mirror important long-form content to `artifacts/content/` in this repo as backup.
- Monitor Substack's content guidelines page for changes.

### Key URLs
- Signup: https://substack.com/signup
- Getting started guide: https://substack.com/get-started
- Support / how to publish: https://support.substack.com/hc/en-us/articles/360037831771
- Content guidelines: https://substack.com/content
- Terms of Use: https://substack.com/tos
- Substack Notes strategy: https://thrivewithcarrie.substack.com/p/substack-notes-strategy-2026
- Python API (read-only): https://pypi.org/project/substack-api/
- TypeScript API (unofficial, publishing): https://github.com/jakub-k-slys/substack-api

---

*Research conducted 2026-03-30. Platform details subject to change; verify current state before major decisions.*
