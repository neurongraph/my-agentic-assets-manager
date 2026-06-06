# MSM Reuse Survey For MAAM

**Date:** 2026-06-06
**Source project:** `/Users/surjitdas/projects/my-skills-manager`
**Target project:** `my-agentic-assets-manager`

## Survey Summary

`my-skills-manager` (MSM) contains useful low-level implementation details for the `skill` asset kind. MAAM should reuse those details as design inputs, but generalize them under MAAM's asset-centric model.

The core rule:

- reuse MSM's proven filesystem, registry, deployment, YAML, and health-check behavior
- do not reuse MSM's global deployment model or skill-only data model as MAAM architecture

## Source Modules Reviewed

- `/Users/surjitdas/projects/my-skills-manager/pyproject.toml`
- `/Users/surjitdas/projects/my-skills-manager/justfile`
- `/Users/surjitdas/projects/my-skills-manager/uv.lock`
- `/Users/surjitdas/projects/my-skills-manager/msm/registry/manager.py`
- `/Users/surjitdas/projects/my-skills-manager/msm/deploy/manager.py`
- `/Users/surjitdas/projects/my-skills-manager/msm/agents/adapters.py`
- `/Users/surjitdas/projects/my-skills-manager/msm/agents/defaults.py`
- `/Users/surjitdas/projects/my-skills-manager/msm/config/models.py`
- `/Users/surjitdas/projects/my-skills-manager/msm/config/paths.py`
- `/Users/surjitdas/projects/my-skills-manager/msm/config/io.py`
- `/Users/surjitdas/projects/my-skills-manager/msm/config/state.py`
- `/Users/surjitdas/projects/my-skills-manager/msm/core/service.py`
- `/Users/surjitdas/projects/my-skills-manager/tests/test_registry.py`
- `/Users/surjitdas/projects/my-skills-manager/tests/test_deploy.py`
- `/Users/surjitdas/projects/my-skills-manager/tests/conftest.py`

## Reusable UV Tooling Details

MSM uses a compact `uv`-first Python project setup that MAAM should reuse almost directly.

### Package Metadata

MSM's `pyproject.toml` establishes these patterns:

- PEP 621 `[project]` metadata
- Python `>=3.12`
- runtime dependencies declared in `dependencies`
- Typer console script in `[project.scripts]`
- `dev` dependency group for pytest
- Hatchling build backend
- explicit wheel package selection
- pytest test path configuration

MAAM equivalent:

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

Git tooling such as GitPython should remain optional until MAAM needs Python-level Git APIs. MSM currently uses shell-driven `git` subprocess calls successfully for clone, sparse checkout, and pull.

### Lockfile Policy

MSM commits `uv.lock`. MAAM should also commit `uv.lock` once dependencies are resolved.

Use:

```bash
uv sync
uv run pytest
uv run maam --help
uv run maam doctor
```

### Global Tool Install For Local Use

MSM's `just setup` installs the CLI with:

```bash
uv tool install --reinstall .
```

MAAM should support the same local developer flow:

```bash
uv tool install --reinstall .
maam doctor
```

This is a developer convenience, not a requirement for tests. Tests should prefer `uv run maam ...` so they use the workspace environment.

### Justfile Workflow

MSM wraps common commands in `justfile`. MAAM should carry this forward with renamed commands:

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

Later MAAM-specific shortcuts can be added for asset listing, registry update, and sync once those commands exist.

### Agent-Facing Command Docs

MSM documents these commands in `CLAUDE.md` and `AGENTS.md`:

```bash
uv sync
uv run msm --help
uv run pytest
uv run pytest tests/test_core.py
uv run pytest tests/test_core.py::test_skill_add_and_export
uv run msm doctor
```

MAAM should include equivalent guidance once the package exists:

```bash
uv sync
uv run maam --help
uv run pytest
uv run pytest tests/test_cli.py
uv run maam doctor
```

## Reusable Skill Details

### Skill Package Shape

MSM treats a directory containing `SKILL.md` as a valid skill package.

MAAM should preserve this as the minimum payload contract for `kind: skill`:

```text
postgres-expert/
├── ASSET.yaml
└── SKILL.md
```

For migrated or imported MSM skills, `SKILL.md` remains required. `ASSET.yaml` becomes MAAM's canonical manifest.

### SKILL.md Metadata Bridge

MSM extracts optional metadata from YAML front matter at the top of `SKILL.md`:

```markdown
---
name: postgres-expert
description: PostgreSQL optimization
version: 0.1.0
tags:
  - postgres
---
```

MAAM should support this as an import convenience for `skill` assets:

- if `ASSET.yaml` exists, trust `ASSET.yaml`
- if importing an MSM-style skill without `ASSET.yaml`, infer a draft asset manifest from `SKILL.md` front matter
- require or synthesize `kind: skill`
- use the directory name as `name` when front matter omits it
- copy `description`, `version`, and `tags` when present
- write an explicit `ASSET.yaml` into MAAM's local registry copy

This keeps MAAM declarative while preserving compatibility with existing skill packages.

### Registry Resolution

MSM supports both direct local registry entries and nested remote registry entries:

```text
registry-root/
├── postgres-expert/
│   └── SKILL.md
└── skills/
    └── spark-scala/
        └── SKILL.md
```

MAAM's canonical layout should remain:

