# my-agentic-assets-manager (MAAM)

MAAM is a project-local asset manager for agentic development environments.

It manages reusable asset packages and deploys them into project-local directories for supported tools and agents. This makes agentic environments composable, reproducible, and cleanly isolated at the repository level.

## Core Features

- **Assets First:** Support multiple kinds (`skill`, `agent`, `prompt-pack`, `mcp-server`, `settings`).
- **Project Local:** Deployments stay within the project directory (e.g., `.claude/skills`).
- **Declarative:** Environments defined through `project.yaml` and reusable `profiles`.
- **MSM Compatible:** Imports existing MSM `SKILL.md` packages as `kind: skill`.
- **Sync Workflow:** A single `maam sync` command reconciles your project environment.

## Installation

Requires Python 3.12+ and `uv`.

```bash
# Clone the repository
git clone <repo-url>
cd my-agentic-assets-manager

# Install dependencies and CLI
uv sync
```

## Getting Started

1. **Initialize a Project:**
   ```bash
   maam project init
   ```

2. **Add an Asset:**
   ```bash
   maam asset add ./my-cool-skill
   ```

3. **Configure Your Project:**
   Edit `.maam/project.yaml`:
   ```yaml
   local_assets:
     - my-cool-skill
   ```

4. **Synchronize:**
   ```bash
   maam sync
   ```

## Asset Kinds

MAAM supports the following asset kinds:

- `skill`: Core capability or set of instructions (usually a `SKILL.md`).
- `agent`: Specialized agent definition or prompt.
- `prompt-pack`: Collection of reusable prompts.
- `mcp-server`: Model Context Protocol server configuration.
- `settings`: Tool-specific configuration or policy files.

## Tool Capabilities

Tools define where specific asset kinds should be deployed within a project. Default mappings include:

- **claude-code**: `.claude/skills`, `.claude/agents`, `.claude/prompts`
- **codex**: `.codex/skills`, `.codex/agents`
- **antigravity**: `.agents/skills`, `.agents/agents`
- **opencode**: `.agents/skills`, `.agents/agents`
- **bob**: `.bob/skills`, `.bob/agents`
- **pi**: `.agents/skills`, `.agents/agents`

You can add custom capabilities:
```bash
maam tool add-capability my-custom-tool agent .custom/agents
```

## Examples

Check the `examples/` directory for:
- Sample profiles (`coding-project`, `obsidian-vault`, `office-work`)
- Sample user configuration with registry references.
- Sample project configuration.
- Sample asset layout.

## Health and Portability

- **Doctor:** Run `maam doctor` to check for broken symlinks, missing sources, or config errors.
- **Portability:** Use `maam export backup.yaml` and `maam import-config backup.yaml` to move your setup between machines.

## Development

```bash
# Run tests
uv run pytest

# Check project health
uv run maam doctor
```
