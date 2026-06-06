import pytest
from pathlib import Path
from maam.config.models import UserConfig, ProjectConfig, AssetKind, AssetManifest, ProfileConfig, ProfileToolConfig
from maam.config.io import save_model
from maam.core.service import MAAMService

@pytest.fixture
def mock_env(tmp_path):
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()
    
    # Setup local asset
    asset_src = tmp_path / "shared-asset"
    asset_src.mkdir()
    save_model(asset_src / "ASSET.yaml", AssetManifest(
        name="shared-asset", kind="skill", version="0.1.0", description="test"
    ))
    
    return {"home": home, "project": project, "asset_src": asset_src}

def test_sync_with_profile(mock_env, monkeypatch):
    monkeypatch.setenv("MAAM_HOME", str(mock_env["home"]))
    
    user_config = UserConfig()
    service = MAAMService(user_config, mock_env["project"])
    service.catalog.add_local_asset(mock_env["asset_src"])
    
    # Create profile
    profile = ProfileConfig(
        name="test-profile",
        assets=["shared-asset"]
    )
    save_model(mock_env["home"] / "profiles" / "test-profile.yaml", profile)
    
    # Configure project to use profile
    save_model(mock_env["project"] / ".maam" / "project.yaml", ProjectConfig(profile="test-profile"))
    
    deployments = service.sync()
    assert len(deployments) > 0
    assert any(d.asset_name == "shared-asset" for d in deployments)

def test_sync_with_profile_tool_override(mock_env, monkeypatch):
    monkeypatch.setenv("MAAM_HOME", str(mock_env["home"]))
    
    # Setup two assets
    asset2_src = mock_env["asset_src"].parent / "tool-asset"
    asset2_src.mkdir()
    save_model(asset2_src / "ASSET.yaml", AssetManifest(
        name="tool-asset", kind="skill", version="0.1.0", description="tool only"
    ))
    
    user_config = UserConfig()
    service = MAAMService(user_config, mock_env["project"])
    service.catalog.add_local_asset(mock_env["asset_src"])
    service.catalog.add_local_asset(asset2_src)
    
    # Profile: shared-asset for all, tool-asset for claude-code only
    profile = ProfileConfig(
        name="complex",
        assets=["shared-asset"],
        tools={"claude-code": ProfileToolConfig(assets=["tool-asset"])}
    )
    save_model(mock_env["home"] / "profiles" / "complex.yaml", profile)
    
    save_model(mock_env["project"] / ".maam" / "project.yaml", ProjectConfig(profile="complex"))
    
    deployments = service.sync()
    
    # shared-asset should be in multiple tools
    # tool-asset should be only in claude-code
    tool_assets = [d.asset_name for d in deployments if d.tool == "claude-code"]
    assert "shared-asset" in tool_assets
    assert "tool-asset" in tool_assets
    
    other_assets = [d.asset_name for d in deployments if d.tool == "codex"]
    assert "shared-asset" in other_assets
    assert "tool-asset" not in other_assets
