<img src="assets/icon.svg" width="64" height="64" alt="">

# python-template

A [Copier](https://copier.readthedocs.io/) template for our Python projects.
One template, three variants, the same architecture and tooling in each.

| Variant | What you get on top of the shared base |
| --- | --- |
| `django` | Django 6 + Postgres, split settings, custom user, htmx (vendored) with template partials, TypeScript + Tailwind built by Vite, background tasks, production hardening, Dockerfile, compose |
| `cli` | Typer command line, typed configuration, Dockerfile |
| `library` | Typed package published to the GitLab package registry |

## Use it

```sh
uvx copier copy <this-repo-url> my-project
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
  `interfaces > services > integrations > domain`. New top-level packages must
  be assigned a layer. See the generated `AGENTS.md`.
- **Tests** in top-level `tests/` split into `unit`, `integration` and
  `functional`. Unit and integration tests must mirror the source tree
  (`scripts/check_test_mirror.py`). 80% branch coverage floor, warnings are errors.
- **ruff** (lint + format, the aarbox rule set tidied up, line length 99),
  **ty** for type checking, **pyproject-fmt**, **pip-audit**.
- **pre-commit**: fast checks on commit; type check, architecture and unit
  tests on push. Hooks run tools from the project environment, so versions are
  pinned by the lock files and match CI.
- **pydantic-settings** for typed, validated configuration (not in libraries).
- **GitLab CI**: lint, type check, architecture, tests with coverage reports,
  dependency audit, Docker image build and push, and tag-driven releases with
  generated notes. Versions come from git tags (hatch-vcs).
- **Renovate** config, dev container, `.editorconfig`, VS Code settings,
  `AGENTS.md` / `CLAUDE.md` for coding agents.

## Django specifics

- `domain` is the Django app that owns models and migrations; `interfaces` is
  the app that owns views, templates, static files and admin.
- Vite + django-vite build `frontend/src` (TypeScript, Tailwind v4). pnpm and
  Biome for JavaScript tooling. htmx is vendored under
  `interfaces/static/vendor/` and updated with `just vendor-htmx <version>`.
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
- The self-tests use SQLite for Django unless `DATABASE_URL` is set; CI sets it
  to a Postgres service.
- Tag releases of the template (`v1.0.0`, ...): `copier update` moves projects
  between tags.
