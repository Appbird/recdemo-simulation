from __future__ import annotations

import argparse
import json
from pathlib import Path

from .builders import render_prompt_template, strip_prompt_comment_lines


def parse_kv(items: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Invalid --var value: {item}. Use key=value format.")
        key, value = item.split("=", 1)
        out[key] = value
    return out


def load_vars(vars_json: Path | None, cli_vars: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    if vars_json is not None:
        raw = json.loads(vars_json.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("vars json must be an object")
        values.update({str(k): str(v) for k, v in raw.items()})
    values.update(parse_kv(cli_vars))
    return values


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render prompt templates quickly")
    parser.add_argument("--template", type=Path, required=True, help="Template file path")
    parser.add_argument(
        "--vars-json",
        type=Path,
        default=None,
        help="JSON file containing template variables",
    )
    parser.add_argument(
        "--var",
        action="append",
        default=[],
        help="Template variable in key=value format (repeatable)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    template_raw = args.template.read_text(encoding="utf-8")
    template = strip_prompt_comment_lines(template_raw)
    values = load_vars(args.vars_json, args.var)
    rendered = render_prompt_template(template, values)
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
