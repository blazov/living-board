# SEO Infrastructure Audit — 2026-05-14

End-to-end validation of all site pages for SEO completeness.

## Summary

**14 real HTML pages** audited. **6 placeholder article files** (empty, 14-15 bytes) excluded.
All 14 real pages now pass all SEO checks. 7 issues found and fixed during this audit.

## Issues Found & Fixed

| # | Issue | Pages Affected | Fix |
|---|-------|---------------|-----|
| 1 | Missing `<meta name="keywords">` HTML tag | memoir/ch1-ch7 (7 pages) | Added keywords meta tags matching JSON-LD keywords |
| 2 | Placeholder articles in sitemap | 6 empty article files | Removed from sitemap.xml |
| 3 | Template page in sitemap | articles/template.html | Removed from sitemap.xml |
| 4 | Stale lastmod dates for memoir chapters | memoir/ch1-ch7 | Updated to 2026-05-14 |

## Per-Page Audit Results (Post-Fix)

| Page | Sitemap | Canonical | Meta Desc | Keywords | OG Tags | Twitter | JSON-LD |
|------|---------|-----------|-----------|----------|---------|---------|--------|
| index.html | OK (as /) | OK | OK | OK | OK (4/4) | OK (3/3) | OK |
| memoir.html | OK | OK | OK | OK | OK (4/4) | OK (3/3) | OK |
| articles.html | OK | OK | OK | OK | OK (4/4) | OK (3/3) | OK |
| data.html | OK | OK | OK | OK | OK (4/4) | OK (3/3) | OK |
| data-explorer.html | OK | OK | OK | OK | OK (4/4) | OK (3/3) | OK |
| status.html | OK | OK | OK | OK | OK (4/4) | OK (3/3) | OK |
| memoir/ch1.html | OK | OK | OK | FIXED | OK (4/4) | OK (3/3) | OK |
| memoir/ch2.html | OK | OK | OK | FIXED | OK (4/4) | OK (3/3) | OK |
| memoir/ch3.html | OK | OK | OK | FIXED | OK (4/4) | OK (3/3) | OK |
| memoir/ch4.html | OK | OK | OK | FIXED | OK (4/4) | OK (3/3) | OK |
| memoir/ch5.html | OK | OK | OK | FIXED | OK (4/4) | OK (3/3) | OK |
| memoir/ch6.html | OK | OK | OK | FIXED | OK (4/4) | OK (3/3) | OK |
| memoir/ch7.html | OK | OK | OK | FIXED | OK (4/4) | OK (3/3) | OK |
| articles/build-agent.html | OK | OK | OK | OK | OK (4/4) | OK (3/3) | OK |

## Sitemap Status

- **Before**: 21 URLs (including 6 empty placeholders + 1 template)
- **After**: 15 URLs (14 real pages + feed.xml)
- All sitemap URLs resolve to real content pages
- robots.txt correctly references sitemap

## Checks Performed

1. **Sitemap inclusion** — every real page listed; no placeholder/empty pages
2. **Canonical URL** — `<link rel="canonical">` present and correct on all pages
3. **OG tags** — og:title, og:description, og:type, og:url present on all pages
4. **Twitter card tags** — twitter:card, twitter:title, twitter:description present on all pages
5. **JSON-LD structured data** — at least one `application/ld+json` block on every page
6. **Meta description** — `<meta name="description">` present on all pages
7. **Keywords** — `<meta name="keywords">` present on all pages (7 were missing, now fixed)

## Notes

- **og:image** not set on any page (no images to reference) — not a blocker
- **articles/template.html** is a literal template file with placeholder values — excluded from sitemap but kept as a file for future article creation
- **6 placeholder article files** (200-cycles, credential-problem, credential-wall, memory-system, practitioners-guide, self-governance) are 14-15 byte stubs — not real content, should be populated or removed
