from pathlib import Path

import tomllib


def _load_config_toml(config_path: Path) -> dict:
    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"Invalid config format in {config_path}")
    return data


def load_default_model(config_path: Path) -> str:
    data = _load_config_toml(config_path)
    try:
        model = data["base"]["llm_model"]
    except KeyError as exc:
        raise RuntimeError(f"Missing [base].llm_model in {config_path}") from exc

    if not isinstance(model, str) or not model.strip():
        raise RuntimeError(f"Invalid [base].llm_model in {config_path}")
    return model.strip()


def load_default_analysis_workers(config_path: Path, fallback: int = 4) -> int:
    data = _load_config_toml(config_path)
    analysis = data.get("analysis")
    if analysis is None:
        return fallback
    if not isinstance(analysis, dict):
        raise RuntimeError(f"Invalid [analysis] section in {config_path}")

    workers = analysis.get("workers", fallback)
    if not isinstance(workers, int) or workers <= 0:
        raise RuntimeError(f"Invalid [analysis].workers in {config_path}")
    return workers
