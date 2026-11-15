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
import yaml

TEMPLATE = Path(__file__).resolve().parent.parent
# Variant name -> Copier answers that differ from the defaults.
VARIANTS = {
    "library": {"project_type": "library"},
    "cli": {"project_type": "cli"},
    "django": {"project_type": "django", "css_framework": "tailwind"},
    "django-bootstrap": {"project_type": "django", "css_framework": "bootstrap"},
}
CI_FILES = {"gitlab": ".gitlab-ci.yml", "github": ".github/workflows/ci.yml"}
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
    django = VARIANTS[variant]["project_type"] == "django"
    if django and shutil.which("pnpm") is None:
        pytest.skip("pnpm is required for the Django variant (run `corepack enable`)")
    destination = tmp_path_factory.mktemp(variant) / "project"
    copier.run_copy(
        str(TEMPLATE),
        destination,
        data={
            "project_name": f"Demo {variant}",
            "author_email": "dev@example.org",
            **VARIANTS[variant],
        },
        defaults=True,
        vcs_ref="HEAD",
        quiet=True,
    )
    run(destination, "git", "init", "--quiet")
    run(destination, "uv", "sync", "--quiet")
    if django:
        run(destination, "pnpm", "install", "--silent")
    return destination


def variant_of(project: Path) -> str:
    """Return the variant a generated project was made from."""
    return project.parent.name.rstrip("0123456789")


def package_dir(project: Path) -> Path:
    """Return the generated package directory."""
    return project / "src" / f"demo_{variant_of(project).replace('-', '_')}"


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
    variant = variant_of(project)
    django = VARIANTS[variant]["project_type"] == "django"
    package = package_dir(project)

    for layer in SHARED_LAYERS:
        assert (package / layer / "__init__.py").is_file()
    assert (package / "interface").exists() == (variant != "library")
    assert (package / "interface" / "ui").exists() == django
    assert (package / "interface" / "api").exists() == django
    assert (package / "templates" / "base.html").exists() == django
    assert (project / "package.json").exists() == django
    assert (project / "Dockerfile").exists() == (variant != "library")


def test_css_framework_is_wired_through(project: Path) -> None:
    """Only the chosen CSS framework appears in the dependencies and templates."""
    framework = VARIANTS[variant_of(project)].get("css_framework")
    if framework is None:
        pytest.skip("only Django projects have a frontend")
    other = {"tailwind": "bootstrap", "bootstrap": "tailwind"}[framework]
    package_json = (project / "package.json").read_text()
    base_html = (package_dir(project) / "templates" / "base.html").read_text()

    assert framework in package_json
    assert other not in package_json
    assert ("container" in base_html) == (framework == "bootstrap")
    assert ("max-w-2xl" in base_html) == (framework == "tailwind")


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


@pytest.mark.parametrize("variant", ["library", "cli", "django"])
@pytest.mark.parametrize("provider", CI_FILES)
def test_ci_provider_selects_one_pipeline(tmp_path: Path, variant: str, provider: str) -> None:
    """Exactly the chosen provider's pipeline is generated, and it is valid YAML."""
    copier.run_copy(
        str(TEMPLATE),
        tmp_path,
        data={
            "project_name": f"Demo {variant}",
            "author_email": "dev@example.org",
            "project_type": variant,
            "ci_provider": provider,
        },
        defaults=True,
        vcs_ref="HEAD",
        quiet=True,
    )
    for name, path in CI_FILES.items():
        assert (tmp_path / path).is_file() == (name == provider)
    assert (tmp_path / ".github").exists() == (provider == "github")

    pipeline = yaml.safe_load((tmp_path / CI_FILES[provider]).read_text())
    jobs = pipeline["jobs"] if provider == "github" else pipeline
    assert "release" in jobs
    assert ("image" in jobs) == (variant != "library")
    assert ("publish" in jobs) == (variant == "library")
    assert ("django-check" in jobs) == (variant == "django")
