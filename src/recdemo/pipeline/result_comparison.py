from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ParsedReport:
    source: Path
    category_counts: dict[str, int]
    research_narrations: dict[str, str]


def _extract_section_lines(text: str, section_title: str) -> list[str]:
    lines = text.splitlines()
    collected: list[str] = []
    in_section = False
    header = f"## {section_title}"
    for line in lines:
        if line.startswith("## "):
            if line.strip() == header:
                in_section = True
                continue
            if in_section:
                break
        if in_section:
            collected.append(line)
    return collected


def parse_category_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    section_lines = _extract_section_lines(text, "観点別 該当研究数")
    for raw in section_lines:
        line = raw.strip()
        if not line.startswith("- "):
            continue
        # Format: - category: 12 件
        body = line[2:]
        if ":" not in body:
            continue
        name, rest = body.split(":", 1)
        name = name.strip()
        number_text = rest.strip().replace("件", "").strip()
        try:
            value = int(number_text)
        except ValueError:
            continue
        counts[name] = value
    return counts


def parse_report(path: Path) -> ParsedReport:
    text = path.read_text(encoding="utf-8")
    return ParsedReport(
        source=path,
        category_counts=parse_category_counts(text),
        research_narrations=parse_research_narrations(text),
    )


def parse_research_narrations(text: str) -> dict[str, str]:
    lines = _extract_section_lines(text, "研究ごとの語り")
    narrations: dict[str, str] = {}
    current_research: str | None = None
    in_code = False
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer, current_research
        if current_research is None:
            buffer = []
            return
        body = "\n".join(buffer).strip()
        if body:
            narrations[current_research] = body
        buffer = []

    for raw in lines:
        line = raw.rstrip("\n")
        if line.startswith("### "):
            flush()
            current_research = line[4:].strip()
            in_code = False
            continue

        if line.startswith("```"):
            if in_code:
                in_code = False
            elif line.strip() == "```text":
                in_code = True
            continue

        if in_code:
            buffer.append(line)

    flush()
    return narrations


def build_comparison_report(left: ParsedReport, right: ParsedReport) -> str:
    categories = sorted(set(left.category_counts) | set(right.category_counts))

    lines: list[str] = []
    lines.append("# 比較結果")
    lines.append(f"- A: {left.source}")
    lines.append(f"- B: {right.source}")
    lines.append("\n## 観点別 該当研究数 差分")
    lines.append("| 観点 | A | B | B-A |")
    lines.append("| --- | ---: | ---: | ---: |")

    for category in categories:
        a = left.category_counts.get(category, 0)
        b = right.category_counts.get(category, 0)
        lines.append(f"| {category} | {a} | {b} | {b - a:+d} |")

    lines.append("\n## 増減サマリ")
    increases = [(c, right.category_counts.get(c, 0) - left.category_counts.get(c, 0)) for c in categories]
    inc_only = [(c, d) for c, d in increases if d > 0]
    dec_only = [(c, d) for c, d in increases if d < 0]
    flat_only = [c for c, d in increases if d == 0]

    if inc_only:
        lines.append("- 増加:")
        for c, d in sorted(inc_only, key=lambda x: x[1], reverse=True):
            lines.append(f"  - {c}: +{d}")
    if dec_only:
        lines.append("- 減少:")
        for c, d in sorted(dec_only, key=lambda x: x[1]):
            lines.append(f"  - {c}: {d}")
    if flat_only:
        lines.append("- 変化なし:")
        for c in flat_only:
            lines.append(f"  - {c}")

    lines.append("\n## 研究ごとの語り比較")
    research_keys = sorted(set(left.research_narrations) | set(right.research_narrations))
    same_count = 0
    diff_count = 0
    only_a = 0
    only_b = 0

    for key in research_keys:
        a_text = left.research_narrations.get(key)
        b_text = right.research_narrations.get(key)
        if a_text is None:
            only_b += 1
            continue
        if b_text is None:
            only_a += 1
            continue
        if a_text.strip() == b_text.strip():
            same_count += 1
        else:
            diff_count += 1

    lines.append(f"- 一致: {same_count} 件")
    lines.append(f"- 差分あり: {diff_count} 件")
    lines.append(f"- Aのみ: {only_a} 件")
    lines.append(f"- Bのみ: {only_b} 件")

    for key in research_keys:
        a_text = left.research_narrations.get(key)
        b_text = right.research_narrations.get(key)
        if a_text is None and b_text is None:
            continue
        lines.append(f"\n### {key}")
        if a_text is None:
            lines.append("- ステータス: B のみ")
            lines.append("#### B")
            lines.append("```text")
            lines.append(b_text or "")
            lines.append("```")
            continue
        if b_text is None:
            lines.append("- ステータス: A のみ")
            lines.append("#### A")
            lines.append("```text")
            lines.append(a_text)
            lines.append("```")
            continue
        if a_text.strip() == b_text.strip():
            lines.append("- ステータス: 一致")
            continue

        lines.append("- ステータス: 差分あり")
        lines.append("#### A")
        lines.append("```text")
        lines.append(a_text)
        lines.append("```")
        lines.append("#### B")
        lines.append("```text")
        lines.append(b_text)
        lines.append("```")

    return "\n".join(lines)
