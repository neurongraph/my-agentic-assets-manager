# my-agentic-assets-manager (MAAM) Design

**Date:** 2026-06-06
**Status:** Draft for review
**CLI Name:** `maam`
**Project Name:** `my-agentic-assets-manager`

## Vision

`my-agentic-assets-manager` (MAAM) is a project-local asset manager for agentic development environments.

It manages reusable asset packages and deploys them into project-local directories for supported tools and agents. The goal is to make agentic environments composable, reproducible, version-controlled, and cleanly isolated at the repository level.

MAAM is inspired by the strengths of MSM, but it is a new product with a clean-slate core:
- assets are the primary unit, not skills
- deployments are project-local only
- tools declare capability matrices by asset kind
- profiles define reusable project environments
- every package uses a shared `ASSET.yaml` manifest

MSM's reusable low-level behavior for skill packages has been surveyed and should inform the `skill` kind implementation. The detailed reuse notes live at:
- `docs/superpowers/specs/2026-06-06-msm-reuse-survey.md`

## Product Goals

### Primary Goals

- Manage reusable asset packages for agentic systems
- Support multiple asset kinds under one model
- Support multiple tools/agents with uneven capabilities
- Keep all deployments project-local
- Make environments reproducible through declarative config
- Support reusable project profiles
- Prefer symlink-based deployment with safe fallback behavior
- Validate and reconcile project state with a single `sync` workflow

### Secondary Goals

- Enable future asset kinds without redesigning the core
- Support import/export of project environment definitions
- Support Git-backed remote registries of assets
- Create a strong foundation for future migration tools from MSM

### Non-Goals For V1

- Global or workstation-wide deployment
- Automatic migration from MSM
- Cloud synchronization
- Marketplace hosting
- GUI application
- Asset execution or runtime orchestration
- Plugin architecture for custom deployers

## Core Concepts

### Asset

An asset is a reusable package used by an agentic tool or environment.

Examples:
- `postgres-expert` as a `skill`
- `claude-review-agent` as an `agent`
- `team-prompts` as a `prompt-pack`
- `postgres-mcp` as an `mcp-server`
- `claude-enterprise-settings` as `settings`

Every asset package contains a required `ASSET.yaml` manifest and kind-specific payload files.

### Asset Kind

The first supported asset kinds in v1 are:
- `skill`
- `agent`
- `prompt-pack`
- `mcp-server`
- `settings`

The system must be designed so that adding a new asset kind later does not require redesigning the catalog, deployment state model, or profile model.

### Tool

A tool is an agentic platform or environment target that can receive project-local assets.

Examples:
- `claude-code`
- `codex`
- `opencode`
- `cursor`
- `gemini-cli`

Tools are not hardcoded to one asset layout. Each tool declares which asset kinds it supports and where those kinds should be deployed inside a project.

### Profile

A profile is a reusable project environment definition.

A profile describes:
- which assets are generally desired in a project
- which tools should receive which assets
- optional overlays or additional assets for specific tools

Profiles do not represent global environments. They are templates for project-local deployment only.

### Deployment

A deployment is the materialization of an asset into a tool-specific directory inside a project.

Examples:
- `.claude/skills/postgres-expert`
- `.claude/agents/claude-review-agent`
- `.opencode/agents/repo-maintainer`
- `.cursor/settings/enterprise-policy`

Deployments should prefer symlinks and fall back to copying when symlinks are not available.

### Registry

A registry is a source of asset packages.

MAAM supports:
- a local writable registry for imported assets
- remote Git-backed registries cloned under MAAM-managed storage

Registry content is canonical. Deployments are generated artifacts.

## Design Principles

### Project-Local Only

All deployed assets must live inside the project directory. MAAM does not deploy assets into home-directory or workstation-global tool directories.

This keeps environments:
- easier to reason about
- easier to reproduce
- less likely to leak across repositories
- simpler to validate and clean up

### Declarative First

User config, profile definitions, project config, and manifests should all be human-readable and git-friendly.

