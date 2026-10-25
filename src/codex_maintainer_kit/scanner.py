from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class GitState:
    status: str
    changed_files: list[str]


@dataclass(frozen=True)
class RepositoryScan:
    root: Path
    files: dict[str, bool]
    project_hints: list[str]
    git_state: GitState


def scan_repository(path: str | Path, git_status_output: str | None = None) -> RepositoryScan:
    root = Path(path).resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Repository path does not exist or is not a directory: {root}")

    files = {
        "readme": _any_exists(root, ["README.md", "README.rst", "README.txt", "readme.md"]),
        "license": _any_exists(root, ["LICENSE", "LICENSE.md", "COPYING"]),
        "contributing": _any_exists(root, ["CONTRIBUTING.md", "CONTRIBUTING"]),
        "code_of_conduct": _any_exists(root, ["CODE_OF_CONDUCT.md", "CODE-OF-CONDUCT.md"]),
        "security": _any_exists(root, ["SECURITY.md"]),
        "changelog": _any_exists(root, ["CHANGELOG.md", "CHANGES.md", "RELEASES.md"]),
        "agents": _any_exists(root, ["AGENTS.md"]),
        "issue_templates": (root / ".github" / "ISSUE_TEMPLATE").exists(),
        "ci": _has_ci(root),
        "tests": _has_tests(root),
    }

    return RepositoryScan(
        root=root,
        files=files,
        project_hints=_project_hints(root),
        git_state=_git_state(root, git_status_output),
    )


def _any_exists(root: Path, names: list[str]) -> bool:
    return any((root / name).exists() for name in names)


def _has_ci(root: Path) -> bool:
    return (
        (root / ".github" / "workflows").exists()
        or (root / ".gitlab-ci.yml").exists()
        or (root / "azure-pipelines.yml").exists()
        or (root / ".circleci" / "config.yml").exists()
    )


def _has_tests(root: Path) -> bool:
    if any((root / name).exists() for name in ["tests", "test", "__tests__", "spec"]):
        return True
    test_patterns = ["test_*.py", "*_test.py", "*.test.ts", "*.test.js", "*.spec.ts", "*.spec.js"]
    return any(next(root.rglob(pattern), None) is not None for pattern in test_patterns)


def _project_hints(root: Path) -> list[str]:
    hints: list[str] = []
    markers = [
        ("python", ["pyproject.toml", "setup.py", "requirements.txt"]),
        ("javascript", ["package.json", "pnpm-lock.yaml", "yarn.lock"]),
        ("go", ["go.mod"]),
        ("rust", ["Cargo.toml"]),
        ("ruby", ["Gemfile"]),
        ("php", ["composer.json"]),
        ("java", ["pom.xml", "build.gradle", "build.gradle.kts"]),
        ("swift", ["Package.swift"]),
    ]
    for hint, names in markers:
        if _any_exists(root, names):
            hints.append(hint)
    if _has_any_pattern(root, ["*.csproj", "*.sln"]):
        hints.append("dotnet")
    return hints or ["unknown"]


def _has_any_pattern(root: Path, patterns: list[str]) -> bool:
    return any(next(root.rglob(pattern), None) is not None for pattern in patterns)


def _git_state(root: Path, git_status_output: str | None) -> GitState:
    if git_status_output is None:
        if not (root / ".git").exists():
            return GitState(status="not_a_git_repository", changed_files=[])
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain=v1", "-z"],
                cwd=root,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            return GitState(status="git_unavailable", changed_files=[])
        if result.returncode != 0:
            return GitState(status="git_unavailable", changed_files=[])
        git_status_output = result.stdout.decode("utf-8", errors="surrogateescape")

    changed_files = _parse_porcelain_paths(git_status_output)
    return GitState(status="dirty" if changed_files else "clean", changed_files=changed_files)


def _parse_porcelain_paths(output: str) -> list[str]:
    paths: list[str] = []
    if "\0" in output:
        entries = iter(output.split("\0"))
        for entry in entries:
            if not entry:
                continue
            paths.append(entry[3:])
            # In -z format a rename/copy lists the destination, then the source.
            if "R" in entry[:2] or "C" in entry[:2]:
                next(entries, None)
        return paths

    # Retain support for callers supplying line-delimited status output.
    for line in output.splitlines():
        if not line.strip():
            continue
        raw_path = line[3:] if len(line) > 3 else line.strip()
        if " -> " in raw_path:
            raw_path = raw_path.split(" -> ", 1)[1]
        paths.append(raw_path.strip())
    return paths
