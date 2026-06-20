from pydantic import BaseModel, Field

from stardust import RunContext, run


class ModelConfig(BaseModel):
    name: str
    max_context_tokens: int = Field(gt=0)


class DataConfig(BaseModel):
    name: str
    path: str


class TrainerConfig(BaseModel):
    method: str
    lr: float = Field(gt=0)
    batch_size: int = Field(gt=0)


class TrainConfig(BaseModel):
    seed: int = 42
    model: ModelConfig
    data: DataConfig
    trainer: TrainerConfig


def main(config: TrainConfig, context: RunContext) -> None:
    print(config)
    print(f"Run directory: {context.run_dir}")

    # ML pipeline would go here along side everything else


if __name__ == "__main__":
    run(TrainConfig, main)
