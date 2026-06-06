from pathlib import Path
from typing import Dict, List, Optional

from maam.config.models import AssetKind, ToolConfig, ToolKindConfig, UserConfig


class ToolManager:
    def __init__(self, user_config: UserConfig):
        self.user_config = user_config

    def get_tool_config(self, tool_name: str) -> Optional[ToolConfig]:
        """Return the configuration for a specific tool."""
        return self.user_config.tools.get(tool_name)

    def get_supported_kinds(self, tool_name: str) -> List[AssetKind]:
        """Return a list of asset kinds supported by the tool."""
        config = self.get_tool_config(tool_name)
        if not config or not config.enabled:
            return []
        return list(config.kinds.keys())

    def resolve_target_path(
        self, tool_name: str, kind: AssetKind, project_root: Path
    ) -> Optional[Path]:
        """
        Resolve the target deployment directory for a given tool and asset kind.
        Returns None if the tool or kind is not supported.
        """
        config = self.get_tool_config(tool_name)
        if not config or not config.enabled:
            return None

        kind_config = config.kinds.get(kind)
        if not kind_config:
            return None

        local_path = kind_config.local_path
        if Path(local_path).is_absolute():
            return None

        target = (project_root / local_path).resolve()

        if not str(target).startswith(str(project_root.resolve())):
            return None

        return target

    def list_tools(self, enabled_only: bool = True) -> Dict[str, ToolConfig]:
        """Return all configured tools."""
        if enabled_only:
            return {k: v for k, v in self.user_config.tools.items() if v.enabled}
        return self.user_config.tools