YAML is the default config format.

### Shared Asset Model

Every deployable package must expose a common manifest contract through `ASSET.yaml`, even when the payload is kind-specific.

This keeps:
- registry discovery simple
- validation predictable
- deployment state uniform
- CLI behavior consistent

### Tool Capability Matrix

Tool support is explicit.

MAAM must not assume every tool supports every asset kind. A tool declares a capability matrix mapping supported kinds to project-local target paths.

### Clean-Slate Core

MAAM should borrow ideas from MSM where they are good, but should not preserve MSM abstractions that are too skill-centric or too global-scope-oriented.

## Filesystem Model

### User-Level MAAM Home

The MAAM home directory stores shared control-plane data:

```text
~/.maam/
├── config.yaml
├── registry/
├── registries/<name>/
├── profiles/
└── state/
```

Purpose of each directory:
- `config.yaml`: user config containing registry references and tool capability definitions
- `registry/`: local writable asset registry
- `registries/<name>/`: cloned remote registries
- `profiles/`: reusable project profile definitions
- `state/`: deployment metadata and health records

### Project Layout

A project using MAAM stores only project-local deployment intent and generated assets:

```text
project-root/
├── .maam/
│   ├── project.yaml
│   └── state.yaml
├── .claude/
│   ├── skills/
│   ├── agents/
│   └── settings/
├── .opencode/
│   ├── skills/
│   └── agents/
└── ...
```

Notes:
- `.maam/project.yaml` is the project-local source of truth for desired environment composition
- `.maam/state.yaml` records realized deployments for this project
- tool directories are generated outputs based on tool capability rules

## Registry Layout

Registries expose assets under a shared `assets/` root.

```text
registry-root/
└── assets/
    ├── skills/
    │   └── postgres-expert/
    │       ├── ASSET.yaml
    │       └── SKILL.md
    ├── agents/
    │   └── claude-review-agent/
    │       ├── ASSET.yaml
    │       └── agent.md
    ├── prompt-packs/
    │   └── team-prompts/
    │       ├── ASSET.yaml
    │       └── prompts/
    ├── mcp-servers/
    │   └── postgres-mcp/
    │       ├── ASSET.yaml
    │       └── server.json
    └── settings/
        └── claude-enterprise-settings/
            ├── ASSET.yaml
            └── settings.json
```

Rules:
- every asset must have `ASSET.yaml`
- asset directory name is the canonical package name unless overridden explicitly later
- registries may contain multiple asset kinds
- remote registries should sparse-check out only `assets/`

### Legacy MSM Skill Import Layouts

MAAM's canonical registry layout is `assets/<kind-plural>/<name>/`.

For compatibility with existing MSM skill packages and registries, MAAM should also support import from these legacy layouts:

```text
legacy-registry-root/
├── postgres-expert/
│   └── SKILL.md
└── skills/
    └── spark-scala/
        └── SKILL.md
```

Legacy imports must be normalized into MAAM's canonical layout:

```text
registry-root/
└── assets/
    └── skills/
        └── postgres-expert/
            ├── ASSET.yaml
            └── SKILL.md
```

Rules:
- legacy MSM layouts are accepted as input, not as MAAM's canonical storage format
- imported legacy skills must become `kind: skill` assets
- `ASSET.yaml` remains the canonical manifest after import
- if `ASSET.yaml` is absent, MAAM may infer one from `SKILL.md` front matter

## Data Model

### `AssetManifest`

The common manifest for every asset package.

Required fields:
- `name`
- `kind`
- `version`
- `description`

Recommended fields:
- `owner`
- `tags`
- `payload`
- `compatibility`
- `deployment`
- `dependencies`

Example:

```yaml
name: postgres-expert
kind: skill
version: 0.1.0
description: PostgreSQL optimization guidance for coding agents
owner: surjit
tags:
  - database
  - postgres

payload:
  entrypoint: SKILL.md
  include:
    - prompts/
    - templates/

compatibility:
  tools:
    - claude-code
    - codex
    - opencode
  platforms:
    - macos
    - linux

deployment:
  strategy: symlink

dependencies: []
```

