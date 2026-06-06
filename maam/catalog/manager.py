import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from maam.catalog.skills import import_msm_skill, is_msm_skill, synthesize_manifest
from maam.config.io import load_model, load_yaml, save_yaml
from maam.config.models import AssetKind, AssetManifest, RegistryConfig, UserConfig
from maam.config.paths import get_local_registry_path, get_maam_home


class CatalogManager:
    def __init__(self, user_config: UserConfig):
        self.user_config = user_config
        self.local_path = get_local_registry_path()
        self.registries_path = get_maam_home() / "registries"

    def get_asset_sources(self) -> List[Tuple[str, Path]]:
        sources = []
        if self.local_path.exists():
            sources.append(("local", self.local_path))

        remote_names = sorted(self.user_config.registries.keys())
        for name in remote_names:
            sources.append((name, self.registries_path / name))

        return sources

    def list_assets(
        self,
    ) -> Dict[Tuple[AssetKind, str], List[Tuple[str, Path, AssetManifest]]]:
        assets = {}
        for reg_name, reg_path in self.get_asset_sources():
            if not reg_path.exists():
                continue

            assets_root = reg_path / "assets"
            if assets_root.exists():
                self._discover_in_root(reg_name, assets_root, assets)

            # Legacy layouts typically only have skills or agents
            for kind_name in ["skills", "agents"]:
                kind_path = reg_path / kind_name
                if kind_path.exists() and kind_path != assets_root:
                    self._discover_legacy_in_kind_dir(reg_name, kind_path, assets)

            self._discover_legacy_at_root(reg_name, reg_path, assets)

        return assets

    def _discover_in_root(self, reg_name: str, root: Path, assets: Dict):
        for kind_dir in root.iterdir():
            if not kind_dir.is_dir():
                continue

            kind_str = kind_dir.name.rstrip("s")
            kind = (
                kind_str
                if kind_str in self.user_config.managed_kinds
                else kind_dir.name
            )

            if kind not in self.user_config.managed_kinds:
                continue

            for item in kind_dir.iterdir():
                if item.is_dir():
                    manifest_path = item / "ASSET.yaml"
                    if manifest_path.exists():
                        try:
                            manifest = load_model(AssetManifest, manifest_path)
                            self._add_to_assets(assets, reg_name, item, manifest)
                        except Exception:
                            continue
                    elif (item / "SKILL.md").exists():
                        manifest = synthesize_manifest(item)
                        manifest.kind = kind  # Force kind based on folder for legacy
                        self._add_to_assets(assets, reg_name, item, manifest)
                elif (
                    item.is_file() and item.suffix == ".md" and item.name != "README.md"
                ):
                    # File-based asset (common for agents)
                    manifest = AssetManifest(
                        name=item.stem,
                        kind=kind,
                        version="0.1.0",
                        description=f"{kind.capitalize()}: {item.stem}",
                    )
                    self._add_to_assets(assets, reg_name, item, manifest)

    def _discover_legacy_in_kind_dir(self, reg_name: str, kind_dir: Path, assets: Dict):
        kind_str = kind_dir.name.rstrip("s")
        kind = kind_str if kind_str in self.user_config.managed_kinds else "skill"

        for item in kind_dir.iterdir():
            if item.is_dir():
                if (item / "SKILL.md").exists() and not (item / "ASSET.yaml").exists():
                    manifest = synthesize_manifest(item)
                    manifest.kind = kind
                    self._add_to_assets(assets, reg_name, item, manifest)
            elif item.is_file() and item.suffix == ".md" and item.name != "README.md":
                # File-based asset
                manifest = AssetManifest(
                    name=item.stem,
                    kind=kind,
                    version="0.1.0",
                    description=f"{kind.capitalize()}: {item.stem}",
                )
                self._add_to_assets(assets, reg_name, item, manifest)

    def _discover_legacy_at_root(self, reg_name: str, root: Path, assets: Dict):
        skip = {
            "assets",
            "skills",
            "agents",
            "registries",
            "registry",
            "profiles",
            "tests",
            "docs",
        }
        for asset_dir in root.iterdir():
            if (
                not asset_dir.is_dir()
                or asset_dir.name in skip
                or asset_dir.name.startswith(".")
            ):
                continue
            if (asset_dir / "SKILL.md").exists() and not (
                asset_dir / "ASSET.yaml"
            ).exists():
                manifest = synthesize_manifest(asset_dir)
                # Ensure default legacy kind is allowed
                if manifest.kind not in self.user_config.managed_kinds:
                    if "skill" in self.user_config.managed_kinds:
                        manifest.kind = "skill"
                    else:
                        continue
                self._add_to_assets(assets, reg_name, asset_dir, manifest)

    def _add_to_assets(
        self, assets: Dict, reg_name: str, path: Path, manifest: AssetManifest
    ):
        if manifest.kind not in self.user_config.managed_kinds:
            return

        key = (manifest.kind, manifest.name)
        if key not in assets:
            assets[key] = []
        assets[key].append((reg_name, path, manifest))

    def resolve_asset(
        self, kind: AssetKind, name: str
    ) -> Optional[Tuple[str, Path, AssetManifest]]:
        all_assets = self.list_assets()
        matches = all_assets.get((kind, name))
        if matches:
            return matches[0]
        return None

    def add_local_asset(self, source_path: Path) -> AssetManifest:
        if is_msm_skill(source_path):
            return import_msm_skill(source_path, self.local_path / "assets")

        manifest_path = source_path / "ASSET.yaml"
        if manifest_path.exists():
            manifest = load_model(AssetManifest, manifest_path)
        elif (source_path / "SKILL.md").exists():
            manifest = synthesize_manifest(source_path)
        else:
            # Fallback: assume name from folder, default kind 'skill'
            manifest = AssetManifest(
                name=source_path.name,
                kind="skill",
                version="0.1.0",
                description=f"Local asset from {source_path.name}",
            )

        target_dir = self.local_path / "assets" / f"{manifest.kind}s" / manifest.name

        if target_dir.exists():
            shutil.rmtree(target_dir)

        target_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_path, target_dir, symlinks=True)

        return manifest

    def remove_local_asset(self, kind: AssetKind, name: str) -> bool:
        paths = [
            self.local_path / "assets" / f"{kind}s" / name,
            self.local_path / "assets" / kind / name,
            self.local_path / f"{kind}s" / name,
            self.local_path / kind / name,
        ]
        for p in paths:
            if p.exists():
                shutil.rmtree(p)
                return True
        return False

    def update_registries(self):
        self.registries_path.mkdir(parents=True, exist_ok=True)

        # Calculate sparse-checkout patterns based on managed kinds
        # We want to fetch 'assets/', and plural/singular forms of each kind
        patterns = ["assets"]
        for kind in self.user_config.managed_kinds:
            patterns.append(kind)
            if not kind.endswith("s"):
                patterns.append(f"{kind}s")

        for name, config in self.user_config.registries.items():
            reg_dir = self.registries_path / name

            if not reg_dir.exists():
                # Initial clone with partial clone and sparse-checkout enabled
                clone_cmd = [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "--filter=blob:none",
                    "--sparse",
                ]
                if config.branch:
                    clone_cmd += ["-b", config.branch]
                clone_cmd += [config.url, str(reg_dir)]

                subprocess.run(clone_cmd, check=False)

            if reg_dir.exists():
                # Ensure sparse-checkout patterns are set (updates if changed)
                # This also converts a full clone to a sparse clone if needed
                subprocess.run(
                    ["git", "-C", str(reg_dir), "sparse-checkout", "set"] + patterns,
                    check=False,
                )

                # Pull latest changes
                subprocess.run(
                    ["git", "-C", str(reg_dir), "pull", "--ff-only"], check=False
                )
