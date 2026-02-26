#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def normalize_markdown(text: str) -> str:
    out: list[str] = []
    in_fence = False

    for raw in text.splitlines():
        line = raw.rstrip("\n")

        if line.startswith("```"):
            in_fence = not in_fence
            continue

        if in_fence and line.startswith("### "):
            title = line[4:].strip()
            if out and out[-1] != "":
                out.append("")
            out.append(f"**{title}**")
            out.append("")
            continue

        out.append(line)

    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert fenced text blocks into plain paragraphs and promote in-fence h3 to bold lines."
    )
    parser.add_argument("input", type=Path, help="Input markdown file")
    parser.add_argument("--output", type=Path, default=None, help="Optional output path")
    parser.add_argument("--in-place", action="store_true", help="Overwrite input file")
    args = parser.parse_args()

    input_path: Path = args.input
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path = args.output
    if args.in_place:
        output_path = input_path
    if output_path is None:
        raise ValueError("Specify either --output or --in-place")

    converted = normalize_markdown(input_path.read_text(encoding="utf-8"))
    output_path.write_text(converted, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
