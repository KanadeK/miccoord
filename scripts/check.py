"""Run the complete MicCoord release-equivalent gate."""

from __future__ import annotations

import hashlib
import os
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

from packaging.metadata import Metadata

from miccoord import __version__

ROOT = Path(__file__).resolve().parents[1]
REPORT_FIXTURES = {
    "plan-report.json",
    "plan-report.txt",
    "audit-conflict-report.json",
    "audit-conflict-report.txt",
    "infeasible-report.json",
    "infeasible-report.txt",
    "exhausted-report.json",
    "exhausted-report.txt",
}


def _uv() -> str:
    executable = shutil.which("uv")
    if executable is None:
        raise RuntimeError("uv is required; install it from https://docs.astral.sh/uv/")
    return executable


def _run(
    stage: str,
    command: list[str],
    *,
    cwd: Path = ROOT,
    expected: int = 0,
) -> None:
    print(f"\n[{stage}]", flush=True)
    print(f"$ {shlex.join(command)}", flush=True)
    environment = os.environ.copy()
    environment.setdefault("UV_CACHE_DIR", str(ROOT.parent / ".uv-cache-miccoord"))
    result = subprocess.run(command, cwd=cwd, env=environment, check=False)
    if result.returncode != expected:
        raise RuntimeError(
            f"{stage} exited {result.returncode}; expected {expected}: {shlex.join(command)}"
        )


def _reproduce_examples(temporary: Path) -> None:
    generated = temporary / "generated-examples"
    _run(
        "Regenerate examples",
        [sys.executable, "scripts/generate_examples.py", "--output", str(generated)],
    )
    generated_names = {path.name for path in generated.iterdir() if path.is_file()}
    if generated_names != REPORT_FIXTURES:
        raise RuntimeError(
            f"generated report set differs: expected {REPORT_FIXTURES}, got {generated_names}"
        )
    for name in sorted(REPORT_FIXTURES):
        if (ROOT / "examples" / name).read_bytes() != (generated / name).read_bytes():
            raise RuntimeError(f"generated example differs from committed fixture: {name}")


def _source_cli_smoke(temporary: Path) -> None:
    command = [sys.executable, "-m", "miccoord"]
    _run(
        "Source plan example",
        [
            *command,
            "plan",
            "examples/plan.json",
            "--scan",
            "examples/scan.csv",
            "--format",
            "json",
            "--output",
            str(temporary / "source-plan.json"),
        ],
    )
    _run(
        "Source conflict audit",
        [*command, "audit", "examples/audit-conflict.json"],
        expected=1,
    )
    _run(
        "Source infeasible plan",
        [*command, "plan", "examples/infeasible.json"],
        expected=1,
    )
    _run(
        "Source exhausted plan",
        [*command, "plan", "examples/exhausted.json"],
        expected=2,
    )
    invalid_output = temporary / "invalid-output.json"
    _run(
        "Source invalid input",
        [*command, "audit", "examples/invalid.json", "--output", str(invalid_output)],
        expected=2,
    )
    if invalid_output.exists():
        raise RuntimeError("invalid source run left an output file")


