from pathlib import Path

from recdemo.core.types import EvalConfig
from recdemo.io.result_store import append_eval_result
from recdemo.llm.client import generate_response


def run_eval(cfg: EvalConfig, log_path: Path | None) -> str:
    output_text = generate_response(
        model=cfg.model,
        system_prompt=cfg.system_prompt,
        user_prompt=cfg.user_prompt,
    )

    if log_path is not None:
        append_eval_result(
            log_path=log_path,
            input_path=cfg.input_path,
            model=cfg.model,
            response=output_text,
        )

    return output_text
