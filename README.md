# Codex Maintainer Kit

Codex Maintainer Kit prepares open source repositories for Codex-assisted maintenance.

It scans a local repository, identifies basic maintenance gaps, and generates a `MAINTAINER_BRIEF.md` that a human maintainer can hand to Codex before asking it to improve docs, tests, issue templates, release notes, or repository instructions.

The goal is not to replace maintainers. The goal is to make recurring maintenance work easier to review, delegate, and verify.

## Beginner-Friendly Guides

New to this project? Start with a plain-language explanation:

- [English beginner guide](docs/BEGINNER_GUIDE.md)
- [日本語のやさしい解説](docs/BEGINNER_GUIDE.ja.md)

## Start Here

Choose the shortest path for your situation:

- [Start Here](docs/START_HERE.md) / [まずここから](docs/START_HERE.ja.md): understand the CLI in the first 3 minutes.
- [Use Cases](docs/USE_CASES.md) / [ユースケース](docs/USE_CASES.ja.md): choose when to run an audit, brief, task queue, or review report.

## Why This Exists

Open source maintenance is rarely just writing new code. Maintainers spend time on:

- keeping README and contribution docs accurate
- adding tests before refactors
- preparing releases and changelogs
- reviewing pull requests
- making issue reports easier to act on
- deciding what AI-generated changes are safe to merge

Codex can help with that work, but it needs clear repository context and human review rules. This kit creates that starting context.

## What It Does

- Detects common maintainer files such as `README.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `AGENTS.md`, issue templates, CI workflows, and tests.
- Detects simple project hints such as Python, JavaScript, Go, Rust, Ruby, PHP, Java, .NET, and Swift markers.
- Summarizes current Git working-tree changes.
- Generates an OSS maintenance audit with a health score, maintainer essentials checklist, and prioritized next actions.
- Generates a Markdown maintainer brief with:
  - repository readiness checklist
  - Codex task queue
  - suggested Codex prompt
  - human review rule
- Creates starter maintainer files with `init`.
- Turns readiness gaps into `CODEX_TASKS.md`, JSON, and GitHub issue Markdown files with `tasks`.
- Adds suggested labels, verification commands, and maintainer review checklists to generated issue drafts.
- Generates `CODEX_REVIEW.md` from the current working-tree changes so maintainers can review AI-assisted diffs before merge.

## Installation

From a local checkout:

```bash
python3 -m pip install -e .
```

## GitHub Action

Use [`codex-maintainer-action`](https://github.com/goonobu-dot/codex-maintainer-action) when you want GitHub Actions to generate maintenance artifacts automatically:

```yaml
- uses: goonobu-dot/codex-maintainer-action@v0.2.0
  with:
    output-dir: codex-maintenance
