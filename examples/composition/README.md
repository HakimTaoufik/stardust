# Composition example

This example shows config composition with `defaults`.

The main config selects config groups:

```yaml
defaults:
  - model: olmo3_7b
  - data: trec2021
  - trainer: qlora
```

Run from the repository root:

```bash
uv run examples/composition/train.py --config examples/composition/configs/train.yaml
```

Expected:

- `model/olmo3_7b.yaml` is loaded
- `data/trec2021.yaml` is loaded
- `trainer/qlora.yaml` is loaded
- everything is merged into one final validated config

You can switch config groups from the command line:

```bash
uv run examples/composition/train.py --config examples/composition/configs/train.yaml model=llama_8b data=trec2022
```

Expected:

- `model/llama_8b.yaml` is used instead of `model/olmo3_7b.yaml`
- `data/trec2022.yaml` is used instead of `data/trec2021.yaml`

You can also override normal config values:

```bash
uv run examples/composition/train.py --config examples/composition/configs/train.yaml trainer.lr=5e-5 seed=123
```

Expected:

- the selected config groups stay the same
- `trainer.lr` becomes `5e-5`
- `seed` becomes `123`

You can combine both:

```bash
uv run examples/composition/train.py --config examples/composition/configs/train.yaml model=llama_8b trainer=full_finetune trainer.lr=2e-5
```

Expected:

- `model/llama_8b.yaml` is used
- `trainer/full_finetune.yaml` is used
- then `trainer.lr` is overridden to `2e-5`

This example uses custom run tracking:

```python
from stardust import RunTracking

run(
    TrainConfig,
    main,
    tracking=RunTracking(metadata=True, git=True, status=True, traceback=True),
)
```

This saves config files, metadata, git metadata, status, and failure tracebacks.

You can also use the built-in configurations:

```python
run(Config, main, tracking=RunTracking())
run(Config, main, tracking=RunTracking.reproducible())
run(Config, main, tracking=RunTracking.none())
```

Or choose exactly what to track through typed keyword arguments:

```python
run(Config, main, tracking=RunTracking(config=False, status=True))
```

Available tracking options:

- `config`
- `command`
- `metadata`
- `git`
- `packages`
- `status`
- `traceback`

The example also logs metrics through `RunContext`:

```python
context.log_metric("accuracy", 0.91)
context.log_metrics({"f1": 0.88, "loss": 0.12})
```

This creates `metrics.json` in the run directory.

The example also saves artifacts safely inside the run directory:

```python
summary_path = context.artifact_path("summary.txt")
summary_path.write_text("result", encoding="utf-8")
```

This creates `artifacts/summary.txt`.