### Skill Manifest Compatibility

For `kind: skill`, `SKILL.md` is the required payload entrypoint unless the manifest explicitly declares a different skill entrypoint later.

Existing MSM skills may include YAML front matter at the top of `SKILL.md`:

```markdown
---
name: postgres-expert
description: PostgreSQL optimization guidance
version: 0.1.0
tags:
  - postgres
---
```

MAAM should use this only as an import bridge:
- if `ASSET.yaml` exists, trust `ASSET.yaml`
- if importing a legacy MSM skill without `ASSET.yaml`, synthesize a draft `ASSET.yaml`
- use the directory name as `name` when front matter omits it
- copy `description`, `version`, and `tags` when present
- set `kind: skill`
- set `payload.entrypoint: SKILL.md`

### `ToolConfig`

Defines a tool and its capability matrix by asset kind.

Example:

```yaml
tools:
  claude-code:
    enabled: true
    kinds:
      skill:
        local_path: .claude/skills
      agent:
        local_path: .claude/agents
      settings:
        local_path: .claude/settings

  opencode:
    enabled: true
    kinds:
      skill:
        local_path: .opencode/skills
      agent:
        local_path: .opencode/agents
```

Meaning:
- tool support is explicit per kind
- unsupported kinds are absent
- paths are relative to project root

### `UserConfig`

The primary shared user-level configuration for registries, tool capability definitions, and default behavior.

Fields:
- `version`
- `registry_path`
- `default_deployment_mode`
- `tools`
- `registries`

This file stores shared user preferences and discovery information, not deployed asset state.

### Default Skill Capability Paths

MAAM should carry forward MSM's useful project-local skill path defaults where the tool is still relevant:

```yaml
tools:
  claude-code:
    enabled: true
    kinds:
      skill:
        local_path: .claude/skills
  codex:
    enabled: true
    kinds:
      skill:
        local_path: .codex/skills
  antigravity:
    enabled: true
    kinds:
      skill:
        local_path: .agents/skills
  opencode:
    enabled: true
    kinds:
      skill:
        local_path: .agents/skills
  bob:
    enabled: true
    kinds:
      skill:
        local_path: .bob/skills
  pi:
    enabled: true
    kinds:
      skill:
        local_path: .agents/skills
```

These are project-local defaults only. MAAM v1 must not add MSM's global skill paths.

### `ProfileConfig`

Profiles define reusable project environments.

Example:

```yaml
name: data-platform
description: Assets for data engineering projects

assets:
  - postgres-expert
  - team-prompts

tools:
  claude-code:
    assets:
      - postgres-expert
      - claude-review-agent
      - claude-enterprise-settings
  opencode:
    assets:
      - postgres-expert
      - opencode-repo-agent
```

Rules:
- top-level `assets` apply across the project
- `tools.<name>.assets` are tool-specific additions or overrides
- profiles contain no global/local scope knobs

### `ProjectConfig`

Defines a project’s desired local environment.

Example:

```yaml
profile: data-platform
local_assets:
  - architecture-review

tools:
  claude-code:
    additional_assets:
      - local-review-agent
```

Rules:
- `profile` is optional
- `local_assets` augment the profile
- `tools.<name>.additional_assets` augment profile tool assignments

### `DeploymentRecord`

Tracks one realized asset deployment.

Fields:
- `asset_name`
- `asset_kind`
- `tool`
- `scope`
- `source`
- `target`
- `mode`
- `status`

Notes:
- `scope` is retained as an internal field if helpful, but in v1 its value should always be `project`
- the model must support multiple records for the same asset name across tools or kinds

### `ProjectState`

Stored in `.maam/state.yaml` and used for reconciliation.

Fields:
- `version`
- `deployments`
- optional health metadata later

### `ExportConfig`

