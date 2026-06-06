import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from maam.catalog.manager import CatalogManager
from maam.config.io import save_model
from maam.config.models import AssetKind, AssetManifest, RegistryConfig, UserConfig


@pytest.fixture
def mock_home(tmp_path):
    home = tmp_path / ".maam"
    home.mkdir()
    return home


@pytest.fixture
def catalog_manager(mock_home, monkeypatch):
    monkeypatch.setenv("MAAM_HOME", str(mock_home))
    user_config = UserConfig()
    return CatalogManager(user_config)


def test_add_local_asset(catalog_manager, tmp_path):
    asset_src = tmp_path / "my-skill"
    asset_src.mkdir()
    manifest = AssetManifest(
        name="my-skill", kind="skill", version="1.0.0", description="test skill"
    )
    save_model(asset_src / "ASSET.yaml", manifest)

    catalog_manager.add_local_asset(asset_src)

    # Verify it exists in local registry
    resolved = catalog_manager.resolve_asset("skill", "my-skill")
    assert resolved is not None
    assert resolved[0] == "local"
    assert resolved[2].version == "1.0.0"


def test_add_msm_skill(catalog_manager, tmp_path):
    skill_src = tmp_path / "msm-skill"
    skill_src.mkdir()
    (skill_src / "SKILL.md").write_text(
        "---\nname: msm\ndescription: old\n---\n# Legacy"
    )

    catalog_manager.add_local_asset(skill_src)

    resolved = catalog_manager.resolve_asset("skill", "msm")
    assert resolved is not None
    assert resolved[2].description == "old"
    assert (resolved[1] / "ASSET.yaml").exists()


def test_precedence(mock_home, monkeypatch, tmp_path):
    monkeypatch.setenv("MAAM_HOME", str(mock_home))

    # Setup remote registry
    remote_path = mock_home / "registries" / "remote1"
    remote_asset = remote_path / "assets" / "skills" / "shared-skill"
    remote_asset.mkdir(parents=True)
    save_model(
        remote_asset / "ASSET.yaml",
        AssetManifest(
            name="shared-skill", kind="skill", version="remote", description="rem"
        ),
    )

    # Setup local registry
    local_path = mock_home / "registry" / "assets" / "skills" / "shared-skill"
    local_path.mkdir(parents=True)
    save_model(
        local_path / "ASSET.yaml",
        AssetManifest(
            name="shared-skill", kind="skill", version="local", description="loc"
        ),
    )

    user_config = UserConfig(registries={"remote1": {"url": "http://fake"}})
    manager = CatalogManager(user_config)

    resolved = manager.resolve_asset("skill", "shared-skill")
    assert resolved[0] == "local"
    assert resolved[2].version == "local"


def test_remove_asset(catalog_manager, tmp_path):
    asset_src = tmp_path / "to-remove"
    asset_src.mkdir()
    save_model(
        asset_src / "ASSET.yaml",
        AssetManifest(name="to-remove", kind="agent", version="1.0", description="rem"),
    )

    catalog_manager.add_local_asset(asset_src)
    assert catalog_manager.resolve_asset("agent", "to-remove") is not None

    catalog_manager.remove_local_asset("agent", "to-remove")
    assert catalog_manager.resolve_asset("agent", "to-remove") is None


@patch("maam.catalog.manager.subprocess.run")
def test_update_registries_sparse(mock_run, mock_home, monkeypatch):
    monkeypatch.setenv("MAAM_HOME", str(mock_home))

    user_config = UserConfig(
        managed_kinds=["skill", "agent"],
        registries={"test-reg": RegistryConfig(url="https://github.com/user/repo")},
    )
    manager = CatalogManager(user_config)

    def side_effect(args, **kwargs):
        if "clone" in args:
            Path(args[-1]).mkdir(parents=True)
        return MagicMock()

    mock_run.side_effect = side_effect

    manager.update_registries()

    calls = [call.args[0] for call in mock_run.call_args_list]

    # 1. Clone with sparse and filter
    assert any("--sparse" in args and "--filter=blob:none" in args for args in calls)

    # 2. Sparse-checkout set with patterns
    set_call = next(
        args for args in calls if "sparse-checkout" in args and "set" in args
    )
    assert "assets" in set_call
    assert "skills" in set_call
    assert "agents" in set_call
