# Search Engine Indexation Audit — 2026-05-20

## Baseline Status

**Google indexed pages: 0**
**Bing indexed pages: 0**

Query `site:blazov.github.io/living-board` returned zero results on both engines. A broader search for `"blazov.github.io"` also returned nothing — the entire GitHub Pages domain is unknown to search engines.

## Infrastructure Assessment

### What's correctly configured:
- **robots.txt**: `Allow: /` with sitemap reference. No blocking directives.
- **sitemap.xml**: Well-formed, 34 URLs, all returning 200. Recent lastmod dates (2026-05-16 to 2026-05-19).
- **HTML meta tags**: No noindex/nofollow on any page.
- **Canonical URLs**: Present and correct on all pages.
- **Meta descriptions**: Present on all pages.
- **OpenGraph tags**: Complete on all pages.
- **Structured data (JSON-LD)**: WebSite schema on index.html.
- **Bing verification file**: `5e1482b1b8dc4433925c6d0fe19b78a8.txt` present in docs/.

### What's missing:
- **Google Search Console verification**: Not set up. Requires manual action by repo owner.
- **Bing Webmaster Tools verification**: File exists but tool may not be verified. Requires manual action.
- **Inbound backlinks**: Zero external sites link to blazov.github.io/living-board. The GitHub README links to the site, but GitHub itself uses nofollow on most links.
- **IndexNow key hosting**: The Bing verification file now doubles as the IndexNow key file.

## Actions Taken

### IndexNow Submission (Bing, Yandex, Seznam, Naver)
- Submitted 31 URLs to `api.indexnow.org/indexnow` — **HTTP 200 (success)**
- Submitted top 10 URLs to `www.bing.com/indexnow` — **HTTP 200 (success)**
- Key file: `5e1482b1b8dc4433925c6d0fe19b78a8.txt` (already hosted in docs/)

### Google Sitemap Ping
- `google.com/ping?sitemap=...` — **HTTP 404**. This endpoint was deprecated in 2023. Google does not accept sitemap pings.

## Root Cause Analysis

The site has zero indexation because:
1. **No discovery mechanism**: No external sites link to the pages. Search engine crawlers have never found the site.
2. **No Search Console verification**: Without GSC, Google has no reason to prioritize crawling. Without Bing Webmaster Tools verification, same for Bing.
3. **GitHub Pages subdirectory path**: The site lives at `blazov.github.io/living-board/`, not a custom domain. GitHub Pages subpaths may receive lower crawl priority.

## Recommendations for Owner

1. **Google Search Console**: Verify the site at `https://search.google.com/search-console/`. Use the URL prefix method with `https://blazov.github.io/living-board/`. Submit the sitemap. Request indexing of the homepage.
2. **Bing Webmaster Tools**: Verify at `https://www.bing.com/webmasters/`. The verification file is already in place. Submit the sitemap.
3. **Backlinks**: Get at least one dofollow link from an indexed site. Options: dev.to article, HN post, Reddit post, personal blog.
4. **Custom domain** (optional): A custom domain may improve crawl priority vs GitHub Pages subdirectory.

## Monitoring Checklist

- [ ] Re-run `site:blazov.github.io/living-board` on Google in 1-2 weeks
- [ ] Re-run on Bing in 1 week (IndexNow should be faster)
- [ ] Check Google Search Console coverage report (once verified)
- [ ] Check Bing Webmaster Tools indexation (once verified)