For v1, export/import should focus on portable environment definitions rather than machine-wide state.

Fields:
- `profiles`
- `registries`
- `tools`
- optional project template metadata later

## Architecture

### 1. CLI Layer

Location:
- `maam/cli/`

Responsibilities:
- command parsing
- user-facing messaging
- output formatting
- error translation

Typer should remain a good fit.

### 2. Service Layer

Location:
- `maam/core/`

Responsibilities:
- orchestrate registry resolution, validation, deployment, and sync
- own business workflows
- keep CLI thin

A central `MAAMService` should coordinate operations, similar in spirit to MSM’s `MSMService`, but using asset-centric methods.

### 3. Asset Catalog Layer

Location:
- `maam/catalog/` or `maam/registry/`

Responsibilities:
- discover assets across local and remote registries
- validate manifest presence
- resolve asset names to source paths
- list assets with metadata
- detect duplicates across registries

This layer should be generic across asset kinds.

Implementation details to reuse from MSM:
- local writable registry has precedence over remote registries
- configured remote registries are considered in sorted registry-name order
- list commands return the effective winning asset for each `(kind, name)`
- duplicate checks report all sources for the same `(kind, name)`
- local install copies the source package into MAAM's local registry while preserving internal symlinks
- remote Git registries should use sparse clone/update mechanics, using `assets` instead of MSM's `skills`

### 4. Tool Capability Layer

Location:
- `maam/tools/`

Responsibilities:
- parse tool config
- expose supported kinds for each tool
- resolve project-local target paths per kind
- validate tool definitions

This replaces MSM’s simpler adapter model.

### 5. Deployment Layer

Location:
- `maam/deploy/`

Responsibilities:
- materialize one asset to one target path
- remove stale deployments
- update project deployment state
- support symlink-first with copy fallback

Deployment should be generic at the engine level, with kind-specific validation delegated elsewhere.

Implementation details to reuse from MSM:
- create the target directory before deployment
- deploy a package directory as `<target-dir>/<asset-name>`
- do not rewrite a correct existing symlink
- replace stale targets before materializing
- prefer directory symlinks and fall back to `copytree`
- preserve internal symlinks when copying
- record the actual resulting mode as `symlink` or `copy`
- remove symlinks and files with `unlink`
- remove real directories with recursive directory removal
- remove only recorded project-local deployment targets under a configured tool/kind directory

### 6. Validation Layer

Location:
- `maam/validate/` or distributed helper modules

Responsibilities:
- validate manifests
- validate tool support
- validate profile references
- validate project config
- validate drift and broken deployments

### 7. Config Layer

Location:
- `maam/config/`

Responsibilities:
- pydantic models
- YAML load/save helpers
- standard filesystem paths
- project config and user config IO

## CLI Design

### Asset Commands

```bash
maam asset add <name> [--from PATH]
maam asset remove <name>
maam asset list
maam asset show <name>
maam asset validate <name>
```

Responsibilities:
- install local assets into the writable catalog
- inspect metadata
- validate package structure

### Profile Commands

```bash
maam profile new <name>
maam profile list
maam profile show <name>
maam profile validate <name>
```

Responsibilities:
- scaffold reusable project environment definitions
- inspect and validate profile contents

Note:
- there is no `apply-global`
- profile realization into a project happens through project config plus `sync`

### Project Commands

```bash
maam project init [--profile NAME]
maam project show
```

Responsibilities:
- initialize `.maam/project.yaml`
- optionally bind a project to a known profile

### Sync And Health Commands

```bash
maam sync
maam doctor
```

Responsibilities of `sync`:
- resolve desired assets from project config and profile
- validate tool capability support
- deploy missing assets
- repair broken links
- remove stale project-local deployments
- update `.maam/state.yaml`

Responsibilities of `doctor`:
- validate config files
- report missing assets
- report unsupported tool-kind assignments
- report duplicate assets across registries
- report broken symlinks and missing sources

### Registry Commands

