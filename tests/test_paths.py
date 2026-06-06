import os
from pathlib import Path
from maam.config.paths import get_maam_home, get_project_config_path, expand_path

def test_get_maam_home_default():
    # Should be ~/.maam by default
    home = get_maam_home()
    assert home == Path.home() / ".maam"

def test_get_maam_home_env(monkeypatch):
    monkeypatch.setenv("MAAM_HOME", "/tmp/maam-test")
    home = get_maam_home()
    # Resolve the expected path as well because macOS might add /private
    assert home == Path("/tmp/maam-test").resolve()

def test_get_project_config_path():
    project_dir = Path("/tmp/my-project")
    config_path = get_project_config_path(project_dir)
    assert config_path == project_dir / ".maam" / "project.yaml"

def test_expand_path_absolute():
    abs_path = "/usr/bin/local"
    expanded = expand_path(abs_path)
    assert expanded == Path(abs_path)

def test_expand_path_relative():
    project_dir = Path("/tmp/my-project")
    rel_path = "subdir/file.txt"
    expanded = expand_path(rel_path, project_root=project_dir)
    # Use resolve() on the expected side too
    # But note: project_dir might not exist, resolve() on non-existent path might behave differently
    # Actually, expand_path uses (root / p).resolve()
    assert str(expanded).endswith("tmp/my-project/subdir/file.txt")
