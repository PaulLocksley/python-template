<img src="assets/icon.svg" width="64" height="64" alt="">

# python-template

A [Copier](https://copier.readthedocs.io/) template for our Python projects.
One template, three variants, the same architecture and tooling in each.

| Variant | What you get on top of the shared base |
| --- | --- |
| `django` | Django 6 + Postgres, split settings, custom user, htmx (vendored) with template partials, TypeScript + Tailwind or Bootstrap (the `css_framework` question) built by Vite, background tasks, production hardening, Dockerfile, compose |
| `cli` | Typer command line, typed configuration, Dockerfile |
| `library` | Typed package, published to the GitLab package registry (GitLab) or attached to GitHub releases with optional PyPI trusted publishing (GitHub) |

## Use it

```sh
uvx copier copy <this-repo-url> my-project   # asks for the variant and GitLab or GitHub
cd my-project && git init
uv run just setup
uv run just check
```

Pull later template improvements into an existing project:

```sh
uvx copier update
```

## What every project gets

- **uv** for dependencies (`uv.lock` committed) and **just** for tasks. `just`
  is a dev dependency, so `uv run just ...` works with nothing else installed.
- **Layered architecture enforced by Import Linter**:
  `interface > usecases > domain | vendors > data > utils`, the
  layering. Only `usecases` may call `vendors`, each layer is organised by
  feature, and new top-level packages must be assigned a layer. See the
  generated `AGENTS.md`.
- **Tests** in top-level `tests/` split into `unit`, `integration` and
  `functional`. Unit and integration tests must mirror the source tree
  (`scripts/check_test_mirror.py`). 80% branch coverage floor, warnings are errors.
- **ruff** (lint + format, the rule set tidied up, line length 99),
  **ty** for type checking, **pyproject-fmt**, **pip-audit**.
- **pre-commit**: fast checks on commit; type check, architecture and unit
  tests on push. Hooks run tools from the project environment, so versions are
  pinned by the lock files and match CI.
- **pydantic-settings** for typed, validated configuration (not in libraries).
- **CI on GitLab or GitHub** (the `ci_provider` question): GitLab CI or
  GitHub Actions with the same jobs: lint, type check, architecture, tests with
  coverage reports, dependency audit, Docker image build and push (GitLab
  container registry or ghcr.io), and tag-driven releases with generated notes.
  Versions come from git tags (hatch-vcs).
- **Renovate** config, dev container, `.editorconfig`, VS Code settings,
  `AGENTS.md` / `CLAUDE.md` for coding agents.

## Django specifics

- The package is one Django app, as in: `migrations/`, `templates/`
  and `static/` sit at the package root. Models live in
  `data/<feature>/models.py` and are registered in `models.py`.
- `interface/` is split into `api/` and `ui/`.
- Vite + django-vite build `frontend/src` (TypeScript, plus Tailwind v4 or
  Bootstrap 5). The Django templates exist once per CSS framework, in
  `{% if is_tailwind %}templates{% endif %}/` and
  `{% if is_bootstrap %}templates{% endif %}/`: change both. pnpm and
  Biome for JavaScript tooling. htmx is vendored under
  `static/vendor/` and updated with `just vendor-htmx <version>`.
- `just up` starts Postgres in Docker; the app runs on the host with `just dev`.
- `just django-check` runs `check --deploy` against production settings and
  fails on missing migrations.

## Working on the template

```sh
uv sync
uv run just test          # generates all three variants and runs their checks
uv run just try /tmp/demo # generate a project to look around
```

The files under `template/` are the project skeleton. Only files ending in
`.jinja` are rendered; everything else (including Django HTML templates) is
copied as is. File and directory names wrapped in `{% if ... %}` exist only
for the matching variant.

Things worth knowing when changing it:

- `pyproject.toml.jinja` must render to something `pyproject-fmt` leaves
  untouched, for every variant. The self-tests check this.
- The self-tests use SQLite for Django unless `DATABASE_URL` is set; CI
  (`.github/workflows/ci.yml` or `.gitlab-ci.yml`) sets it to a Postgres service.
- Tag releases of the template (`v1.0.0`, ...): `copier update` moves projects
  between tags.
