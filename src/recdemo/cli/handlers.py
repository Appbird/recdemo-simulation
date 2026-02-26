import argparse
import sys

from recdemo.core.config import load_default_model
from recdemo.core.paths import DEFAULT_LOG_PATH
from recdemo.core.types import EvalConfig
from recdemo.io.content_loader import load_user_prompt_from_input
from recdemo.pipeline.analysis_pipeline import run_analysis
from recdemo.pipeline.eval_pipeline import run_eval
from recdemo.prompt.builders import build_category_definition, build_system_prompt


def handle_eval(args: argparse.Namespace) -> int:
    input_path = args.input
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    model = args.llm or load_default_model(args.config_path)
    system_prompt = build_system_prompt()
    user_prompt = load_user_prompt_from_input(input_path)

    cfg = EvalConfig(
        model=model,
        input_path=input_path,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    log_path = None if args.no_log else DEFAULT_LOG_PATH

    try:
        output_text = run_eval(cfg, log_path=log_path)
    except Exception as exc:
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        return 1

    print(output_text)
    return 0


def handle_analysis(args: argparse.Namespace) -> int:
    input_path = args.input
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    model = args.llm or load_default_model(args.config_path)
    system_prompt = build_system_prompt()
    user_prompt = load_user_prompt_from_input(input_path)
    category_definition = build_category_definition()

    try:
        output_text = run_analysis(
            model=model,
            system_prompt=system_prompt,
            source_content=user_prompt,
            category_definition=category_definition,
        )
    except Exception as exc:
        print(f"Analysis failed: {exc}", file=sys.stderr)
        return 1

    print(output_text)
    return 0
