import pytest
import os
from pathlib import Path
from maam.config.models import UserConfig, ProjectConfig, AssetKind, AssetManifest, ProjectToolConfig
from maam.config.io import save_model, load_model
from maam.core.service import MAAMService

@pytest.fixture
def mock_env(tmp_path):
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()
    
    # Setup local asset
    asset_src = tmp_path / "sample-asset"
    asset_src.mkdir()
    save_model(asset_src / "ASSET.yaml", AssetManifest(
        name="sample-asset", kind="skill", version="0.1.0", description="test"
    ))
    (asset_src / "SKILL.md").write_text("# Hello")
    
    return {"home": home, "project": project, "asset_src": asset_src}

def test_sync_basic(mock_env, monkeypatch):
    monkeypatch.setenv("MAAM_HOME", str(mock_env["home"]))
    
    user_config = UserConfig()
    service = MAAMService(user_config, mock_env["project"])
    
    # Add asset to catalog
    service.catalog.add_local_asset(mock_env["asset_src"])
    
    # Configure project
    project_config = ProjectConfig(local_assets=["sample-asset"])
    save_model(mock_env["project"] / ".maam" / "project.yaml", project_config)
    
    # Sync
    deployments = service.sync()
    
    assert len(deployments) > 0
    # Check default tool claude-code
    target = mock_env["project"] / ".claude" / "skills" / "sample-asset"
    assert target.exists()
    assert target.is_symlink()

def test_sync_cleanup(mock_env, monkeypatch):
    monkeypatch.setenv("MAAM_HOME", str(mock_env["home"]))
    
    user_config = UserConfig()
    service = MAAMService(user_config, mock_env["project"])
    service.catalog.add_local_asset(mock_env["asset_src"])
    
    # Sync with asset
    save_model(mock_env["project"] / ".maam" / "project.yaml", ProjectConfig(local_assets=["sample-asset"]))
    service.sync()
    target = mock_env["project"] / ".claude" / "skills" / "sample-asset"
    assert target.exists()
    
    # Sync without asset
    save_model(mock_env["project"] / ".maam" / "project.yaml", ProjectConfig(local_assets=[]))
    service.sync()
    assert not target.exists()
