from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from stardust.loaders import load_file
from stardust.merge import deep_merge
from stardust.overrides import parse_overrides

# must be a subclass of BaseModel since that's how pydantic works
ConfigT = TypeVar("ConfigT", bound=BaseModel)


def load_config(config_type: type[ConfigT], config_path: str | Path, overrides: list[str] | None = None) -> ConfigT:
    """
    takes the config class, the path to the yaml config file, and a list of overrides
    and returns the validated config object

    if the yaml file is incomplete, the default values from the config class will be used

    Args:
        config_type: the pydantic model class to use for validation
        config_path: the path to the yaml config file
        overrides: a list of overrides in the form of "key=value" strings

    Returns:
        a validated config object
    """
    data = load_file(config_path)

    if overrides:
        data = deep_merge(data, parse_overrides(overrides))

    # validate the config using the pydantic model
    return config_type.model_validate(data)
