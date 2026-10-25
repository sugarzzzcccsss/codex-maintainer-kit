from pathlib import Path
import shutil
import subprocess

import pytest

from codex_maintainer_kit.scanner import scan_repository


def test_scan_repository_detects_maintainer_files(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = \"demo\"\n", encoding="utf-8")
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "test.yml").write_text("name: test\n", encoding="utf-8")

    scan = scan_repository(tmp_path)

    assert scan.root == tmp_path
    assert scan.files["readme"] is True
    assert scan.files["license"] is True
    assert scan.files["ci"] is True
    assert scan.files["contributing"] is False
    assert "python" in scan.project_hints


def test_scan_repository_reports_missing_git_as_unknown_not_failure(tmp_path: Path) -> None:
    scan = scan_repository(tmp_path)

    assert scan.git_state.status == "not_a_git_repository"
    assert scan.git_state.changed_files == []


def test_scan_repository_detects_dirty_git_status(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")

    scan = scan_repository(tmp_path, git_status_output=" M README.md\n?? notes.md\n")

    assert scan.git_state.status == "dirty"
    assert scan.git_state.changed_files == ["README.md", "notes.md"]


def test_scan_repository_detects_additional_project_hints(tmp_path: Path) -> None:
    (tmp_path / "pom.xml").write_text("<project />\n", encoding="utf-8")
    (tmp_path / "Package.swift").write_text("// swift-tools-version: 6.0\n", encoding="utf-8")
    (tmp_path / "Demo.csproj").write_text("<Project />\n", encoding="utf-8")

    scan = scan_repository(tmp_path)

    assert "java" in scan.project_hints
    assert "swift" in scan.project_hints
    assert "dotnet" in scan.project_hints


@pytest.mark.parametrize("filename", ["notes with spaces.md", "中文.md"])
@pytest.mark.skipif(shutil.which("git") is None, reason="Git is required")
def test_scan_repository_preserves_real_git_filenames(tmp_path: Path, filename: str) -> None:
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    subprocess.run(["git", "config", "core.quotePath", "true"], cwd=tmp_path, check=True)
    assert scan_repository(tmp_path).git_state.status == "clean"
    (tmp_path / filename).write_text("# Notes\n", encoding="utf-8")

    scan = scan_repository(tmp_path)

    assert scan.git_state.status == "dirty"
    assert scan.git_state.changed_files == [filename]


@pytest.mark.parametrize("status", ["R ", " R", "C ", " C"])
def test_scan_repository_reads_nul_rename_and_copy_destinations(tmp_path: Path, status: str) -> None:
    scan = scan_repository(
        tmp_path,
        git_status_output=f"{status} new name.md\0old name.md\0 M next.py\0",
    )

    assert scan.git_state.changed_files == ["new name.md", "next.py"]


def test_scan_repository_preserves_nul_delimited_special_characters(tmp_path: Path) -> None:
    filenames = [" leading and trailing ", "a -> b.md", "line\nbreak.py", 'quote".txt', "tab\tname"]
    output = "".join(f"?? {filename}\0" for filename in filenames)

    scan = scan_repository(tmp_path, git_status_output=output)

    assert scan.git_state.changed_files == filenames


@pytest.mark.skipif(shutil.which("git") is None, reason="Git is required")
def test_scan_repository_reports_real_git_rename_destination(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    (tmp_path / "old name.md").write_text("# Notes\n", encoding="utf-8")
    subprocess.run(["git", "add", "old name.md"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
         "-c", "commit.gpgsign=false", "commit", "--quiet", "--no-verify", "-m", "Initial"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(["git", "mv", "old name.md", "new name.md"], cwd=tmp_path, check=True)

    scan = scan_repository(tmp_path)

    assert scan.git_state.changed_files == ["new name.md"]