```

The action runs this CLI, writes a GitHub Actions job summary, and uploads `OSS_MAINTENANCE_AUDIT.md`, `MAINTAINER_BRIEF.md`, `CODEX_TASKS.md`, `codex-tasks.json`, and `CODEX_REVIEW.md` as workflow artifacts.

## Usage

Generate an OSS maintenance audit:

```bash
codex-maintainer-kit audit /path/to/repo --output OSS_MAINTENANCE_AUDIT.md
```

Generate a maintainer brief:

```bash
codex-maintainer-kit brief /path/to/repo --output MAINTAINER_BRIEF.md
```

Generate Codex-ready maintenance tasks:

```bash
codex-maintainer-kit tasks /path/to/repo --output CODEX_TASKS.md
```

Generate a human maintainer review brief for current changes:

```bash
codex-maintainer-kit review /path/to/repo --output CODEX_REVIEW.md
```

Generate machine-readable tasks:

```bash
codex-maintainer-kit tasks /path/to/repo --format json --output codex-tasks.json
```

The JSON output shape is documented in [schema/codex-tasks.schema.json](schema/codex-tasks.schema.json).

Generate GitHub issue drafts:

```bash
codex-maintainer-kit tasks /path/to/repo --github-issues-dir .github/generated-maintenance-issues
```

Customize task output with a local config file:

```toml
# codex-maintainer-kit.toml
project_name = "Example OSS Project"
verification_command = "python3 -m pytest -p no:cacheprovider tests -q"
release_command = "gh release create vX.Y.Z --title vX.Y.Z --notes-file CHANGELOG.md"
default_labels = ["maintenance", "codex"]
```

Currently, `tasks` uses `verification_command` and `default_labels` when generating Markdown, JSON, and GitHub issue drafts. Unknown keys are ignored to keep the config format forwards-compatible.

Settings belong at the top level of this TOML file. Literal strings preserve
backslashes, so a Windows command can be written as
`verification_command = 'C:\tools\verify.ps1'`. Label arrays can span multiple
lines and include comments. The parser uses Python's standard-library `tomllib`
on Python 3.11+ and the `tomli` backport on Python 3.9–3.10.

Preview starter files:

```bash
codex-maintainer-kit init /path/to/repo --dry-run
```

Create starter files:

```bash
codex-maintainer-kit init /path/to/repo
```

The `init` command creates:

- `AGENTS.md`
- `CONTRIBUTING.md`
- `.github/ISSUE_TEMPLATE/maintenance.md`

Existing files are skipped unless `--force` is passed.

## Example Output

See:

- [examples/OSS_MAINTENANCE_AUDIT.generated.md](examples/OSS_MAINTENANCE_AUDIT.generated.md), generated from this repository
- [examples/MAINTAINER_BRIEF.example.md](examples/MAINTAINER_BRIEF.example.md)
- [examples/MAINTAINER_BRIEF.generated.md](examples/MAINTAINER_BRIEF.generated.md), generated from this repository
- [examples/CODEX_TASKS.example.md](examples/CODEX_TASKS.example.md)
- [examples/CODEX_TASKS.generated.md](examples/CODEX_TASKS.generated.md), generated from this repository
- [examples/CODEX_REVIEW.example.md](examples/CODEX_REVIEW.example.md)
- [examples/codex-maintainer-kit.toml](examples/codex-maintainer-kit.toml)
- [schema/codex-tasks.schema.json](schema/codex-tasks.schema.json)

## Codex for Open Source

This project was created for maintainers who want to use Codex in open source workflows without removing human review.

The application notes and publishing checklist live in:

- [docs/CODEX_FOR_OSS_APPLICATION.md](docs/CODEX_FOR_OSS_APPLICATION.md)
- [docs/PUBLISHING_CHECKLIST.md](docs/PUBLISHING_CHECKLIST.md)
- [docs/RELEASE_WORKFLOW.md](docs/RELEASE_WORKFLOW.md)

## How This Differs From Existing Tools

This project is intentionally not a replacement for mature repository health or security tools.

- [OpenSSF Scorecard](https://github.com/ossf/scorecard) measures open source security posture.
- [Repolinter](https://github.com/todogroup/repolinter) linted repository metadata and policy files.

Codex Maintainer Kit focuses on a narrower workflow: creating a practical maintenance brief, turning gaps into Codex-ready tasks, generating issue drafts, and keeping human review as the final checkpoint.

## Maintainer Workflow

1. Run `codex-maintainer-kit audit` to understand the repository's maintenance health.
2. Run `codex-maintainer-kit brief`, or run `codex-maintainer-action` in GitHub Actions.
3. Review the generated checklist.
4. Run `codex-maintainer-kit tasks`.
5. Convert the generated task file or issue drafts into scoped maintenance work.
6. Ask Codex to make the smallest useful change.
7. Run `codex-maintainer-kit review` to create a focused review brief for the current diff.
8. Run tests and inspect the diff.
9. Merge only after human review.

## Development

Run tests:

```bash
python3 -m pytest tests -q
```

Run the CLI without installing:

```bash
PYTHONPATH=src python3 -m codex_maintainer_kit.cli brief . --output /tmp/maintainer-brief.md
PYTHONPATH=src python3 -m codex_maintainer_kit.cli audit . --output /tmp/oss-maintenance-audit.md
PYTHONPATH=src python3 -m codex_maintainer_kit.cli tasks . --output /tmp/codex-tasks.md
PYTHONPATH=src python3 -m codex_maintainer_kit.cli review . --output /tmp/codex-review.md
```

## License

MIT
