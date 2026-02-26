from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class ParsedReport:
    source: Path
    category_counts: dict[str, int]
    research_narrations: dict[str, str]
    research_points: dict[str, list[str]]


def _anchor_slug(text: str) -> str:
    slug = text.strip().lower().replace(" ", "-")
    allowed = []
    for ch in slug:
        if ch.isalnum() or ch in {"-", "_"} or ord(ch) > 127:
            allowed.append(ch)
    return "".join(allowed)


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


def _extract_reason_text(point: str) -> str:
    if point.startswith("[") and "]" in point:
        return point[point.index("]") + 1 :].strip()
    return point.strip()


def _sample_reason_for_category(points: list[str], category: str) -> str:
    for point in points:
        if category in _extract_categories_from_point(point):
            return _extract_reason_text(point)
    return "-"


def _format_table_cell(text: str, max_len: int = 120) -> str:
    # Remove parenthetical asides from table samples for readability.
    normalized = re.sub(r"\([^)]*\)", "", text)
    normalized = re.sub(r"（[^）]*）", "", normalized)
    normalized = " ".join(normalized.split())
    if len(normalized) > max_len:
        normalized = normalized[: max_len - 1].rstrip() + "…"
    return normalized.replace("|", "\\|")


def _bold_category_prefix(point: str) -> str:
    # Format: [カテゴリ] 理由 or [カテゴリ1, カテゴリ2] 理由
    if not point.startswith("[") or "]" not in point:
        return point
    end = point.index("]")
    categories = point[1:end].strip()
    reason = point[end + 1 :].strip()
    return f"[**{categories}**] {reason}"


def _study_link(study: str) -> str:
    return f"[{study}](#{_anchor_slug(study)})"


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


