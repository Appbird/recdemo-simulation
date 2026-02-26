from __future__ import annotations

import argparse
from pathlib import Path

from recdemo.core.paths import DEFAULT_CONFIG_PATH, DOTENV_PATH
from recdemo.runtime.env import load_dotenv_if_exists
from recdemo.runtime.logging import configure_logging

from .handlers import handle_analysis, handle_eval


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Re:commend-demo simulation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    eval_parser = subparsers.add_parser("eval", help="Evaluate one paper/content input")
    analysis_parser = subparsers.add_parser(
        "analysis",
        help="Generate narration and categorize reasons by evaluation category",
    )

    for target_parser in [eval_parser, analysis_parser]:
        target_parser.add_argument("input", type=Path, help="Path to input file (.pdf or text)")
        target_parser.add_argument(
            "--llm",
            dest="llm",
            default=None,
            help="LLM model name (defaults to configs/default.toml [base].llm_model)",
        )
        target_parser.add_argument(
            "--config",
            dest="config_path",
            type=Path,
            default=DEFAULT_CONFIG_PATH,
            help="Path to config TOML for default model",
        )

    eval_parser.add_argument(
        "--no-log",
        action="store_true",
        help="Disable appending result records to outputs/eval_results.jsonl",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    args = parse_args(argv)
    load_dotenv_if_exists(DOTENV_PATH)

    handlers = {
        "eval": handle_eval,
        "analysis": handle_analysis,
    }
    return handlers[args.command](args)
