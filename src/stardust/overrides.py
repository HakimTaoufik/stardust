from typing import Any

import yaml


def parse_value(value: str) -> Any:
    """parse a string and standarize it using yaml.safe_load to handle booleans, numbers, lists, etc.."""
    return yaml.safe_load(value)


def set_nested(data: dict[str, Any], key: str, value: Any) -> None:
    """
    set a value inside a nested dictionary using a dotted key in place

    Example:
        key = "model.name"
        value = "allenai/Olmo-3-7B-Instruct"

        becomes:

        {
            "model": {
                "name": "allenai/Olmo-3-7B-Instruct"
            }
        }

    Args:
        data: the dictionary to modify
        key: a dotted key such as "lr" or "model.name"
        value: the value to store at that key
    """
    parts = key.split(".")
    current = data

    for part in parts[:-1]:
        current = current.setdefault(part, {})

    current[parts[-1]] = value


def parse_overrides(overrides: list[str]) -> dict[str, Any]:
    """
    parse command-line overrides into a nested dictionary

    Examples:
        ["lr=0.001"] becomes:

        {
            "lr": 0.001
        }

        ["model.name=allenai/Olmo-3-7B-Instruct"] becomes:

        {
            "model": {
                "name": "allenai/Olmo-3-7B-Instruct"
            }
        }

    Args:
        overrides: a list of command-line overrides in key=value format.

    Returns:
        a nested dictionary containing all parsed overrides.
    """
    data: dict[str, Any] = {}

    for override in overrides:
        key, value = override.split("=", 1)
        set_nested(data, key, parse_value(value))

    return data