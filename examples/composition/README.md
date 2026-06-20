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

This example uses full run tracking:

```python
run(TrainConfig, main, tracking="full")
```

This saves:

```text
runs/.../
  config.resolved.json
  config.resolved.yaml
  command.txt
  metadata.json
```

`command.txt` contains the command used to start the run.

`metadata.json` contains basic run metadata, including:

- start time
- Python version
- platform
- config path
- CLI overrides