```text
registry-root/
└── assets/
    └── skills/
        └── postgres-expert/
            ├── ASSET.yaml
            └── SKILL.md
```

However, MAAM's `skill` importer should accept legacy MSM registry roots containing:

- `<root>/<skill-name>/SKILL.md`
- `<root>/skills/<skill-name>/SKILL.md`

Imported legacy entries should be normalized into `assets/skills/<name>/`.

### Registry Precedence

MSM uses this precedence:

1. local writable registry
2. configured remote registries in sorted name order

MAAM should keep the same predictable rule, generalized to assets:

- local `~/.maam/registry` wins over remote registries
- duplicate detection reports all sources
- list operations return one effective asset per `(kind, name)`, with the winning source shown
- doctor reports duplicates as warnings unless resolution is ambiguous

### Remote Git Registry Mechanics

MSM clones remote registries with:

- `git clone --filter=blob:none --sparse`
- `git sparse-checkout set skills`
- update via `git pull --ff-only`

MAAM should reuse the sparse clone strategy with MAAM's canonical remote path:

```bash
git sparse-checkout set assets
```

For legacy MSM skill registries, MAAM may support an explicit import mode that sparse-checks out `skills` and normalizes the result into a MAAM registry.

### Deployment Materialization

MSM's deployment engine has good behavior to preserve:

- create the target directory before deploying
- deploy a package directory as `<target-dir>/<asset-name>`
- prefer directory symlinks
- if symlinks fail, copy the directory
- preserve symlinks inside copied trees
- do not rewrite a correct existing symlink
- replace stale targets before materializing
- record whether the resulting deployment is `symlink` or `copy`

MAAM should generalize this from `deploy_skill()` to `deploy_asset()` with fields:

- `asset_name`
- `asset_kind`
- `tool`
- `scope`, always `project` in v1
- `source`
- `target`
- `mode`
- `status`

### Safe Removal

MSM safely removes deployment targets by handling symlinks/files with `unlink()` and real directories with `rmtree()`.

MAAM should preserve this distinction and add a project-local safety rule:

- only remove targets recorded in `.maam/state.yaml`
- only remove targets under the configured tool/kind target directory
- never remove paths outside the project root

### Broken Link Detection

MSM reports a broken deployment when a recorded target is a symlink whose source no longer exists.

MAAM should keep this in `doctor` and `sync`:

- `doctor` reports broken symlinks
- `sync` repairs broken symlinks when the source asset still resolves
- `sync` removes stale targets when the desired asset is no longer configured

### YAML IO

MSM's YAML helpers are worth preserving:

- missing YAML files read as `{}` for config-loading convenience
- non-mapping YAML raises a clear error
- writes create parent directories
- Pydantic models dump through JSON mode before YAML serialization
- empty `None`, empty list, and empty dict values are stripped from persisted YAML
- output preserves key order with `sort_keys=False`

MAAM should reuse the behavior but make auto-creation explicit. In particular, Phase 1 and Phase 2 path helpers should not create config by merely resolving paths.

### Path Helpers

MSM's path design translates directly:

- environment override: `MSM_HOME`
- user config path
- local registry path
- remote registries path
- profiles path
- deployment state path
- project config path
- relative path expansion against a project root

MAAM equivalent:

- environment override: `MAAM_HOME`
- user config: `~/.maam/config.yaml`
- local registry: `~/.maam/registry`
- remote registries: `~/.maam/registries`
- profiles: `~/.maam/profiles`
- user-level health state if needed: `~/.maam/state`
- project config: `<project>/.maam/project.yaml`
- project state: `<project>/.maam/state.yaml`

### Tool Defaults For Skill Support

MSM includes skill defaults for these tools:

```yaml
claude-code:
  skill: .claude/skills
codex:
  skill: .codex/skills
antigravity:
  skill: .agents/skills
opencode:
  skill: .agents/skills
bob:
  skill: .bob/skills
pi:
  skill: .agents/skills
```

MAAM should carry these as default `skill` capability paths where the tool remains relevant. MAAM must not add global paths for these tools in v1.

### State Upsert Identity

MSM upserts deployment records by:

- skill
- agent
- scope
- target

MAAM should upsert by:

- asset name
- asset kind
- tool
- scope
- target

This avoids duplicate records while allowing the same asset to be deployed to multiple tools.

## Reusable Tests

MAAM should adapt MSM's tests into asset-centric tests:

- install/list/resolve/remove a local skill asset
- import a legacy MSM skill directory containing `SKILL.md`
- parse SKILL.md front matter into a generated `ASSET.yaml`
- resolve legacy `<root>/skills/<name>` during import
- clone a remote MAAM registry with sparse checkout of `assets`
- update a remote registry and discover a new asset
- prefer local assets over remote duplicates
- report duplicate `(kind, name)` assets across sources
- deploy a skill asset by symlink
- prove deployment idempotency
- fall back to copy when symlink creation fails
- remove a deployment safely
- detect broken symlinks from project state

## Things Not To Carry Forward

Do not carry these MSM design choices into MAAM v1:

- global deployment paths
- `global_skills`
- agent-specific data model names where `tool` is the better term
- user-level deployment state as the source of project reconciliation
- skill-only registry layout as canonical
- `profile global-apply` and `profile local-apply`

MAAM should preserve the implementation wisdom while replacing the architecture with an asset-first, project-local sync model.
