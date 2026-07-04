import json
import platform
import shlex
import subprocess
import sys
import traceback
from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields
from datetime import datetime
from importlib.metadata import PackageNotFoundError, distributions, version
from pathlib import Path
from typing import TypeVar

import yaml
from pydantic import BaseModel

from stardust.core import load_config

ConfigT = TypeVar("ConfigT", bound=BaseModel)
MetricValue = int | float | str | bool | None


@dataclass(frozen=True, slots=True, kw_only=True)
class RunTracking:
    """select the files and runtime information to save for a run"""

    config: bool = True
    command: bool = False
    metadata: bool = False
    git: bool = False
    packages: bool = False
    status: bool = False
    traceback: bool = False

    def __post_init__(self) -> None:
        for option in fields(self):
            if not isinstance(getattr(self, option.name), bool):
                raise TypeError(f"RunTracking.{option.name} must be a bool")

    @classmethod
    def reproducible(
        cls,
        *,
        config: bool = True,
        command: bool = True,
        metadata: bool = True,
        git: bool = True,
        packages: bool = True,
        status: bool = True,
        traceback: bool = True,
    ) -> "RunTracking":
        """track everything needed to inspect and reproduce a run"""
        return cls(
            config=config,
            command=command,
            metadata=metadata,
            git=git,
            packages=packages,
            status=status,
            traceback=traceback,
        )

    @classmethod
    def none(cls) -> "RunTracking":
        """disable all built-in run tracking"""
        return cls(
            config=False,
            command=False,
            metadata=False,
            git=False,
            packages=False,
            status=False,
            traceback=False,
        )

    def _enabled_names(self) -> list[str]:
        return [option.name for option in fields(self) if getattr(self, option.name)]


_DEFAULT_TRACKING = RunTracking()


@dataclass
class RunContext:
    """context object that is passed to the main function of a stardust run"""

    run_dir: Path
    config_path: Path
    overrides: list[str]

    @property
    def metrics_path(self) -> Path:
        """path to the metrics file for this run"""
        return self.run_dir / "metrics.json"

    @property
    def artifacts_dir(self) -> Path:
        """directory where artifacts for this run should be saved"""
        path = self.run_dir / "artifacts"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def log_metric(self, name: str, value: MetricValue) -> None:
        """log a single metric to metrics.json"""
        validate_metric(name, value)

        metrics = load_metrics(self.metrics_path)
        metrics[name] = value
        save_json(self.metrics_path, metrics)

    def log_metrics(self, metrics: Mapping[str, MetricValue]) -> None:
        """log multiple metrics to metrics.json"""
        for name, value in metrics.items():
            validate_metric(name, value)

        current_metrics = load_metrics(self.metrics_path)
        current_metrics.update(metrics)
        save_json(self.metrics_path, current_metrics)

    def artifact_path(self, path: str | Path) -> Path:
        """return a safe path inside the artifacts directory"""
        artifact_path = Path(path)

        if artifact_path.is_absolute():
            raise ValueError("artifact path must be relative")

        if ".." in artifact_path.parts:
            raise ValueError("artifact path must not contain '..'")

        full_path = self.artifacts_dir / artifact_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        return full_path


def create_run_dir() -> Path:
    now = datetime.now()
    run_dir = Path("runs") / now.strftime("%Y-%m-%d") / now.strftime("%H-%M-%S-%f")
    run_dir.mkdir(parents=True)
    return run_dir


