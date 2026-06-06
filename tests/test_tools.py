import pytest
from pathlib import Path
from maam.config.models import UserConfig, AssetKind, ToolConfig, ToolKindConfig
from maam.tools.manager import ToolManager

def test_tool_manager_defaults():
    config = UserConfig()
    manager = ToolManager(config)
    
    assert "claude-code" in manager.list_tools()
    assert "skill" in manager.get_supported_kinds("claude-code")
    assert "agent" in manager.get_supported_kinds("claude-code")

def test_resolve_target_path(tmp_path):
    config = UserConfig()
    manager = ToolManager(config)
    
    # Standard relative path
    target = manager.resolve_target_path("claude-code", "skill", tmp_path)
    assert target == tmp_path / ".claude" / "skills"

def test_resolve_target_path_escape_attempt(tmp_path):
    config = UserConfig(
        tools={
            "evil-tool": ToolConfig(
                kinds={"skill": ToolKindConfig(local_path="../../etc")}
            )
        }
    )
    manager = ToolManager(config)
    
    target = manager.resolve_target_path("evil-tool", "skill", tmp_path)
    assert target is None

def test_unsupported_kind(tmp_path):
    config = UserConfig()
    manager = ToolManager(config)
    
    # claude-code default doesn't have settings
    target = manager.resolve_target_path("claude-code", "settings", tmp_path)
    assert target is None
