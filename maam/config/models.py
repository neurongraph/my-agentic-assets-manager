from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator

AssetKind = str


class DeploymentMode(str, Enum):
    SYMLINK = "symlink"
    COPY = "copy"


class AssetPayload(BaseModel):
    entrypoint: Optional[str] = None
    include: List[str] = Field(default_factory=list)


class AssetCompatibility(BaseModel):
    tools: List[str] = Field(default_factory=list)
    platforms: List[str] = Field(default_factory=list)


class AssetDeployment(BaseModel):
    strategy: DeploymentMode = DeploymentMode.SYMLINK


class AssetManifest(BaseModel):
    name: str
    kind: AssetKind
    version: str
    description: str
    owner: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    payload: AssetPayload = Field(default_factory=AssetPayload)
    compatibility: AssetCompatibility = Field(default_factory=AssetCompatibility)
    deployment: AssetDeployment = Field(default_factory=AssetDeployment)
    dependencies: List[str] = Field(default_factory=list)


class ToolKindConfig(BaseModel):
    local_path: str

    @model_validator(mode="before")
    @classmethod
    def from_str(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"local_path": data}
        return data


class ToolConfig(BaseModel):
    enabled: bool = True
    kinds: Dict[AssetKind, ToolKindConfig] = Field(default_factory=dict)


class RegistryConfig(BaseModel):
    url: str
    branch: Optional[str] = None


def get_default_tools() -> Dict[str, ToolConfig]:
    """Provide default tool configurations for common agent harnesses."""
    defaults = {
        "claude-code": {
            "skill": ".claude/skills",
            "agent": ".claude/agents",
            "prompt-pack": ".claude/prompts",
        },
        "codex": {"skill": ".codex/skills", "agent": ".codex/agents"},
        "antigravity": {"skill": ".agents/skills", "agent": ".agents/agents"},
        "opencode": {"skill": ".agents/skills", "agent": ".agents/agents"},
        "bob": {"skill": ".bob/skills", "agent": ".bob/agents"},
        "pi": {"skill": ".agents/skills", "agent": ".agents/agents"},
    }

    tools = {}
    for name, kinds in defaults.items():
        kind_configs = {
            kind: ToolKindConfig(local_path=path) for kind, path in kinds.items()
        }
        tools[name] = ToolConfig(enabled=True, kinds=kind_configs)
    return tools


class UserConfig(BaseModel):
    version: str = "1"
    registry_path: Optional[str] = None
    default_deployment_mode: DeploymentMode = DeploymentMode.SYMLINK
    managed_kinds: List[str] = Field(
        default_factory=lambda: [
            "skill",
            "agent",
            "prompt-pack",
            "mcp-server",
            "settings",
        ]
    )
    tools: Dict[str, ToolConfig] = Field(default_factory=get_default_tools)
    registries: Dict[str, RegistryConfig] = Field(default_factory=dict)


class ProfileToolConfig(BaseModel):
    assets: List[str] = Field(default_factory=list)


class ProfileConfig(BaseModel):
    name: str
    description: Optional[str] = None
    assets: List[str] = Field(default_factory=list)
    tools: Dict[str, ProfileToolConfig] = Field(default_factory=dict)


class ProjectToolConfig(BaseModel):
    additional_assets: List[str] = Field(default_factory=list)


class ProjectConfig(BaseModel):
    profile: Optional[str] = None
    local_assets: List[str] = Field(default_factory=list)
    tools: Dict[str, ProjectToolConfig] = Field(default_factory=dict)


class DeploymentStatus(str, Enum):
    ACTIVE = "active"
    BROKEN = "broken"
    STALE = "stale"


class DeploymentRecord(BaseModel):
    asset_name: str
    asset_kind: AssetKind
    tool: str
    scope: str = "project"
    source: str
    target: str
    mode: DeploymentMode
    status: DeploymentStatus = DeploymentStatus.ACTIVE


class ProjectState(BaseModel):
    version: str = "1"
    deployments: List[DeploymentRecord] = Field(default_factory=list)


class ExportConfig(BaseModel):
    profiles: Dict[str, ProfileConfig] = Field(default_factory=dict)
    registries: Dict[str, RegistryConfig] = Field(default_factory=dict)
    tools: Dict[str, ToolConfig] = Field(default_factory=dict)
