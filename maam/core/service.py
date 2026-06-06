import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from maam.catalog.manager import CatalogManager
from maam.config.io import load_model, save_model
from maam.config.models import (
    AssetKind,
    DeploymentMode,
    DeploymentRecord,
    DeploymentStatus,
    ExportConfig,
    ProfileConfig,
    ProjectConfig,
    ProjectState,
    UserConfig,
)
from maam.config.paths import (
    get_maam_home,
    get_project_config_path,
    get_project_state_path,
    get_user_config_path,
)
from maam.deploy.engine import DeploymentEngine
from maam.tools.manager import ToolManager


class MAAMService:
    def __init__(self, user_config: UserConfig, project_dir: Path):
        self.user_config = user_config
        self.project_dir = project_dir
        self.catalog = CatalogManager(user_config)
        self.tools = ToolManager(user_config)
        self.deployer = DeploymentEngine()
        self.profiles_path = get_maam_home() / "profiles"

    def get_profile(self, name: str) -> Optional[ProfileConfig]:
        """Load a profile by name."""
        path = self.profiles_path / f"{name}.yaml"
        if path.exists():
            try:
                return load_model(ProfileConfig, path)
            except Exception:
                return None
        return None

    def sync(self) -> List[DeploymentRecord]:
        """
        Reconcile the project state with the desired config.
        Supports both 'name' and 'kind:name' syntax.
        """
        project_config_path = get_project_config_path(self.project_dir)
        if not project_config_path.exists():
            return []

        project_config = load_model(ProjectConfig, project_config_path)
        project_state_path = get_project_state_path(self.project_dir)
        project_state = load_model(ProjectState, project_state_path)

        all_available = self.catalog.list_assets()

        def find_assets(identifier: str) -> List[Tuple[AssetKind, str, Path]]:
            matches = []
            target_kind = None
            name = identifier

            if ":" in identifier:
                kind_part, name = identifier.split(":", 1)
                try:
                    target_kind = AssetKind(kind_part)
                except ValueError:
                    pass  # Treat as part of the name if not a valid kind

            for (kind, a_name), sources in all_available.items():
                if a_name == name:
                    if target_kind is None or kind == target_kind:
                        matches.append((kind, a_name, sources[0][1]))
            return matches

        desired: Set[Tuple[str, AssetKind, str]] = set()

        def add_desired(identifier: str, tool_limit: Optional[str] = None):
            matches = find_assets(identifier)
            for kind, name, _ in matches:
                tools_to_check = [tool_limit] if tool_limit else self.tools.list_tools()
                for tool_name in tools_to_check:
                    if tool_name and kind in self.tools.get_supported_kinds(tool_name):
                        desired.add((name, kind, tool_name))

        # 1. Resolve profile
        if project_config.profile:
            profile = self.get_profile(project_config.profile)
            if profile:
                for ident in profile.assets:
                    add_desired(ident)
                for tool_name, tool_cfg in profile.tools.items():
                    for ident in tool_cfg.assets:
                        add_desired(ident, tool_limit=tool_name)

        # 2. Resolve project-local additions
        for ident in project_config.local_assets:
            add_desired(ident)

        for tool_name, tool_cfg in project_config.tools.items():
            for ident in tool_cfg.additional_assets:
                add_desired(ident, tool_limit=tool_name)

        # 3. Reconcile
        new_state = ProjectState()
        active_targets = {}

        for asset_name, kind, tool_name in desired:
            resolved = self.catalog.resolve_asset(kind, asset_name)
            if not resolved:
                continue

            _, source_path, manifest = resolved
            target_dir = self.tools.resolve_target_path(
                tool_name, kind, self.project_dir
            )
            if not target_dir:
                continue

            # Respect manifest strategy if specified, otherwise use global default
            mode_preference = self.user_config.default_deployment_mode
            if manifest.deployment.strategy == DeploymentMode.COPY:
                mode_preference = DeploymentMode.COPY

            record = self.deployer.deploy_asset(
                name=asset_name,
                kind=kind,
                tool=tool_name,
                source=source_path,
                target_dir=target_dir,
                mode_preference=mode_preference,
            )
            new_state.deployments.append(record)
            active_targets[record.target] = record

        # 4. Cleanup stale
        for old_record in project_state.deployments:
            if old_record.target not in active_targets:
                self.deployer.remove_deployment(old_record)

        save_model(project_state_path, new_state)
        return new_state.deployments

    def export_config(self, output_path: Path):
        export = ExportConfig(
            registries=self.user_config.registries, tools=self.user_config.tools
        )
        if self.profiles_path.exists():
            for p_file in self.profiles_path.glob("*.yaml"):
                try:
                    profile = load_model(ProfileConfig, p_file)
                    export.profiles[profile.name] = profile
                except Exception:
                    continue
        save_model(output_path, export)

    def import_config(self, input_path: Path):
        export = load_model(ExportConfig, input_path)
        for name, config in export.registries.items():
            self.user_config.registries[name] = config
        for name, config in export.tools.items():
            self.user_config.tools[name] = config
        save_model(get_user_config_path(), self.user_config)
        self.profiles_path.mkdir(parents=True, exist_ok=True)
        for name, profile in export.profiles.items():
            save_model(self.profiles_path / f"{name}.yaml", profile)
