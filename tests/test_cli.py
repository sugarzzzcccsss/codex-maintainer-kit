from pathlib import Path
import json

from codex_maintainer_kit.cli import main


def test_brief_command_writes_markdown_file(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    output = tmp_path / "brief.md"

    exit_code = main(["brief", str(repo), "--output", str(output)])

    assert exit_code == 0
    text = output.read_text(encoding="utf-8")
    assert text.startswith("# Maintainer Brief")
    assert "Codex Task Queue" in text


def test_init_dry_run_lists_files_without_writing(tmp_path: Path, capsys) -> None:
    exit_code = main(["init", str(tmp_path), "--dry-run"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "AGENTS.md" in captured.out
    assert "CONTRIBUTING.md" in captured.out
    assert not (tmp_path / "AGENTS.md").exists()


def test_tasks_command_writes_markdown_file(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    output = tmp_path / "CODEX_TASKS.md"

    exit_code = main(["tasks", str(repo), "--output", str(output)])

    assert exit_code == 0
    text = output.read_text(encoding="utf-8")
    assert text.startswith("# Codex Maintenance Tasks")
    assert "## Task 1: Add LICENSE" in text


def test_audit_command_writes_markdown_file(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    output = tmp_path / "OSS_MAINTENANCE_AUDIT.md"

    exit_code = main(["audit", str(repo), "--output", str(output)])

    assert exit_code == 0
    text = output.read_text(encoding="utf-8")
    assert text.startswith("# OSS Maintenance Audit")
    assert "Health score:" in text
    assert "## Prioritized Next Actions" in text


def test_review_command_writes_markdown_file(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    output = tmp_path / "CODEX_REVIEW.md"

    exit_code = main(["review", str(repo), "--output", str(output)])

    assert exit_code == 0
    text = output.read_text(encoding="utf-8")
    assert text.startswith("# Codex Change Review")
    assert "Risk level:" in text
    assert "## Maintainer Review Checklist" in text


def test_tasks_command_writes_json_file(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    output = tmp_path / "tasks.json"

    exit_code = main(["tasks", str(repo), "--format", "json", "--output", str(output)])

    assert exit_code == 0
    text = output.read_text(encoding="utf-8")
    assert '"tasks"' in text
    assert '"id": "update-readme"' in text


def test_tasks_command_writes_github_issue_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    issues_dir = tmp_path / "issues"

    exit_code = main(["tasks", str(repo), "--github-issues-dir", str(issues_dir)])

    assert exit_code == 0
    files = sorted(path.name for path in issues_dir.iterdir())
    assert "01-add-license.md" in files
    assert "02-add-agents.md" in files
    assert (issues_dir / "01-add-license.md").read_text(encoding="utf-8").startswith("# Add LICENSE")


def test_tasks_command_uses_local_config_file(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8")
    (repo / "codex-maintainer-kit.toml").write_text(
        'verification_command = "npm test"\ndefault_labels = ["custom"]\n',
        encoding="utf-8",
    )
    output = tmp_path / "CODEX_TASKS.md"

    exit_code = main(["tasks", str(repo), "--output", str(output)])

    assert exit_code == 0
    text = output.read_text(encoding="utf-8")
    assert "`npm test`" in text


def test_tasks_json_preserves_literal_verification_command(tmp_path: Path) -> None:
    command = r"C:\tools\new\verify.ps1"
    (tmp_path / "codex-maintainer-kit.toml").write_text(
        f"verification_command = '{command}'\n", encoding="utf-8"
    )
    output = tmp_path / "tasks.json"

    assert main(["tasks", str(tmp_path), "--format", "json", "--output", str(output)]) == 0

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["tasks"]
    assert all(task["verification_command"] == command for task in payload["tasks"])
