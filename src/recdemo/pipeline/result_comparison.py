from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ParsedReport:
    source: Path
    category_counts: dict[str, int]
    research_narrations: dict[str, str]
    research_points: dict[str, list[str]]


def _extract_categories_from_point(point: str) -> tuple[str, ...]:
    # Format: [カテゴリ] 理由 or [カテゴリ1, カテゴリ2] 理由
    if not point.startswith("[") or "]" not in point:
        return tuple()
    head = point[1 : point.index("]")]
    categories = tuple(c.strip() for c in head.split(",") if c.strip())
    return categories


def _collect_research_categories(points: list[str] | None) -> set[str]:
    if not points:
        return set()
    categories: set[str] = set()
    for point in points:
        categories.update(_extract_categories_from_point(point))
    return categories


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
        research_points=parse_research_points(text),
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


def parse_research_points(text: str) -> dict[str, list[str]]:
    lines = _extract_section_lines(text, "研究ごとの観点比較")
    points: dict[str, list[str]] = {}
    current_research: str | None = None

    for raw in lines:
        line = raw.strip()
        if line.startswith("### "):
            current_research = line[4:].strip()
            points.setdefault(current_research, [])
            continue
        if current_research is None:
            continue
        if not line.startswith("- ["):
            continue
        # Format: - [カテゴリ] 理由
        points[current_research].append(line[2:].strip())

    return points


def build_comparison_report(left: ParsedReport, right: ParsedReport) -> str:
    categories = sorted(set(left.category_counts) | set(right.category_counts))
    research_keys = sorted(set(left.research_points) | set(right.research_points))

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

    lines.append("\n## 研究ごとの観点増減（表）")
    lines.append("| 研究 | 増えた観点 (B-A) | 減った観点 (A-B) |")
    lines.append("| --- | --- | --- |")
    for key in research_keys:
        a_categories = _collect_research_categories(left.research_points.get(key))
        b_categories = _collect_research_categories(right.research_points.get(key))
        added = sorted(b_categories - a_categories)
        removed = sorted(a_categories - b_categories)
        added_text = ", ".join(added) if added else "-"
        removed_text = ", ".join(removed) if removed else "-"
        lines.append(f"| {key} | {added_text} | {removed_text} |")

    lines.append("\n## 研究ごとの評価観点比較")
    same_count = 0
    diff_count = 0
    only_a = 0
    only_b = 0

    for key in research_keys:
        a_points = left.research_points.get(key)
        b_points = right.research_points.get(key)
        if a_points is None:
            only_b += 1
            continue
        if b_points is None:
            only_a += 1
            continue
        if set(a_points) == set(b_points):
            same_count += 1
        else:
            diff_count += 1

    lines.append(f"- 一致: {same_count} 件")
    lines.append(f"- 差分あり: {diff_count} 件")
    lines.append(f"- Aのみ: {only_a} 件")
    lines.append(f"- Bのみ: {only_b} 件")

    for key in research_keys:
        a_points = left.research_points.get(key)
        b_points = right.research_points.get(key)
        if a_points is None and b_points is None:
            continue
        lines.append(f"\n### {key}")
        if a_points is None:
            lines.append("- ステータス: B のみ")
            for p in b_points or []:
                lines.append(f"- B: {p}")
            continue
        if b_points is None:
            lines.append("- ステータス: A のみ")
            for p in a_points:
                lines.append(f"- A: {p}")
            continue
        a_set = set(a_points)
        b_set = set(b_points)
        common = sorted(a_set & b_set)
        only_a_points = sorted(a_set - b_set)
        only_b_points = sorted(b_set - a_set)

        if not only_a_points and not only_b_points:
            lines.append("- ステータス: 一致")
            for p in common:
                lines.append(f"- 共通: {p}")
            continue

        lines.append("- ステータス: 差分あり")
        if common:
            lines.append("- 共通:")
            for p in common:
                lines.append(f"  - {p}")
        if only_a_points:
            lines.append("- Aのみ:")
            for p in only_a_points:
                lines.append(f"  - {p}")
        if only_b_points:
            lines.append("- Bのみ:")
            for p in only_b_points:
                lines.append(f"  - {p}")

    return "\n".join(lines)
