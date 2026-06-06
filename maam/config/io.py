import yaml
import json
from pathlib import Path
from typing import Any, Dict, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

def load_yaml(path: Path) -> Dict[str, Any]:
    """
    Load a YAML file. 
    Returns an empty dict if the file does not exist.
    Raises ValueError if the content is not a mapping.
    """
    if not path.exists():
        return {}
    
    with open(path, "r") as f:
        data = yaml.safe_load(f)
        
    if data is None:
        return {}
        
    if not isinstance(data, dict):
        raise ValueError(f"YAML file {path} must contain a mapping, found {type(data)}")
        
    return data

def save_yaml(path: Path, data: Any) -> None:
    """
    Save data to a YAML file.
    Creates parent directories if they don't exist.
    If data is a Pydantic model, it is serialized to a dict first,
    stripping None and empty containers.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    
    output = data
    if isinstance(data, BaseModel):
        # Convert to JSON-compatible dict first to handle Enums, Paths, etc.
        # Then strip empty values.
        raw_json = data.model_dump_json()
        output = json.loads(raw_json)
        output = _strip_empty(output)
        
    with open(path, "w") as f:
        yaml.safe_dump(output, f, sort_keys=False)

def _strip_empty(data: Any) -> Any:
    """
    Recursively strip None, empty lists, and empty dicts.
    """
    if isinstance(data, dict):
        return {
            k: v for k, v in (
                (k, _strip_empty(v)) for k, v in data.items()
            ) if v is not None and (not isinstance(v, (list, dict)) or v)
        }
    if isinstance(data, list):
        return [
            v for v in (
                _strip_empty(x) for x in data
            ) if v is not None and (not isinstance(v, (list, dict)) or v)
        ]
    return data

def load_model(model_cls: Type[T], path: Path) -> T:
    """
    Load a YAML file and parse it into a Pydantic model.
    """
    data = load_yaml(path)
    return model_cls.model_validate(data)

def save_model(path: Path, model: BaseModel) -> None:
    """
    Alias for save_yaml(path, model).
    """
    save_yaml(path, model)
