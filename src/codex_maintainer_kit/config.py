from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


CONFIG_FILENAME = "codex-maintainer-kit.toml"


@dataclass(frozen=True)
class MaintainerConfig:
    project_name: str | None = None
    verification_command: str | None = None
    release_command: str | None = None
    default_labels: list[str] | None = None

    def __post_init__(self) -> None:
        if self.default_labels is None:
            object.__setattr__(self, "default_labels", [])


def load_config(root: str | Path) -> MaintainerConfig:
    path = Path(root) / CONFIG_FILENAME
    if not path.exists():
        return MaintainerConfig()

    with path.open("rb") as config_file:
        values = tomllib.load(config_file)

    return MaintainerConfig(
        project_name=_optional_string(values.get("project_name")),
        verification_command=_optional_string(values.get("verification_command")),
        release_command=_optional_string(values.get("release_command")),
        default_labels=_string_list(values.get("default_labels")),
    )


def _optional_string(value: object | None) -> str | None:
    if value is None or isinstance(value, str):
        return value
    raise ValueError(f"Expected string value, got: {value!r}")


def _string_list(value: object | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    raise ValueError(f"Expected list of strings, got: {value!r}")
