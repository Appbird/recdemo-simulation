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


def load_default_analysis_input_kind(config_path: Path, fallback: str = "paper") -> str:
    data = _load_config_toml(config_path)
    analysis = data.get("analysis")
    if analysis is None:
        return fallback
    if not isinstance(analysis, dict):
        raise RuntimeError(f"Invalid [analysis] section in {config_path}")

    input_kind = analysis.get("input_kind", fallback)
    if input_kind not in {"paper", "narrative"}:
        raise RuntimeError(f"Invalid [analysis].input_kind in {config_path}")
    return input_kind


def load_default_analysis_output_path(config_path: Path) -> Path | None:
    data = _load_config_toml(config_path)
    analysis = data.get("analysis")
    if analysis is None:
        return None
    if not isinstance(analysis, dict):
        raise RuntimeError(f"Invalid [analysis] section in {config_path}")

    output = analysis.get("output", "")
    if not isinstance(output, str):
        raise RuntimeError(f"Invalid [analysis].output in {config_path}")
    output = output.strip()
    if not output:
        return None
    return Path(output)


def _load_compare_section(config_path: Path) -> dict | None:
    data = _load_config_toml(config_path)
    compare = data.get("compare")
    if compare is None:
        return None
    if not isinstance(compare, dict):
        raise RuntimeError(f"Invalid [compare] section in {config_path}")
    return compare


def load_default_compare_left_path(config_path: Path) -> Path | None:
    compare = _load_compare_section(config_path)
    if compare is None:
        return None
    left = compare.get("left", "")
    if not isinstance(left, str):
        raise RuntimeError(f"Invalid [compare].left in {config_path}")
    left = left.strip()
    if not left:
        return None
    return Path(left)


def load_default_compare_right_path(config_path: Path) -> Path | None:
    compare = _load_compare_section(config_path)
    if compare is None:
        return None
    right = compare.get("right", "")
    if not isinstance(right, str):
        raise RuntimeError(f"Invalid [compare].right in {config_path}")
    right = right.strip()
    if not right:
        return None
    return Path(right)


def load_default_compare_output_path(config_path: Path) -> Path | None:
    compare = _load_compare_section(config_path)
    if compare is None:
        return None
    output = compare.get("output", "")
    if not isinstance(output, str):
        raise RuntimeError(f"Invalid [compare].output in {config_path}")
    output = output.strip()
    if not output:
        return None
    return Path(output)


def load_default_compare_left_name(config_path: Path, fallback: str = "A") -> str:
    compare = _load_compare_section(config_path)
    if compare is None:
        return fallback
    left_name = compare.get("left_name", fallback)
    if not isinstance(left_name, str) or not left_name.strip():
        raise RuntimeError(f"Invalid [compare].left_name in {config_path}")
    return left_name.strip()


def load_default_compare_right_name(config_path: Path, fallback: str = "B") -> str:
    compare = _load_compare_section(config_path)
    if compare is None:
        return fallback
    right_name = compare.get("right_name", fallback)
    if not isinstance(right_name, str) or not right_name.strip():
        raise RuntimeError(f"Invalid [compare].right_name in {config_path}")
    return right_name.strip()
