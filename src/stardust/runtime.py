import json
import yaml
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from stardust.core import load_config

ConfigT = TypeVar("ConfigT", bound=BaseModel)


@dataclass
class RunContext:
    """context object that is passed to the main function of a stardust run"""

    run_dir: Path
    config_path: Path
    overrides: list[str]


def create_run_dir() -> Path:
    now = datetime.now()
    run_dir = Path("runs") / now.strftime("%Y-%m-%d") / now.strftime("%H-%M-%S-%f")
    run_dir.mkdir(parents=True)
    return run_dir


def save_resolved_config(config: BaseModel, run_dir: Path) -> None:
    """save the resolved config to a json and yaml files in the run directory with all the default values filled in"""
    data = config.model_dump(mode="json")

    json_path = run_dir / "config.resolved.json"
    json_path.write_text(json.dumps(data, indent=2))

    yaml_path = run_dir / "config.resolved.yaml"
    yaml_path.write_text(yaml.safe_dump(data, indent=2, sort_keys=False))


def parse_args() -> tuple[Path, list[str]]:
    """
    parse command line arguments and return the config path and overrides

    Returns:
        config_path: the path to the yaml config file
        overrides: a list of overrides in the form of "key=value" strings
    """
    args = sys.argv[1:]

    if len(args) < 2 or args[0] not in {"--config", "-c"}:
        raise SystemExit("Usage: python train.py --config config.yaml key=value")

    config_path = Path(args[1])
    overrides = args[2:]

    return config_path, overrides


def run(config_type: type[ConfigT], main: Callable[[ConfigT, RunContext], None]) -> None:
    """
    main entry point for stardust.

    Args:
        config_type: the pydantic model class to use for validation
        main: the main function to run, which takes the validated config and a RunContext
    """
    config_path, overrides = parse_args()
    config = load_config(config_type, config_path, overrides)

    run_dir = create_run_dir()
    save_resolved_config(config, run_dir)

    context = RunContext(
        run_dir=run_dir,
        config_path=config_path,
        overrides=overrides,
    )

    main(config, context)