def build_comparison_report(
    left: ParsedReport,
    right: ParsedReport,
    left_name: str = "A",
    right_name: str = "B",
) -> str:
    categories = sorted(set(left.category_counts) | set(right.category_counts))
    research_keys = sorted(set(left.research_points) | set(right.research_points))
    left_category_to_studies: dict[str, set[str]] = {category: set() for category in categories}
    right_category_to_studies: dict[str, set[str]] = {category: set() for category in categories}
    for key in research_keys:
        left_categories = _collect_research_categories(left.research_points.get(key, []))
        right_categories = _collect_research_categories(right.research_points.get(key, []))
        for category in left_categories:
            left_category_to_studies.setdefault(category, set()).add(key)
        for category in right_categories:
            right_category_to_studies.setdefault(category, set()).add(key)

    lines: list[str] = []
    lines.append("# 比較結果")
    lines.append(f"- {left_name}: {left.source}")
    lines.append(f"- {right_name}: {right.source}")
    lines.append("\n## 目次")
    lines.append("- [観点別 該当研究数 差分](#観点別-該当研究数-差分)")
    lines.append("- [観点別 研究対応一覧](#観点別-研究対応一覧)")
    lines.append("- [研究ごとの観点比較表](#研究ごとの観点比較表)")
    lines.append("- [研究ごとの差分詳細](#研究ごとの差分詳細)")
    for key in research_keys:
        lines.append(f"- [研究: {key}](#{_anchor_slug(key)})")

    lines.append("\n## 観点別 該当研究数 差分")
    lines.append(f"| 観点 | {left_name} | {right_name} | {right_name}-{left_name} |")
    lines.append("| --- | ---: | ---: | ---: |")

    category_rows: list[tuple[str, int, int, int]] = []
    for category in categories:
        a = left.category_counts.get(category, 0)
        b = right.category_counts.get(category, 0)
        diff = b - a
        category_rows.append((category, a, b, diff))
    category_rows.sort(key=lambda row: (-row[3], row[0]))
    for category, a, b, diff in category_rows:
        lines.append(f"| **{category}** | {a} | {b} | {diff:+d} |")

    lines.append("\n## 観点別 研究対応一覧")
    lines.append(
        f"| 観点 | {left_name}/{right_name} 両方で該当 | {left_name}でのみ該当 | {right_name}でのみ該当 |"
    )
    lines.append("| --- | --- | --- | --- |")
    for category in [row[0] for row in category_rows]:
        a_studies = sorted(left_category_to_studies.get(category, set()))
        b_studies = sorted(right_category_to_studies.get(category, set()))
        common_studies = sorted(set(a_studies) & set(b_studies))
        only_a_studies = sorted(set(a_studies) - set(b_studies))
        only_b_studies = sorted(set(b_studies) - set(a_studies))
        row_count = max(len(common_studies), len(only_a_studies), len(only_b_studies), 1)
        for idx in range(row_count):
            category_cell = f"**{category}**" if idx == 0 else "^"
            common_cell = _study_link(common_studies[idx]) if idx < len(common_studies) else "-"
            only_a_cell = _study_link(only_a_studies[idx]) if idx < len(only_a_studies) else "-"
            only_b_cell = _study_link(only_b_studies[idx]) if idx < len(only_b_studies) else "-"
            lines.append(f"| {category_cell} | {common_cell} | {only_a_cell} | {only_b_cell} |")
        lines.append("| --- | --- | --- | --- |")

    lines.append("\n## 研究ごとの観点比較表")
    lines.append(f"| 研究 | {left_name}にしかない観点 | {right_name}にしかない観点 |")
    lines.append("| --- | --- | --- |")
    for key in research_keys:
        a_points_raw = left.research_points.get(key, [])
        b_points_raw = right.research_points.get(key, [])
        a_categories = _collect_research_categories(a_points_raw)
        b_categories = _collect_research_categories(b_points_raw)
        only_a_categories = sorted(a_categories - b_categories)
        only_b_categories = sorted(b_categories - a_categories)
        row_count = max(len(only_a_categories), len(only_b_categories), 1)
        for idx in range(row_count):
            study_cell = f"[{key}](#{_anchor_slug(key)})" if idx == 0 else "^"
            if idx < len(only_a_categories):
                a_category = only_a_categories[idx]
                a_sample = _sample_reason_for_category(a_points_raw, a_category)
                only_a_text = f"**{a_category}**: {_format_table_cell(a_sample)}"
            else:
                only_a_text = "-"
            if idx < len(only_b_categories):
                b_category = only_b_categories[idx]
                b_sample = _sample_reason_for_category(b_points_raw, b_category)
                only_b_text = f"**{b_category}**: {_format_table_cell(b_sample)}"
            else:
                only_b_text = "-"
            lines.append(f"| {study_cell} | {only_a_text} | {only_b_text} |")
        lines.append("| --- | --- | --- |")

    lines.append("\n## 研究ごとの差分詳細")
    for key in research_keys:
        a_points = sorted(set(left.research_points.get(key, [])))
        b_points = sorted(set(right.research_points.get(key, [])))
        a_set = set(a_points)
        b_set = set(b_points)
        only_a_points = sorted(a_set - b_set)
        only_b_points = sorted(b_set - a_set)

        lines.append(f"\n### {key}")
        lines.append(f"\n#### {left_name}の主張")
        if a_points:
            for p in a_points:
                lines.append(f"- {_bold_category_prefix(p)}")
        else:
            lines.append("- なし")
        lines.append(f"\n#### {right_name}の主張")
        if b_points:
            for p in b_points:
                lines.append(f"- {_bold_category_prefix(p)}")
        else:
            lines.append("- なし")
        lines.append(f"\n#### {left_name}にしかない主張")
        if only_a_points:
            for p in only_a_points:
                lines.append(f"- {_bold_category_prefix(p)}")
        else:
            lines.append("- なし")
        lines.append(f"\n#### {right_name}にしかない主張")
        if only_b_points:
            for p in only_b_points:
                lines.append(f"- {_bold_category_prefix(p)}")
        else:
            lines.append("- なし")

    return "\n".join(lines)
