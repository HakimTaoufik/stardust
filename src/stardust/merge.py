from copy import deepcopy
from typing import Any


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    merge two dictionaries recursively

    Values from `override` replace values from `base`.
    If both values are dictionaries, they are merged instead of replacing the whole nested dictionary.

    This is useful for applying command-line overrides on top of a config file

    Example:
        base = {
            "lr": 0.0001,
            "model": {
                "name": "allenai/Olmo-3-7B-Instruct",
                "max_context_tokens": 8192,
            },
        }

        override = {
            "model": {
                "max_context_tokens": 16384,
            },
        }

        result = deep_merge(base, override)

        result == {
            "lr": 0.0001,
            "model": {
                "name": "allenai/Olmo-3-7B-Instruct",
                "max_context_tokens": 16384,
            },
        }

    Args:
        base: the original dictionary.
        override: the dictionary containing values that should override `base`.

    Returns:
        a new merged dictionary where the input dictionaries are not modified
        and values from `override` replace values from `base`
    """
    result = deepcopy(base)

    for key, value in override.items():
        if isinstance(result.get(key), dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)

    return result
