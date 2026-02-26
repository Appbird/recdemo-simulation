import argparse
import sys
from pathlib import Path

from recdemo.core.config import (
    load_default_analysis_input_kind,
    load_default_analysis_output_path,
    load_default_analysis_workers,
    load_default_model,
)
from recdemo.core.paths import DEFAULT_LOG_PATH
from recdemo.core.types import EvalConfig
from recdemo.io.content_loader import load_user_prompt_from_input
from recdemo.pipeline.analysis_pipeline import (
    assign_categories,
    extract_reasons,
    generate_narration,
    run_analysis,
)
from recdemo.pipeline.batch_analysis import (
    INPUT_KIND_NARRATIVE,
    INPUT_KIND_PAPER,
    format_directory_report,
    run_analysis_for_directory,
)
from recdemo.pipeline.eval_pipeline import run_eval
from recdemo.pipeline.result_comparison import (
    build_comparison_report,
    parse_report,
)
from recdemo.prompt.builders import (
    build_category_definition,
    build_system_prompt,
)


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
    category_definition = build_category_definition()
    output_path = args.output or load_default_analysis_output_path(args.config_path)
    input_kind = args.input_kind or load_default_analysis_input_kind(args.config_path)

    def _print_compact_done(message_path: Path, content: str) -> None:
        print(f"DONE! Output written to: {message_path}")
        if content.startswith("# 集計結果"):
            lines = content.splitlines()
            summary_lines: list[str] = []
            for line in lines[1:]:
                if line.startswith("## "):
                    break
                if line.strip():
                    summary_lines.append(line)
            if summary_lines:
                print("\n".join(summary_lines))

    if input_path.is_dir():
        workers = args.workers
        if workers is None:
            workers = load_default_analysis_workers(args.config_path)
        try:
            batch_result = run_analysis_for_directory(
                root_dir=input_path,
                model=model,
                system_prompt=system_prompt,
                category_definition=category_definition,
                workers=workers,
                input_kind=input_kind,
            )
            report = format_directory_report(batch_result)
        except Exception as exc:
            print(f"Analysis failed: {exc}", file=sys.stderr)
            return 1
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report, encoding="utf-8")
            _print_compact_done(output_path, report)
        else:
            print(report)
        return 0

    if input_kind == INPUT_KIND_PAPER:
        if input_path.suffix.lower() != ".pdf":
            print(f"Analysis input must be a PDF file for input-kind=paper: {input_path}", file=sys.stderr)
            return 1
    elif input_kind == INPUT_KIND_NARRATIVE:
        if input_path.suffix.lower() != ".txt" or not input_path.name.startswith("narrative_"):
            print(
                "Analysis input must be a narrative text file (narrative_*.txt) "
                f"for input-kind=narrative: {input_path}",
                file=sys.stderr,
            )
            return 1
    else:
        print(f"Unsupported input kind: {input_kind}", file=sys.stderr)
        return 1

    try:
        if input_kind == INPUT_KIND_PAPER:
            user_prompt = load_user_prompt_from_input(input_path)
            output_text = run_analysis(
                model=model,
                system_prompt=system_prompt,
                source_content=user_prompt,
                category_definition=category_definition,
            )
        else:
            narration = input_path.read_text(encoding="utf-8")
            reasons = extract_reasons(
                model=model,
                narration=narration,
            )
            categorized = assign_categories(
                model=model,
                reasons=reasons,
                category_definition=category_definition,
            )
            output_text = f"# 語りの内容\n{narration}\n\n# 評価観点\n{categorized}".strip()
    except Exception as exc:
        print(f"Analysis failed: {exc}", file=sys.stderr)
        return 1

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_text, encoding="utf-8")
        _print_compact_done(output_path, output_text)
    else:
        print(output_text)
    return 0


def _read_text_file(input_path: Path, error_prefix: str) -> str | None:
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return None
    try:
        return input_path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"{error_prefix}: {exc}", file=sys.stderr)
        return None


def handle_analysis_step1(args: argparse.Namespace) -> int:
    input_path = args.input
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1
    if input_path.suffix.lower() != ".pdf":
        print(f"Analysis step1 input must be a PDF file: {input_path}", file=sys.stderr)
        return 1

    model = args.llm or load_default_model(args.config_path)
    system_prompt = build_system_prompt()
    source_content = load_user_prompt_from_input(input_path)

    try:
        narration = generate_narration(
            model=model,
            system_prompt=system_prompt,
            source_content=source_content,
        )
    except Exception as exc:
        print(f"Analysis step1 failed: {exc}", file=sys.stderr)
        return 1

    print(narration)
    return 0


def handle_analysis_step2(args: argparse.Namespace) -> int:
    input_path = args.input
    narration = _read_text_file(input_path, "Failed to read narration file")
    if narration is None:
        return 1

    model = args.llm or load_default_model(args.config_path)
    try:
        reasons = extract_reasons(
            model=model,
            narration=narration,
        )
    except Exception as exc:
        print(f"Analysis step2 failed: {exc}", file=sys.stderr)
        return 1

    print(reasons)
    return 0


def handle_analysis_step3(args: argparse.Namespace) -> int:
    input_path = args.input
    reasons = _read_text_file(input_path, "Failed to read reasons file")
    if reasons is None:
        return 1

    model = args.llm or load_default_model(args.config_path)
    category_definition = build_category_definition()

    try:
        categorized = assign_categories(
            model=model,
            reasons=reasons,
            category_definition=category_definition,
        )
    except Exception as exc:
        print(f"Analysis step3 failed: {exc}", file=sys.stderr)
        return 1

    print(categorized)
    return 0


def handle_compare_results(args: argparse.Namespace) -> int:
    left_path: Path = args.left
    right_path: Path = args.right
    output_path: Path | None = args.output

    for p in [left_path, right_path]:
        if not p.exists():
            print(f"Input file not found: {p}", file=sys.stderr)
            return 1

    try:
        left = parse_report(left_path)
        right = parse_report(right_path)
        content = build_comparison_report(left, right)
    except Exception as exc:
        print(f"Compare failed: {exc}", file=sys.stderr)
        return 1

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        print(f"DONE! Output written to: {output_path}")
    else:
        print(content)
    return 0
