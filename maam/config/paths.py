import os
from pathlib import Path
from typing import Optional

def get_maam_home() -> Path:
    """
    Return the MAAM home directory. Defaults to ~/.maam.
    Can be overridden by MAAM_HOME environment variable.
    """
    home = os.environ.get("MAAM_HOME")
    if home:
        return Path(home).expanduser().resolve()
    return Path.home() / ".maam"

def get_user_config_path() -> Path:
    """Return the path to the user config file."""
    return get_maam_home() / "config.yaml"

def get_local_registry_path() -> Path:
    """Return the path to the local writable registry."""
    return get_maam_home() / "registry"

def get_project_dir(start: Optional[Path] = None) -> Path:
    """
    Return the project root directory.
    Currently returns the current working directory.
    Future versions might search upwards for .maam/
    """
    return Path(start or os.getcwd()).resolve()

def get_project_config_path(project_dir: Optional[Path] = None) -> Path:
    """Return the path to the project config file."""
    root = project_dir or get_project_dir()
    return root / ".maam" / "project.yaml"

def get_project_state_path(project_dir: Optional[Path] = None) -> Path:
    """Return the path to the project state file."""
    root = project_dir or get_project_dir()
    return root / ".maam" / "state.yaml"

def expand_path(path: str, project_root: Optional[Path] = None) -> Path:
    """
    Expand a path string. 
    If absolute, return as Path.
    If relative, resolve against project_root (defaults to CWD).
    """
    p = Path(path)
    if p.is_absolute():
        return p
    
    root = project_root or get_project_dir()
    return (root / p).resolve()
