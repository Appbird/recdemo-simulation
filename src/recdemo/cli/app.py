from __future__ import annotations

import argparse
from pathlib import Path

from recdemo.core.paths import DEFAULT_CONFIG_PATH, DOTENV_PATH
from recdemo.runtime.env import load_dotenv_if_exists
from recdemo.runtime.logging import configure_logging

from .handlers import (
    handle_analysis,
    handle_analysis_step1,
    handle_analysis_step2,
    handle_analysis_step3,
    handle_eval,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Re:commend-demo simulation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    eval_parser = subparsers.add_parser("eval", help="Evaluate one paper/content input")
    analysis_parser = subparsers.add_parser(
        "analysis",
        help="Generate narration and categorize reasons by evaluation category",
    )
    step1_parser = subparsers.add_parser(
        "analysis-step1",
        help="Analysis step1 only: generate narration from paper/content input",
    )
    step2_parser = subparsers.add_parser(
        "analysis-step2",
        help="Analysis step2 only: extract bullet reasons from narration text",
    )
    step3_parser = subparsers.add_parser(
        "analysis-step3",
        help="Analysis step3 only: assign categories to reason bullets",
    )
    bullet_points_parser = subparsers.add_parser(
        "bullet-points",
        help="Alias of analysis-step2: extract bullet reasons from narration text",
    )
    categorize_parser = subparsers.add_parser(
        "categorize",
        help="Alias of analysis-step3: assign categories to reason bullets",
    )

    eval_parser.add_argument("input", type=Path, help="Path to input file (.pdf or text)")
    analysis_parser.add_argument("input", type=Path, help="Path to input PDF file or directory")
    step1_parser.add_argument("input", type=Path, help="Path to input PDF file")
    step2_parser.add_argument("input", type=Path, help="Path to narration text file")
    step3_parser.add_argument("input", type=Path, help="Path to reasons text file")
    bullet_points_parser.add_argument("input", type=Path, help="Path to narration text file")
    categorize_parser.add_argument("input", type=Path, help="Path to reasons text file")

    for target_parser in [
        eval_parser,
        analysis_parser,
        step1_parser,
        step2_parser,
        step3_parser,
        bullet_points_parser,
        categorize_parser,
    ]:
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

    analysis_parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Worker count for directory analysis (default: configs/default.toml [analysis].workers)",
    )
    analysis_parser.add_argument(
        "--input-kind",
        choices=["paper", "narrative"],
        default="paper",
        help="Input kind for analysis. paper: PDF input, narrative: narrative_*.txt input",
    )
    analysis_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output file path (e.g. result.md)",
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
        "analysis-step1": handle_analysis_step1,
        "analysis-step2": handle_analysis_step2,
        "analysis-step3": handle_analysis_step3,
        "bullet-points": handle_analysis_step2,
        "categorize": handle_analysis_step3,
    }
    return handlers[args.command](args)
