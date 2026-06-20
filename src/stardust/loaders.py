import json
import sys
from pathlib import Path
from typing import Any

import yaml

# tomlib is part of the standard library of python 3.11+
# tomli is the backport for python 3.10
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def _read_config_file(path: Path) -> str:
    """read a config file as text"""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {path}") from None


def _validate_config_data(data: Any, path: Path) -> dict[str, Any]:
    """Validate that the config data is a dictionary and not empty"""
    if data is None:
        raise ValueError(f"Config file {path} is empty")

    if not isinstance(data, dict):
        raise TypeError(f"Config file {path} must be a dictionary")

    return data


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a yaml file and return its content as a dictionary"""
    path = Path(path)

    try:
        data = yaml.safe_load(_read_config_file(path))
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid YAML config file {path}: {error}") from error

    return _validate_config_data(data, path)


def load_json(path: str | Path) -> dict[str, Any]:
    """Load a json config file and return its content as a dictionary"""
    path = Path(path)

    try:
        data = json.loads(_read_config_file(path))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON config file {path}: {error.msg} at line {error.lineno}, column {error.colno}") from error

    return _validate_config_data(data, path)


def load_toml(path: str | Path) -> dict[str, Any]:
    """Load a toml config file and return its content as a dictionary"""
    path = Path(path)

    try:
        data = tomllib.loads(_read_config_file(path))
    except tomllib.TOMLDecodeError as error:
        raise ValueError(f"Invalid TOML config file {path}: {error}") from error

    return _validate_config_data(data, path)


def load_file(path: str | Path) -> dict[str, Any]:
    """Load a config file based on its extension"""
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix in {".yaml", ".yml"}:
        return load_yaml(path)

    if suffix == ".json":
        return load_json(path)

    if suffix == ".toml":
        return load_toml(path)

    raise ValueError(f"Unsupported config file extension {suffix!r}. Supported extensions are: .yaml, .yml, .json, .toml")
