from pathlib import Path

import pytest

from codex_maintainer_kit.config import load_config


def test_load_config_returns_defaults_when_file_is_missing(tmp_path: Path) -> None:
    config = load_config(tmp_path)

    assert config.project_name is None
    assert config.verification_command is None
    assert config.default_labels == []


def test_load_config_reads_supported_flat_toml_values(tmp_path: Path) -> None:
    (tmp_path / "codex-maintainer-kit.toml").write_text(
        '\n'.join(
            [
                'project_name = "Demo Project"',
                'verification_command = "npm test"',
                'release_command = "npm run release"',
                'default_labels = ["maintenance", "codex"]',
            ]
        ),
        encoding="utf-8",
    )

    config = load_config(tmp_path)

    assert config.project_name == "Demo Project"
    assert config.verification_command == "npm test"
    assert config.release_command == "npm run release"
    assert config.default_labels == ["maintenance", "codex"]


def test_load_config_preserves_literal_string_backslashes(tmp_path: Path) -> None:
    command = r"C:\tools\new\verify.ps1"
    (tmp_path / "codex-maintainer-kit.toml").write_text(
        f"verification_command = '{command}'\n", encoding="utf-8"
    )

    assert load_config(tmp_path).verification_command == command


def test_load_config_reads_multiline_arrays_with_comments(tmp_path: Path) -> None:
    (tmp_path / "codex-maintainer-kit.toml").write_text(
        'default_labels = [\n  "maintenance", # the primary label\n  "codex",\n]\n',
        encoding="utf-8",
    )

    assert load_config(tmp_path).default_labels == ["maintenance", "codex"]


def test_load_config_reads_quoted_keys(tmp_path: Path) -> None:
    (tmp_path / "codex-maintainer-kit.toml").write_text(
        '"verification_command" = "pytest -q"\n', encoding="utf-8"
    )

    assert load_config(tmp_path).verification_command == "pytest -q"


def test_load_config_ignores_unknown_tables(tmp_path: Path) -> None:
    (tmp_path / "codex-maintainer-kit.toml").write_text(
        'verification_command = "pytest -q"\n'
        '[other_tool]\nverification_command = "do not use this"\n',
        encoding="utf-8",
    )

    assert load_config(tmp_path).verification_command == "pytest -q"


@pytest.mark.parametrize(
    "setting",
    [
        "project_name = 42",
        "verification_command = false",
        "release_command = []",
        'default_labels = "maintenance"',
        'default_labels = ["maintenance", 42]',
    ],
)
def test_load_config_rejects_wrong_types(tmp_path: Path, setting: str) -> None:
    (tmp_path / "codex-maintainer-kit.toml").write_text(setting, encoding="utf-8")

    with pytest.raises(ValueError):
        load_config(tmp_path)
