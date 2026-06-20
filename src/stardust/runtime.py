import json
import platform
import shlex
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, TypeVar

import yaml
from pydantic import BaseModel

from stardust.core import load_config

ConfigT = TypeVar("ConfigT", bound=BaseModel)
TrackingMode = Literal["config", "full"]


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
    json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    yaml_path = run_dir / "config.resolved.yaml"
    yaml_path.write_text(yaml.safe_dump(data, indent=2, sort_keys=False), encoding="utf-8")


def save_command(run_dir: Path) -> None:
    """save the command used to start the run"""
    command = shlex.join(sys.argv)
    (run_dir / "command.txt").write_text(command + "\n", encoding="utf-8")


def save_metadata(run_dir: Path, config_path: Path, overrides: list[str], tracking: TrackingMode) -> None:
    """save basic metadata about the run"""
    metadata = {
        "started_at": datetime.now().isoformat(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "config_path": str(config_path),
        "overrides": overrides,
        "tracking": tracking,
    }

    metadata_path = run_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def save_run_snapshot(config: BaseModel, run_dir: Path, config_path: Path, overrides: list[str], tracking: TrackingMode) -> None:
    """save run files depending on the selected tracking mode"""
    save_resolved_config(config, run_dir)

    if tracking == "config":
        return

    if tracking == "full":
        save_command(run_dir)
        save_metadata(run_dir, config_path, overrides, tracking)
        return

    raise ValueError("tracking must be either 'config' or 'full'")


def parse_args() -> tuple[Path, list[str]]:
    """
    parse command line arguments and return the config path and overrides

    Returns:
        config_path: the path to the config file
        overrides: a list of overrides in the form of "key=value" strings
    """
    args = sys.argv[1:]

    if len(args) < 2 or args[0] not in {"--config", "-c"}:
        raise SystemExit("Usage: python train.py --config CONFIG_FILE key=value")

    config_path = Path(args[1])
    overrides = args[2:]

    return config_path, overrides


def run(config_type: type[ConfigT], main: Callable[[ConfigT, RunContext], None], tracking: TrackingMode = "config") -> None:
    """
    main entry point for stardust.

    Args:
        config_type: the pydantic model class to use for validation
        main: the main function to run, which takes the validated config and a RunContext
        tracking: what to save in the run directory. use "config" or "full"
    """
    config_path, overrides = parse_args()
    config = load_config(config_type, config_path, overrides)

    run_dir = create_run_dir()
    save_run_snapshot(config, run_dir, config_path, overrides, tracking)

    context = RunContext(
        run_dir=run_dir,
        config_path=config_path,
        overrides=overrides,
    )

    main(config, context)