def save_json(path: Path, data: object) -> None:
    """save data as pretty json"""
    try:
        content = json.dumps(data, indent=2, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError("data must be JSON serializable") from error

    path.write_text(content + "\n", encoding="utf-8")


def validate_metric(name: str, value: MetricValue) -> None:
    """validate a metric name and value"""
    if not name:
        raise ValueError("metric name must not be empty")

    if not isinstance(value, int | float | str | bool) and value is not None:
        raise TypeError("metric value must be an int, float, str, bool, or None")


def load_metrics(path: Path) -> dict[str, MetricValue]:
    """load metrics from metrics.json if it exists"""
    if not path.exists():
        return {}

    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError("metrics.json must contain a JSON object")

    for name, value in data.items():
        validate_metric(name, value)

    return data


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


def get_stardust_version() -> str | None:
    """return the installed stardust package version if available"""
    try:
        return version("stardust-config")
    except PackageNotFoundError:
        return None


def run_command(command: list[str]) -> str | None:
    """run a command and return stdout, or None if it fails"""
    try:
        result = subprocess.run(command, capture_output=True, check=True, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    return result.stdout.strip()


def save_metadata(run_dir: Path, config_path: Path, overrides: list[str], tracking: RunTracking) -> None:
    """save basic metadata about the run"""
    metadata = {
        "started_at": datetime.now().astimezone().isoformat(),
        "run_dir": str(run_dir),
        "working_dir": str(Path.cwd()),
        "config_path": str(config_path),
        "overrides": overrides,
        "tracking": tracking._enabled_names(),
        "python_version": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "hostname": platform.node(),
        "stardust_version": get_stardust_version(),
    }

    metadata_path = run_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def save_git_metadata(run_dir: Path) -> None:
    """save git metadata if the run is inside a git repository"""
    git_root = run_command(["git", "rev-parse", "--show-toplevel"])

    metadata: dict[str, bool | str | None] = {
        "available": git_root is not None,
    }

    if git_root is not None:
        status = run_command(["git", "status", "--porcelain"])

        metadata.update(
            {
                "root": git_root,
                "branch": run_command(["git", "branch", "--show-current"]),
                "commit": run_command(["git", "rev-parse", "HEAD"]),
                "is_dirty": bool(status),
            }
        )

    git_path = run_dir / "git.json"
    git_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def save_packages(run_dir: Path) -> None:
    """save installed python packages in the current environment"""
    packages: list[dict[str, str]] = []

    for package in distributions():
        name = package.metadata.get("Name")

        if name is None:
            continue

        packages.append(
            {
                "name": name,
                "version": package.version,
            }
        )

    packages.sort(key=lambda package: package["name"].lower())

    packages_path = run_dir / "packages.json"
    packages_path.write_text(json.dumps(packages, indent=2), encoding="utf-8")


def save_status(run_dir: Path, status: str, started_at: datetime, error: BaseException | None = None) -> None:
    """save the current run status"""
    data: dict[str, str | float] = {
        "status": status,
        "started_at": started_at.isoformat(),
    }

    if status in {"finished", "failed"}:
        ended_at = datetime.now().astimezone()
        data["ended_at"] = ended_at.isoformat()
        data["duration_seconds"] = (ended_at - started_at).total_seconds()

    if error is not None:
        data["error_type"] = type(error).__name__
        data["error_message"] = str(error)

    status_path = run_dir / "status.json"
    status_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def save_traceback(run_dir: Path) -> None:
    """save the traceback of a failed run"""
    traceback_path = run_dir / "traceback.txt"
    traceback_path.write_text(traceback.format_exc(), encoding="utf-8")


def save_run_snapshot(
    config: BaseModel,
    run_dir: Path,
    config_path: Path,
    overrides: list[str],
    tracking: RunTracking,
) -> None:
    """save the selected run files"""
    if tracking.config:
        save_resolved_config(config, run_dir)
    if tracking.command:
        save_command(run_dir)
    if tracking.metadata:
        save_metadata(run_dir, config_path, overrides, tracking)
    if tracking.git:
        save_git_metadata(run_dir)
    if tracking.packages:
        save_packages(run_dir)


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


def run(
    config_type: type[ConfigT],
    main: Callable[[ConfigT, RunContext], None],
    tracking: RunTracking | None = _DEFAULT_TRACKING,
) -> None:
    """
    main entry point for stardust.

    Args:
        config_type: the pydantic model class to use for validation
        main: the main function to run, which takes the validated config and a RunContext
        tracking: typed settings for files and runtime information to save
    """
    started_at = datetime.now().astimezone()
    
    if tracking is None:
        tracking = RunTracking.none()
    
    if not None and not isinstance(tracking, RunTracking):
        raise TypeError("tracking must be a RunTracking instance")

    config_path, overrides = parse_args()
    config = load_config(config_type, config_path, overrides)

    run_dir = create_run_dir()
    save_run_snapshot(config, run_dir, config_path, overrides, tracking)

    context = RunContext(
        run_dir=run_dir,
        config_path=config_path,
        overrides=overrides,
    )

    if tracking.status:
        save_status(run_dir, "running", started_at)

    try:
        main(config, context)
    except Exception as error:
        if tracking.status:
            save_status(run_dir, "failed", started_at, error)
        if tracking.traceback:
            save_traceback(run_dir)
        raise

    if tracking.status:
        save_status(run_dir, "finished", started_at)
