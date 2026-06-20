# Basic example

This example shows the simplest Stardust workflow:

- load one config file
- validate it with pydantic
- apply command-line overrides
- create a run directory
- save the resolved config

Run from the repository root:

```bash
uv run examples/basic/train.py --config examples/basic/config.yaml
```

or:

```bash
uv run examples/basic/train.py --config examples/basic/config.json
```

as it works with all 3 file formats

Expected:

- the validated config is printed
- a run directory is created under `runs/` with timestamps
- the resolved config is saved as:
  - `config.resolved.json`
  - `config.resolved.yaml`

You can override values from the command line:

```bash
uv run examples/basic/train.py --config examples/basic/config.yaml lr=0.001 model.max_context_tokens=4096
```

Expected:

- `lr` becomes `0.001`
- `model.max_context_tokens` becomes `4096`
- the saved resolved config includes these final values

Notice that even if you don't explicit all the values in the `config.yaml` file, the run will save the default values in the pydantic config in `train.py`.


By default, Stardust uses simple config tracking.

This saves only the resolved config:

```text
runs/.../
  config.resolved.json
  config.resolved.yaml
```