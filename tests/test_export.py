import pytest
from pathlib import Path
from maam.config.models import UserConfig, ProfileConfig, RegistryConfig
from maam.config.io import save_model, load_model
from maam.core.service import MAAMService

@pytest.fixture
def mock_env(tmp_path):
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()
    return {"home": home, "project": project}

def test_export_import(mock_env, monkeypatch):
    monkeypatch.setenv("MAAM_HOME", str(mock_env["home"]))
    
    user_config = UserConfig(
        registries={"central": RegistryConfig(url="https://github.com/maam/registry")}
    )
    save_model(mock_env["home"] / "config.yaml", user_config)
    
    # Create a profile
    profile = ProfileConfig(name="data-science", assets=["numpy-expert"])
    (mock_env["home"] / "profiles").mkdir()
    save_model(mock_env["home"] / "profiles" / "data-science.yaml", profile)
    
    service = MAAMService(user_config, mock_env["project"])
    export_path = mock_env["project"] / "maam-export.yaml"
    service.export_config(export_path)
    
    assert export_path.exists()
    
    # Now setup a NEW home and import
    new_home = mock_env["home"].parent / "new-home"
    new_home.mkdir()
    monkeypatch.setenv("MAAM_HOME", str(new_home))
    
    new_user_config = UserConfig()
    new_service = MAAMService(new_user_config, mock_env["project"])
    new_service.import_config(export_path)
    
    # Verify import
    assert "central" in new_service.user_config.registries
    assert (new_home / "profiles" / "data-science.yaml").exists()
    
def test_health_check_broken_symlink(mock_env, monkeypatch):
    monkeypatch.setenv("MAAM_HOME", str(mock_env["home"]))
    from maam.validate.health import HealthChecker
    from maam.config.models import ProjectState, DeploymentRecord, AssetKind, DeploymentMode
    
    checker = HealthChecker(UserConfig(), mock_env["project"])
    
    # Create a broken symlink
    target = mock_env["project"] / "broken-link"
    import os
    os.symlink("/non/existent/path", target)
    
    state = ProjectState(deployments=[
        DeploymentRecord(
            asset_name="broken",
            asset_kind="skill",
            tool="test",
            source="/non/existent/path",
            target=str(target),
            mode=DeploymentMode.SYMLINK
        )
    ])
    
    issues = checker.check_deployments(state)
    assert any("Broken symlink" in msg for _, msg in issues)
