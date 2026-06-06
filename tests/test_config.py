from pathlib import Path

import pytest

from maam.config.io import load_model, load_yaml, save_model
from maam.config.models import (
    AssetKind,
    AssetManifest,
    DeploymentMode,
    ToolConfig,
    UserConfig,
)


def test_asset_manifest_minimal():
    data = {
        "name": "test-asset",
        "kind": "skill",
        "version": "0.1.0",
        "description": "A test asset",
    }
    manifest = AssetManifest.model_validate(data)
    assert manifest.name == "test-asset"
    assert manifest.kind == "skill"
    assert manifest.deployment.strategy == DeploymentMode.SYMLINK


def test_user_config_defaults():
    config = UserConfig()
    assert config.version == "1"
    assert config.default_deployment_mode == DeploymentMode.SYMLINK
    assert "claude-code" in config.tools
    assert config.tools["claude-code"].kinds["skill"].local_path == ".claude/skills"


def test_save_load_model(tmp_path):
    path = tmp_path / "config.yaml"
    config = UserConfig(
        tools={
            "claude-code": ToolConfig(kinds={"skill": {"local_path": ".claude/skills"}})
        }
    )
    save_model(path, config)

    # Verify file content doesn't have nulls/empty lists
    raw = load_yaml(path)
    assert "tools" in raw
    assert "claude-code" in raw["tools"]
    # Bools are preserved
    assert raw["tools"]["claude-code"]["enabled"] is True

    loaded = load_model(UserConfig, path)
    assert loaded.tools["claude-code"].kinds["skill"].local_path == ".claude/skills"


def test_load_non_existent_returns_empty(tmp_path):
    path = tmp_path / "missing.yaml"
    data = load_yaml(path)
    assert data == {}

    config = load_model(UserConfig, path)
    assert isinstance(config, UserConfig)
    assert "claude-code" in config.tools
    assert config.tools["claude-code"].kinds["skill"].local_path == ".claude/skills"


def test_strip_empty():
    from maam.config.io import _strip_empty

    data = {
        "a": 1,
        "b": None,
        "c": [],
        "d": {},
        "e": [1, None, [], {}],
        "f": {"inner": None},
    }
    stripped = _strip_empty(data)
    assert stripped == {"a": 1, "e": [1]}
