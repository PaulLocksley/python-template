# List the available recipes
default:
    @just --list

# Lint the template's own tests
lint:
    uv run ruff check
    uv run ruff format --check

# Generate every variant and run its full check suite (slow; needs pnpm for Django)
test *args:
    uv run pytest {{ args }}

# Generate a project into a directory to look around, e.g. `just try /tmp/demo`
try destination *args:
    uv run copier copy --vcs-ref HEAD {{ args }} . {{ destination }}
