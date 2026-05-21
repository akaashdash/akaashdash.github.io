# FAQ and Troubleshooting

## Deployment

### Site fails to deploy

Check the Actions tab on GitHub for the error. Common causes:

- **YAML syntax error in `_config.yml`**: Run `bundle exec jekyll build` locally to see the exact line. YAML is sensitive to indentation and special characters (`:`, `&`, `#` in unquoted strings).
- **`imagemagick` or `jupyter` not available**: The deploy workflow installs these via apt. If the install step fails, check `.github/workflows/deploy.yml`.
- **Workflow permissions**: Go to Settings → Actions → General → Workflow permissions and ensure "Read and write permissions" is selected.

### Site deploys but looks broken (CSS not loading)

Almost always a `url`/`baseurl` mismatch. In `_config.yml`:

```yaml
url: https://akaashdash.github.io
baseurl:   # must be empty — do NOT delete this key
```

Hard-refresh after fixing: `Cmd+Shift+R` (Chrome/Mac) or open a private window.

### Pages source must be "GitHub Actions"

This repo uses the Pages artifact API, not a `gh-pages` branch. In repository Settings → Pages → Build and deployment, the Source must be **GitHub Actions** (not "Deploy from a branch"). If it's set to a branch, deploys will do nothing visible.

## Local development

### Docker won't start / port conflict

```bash
docker compose down
docker compose up
```

If port 8080 is in use:

```bash
lsof -i :8080 | grep LISTEN | awk '{print $2}' | xargs kill
docker compose up
```

### `_config.yml` changes don't appear

`_config.yml` is only read at startup. Restart Jekyll:

```bash
docker compose down && docker compose up
```

### Ruby gem errors without Docker

```bash
rm Gemfile.lock
bundle install
bundle exec jekyll serve
```

## Content

### Blog post not showing up

Check:
- Filename format: `YYYY-MM-DD-title.md` (must match exactly)
- File is in `_posts/`, not a subdirectory
- Date is not in the future (Jekyll won't publish future-dated posts by default)
- Frontmatter is valid YAML with `layout: post`

### Image not loading

- Path should be relative from the repo root: `assets/img/filename.jpg`
- Linux/macOS are case-sensitive — filename casing must match exactly
- WebP versions are auto-generated during build from files in `assets/img/`. The originals must be `.jpg`, `.jpeg`, `.png`, `.tiff`, or `.gif`.

### Math not rendering

`enable_math: true` is set globally, so MathJax is loaded on all pages. If a post's math isn't rendering:

- Inline: use `$...$` or `\\(...\\)`
- Display: use `$$...$$` or `\\[...\\]`
- Avoid `\` at the end of a Markdown line (Markdown may strip it before MathJax sees it)

## Styling

### Style change not visible after edit

1. Hard refresh: `Cmd+Shift+R`
2. If still not visible after a Docker restart, check that the SCSS compiles without errors. Jekyll logs compilation errors in the terminal output.

### Changing theme color

Edit `_sass/_themes.scss` and update `--global-theme-color`. Predefined color names are in `_sass/_variables.scss`.

## GitHub Actions

### What workflows exist

Only one workflow: `.github/workflows/deploy.yml`

It triggers on push to `main` and on manual dispatch. It builds the site and deploys to GitHub Pages.

The upstream al-folio repo has many additional workflows (lint, accessibility, lighthouse, citation updates) that have been removed here.

### Prettier formatter failing

If prettier is enabled (it runs via `npm` and `.prettierrc`), it formats Markdown, YAML, and Liquid files. Run it locally before pushing:

```bash
npx prettier . --write
```

Or disable the prettier workflow by deleting `.github/workflows/prettier.yml` if it exists (it was removed from this repo already).

## Common `_config.yml` mistakes

```yaml
# Wrong — unquoted colon
title: My Site: A Blog

# Right
title: "My Site: A Blog"
```

```yaml
# Wrong — deleted baseurl key
url: https://akaashdash.github.io

# Right — key must be present even if empty
url: https://akaashdash.github.io
baseurl:
```
