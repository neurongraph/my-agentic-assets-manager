# MAAM Phase 1 Bootstrap Plan

**Date:** 2026-06-06
**Status:** Ready for implementation
**Source spec:** `docs/superpowers/specs/2026-06-06-maam-design.md`
**MSM reuse survey:** `docs/superpowers/specs/2026-06-06-msm-reuse-survey.md`

## Phase Objective

Create the first runnable MAAM Python package and CLI skeleton.

Phase 1 should make the project installable, testable, and ready for the model/config work in Phase 2. It should not implement full asset discovery, deployment, profiles, or sync behavior yet.

## Phase Boundary

### In Scope

- initialize Python package metadata
- create `uv`-managed project tooling
- add `uv.lock` after dependency resolution
- add a `justfile` for common developer commands
- create `maam` CLI entrypoint
- create the top-level package layout from the design spec
- add a minimal `maam --version`
- add a minimal `maam doctor`
- define default path helpers for MAAM home and project config locations
- add lightweight tests proving the package and CLI load
- add a README with the current product shape and development commands
- reserve module locations for MSM-derived skill import, registry, YAML, and deployment behavior

### Out Of Scope

- real registry cloning
- real asset install/remove workflows
- project sync or deployment reconciliation
- profile resolution
- remote import/export
- deep manifest validation
- migration from MSM

## Proposed Repository Shape

```text
my-agentic-assets-manager/
├── pyproject.toml
├── uv.lock
├── justfile
├── README.md
├── maam/
│   ├── __init__.py
│   ├── cli/
│   │   ├── __init__.py
│   │   └── app.py
│   ├── core/
│   │   └── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── io.py
│   │   └── paths.py
│   ├── catalog/
│   │   ├── __init__.py
│   │   └── legacy_skills.py
│   ├── tools/
│   │   └── __init__.py
│   ├── deploy/
│   │   ├── __init__.py
│   │   └── engine.py
│   └── validate/
│       └── __init__.py
├── tests/
│   ├── test_cli.py
│   └── test_paths.py
└── docs/
```

## Dependency Choices

Use the stack already recommended by the design spec:

- Python 3.12+
- `uv`
- Typer
- Rich
- PyYAML
- Pydantic
- pytest

Phase 1 only needs Typer, Rich, and pytest directly. PyYAML and Pydantic can be declared now because Phase 2 immediately uses them.

Use the same compact `uv` pattern proven in MSM:

```toml
[project]
name = "my-agentic-assets-manager"
version = "0.1.0"
description = "Project-local asset manager for agentic development environments"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.7",
    "pyyaml>=6.0",
    "rich>=13.7",
    "typer>=0.12",
]

[project.scripts]
maam = "maam.cli.app:app"

[dependency-groups]
dev = [
    "pytest>=8.2",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["maam"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Git operations should start as shell-driven `git` subprocess calls in later phases, matching MSM's working implementation. Add GitPython only if later behavior needs Python-level Git APIs.

## Justfile Contract

Add a `justfile` based on MSM's developer workflow:

```just
default:
    @just --list

install:
    uv tool install --reinstall .

setup:
    uv sync
    uv tool install --reinstall .
    maam doctor

sync:
    uv sync

test:
    uv run pytest

test-file FILE:
    uv run pytest {{ FILE }} -v

test-one NAME:
    uv run pytest -k {{ NAME }} -v

doctor:
    uv run maam doctor
```

Phase 1 verification should use `uv run ...`; `uv tool install --reinstall .` is a developer convenience for trying the installed CLI.

## CLI Contract

### `maam --version`

Expected behavior:

- exits successfully
- prints the installed package version

### `maam doctor`

Expected behavior in Phase 1:

- exits successfully
- prints a concise health summary
- reports the resolved MAAM home path
- reports whether the current directory appears to have `.maam/project.yaml`
- does not require any config files to already exist

Example output shape:

```text
MAAM doctor
Version: 0.1.0
MAAM home: /Users/example/.maam
Project config: not found
Status: bootstrap ready
```

## Path Helper Contract

Add `maam/config/paths.py` with small, testable functions:

- `get_maam_home() -> Path`
- `get_user_config_path() -> Path`
- `get_local_registry_path() -> Path`
- `get_project_dir(start: Path | None = None) -> Path`
- `get_project_config_path(project_dir: Path | None = None) -> Path`
- `get_project_state_path(project_dir: Path | None = None) -> Path`

Phase 1 behavior:

- default MAAM home is `~/.maam`
- `MAAM_HOME` environment variable overrides the default
- project config path is `<project>/.maam/project.yaml`
- project state path is `<project>/.maam/state.yaml`
- no filesystem writes are performed by path helper functions
- include an `expand_path(path, project_root=None)` helper matching MSM's behavior for later tool target resolution

## MSM Reuse Hooks

Phase 1 should not implement full MSM compatibility, but it should reserve the module boundaries:

- `maam/config/io.py` for MSM-style YAML load/save behavior
- `maam/catalog/legacy_skills.py` for importing existing `SKILL.md` packages
- `maam/deploy/engine.py` for the future generic version of MSM's symlink/copy deployment engine

These files may contain small placeholders or TODO-oriented docstrings in Phase 1. The important part is that the package shape anticipates the reuse work documented in the survey.

## Test Plan

Add focused bootstrap tests:

- CLI module imports
- `maam --version` exits with code 0
- `maam doctor` exits with code 0 without existing config
- `MAAM_HOME` override changes path resolution
- project config and state paths resolve under the provided project directory
- `expand_path` leaves absolute paths absolute and resolves relative paths against a provided project directory

Run:

```bash
uv sync
uv run pytest
uv run maam --help
uv run maam doctor
```

## Acceptance Criteria

Phase 1 is complete when:

- `uv sync` creates or updates `uv.lock`
- `uv run maam --version` works
- `uv run maam doctor` works in an empty project directory
- `uv run pytest` passes
- `just test` runs the test suite
- `just doctor` runs the bootstrap doctor command
- package layout exists for the layers named in the design spec
- package layout includes the MSM reuse hook modules
- README explains what MAAM is and how to run the bootstrap CLI
- README mentions MAAM will import MSM-style `SKILL.md` packages through `kind: skill`
- no generated deployment directories are created by default

## Implementation Order

1. Add `pyproject.toml` with package metadata, dependencies, CLI script, Hatchling config, dependency groups, and pytest config.
2. Add `justfile` with MSM-derived `uv` commands renamed for MAAM.
3. Add the package directories and empty layer modules.
4. Implement `maam/cli/app.py` with Typer and Rich.
5. Implement `maam/config/paths.py`.
6. Add CLI and path tests.
7. Add README bootstrap documentation with `uv sync`, `uv run maam doctor`, and `uv run pytest`.
8. Run `uv sync`, commit the generated `uv.lock`, run tests, and fix any packaging issues.

## Phase 2 Handoff

After Phase 1, continue into Core Models And Config IO:

- define Pydantic models for `AssetManifest`, `ToolConfig`, `UserConfig`, `ProfileConfig`, `ProjectConfig`, `DeploymentRecord`, `ProjectState`, and `ExportConfig`
- implement YAML load/save helpers
- add model validation tests
- update `maam doctor` to parse config files when present

The Phase 1 CLI should intentionally remain thin so Phase 2 can attach real validation behavior without redesigning the command surface.