def _write_examples_archive(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for source in sorted(item for item in (ROOT / "examples").iterdir() if item.is_file()):
            info = zipfile.ZipInfo(f"miccoord-examples/{source.name}", (2026, 8, 30, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes(), compresslevel=9)


def _verify_packages(wheel: Path, source_distribution: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        wheel_names = set(archive.namelist())
        wheel_metadata = archive.read(f"miccoord-{__version__}.dist-info/METADATA")
    required_wheel = {
        "miccoord/__init__.py",
        "miccoord/cli.py",
        "miccoord/intermod.py",
        "miccoord/io.py",
        "miccoord/model.py",
        "miccoord/planner.py",
        "miccoord/py.typed",
        "miccoord/reporting.py",
        f"miccoord-{__version__}.dist-info/METADATA",
        f"miccoord-{__version__}.dist-info/entry_points.txt",
    }
    if missing := required_wheel - wheel_names:
        raise RuntimeError(f"wheel is missing required files: {sorted(missing)}")
    if any(name.startswith(("tests/", "docs/", "examples/")) for name in wheel_names):
        raise RuntimeError("wheel contains repository-only files")

    prefix = f"miccoord-{__version__}/"
    with tarfile.open(source_distribution, "r:gz") as archive:
        source_names = set(archive.getnames())
        source_metadata_member = archive.getmember(f"{prefix}PKG-INFO")
        source_metadata_file = archive.extractfile(source_metadata_member)
        if source_metadata_file is None:
            raise RuntimeError("source distribution PKG-INFO is unreadable")
        source_metadata = source_metadata_file.read()
    required_source = {
        f"{prefix}LICENSE",
        f"{prefix}README.md",
        f"{prefix}pyproject.toml",
        f"{prefix}src/miccoord/cli.py",
    }
    if missing := required_source - source_names:
        raise RuntimeError(f"source distribution is missing required files: {sorted(missing)}")

    unsafe_markers = ("/.env", ".pem", ".key", "/.git/", "/.venv/", "__pycache__")
    if unsafe := sorted(
        name
        for name in wheel_names | source_names
        if any(marker in name for marker in unsafe_markers)
    ):
        raise RuntimeError(f"package contains unsafe path(s): {unsafe}")

    for label, raw_metadata in (
        ("wheel", wheel_metadata),
        ("source distribution", source_metadata),
    ):
        metadata = Metadata.from_email(raw_metadata, validate=True)
        if str(metadata.name) != "miccoord" or str(metadata.version) != __version__:
            raise RuntimeError(
                f"{label} metadata identity differs: {metadata.name} {metadata.version}"
            )


def _build_assets(uv: str, temporary: Path) -> tuple[Path, ...]:
    built = temporary / "built"
    _run(
        "Build wheel and source distribution",
        [uv, "build", "--offline", "--out-dir", str(built)],
    )
    wheel = built / f"miccoord-{__version__}-py3-none-any.whl"
    source_distribution = built / f"miccoord-{__version__}.tar.gz"
    if not wheel.is_file() or not source_distribution.is_file():
        raise RuntimeError("uv build did not produce the expected wheel and source distribution")
    _verify_packages(wheel, source_distribution)
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    release_wheel = output / wheel.name
    release_source = output / source_distribution.name
    shutil.copyfile(wheel, release_wheel)
    shutil.copyfile(source_distribution, release_source)
    examples = output / f"miccoord-{__version__}-examples.zip"
    _write_examples_archive(examples)

    assets = (release_wheel, release_source, examples)
    checksums = output / "SHA256SUMS"
    checksums.write_text(
        "".join(
            f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in assets
        ),
        encoding="ascii",
        newline="\n",
    )
    return (*assets, checksums)


def _venv_path(venv: Path, windows_name: str, unix_name: str) -> Path:
    return venv / (f"Scripts/{windows_name}" if os.name == "nt" else f"bin/{unix_name}")


def _smoke_test_wheel(uv: str, temporary: Path, wheel: Path) -> None:
    venv = temporary / "wheel-venv"
    _run("Create clean wheel environment", [uv, "venv", str(venv), "--python", sys.executable])
    python = _venv_path(venv, "python.exe", "python")
    executable = _venv_path(venv, "miccoord.exe", "miccoord")
    _run(
        "Install built wheel",
        [uv, "pip", "install", "--offline", "--python", str(python), str(wheel)],
    )
    _run("Check installed dependencies", [uv, "pip", "check", "--python", str(python)])

    smoke = temporary / "installed-smoke"
    smoke.mkdir()
    _run("Installed version", [str(executable), "--version"], cwd=smoke)
    _run(
        "Installed plan example",
        [
            str(executable),
            "plan",
            str(ROOT / "examples" / "plan.json"),
            "--scan",
            str(ROOT / "examples" / "scan.csv"),
        ],
        cwd=smoke,
    )
    _run(
        "Installed conflict audit",
        [str(executable), "audit", str(ROOT / "examples" / "audit-conflict.json")],
        cwd=smoke,
        expected=1,
    )
    _run(
        "Installed infeasible plan",
        [str(executable), "plan", str(ROOT / "examples" / "infeasible.json")],
        cwd=smoke,
        expected=1,
    )
    _run(
        "Installed invalid input",
        [str(executable), "audit", str(ROOT / "examples" / "invalid.json")],
        cwd=smoke,
        expected=2,
    )


def _verify_tag() -> None:
    if os.environ.get("GITHUB_REF_TYPE") != "tag":
        return
    expected = f"v{__version__}"
    actual = os.environ.get("GITHUB_REF_NAME")
    if actual != expected:
        raise RuntimeError(f"release tag {actual!r} does not match package version {expected!r}")


def main() -> int:
    uv = _uv()
    _verify_tag()
    _run("Lockfile", [uv, "lock", "--check"])
    python_paths = ["src", "tests", "scripts"]
    _run("Formatting", [sys.executable, "-m", "ruff", "format", "--check", *python_paths])
    _run("Lint", [sys.executable, "-m", "ruff", "check", *python_paths])
    _run("Types", [sys.executable, "-m", "mypy", *python_paths])
    with tempfile.TemporaryDirectory(prefix=".miccoord-check-", dir=ROOT) as name:
        temporary = Path(name)
        _run(
            "Tests and branch coverage",
            [
                sys.executable,
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "--basetemp",
                str(temporary / "pytest"),
                "--cov=miccoord",
                "--cov-branch",
                "--cov-report=term-missing",
                "--cov-fail-under=90",
            ],
        )
        _run(
            "Dependency audit",
            [
                sys.executable,
                "-m",
                "pip_audit",
                "--local",
                "--cache-dir",
                str(ROOT / ".pip-audit-cache"),
                "--progress-spinner",
                "off",
            ],
        )
        _reproduce_examples(temporary)
        _source_cli_smoke(temporary)
        assets = _build_assets(uv, temporary)
        _smoke_test_wheel(uv, temporary, assets[0])

    print("\nMICCOORD_RELEASE_GATE=PASS")
    for asset in assets:
        print(asset)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