```bash
maam registry add <name> <git-url>
maam registry update
maam registry list
```

Responsibilities:
- store Git registry references
- clone and update remote registries
- expose registry inventory

### Tool Commands

```bash
maam tool list
maam tool capabilities
maam tool validate
```

Responsibilities:
- inspect configured tools
- show supported asset kinds and target paths
- validate tool definitions

### Import/Export Commands

```bash
maam export
maam import <path>
```

Responsibilities:
- move environment definitions between machines or teams
- transport profiles, registry references, and tool definitions
- avoid exporting ephemeral project deployment outputs

## Validation Rules

### Manifest Validation

For every asset:
- `ASSET.yaml` must exist
- required fields must be present
- `kind` must be one of the supported kinds
- declared payload entrypoints should exist
- dependencies should have valid shape even if not fully resolved in v1

### Registry Validation

- duplicate asset names across registries should be detected
- local registry should take precedence over remote registries
- remote registry layout must contain `assets/`
- missing clones should be reported cleanly

### Tool Validation

- tool names must be unique
- each supported kind must declare a relative `local_path`
- paths must not escape the project root through normalization
- disabled tools should be ignored by deployment workflows

### Profile Validation

- all referenced assets must resolve
- all tool names must exist in user config
- tool-specific asset assignments must use kinds supported by that tool
- duplicate assignments should be tolerated but normalized during deployment

### Project Validation

- referenced profile must exist
- local asset references must resolve
- tool-specific additions must reference configured tools
- tool-specific additions must be compatible with tool capability support

### Deployment Validation

- broken symlinks must be reported
- missing source paths must be reported
- realized target paths outside declared tool kind directories must be reported as drift
- stale project-local deployments should be removable by `sync`

## Deployment Flow

The primary workflow is `maam sync`.

Resolution algorithm:
1. load user config
2. load project config
3. if configured, load referenced profile
4. compute desired asset set from profile assets plus project additions
5. compute desired tool-specific asset set
6. resolve each asset to a source path and manifest
7. validate that each asset kind is supported by the target tool
8. materialize the asset into the configured project-local directory
9. record deployment state in `.maam/state.yaml`
10. remove prior deployments in project state that are no longer desired

Important behavior:
- deployment is idempotent
- unchanged correct symlinks should not be rewritten
- copy fallback should be recorded in state
- desired state is derived from config, not from previous state

## Kind-Specific Payload Expectations

V1 should support shared state management with light kind-specific validation.

### `skill`
Expected payload:
- `SKILL.md` by default
- optional prompts, templates, helpers

Compatibility behavior:
- support importing MSM-style skill directories where `SKILL.md` is the only manifest-like file
- parse optional YAML front matter in `SKILL.md` during import
- normalize legacy skills by writing `ASSET.yaml` into the registry copy

### `agent`
Expected payload:
- tool-specific agent prompt or descriptor files
- optional supporting templates or instructions

### `prompt-pack`
Expected payload:
- one or more prompt files or prompt directories

### `mcp-server`
Expected payload:
- declarative MCP server config or packaged server metadata
- optional launch instructions or templates

### `settings`
Expected payload:
- tool-specific settings/config files

The engine should not deeply understand every payload format in v1. It should validate presence and structural basics, then deploy files as-is.

## Recommended Python Stack

- Python 3.12+
- uv
- Typer
- Rich
- PyYAML
- Pydantic
- GitPython or shell-driven Git operations

Tooling guidance inherited from MSM:
- manage the project with `uv`
- commit `uv.lock`
- expose the CLI through `[project.scripts]` as `maam = "maam.cli.app:app"`
- use Hatchling as the build backend
- keep pytest in the `dev` dependency group
- prefer `uv run maam ...` and `uv run pytest` for local verification
- provide a `justfile` for common `uv` workflows
- start with shell-driven Git subprocess calls for sparse registry clone/update; add GitPython only if later phases need richer Git APIs

## Suggested Package Layout

