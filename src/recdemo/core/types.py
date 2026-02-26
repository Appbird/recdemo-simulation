from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EvalConfig:
    model: str
    input_path: Path
    system_prompt: str
    user_prompt: str
