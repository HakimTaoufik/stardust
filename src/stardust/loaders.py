from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a yaml file and return its content as a dictionary"""
    path = Path(path)
    data = yaml.safe_load(path.read_text())

    if data is None:
        raise ValueError(f"Config file {path} is empty")

    if not isinstance(data, dict):
        raise TypeError(f"Config file {path} must be a dictionary")

    return data
