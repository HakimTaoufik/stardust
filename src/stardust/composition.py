from pathlib import Path
from typing import Any

from stardust.loaders import load_file
from stardust.merge import deep_merge
from stardust.overrides import parse_overrides

SUPPORTED_EXTENSIONS = [".yaml", ".yml", ".json", ".toml"]


def parse_defaults(defaults: Any) -> dict[str, str]:
    """parse the defaults list from a config file and return a dictionary of config groups and their default names"""
    if defaults is None:
        return {}

    if not isinstance(defaults, list):
        raise TypeError("Config 'defaults' must be a list")

    groups: dict[str, str] = {}

    for item in defaults:
        if not isinstance(item, dict) or len(item) != 1:
            raise TypeError("Each defaults entry must look like {'group': 'name'}")

        group, name = next(iter(item.items()))

        if not isinstance(group, str) or not isinstance(name, str):
            raise TypeError("Defaults groups and names must be strings")

        groups[group] = name

    return groups


def split_overrides(overrides: list[str] | None, groups: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    """
    split CLI overrides into config group overrides and normal value overrides

    Arguments:
        overrides: a list of overrides in the form of "key=value" strings
        groups: a dictionary of config groups and their default names

    Returns:
        group_overrides: a dictionary of config group overrides
        value_overrides: a list of normal value overrides
    """
    group_overrides: dict[str, str] = {}
    value_overrides: list[str] = []

    for override in overrides or []:
        if "=" not in override:
            raise ValueError(f"Invalid override {override!r}. Expected format: key=value")

        key, value = override.split("=", 1)

        if not key:
            raise ValueError(f"Invalid override {override!r}. Override key cannot be empty")

        if key in groups:
            if not value:
                raise ValueError(f"Invalid group override {override!r}. Group name cannot be empty")

            group_overrides[key] = value
        else:
            value_overrides.append(override)

    return group_overrides, value_overrides


def find_group_file(config_dir: Path, group: str, name: str) -> Path:
    """
    find a config group file by trying all supported config extensions

    Arguments:
        config_dir: the directory where the config files are located
        group: the config group name (e.g., "model", "dataset")
        name: the config group value (e.g., "resnet50", "imagenet")

    Returns:
        the path to the config group file
    """
    paths = [config_dir / group / f"{name}{extension}" for extension in SUPPORTED_EXTENSIONS]

    for path in paths:
        if path.exists():
            return path

    looked_for = "\n".join(f"  {path}" for path in paths)
    raise FileNotFoundError(f"Could not find config group {group!r} with value {name!r}.\nLooked for:\n{looked_for}")


def compose_config(config_path: str | Path, overrides: list[str] | None = None) -> dict[str, Any]:
    """
    compose a config file with its defaults and CLI overrides

    Arguments:
        config_path: the path to the main config file
        overrides: a list of CLI overrides in the form of "key=value" strings

    Returns:
        a dictionary containing the composed config
    """
    config_path = Path(config_path)
    config_dir = config_path.parent

    main_config = load_file(config_path)

    defaults = parse_defaults(main_config.get("defaults"))
    group_overrides, value_overrides = split_overrides(overrides, defaults)

    selected_groups = deep_merge(defaults, group_overrides)

    config: dict[str, Any] = {}

    for group, name in selected_groups.items():
        group_path = find_group_file(config_dir, group, name)
        group_config = load_file(group_path)

        if "defaults" in group_config:
            raise ValueError(f"Nested defaults are not supported yet: {group_path}")

        config = deep_merge(config, group_config)

    main_config = {key: value for key, value in main_config.items() if key != "defaults"}
    config = deep_merge(config, main_config)

    if value_overrides:
        config = deep_merge(config, parse_overrides(value_overrides))

    return config
