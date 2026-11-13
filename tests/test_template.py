"""Generate every variant of the template and run its own checks against it.

These tests are slow by nature: each variant gets a real environment
(``uv sync``, and for Django ``pnpm install``) and then runs ``just check``,
which is exactly what CI runs in a generated project.
"""

import os
import shutil
import subprocess
from pathlib import Path

import copier
import pytest

TEMPLATE = Path(__file__).resolve().parent.parent
VARIANTS = ("library", "cli", "django")
SHARED_LAYERS = ("usecases", "domain", "vendors", "data", "utils")
# (importing layer, imported layer) pairs that the architecture forbids.
FORBIDDEN_IMPORTS = (
    ("domain", "usecases"),
    ("domain", "vendors"),
    ("data", "domain"),
    ("vendors", "data"),
    ("vendors", "domain"),
    ("utils", "data"),
    ("interface", "vendors"),
)


def run(project: Path, *command: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a command inside a generated project, isolated from this repo's environment."""
    env = {k: v for k, v in os.environ.items() if k not in {"VIRTUAL_ENV", "UV_PROJECT"}}
    # Postgres in CI (DATABASE_URL set there); SQLite when run on a laptop.
    env.setdefault("DATABASE_URL", f"sqlite:///{project / 'db.sqlite3'}")
    result = subprocess.run(  # noqa: S603
        command, cwd=project, env=env, capture_output=True, text=True, check=False
    )
    if check and result.returncode != 0:
        pytest.fail(f"{' '.join(command)} failed:\n{result.stdout}\n{result.stderr}")
    return result


@pytest.fixture(scope="session", params=VARIANTS)
def project(request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate one variant and install its dependencies."""
    variant: str = request.param
    if variant == "django" and shutil.which("pnpm") is None:
        pytest.skip("pnpm is required for the Django variant (run `corepack enable`)")
    destination = tmp_path_factory.mktemp(variant) / "project"
    copier.run_copy(
        str(TEMPLATE),
        destination,
        data={
            "project_name": f"Demo {variant}",
            "author_email": "dev@example.org",
            "project_type": variant,
        },
        defaults=True,
        vcs_ref="HEAD",
        quiet=True,
    )
    run(destination, "git", "init", "--quiet")
    run(destination, "uv", "sync", "--quiet")
    if variant == "django":
        run(destination, "pnpm", "install", "--silent")
    return destination


def package_dir(project: Path) -> Path:
    """Return the generated package directory."""
    return project / "src" / f"demo_{project.parent.name.rstrip('0123456789')}"


def test_generated_project_passes_its_own_checks(project: Path) -> None:
    """A fresh project is green: lint, types, architecture, tests, and the frontend."""
    run(project, "uv", "run", "just", "check")


def test_generated_pyproject_is_already_formatted(project: Path) -> None:
    """pyproject-fmt has nothing to change, for any combination of template options."""
    run(project, "uv", "run", "pyproject-fmt", "--check", "pyproject.toml")


def test_git_hooks_pass_on_a_fresh_project(project: Path) -> None:
    """The commit-stage hooks accept the generated files untouched."""
    run(project, "git", "add", "--all")
    run(project, "uv", "run", "pre-commit", "run", "--all-files")


def test_has_the_expected_layers(project: Path) -> None:
    """Each variant gets its layers, and libraries get no interface layer."""
    variant = project.parent.name.rstrip("0123456789")
    package = package_dir(project)

    for layer in SHARED_LAYERS:
        assert (package / layer / "__init__.py").is_file()
    assert (package / "interface").exists() == (variant != "library")
    assert (package / "interface" / "ui").exists() == (variant == "django")
    assert (package / "interface" / "api").exists() == (variant == "django")
    assert (project / "package.json").exists() == (variant == "django")
    assert (project / "Dockerfile").exists() == (variant != "library")


@pytest.mark.parametrize(("importer", "imported"), FORBIDDEN_IMPORTS)
def test_forbidden_import_breaks_a_contract(project: Path, importer: str, imported: str) -> None:
    """Import Linter rejects each import direction the architecture rules out."""
    package = package_dir(project)
    if not (package / importer).exists():
        pytest.skip(f"this variant has no {importer} layer")
    offender = package / importer / "offender.py"
    offender.write_text(
        f'"""Violates layering."""\n\nfrom {package.name} import {imported}  # noqa: F401\n'
    )
    try:
        result = run(project, "uv", "run", "lint-imports", check=False)
    finally:
        offender.unlink()

    assert result.returncode != 0
    assert "BROKEN" in result.stdout


def test_usecases_may_call_vendors(project: Path) -> None:
    """The one sanctioned route to an external system stays open."""
    package = package_dir(project)
    caller = package / "usecases" / "caller.py"
    caller.write_text(f'"""Allowed."""\n\nfrom {package.name} import vendors  # noqa: F401\n')
    try:
        run(project, "uv", "run", "lint-imports")
    finally:
        caller.unlink()


def test_unassigned_top_level_package_breaks_the_layers_contract(project: Path) -> None:
    """A new top-level package must be given a layer before the build passes."""
    stray = package_dir(project) / "helpers"
    stray.mkdir()
    (stray / "__init__.py").write_text('"""Not assigned to a layer."""\n')
    try:
        result = run(project, "uv", "run", "lint-imports", check=False)
    finally:
        shutil.rmtree(stray)

    assert result.returncode != 0


def test_orphan_test_file_breaks_the_mirror_check(project: Path) -> None:
    """A unit test with no matching source module is reported."""
    orphan = project / "tests" / "unit" / "domain" / "test_nothing.py"
    orphan.write_text("")
    try:
        result = run(project, "uv", "run", "python", "scripts/check_test_mirror.py", check=False)
    finally:
        orphan.unlink()

    assert result.returncode == 1
    assert "tests/unit/domain/test_nothing.py" in result.stderr
