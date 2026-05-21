# Agent Guidelines

Quick reference for AI coding agents (Claude Code, Copilot, etc.) working on this repo.

## What this repo is

Personal website of Akaash Dash at https://akaashdash.github.io. Built on the al-folio Jekyll theme, stripped down to a minimal personal site with an about page and blog. Many al-folio features exist as latent capabilities but are not currently active.

## Key docs to read

| Task | Document |
|------|----------|
| Understand the site structure and what's active | [CUSTOMIZE.md](CUSTOMIZE.md) |
| Local dev and deploy mechanics | [INSTALL.md](INSTALL.md) |
| Common errors and gotchas | [FAQ.md](FAQ.md) |

## Essential commands

```bash
# Start local dev server
docker compose pull && docker compose up
# Site at http://localhost:8080

# Restart after _config.yml changes
docker compose down && docker compose up

# Rebuild after Gemfile changes
docker compose up --build
```

## Critical facts

- **Branch**: all changes on `main`. There is no `gh-pages` branch.
- **Deploy**: push to `main` → GitHub Actions builds → deploys via Pages artifact API. Takes ~3 min.
- **Config reload**: `_config.yml` only reloads on Jekyll restart (Docker down/up). All other files hot-reload.
- **`baseurl`**: must remain present as `baseurl:` (empty) — never delete this key.
- **URL**: `https://akaashdash.github.io` — no trailing slash, no `baseurl`.

## Active pages

```
/           →  _pages/about.md   (layout: about)
/blog/      →  _pages/blog.md    (layout: default, paginated)
/blog/YYYY/TITLE/  →  _posts/YYYY-MM-DD-title.md  (layout: post)
```

## File editing guide

| What you're changing | Where |
|----------------------|-------|
| Bio text | `_pages/about.md` (below the frontmatter) |
| Profile picture | Replace `assets/img/prof_pic.jpg` |
| Social links | `_data/socials.yml` (email, github_username, linkedin_username) |
| Nav order / pages | Frontmatter of files in `_pages/` |
| Site title, URL, description | `_config.yml` top section |
| Theme color | `_sass/_themes.scss` → `--global-theme-color` |
| Custom CSS | `_sass/_custom.scss` |
| Layout/UI settings | `_config.yml` Layout section |
| Feature flags | `_config.yml` Optional Features section |

## Adding a blog post

Create `_posts/YYYY-MM-DD-slug.md`:

```yaml
---
layout: post
title: Title Here
date: 2024-06-01
description: One-line summary for the listing page
tags: tag1 tag2
categories: cat
---

Post content here. Supports LaTeX ($$...$$), code fences, images, etc.
```

## YAML safety rules

- Quote strings that contain `:`, `&`, `#`, or `>`: `title: "My Title: Subtitle"`
- Never delete the `baseurl:` key (leave it empty)
- YAML is indentation-sensitive — use 2 spaces, no tabs

## What NOT to do

- Do not push to or create a `gh-pages` branch
- Do not run `jekyll clean` in a publishing directory
- Do not delete `baseurl:` from `_config.yml`
- Do not commit `_site/` (it's built by CI)

## Latent features (available but inactive)

Many al-folio features are present but disabled. Check the [Latent features section of CUSTOMIZE.md](CUSTOMIZE.md#latent-features) for the full list. Short version:

- Dark mode: set `enable_darkmode: true`
- Search: set `search_enabled: true`
- Comments: configure `giscus` block in `_config.yml`
- Analytics: set `enable_google_analytics: true` + ID
- Publications: gem installed, needs `_bibliography/papers.bib` + layout restored from upstream
- Collections (projects, books, news, teachings): config entries exist, just need content directories

## Rich post content

Blog posts support many media/visualization types beyond basic Markdown. All gems/libraries are already installed. See [Post content features in CUSTOMIZE.md](CUSTOMIZE.md#post-content-features) for full syntax. Quick list:

- Image grids, carousels (Swiper), before/after sliders, photo galleries (Lightbox2, PhotoSwipe, Spotlight, VenoBox)
- Video embeds (local, YouTube, Vimeo) and audio embeds
- Charts: Chart.js, ECharts, Vega-Lite, Plotly
- GeoJSON maps (Leaflet) — `map: true` in frontmatter
- Code diff viewer (diff2html) — `code_diff: true`
- Mermaid diagrams, TikZ figures, typograms (ASCII art diagrams)
- Pseudocode rendering — `pseudocode: true`
- Custom styled blockquotes (tip, warning, danger)
- Bootstrap tables loaded from JSON
- In-post citations (requires jekyll-scholar active)
- Table of contents inline (`toc: true`) or sidebar (`toc_sidebar: true`)

## Upstream reference

This repo is based on https://github.com/alshedivat/al-folio. When restoring a removed feature, find the original file there. The upstream `main` branch is authoritative for layouts, includes, and plugins that were deleted here.
