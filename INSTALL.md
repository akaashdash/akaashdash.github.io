# Installing and Deploying

## Local Development

### Docker (recommended)

```bash
docker compose pull
docker compose up
```

Site runs at `http://localhost:8080`. Changes to Markdown, Liquid, and SCSS files hot-reload. Changes to `_config.yml` require a restart:

```bash
docker compose down && docker compose up
```

To rebuild the image (after Gemfile changes):

```bash
docker compose up --build
```

### Without Docker

Requires Ruby 3.3.x and Bundler. Also requires `imagemagick` and `jupyter` on PATH (used by Jekyll plugins).

```bash
bundle install
bundle exec jekyll serve
```

Site runs at `http://localhost:4000`.

On macOS:

```bash
brew install imagemagick jupyter
bundle install
bundle exec jekyll serve
```

### Dev Containers

The repo includes a `.devcontainer/` config. Opening in VS Code with the Dev Containers extension will set up the environment automatically.

## Deployment

Deployment is fully automated. Pushing to `main` triggers `.github/workflows/deploy.yml`, which:

1. Checks out the repo
2. Sets up Ruby 3.3.5 with bundler cache
3. Installs `imagemagick` and `jupyter` via apt
4. Runs `bundle exec jekyll build` with `JEKYLL_ENV=production`
5. Uploads the `_site/` artifact
6. Deploys to GitHub Pages via the Pages artifact API

**No `gh-pages` branch is used.** The Pages source in repository Settings should be set to "GitHub Actions" (not a branch). This is different from the upstream al-folio default.

To manually trigger a deploy: Actions tab → "Deploy site" → "Run workflow".

## Dependencies

Ruby gems are managed by Bundler (`Gemfile` / `Gemfile.lock`). To update all gems:

```bash
bundle update --all
docker compose up --build  # rebuild image to apply
```

Node packages (`package.json`) are used only for Prettier (code formatting). Not needed for building or running the site.
