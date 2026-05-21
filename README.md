# akaashdash.github.io

Personal website of Akaash Dash — quantitative researcher and software engineer, master's student at Georgia Tech (QCF).

Live at: **https://akaashdash.github.io**

Built on [al-folio](https://github.com/alshedivat/al-folio) (Jekyll theme) with heavy customization. Many al-folio features have been stripped (publications, projects, CV, teaching, news, dark mode, search). What remains is a minimal personal site with an about page and blog.

## Pages

| Page | File | URL |
|------|------|-----|
| About (home) | `_pages/about.md` | `/` |
| Blog | `_pages/blog.md` | `/blog/` |
| 404 | `_pages/404.md` | — |

## Running locally

```bash
docker compose pull
docker compose up
```

Visit `http://localhost:8080`. File changes hot-reload. `_config.yml` changes require a restart (`docker compose down && docker compose up`).

## Deployment

Push to `main`. GitHub Actions (`.github/workflows/deploy.yml`) builds with Jekyll and deploys directly to GitHub Pages using the Pages artifact API (no `gh-pages` branch). Takes ~3 minutes.

## Documentation

- [INSTALL.md](INSTALL.md) — Local setup options and deployment details
- [CUSTOMIZE.md](CUSTOMIZE.md) — Content, config, and styling reference
- [FAQ.md](FAQ.md) — Common issues and troubleshooting

## License

MIT — based on [al-folio](https://github.com/alshedivat/al-folio).
