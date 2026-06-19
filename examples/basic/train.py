from pydantic import BaseModel, Field

from stardust import RunContext, run


class ModelConfig(BaseModel):
    name: str
    # Field with a constraint that it must be greater than 0
    max_context_tokens: int = Field(gt=0)


class TrainConfig(BaseModel):
    seed: int = 42
    batch_size: int = Field(gt=0)
    lr: float = Field(gt=0)
    # notice the nested configs
    model: ModelConfig


def main(config: TrainConfig, context: RunContext) -> None:
    print(config)
    print(f"Run directory: {context.run_dir}")


if __name__ == "__main__":
    run(TrainConfig, main)