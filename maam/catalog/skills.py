import yaml
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from maam.config.models import AssetManifest, AssetKind
from maam.config.io import save_model

def is_msm_skill(path: Path) -> bool:
    """
    Check if a path looks like an MSM-format skill directory.
    Must contain SKILL.md and NOT contain ASSET.yaml.
    """
    return (path / "SKILL.md").exists() and not (path / "ASSET.yaml").exists()

def synthesize_manifest(path: Path) -> AssetManifest:
    """
    Read SKILL.md, extract front matter if present, and create an AssetManifest.
    """
    skill_md_path = path / "SKILL.md"
    content = skill_md_path.read_text()
    
    metadata: Dict[str, Any] = {}
    
    # Simple front matter parser
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1]) or {}
            except Exception:
                pass
                
    return AssetManifest(
        name=metadata.get("name") or path.name,
        kind="skill",
        version=str(metadata.get("version") or "0.1.0"),
        description=metadata.get("description") or "Imported MSM skill",
        tags=metadata.get("tags") or [],
        owner=metadata.get("owner"),
    )

def import_msm_skill(path: Path, target_registry_assets: Path) -> AssetManifest:
    """
    Import an MSM-format skill into the canonical MAAM layout.
    Writes ASSET.yaml into the target directory.
    """
    manifest = synthesize_manifest(path)
    target_dir = target_registry_assets / "skills" / manifest.name
    
    if target_dir.exists():
        shutil.rmtree(target_dir)
    
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(path, target_dir, symlinks=True)
    
    # Save the synthesized manifest
    save_model(target_dir / "ASSET.yaml", manifest)
    
    return manifest
