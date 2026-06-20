from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a yaml file and return its content as a dictionary"""
    path = Path(path)
    data = yaml.safe_load(path.read_text())

    assert data is not None, f"Config file {path} is empty"
    assert isinstance(data, dict), f"Config file {path} must works as a dictionary"

    return data