```text
my-agentic-assets-manager/
├── pyproject.toml
├── README.md
├── maam/
│   ├── cli/
│   ├── core/
│   ├── config/
│   ├── catalog/
│   ├── tools/
│   ├── deploy/
│   └── validate/
├── tests/
├── docs/
│   └── superpowers/
│       ├── specs/
│       └── plans/
└── examples/
```

## Phased Implementation Plan

The detailed Phase 1 bootstrap execution plan lives at:
- `docs/superpowers/plans/2026-06-06-maam-phase-1-bootstrap.md`

### Phase 1: Project Bootstrap

- create the new Python package and CLI entrypoint `maam`
- scaffold docs, tests, and package layout
- establish default user config shape

### Phase 2: Core Models And Config IO

- implement Pydantic models for manifests, tool config, profiles, project config, export config, and deployment state
- implement YAML load/save helpers
- implement standard path helpers for user config and project config
- reuse MSM YAML behavior: missing files read as empty mappings where appropriate, non-mapping YAML fails clearly, persisted models omit empty values, and writes create parent directories

### Phase 3: Asset Catalog And Registry Support

- implement local asset install/remove/list/show/resolve
- implement remote Git registry add/update
- implement multi-kind discovery under `assets/`
- implement duplicate detection and precedence rules
- implement legacy MSM skill import from `<root>/<name>/SKILL.md` and `<root>/skills/<name>/SKILL.md`
- synthesize `ASSET.yaml` from `SKILL.md` front matter when importing legacy skills

### Phase 4: Tool Capability Resolution

- implement tool capability models and validation
- implement per-kind target path resolution relative to a project root
- implement tool inspection commands
- seed project-local `skill` capability defaults from MSM's existing agent defaults where applicable

### Phase 5: Deployment Engine And Sync

- implement generic project-local deployment engine
- implement project state recording in `.maam/state.yaml`
- implement reconciliation and stale deployment cleanup
- implement `maam sync`
- preserve MSM deployment semantics for symlink idempotency, copy fallback, safe removal, and broken symlink detection

### Phase 6: Profiles And Project Workflows

- implement profile scaffold/list/show/validate
- implement project initialization and profile binding
- implement profile-aware sync resolution

### Phase 7: Doctor And Import/Export

- implement environment health checks
- implement export/import for profiles, tools, and registries
- ensure exported data represents declarative intent, not generated outputs

### Phase 8: Documentation And Samples

- write README and user guide
- add sample registry and example project configs
- document supported asset kinds and capability matrices

## Risks And Mitigations

### Risk: Over-generalizing asset kinds too early
Mitigation:
- keep the common model generic
- keep kind-specific validation shallow in v1
- add deeper kind-specific behavior only when required

### Risk: Tool capability definitions become verbose
Mitigation:
- ship sensible defaults for common tools
- keep per-kind path templates compact
- offer inspection commands for debugging

### Risk: Name collisions across asset kinds
Mitigation:
- state should record both `asset_name` and `asset_kind`
- profile validation should resolve by manifest kind
- CLI output should show kind explicitly where ambiguity exists

### Risk: Project-local only may not satisfy all users
Mitigation:
- keep the codebase open to future higher-level workflows
- do not reintroduce global deploy behavior in v1
- consider optional future workspace templates or bootstrap commands instead

## Open Decisions Deferred Beyond This Spec

These are intentionally deferred so v1 stays focused:
- version pinning between registries and projects
- dependency resolution between assets
- merge semantics for settings assets
- deep validation for MCP runtime launch behavior
- migration tooling from MSM
- asset publishing workflows

## Recommendation

Build MAAM as a clean-slate, project-local asset management platform with:
- a shared `ASSET.yaml` manifest
- an asset catalog spanning multiple kinds
- explicit tool capability matrices
- profile-driven project environments
- a single `sync`-based reconciliation workflow

This preserves the best ideas from MSM while correcting the two biggest limitations for the next system:
- skill-centric modeling
- global-scope deployment complexity
