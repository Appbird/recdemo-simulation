from pathlib import Path

import tomllib


def load_default_model(config_path: Path) -> str:
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    try:
        model = data["base"]["llm_model"]
    except KeyError as exc:
        raise RuntimeError(f"Missing [base].llm_model in {config_path}") from exc

    if not isinstance(model, str) or not model.strip():
        raise RuntimeError(f"Invalid [base].llm_model in {config_path}")
    return model.strip()
