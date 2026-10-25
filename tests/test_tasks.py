import json
from pathlib import Path

from codex_maintainer_kit.scanner import GitState, RepositoryScan
from codex_maintainer_kit.config import MaintainerConfig
from codex_maintainer_kit.tasks import (
    build_tasks,
    render_issue_markdown,
    render_tasks_json,
    render_tasks_markdown,
)


def test_build_tasks_creates_prioritized_tasks_for_missing_repo_files() -> None:
    scan = RepositoryScan(
        root=Path("/repo/demo"),
        files={
            "readme": True,
            "license": False,
            "contributing": False,
            "code_of_conduct": True,
            "security": False,
            "changelog": True,
            "agents": False,
            "issue_templates": False,
            "ci": True,
            "tests": True,
        },
        project_hints=["python"],
        git_state=GitState(status="clean", changed_files=[]),
    )

    tasks = build_tasks(scan)

    assert [task.id for task in tasks][:2] == ["add-license", "add-agents"]
    assert tasks[0].priority == "high"
    assert "Human review" in tasks[0].review_notes
    assert any(task.id == "add-issue-templates" for task in tasks)


def test_build_tasks_adds_review_task_when_no_foundational_gaps_exist() -> None:
    scan = RepositoryScan(
        root=Path("/repo/ready"),
        files={
            "readme": True,
            "license": True,
            "contributing": True,
            "code_of_conduct": True,
            "security": True,
            "changelog": True,
            "agents": True,
            "issue_templates": True,
            "ci": True,
            "tests": True,
        },
        project_hints=["python"],
        git_state=GitState(status="clean", changed_files=[]),
    )

    tasks = build_tasks(scan)

    assert len(tasks) == 1
    assert tasks[0].id == "codex-maintenance-review"


def test_build_tasks_applies_configured_verification_command_and_labels() -> None:
    scan = RepositoryScan(
        root=Path("/repo/demo"),
        files={
            "readme": True,
            "license": False,
            "contributing": True,
            "code_of_conduct": True,
            "security": True,
            "changelog": True,
            "agents": True,
            "issue_templates": True,
            "ci": True,
            "tests": True,
        },
        project_hints=["javascript"],
        git_state=GitState(status="clean", changed_files=[]),
    )
    config = MaintainerConfig(verification_command="npm test", default_labels=["custom"])

    task = build_tasks(scan, config=config)[0]

    assert task.verification_command == "npm test"
    assert "custom" in task.suggested_labels


def test_render_tasks_markdown_includes_completion_and_prompt() -> None:
    scan = RepositoryScan(
        root=Path("/repo/demo"),
        files={
            "readme": True,
            "license": False,
            "contributing": True,
            "code_of_conduct": True,
            "security": True,
            "changelog": True,
            "agents": True,
            "issue_templates": True,
            "ci": True,
            "tests": True,
        },
        project_hints=["python"],
        git_state=GitState(status="clean", changed_files=[]),
    )

    markdown = render_tasks_markdown(scan, build_tasks(scan))

    assert markdown.startswith("# Codex Maintenance Tasks")
    assert "## Task 1: Add LICENSE" in markdown
    assert "### Codex Prompt" in markdown
    assert "### Completion Criteria" in markdown


def test_render_tasks_json_is_machine_readable() -> None:
    scan = RepositoryScan(
        root=Path("/repo/demo"),
        files={
            "readme": True,
            "license": False,
            "contributing": True,
            "code_of_conduct": True,
            "security": True,
            "changelog": True,
            "agents": True,
            "issue_templates": True,
            "ci": True,
            "tests": True,
        },
        project_hints=["python"],
        git_state=GitState(status="clean", changed_files=[]),
    )

    payload = json.loads(render_tasks_json(scan, build_tasks(scan)))

    assert payload["repository"] == str(scan.root)
    assert payload["tasks"][0]["id"] == "add-license"
    assert payload["tasks"][0]["completion_criteria"]
    assert payload["tasks"][0]["suggested_labels"]
    assert payload["tasks"][0]["verification_command"]


def test_task_json_schema_documents_public_output_fields() -> None:
    schema_path = Path(__file__).resolve().parents[1] / "schema" / "codex-tasks.schema.json"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    task_required = schema["properties"]["tasks"]["items"]["required"]

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert "repository" in schema["required"]
    assert "tasks" in schema["required"]
    assert "id" in task_required
    assert "codex_prompt" in task_required
    assert "suggested_labels" in task_required
    assert "verification_command" in task_required


def test_render_issue_markdown_is_ready_to_paste_into_github() -> None:
    scan = RepositoryScan(
        root=Path("/repo/demo"),
        files={
            "readme": True,
            "license": False,
            "contributing": True,
            "code_of_conduct": True,
            "security": True,
            "changelog": True,
            "agents": True,
            "issue_templates": True,
            "ci": True,
            "tests": True,
        },
        project_hints=["python"],
        git_state=GitState(status="clean", changed_files=[]),
    )
    task = build_tasks(scan)[0]

    issue = render_issue_markdown(task)

    assert issue.startswith("# Add LICENSE")
    assert "## Suggested Labels" in issue
    assert "## Codex Prompt" in issue
    assert "## Verification Command" in issue
    assert "## Human Review" in issue
