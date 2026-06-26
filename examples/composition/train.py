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

    # ML pipeline would go here
    accuracy = 0.91
    f1 = 0.88

    context.log_metric("accuracy", accuracy)
    context.log_metrics(
        {
            "f1": f1,
            "loss": 0.12,
        }
    )

    summary_path = context.artifact_path("summary.txt")
    summary_path.write_text(
        f"model={config.model.name}\naccuracy={accuracy}\nf1={f1}\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    run(
        TrainConfig,
        main,
        tracking=["config", "metadata", "git", "status", "traceback"],
    )
