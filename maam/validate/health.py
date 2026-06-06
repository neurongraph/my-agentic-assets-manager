from pathlib import Path
from typing import List, Tuple, Optional
from maam.config.models import ProjectState, ProjectConfig, UserConfig, AssetKind
from maam.catalog.manager import CatalogManager
from maam.tools.manager import ToolManager

class HealthChecker:
    def __init__(self, user_config: UserConfig, project_dir: Path):
        self.user_config = user_config
        self.project_dir = project_dir
        self.catalog = CatalogManager(user_config)
        self.tools = ToolManager(user_config)

    def check_deployments(self, state: ProjectState) -> List[Tuple[str, str]]:
        """
        Check existing deployments for health issues.
        Returns a list of (level, message).
        """
        issues = []
        for d in state.deployments:
            target = Path(d.target)
            if not target.exists() and not target.is_symlink():
                issues.append(("error", f"Deployment target missing: {d.tool}/{d.asset_name} -> {target}"))
                continue
            
            if target.is_symlink():
                source = Path(os.readlink(target)) if hasattr(os, 'readlink') else Path(d.source)
                if not source.exists():
                    issues.append(("error", f"Broken symlink: {d.tool}/{d.asset_name} (source missing: {source})"))
            elif not target.is_dir():
                issues.append(("warning", f"Deployment target is not a directory: {target}"))
                
        return issues

    def check_config_resolution(self, project_config: ProjectConfig) -> List[Tuple[str, str]]:
        """
        Check if all assets and profiles mentioned in config can be resolved.
        """
        issues = []
        
        # Check profile
        if project_config.profile:
            profile_path = (self.catalog.get_maam_home() / "profiles" / f"{project_config.profile}.yaml")
            if not profile_path.exists():
                issues.append(("error", f"Referenced profile not found: {project_config.profile}"))

        # Check local assets
        for asset_name in project_config.local_assets:
            # Try to resolve in any kind
            found = False
            for kind in AssetKind:
                if self.catalog.resolve_asset(kind, asset_name):
                    found = True
                    break
            if not found:
                issues.append(("warning", f"Project asset could not be resolved: {asset_name}"))

        return issues
import os
