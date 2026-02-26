from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from recdemo.io.content_loader import load_user_prompt_from_input

from .analysis_pipeline import assign_categories, extract_reasons, run_analysis_structured

logger = logging.getLogger(__name__)

INPUT_KIND_PAPER = "paper"
INPUT_KIND_NARRATIVE = "narrative"


@dataclass(frozen=True)
class CategorizedReason:
    categories: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class FileAnalysisResult:
    file_path: Path
    narration: str
    categorized_text: str
    items: tuple[CategorizedReason, ...]


@dataclass(frozen=True)
class FileAnalysisError:
    file_path: Path
    error_message: str


@dataclass(frozen=True)
class DirectoryAnalysisResult:
    root_dir: Path
    successes: tuple[FileAnalysisResult, ...]
    failures: tuple[FileAnalysisError, ...]
    category_names: tuple[str, ...]


def parse_category_names(category_definition: str) -> tuple[str, ...]:
    names: list[str] = []
    for raw_line in category_definition.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = re.match(r"^\d+\.\s*(.+)$", line)
        if match:
            names.append(match.group(1).strip())

    if "その他" not in names:
        names.append("その他")
    return tuple(names)


def discover_input_files(root_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith("."):
            continue
        if path.suffix.lower() != ".pdf":
            continue
        files.append(path)
    return files


def discover_narrative_files(root_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith("."):
            continue
        if path.suffix.lower() != ".txt":
            continue
        if not path.name.startswith("narrative_"):
            continue
        files.append(path)
    return files


def parse_categorized_lines(categorized_text: str) -> tuple[CategorizedReason, ...]:
    items: list[CategorizedReason] = []
    pattern = re.compile(r"^\[(.+)\]\s*(.+)$")
    for raw_line in categorized_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = pattern.match(line)
        if not match:
            continue
        category_text = match.group(1)
        reason_text = match.group(2).strip()
        categories = tuple(c.strip() for c in category_text.split(",") if c.strip())
        if not categories:
            categories = ("その他",)
        if reason_text:
            items.append(CategorizedReason(categories=categories, reason=reason_text))
    return tuple(items)


def _analyze_single_file(
    file_path: Path,
    model: str,
    system_prompt: str,
    category_definition: str,
    input_kind: str,
) -> FileAnalysisResult:
    if input_kind == INPUT_KIND_PAPER:
        source_content = load_user_prompt_from_input(file_path)
        narration, categorized_text = run_analysis_structured(
            model=model,
            system_prompt=system_prompt,
            source_content=source_content,
            category_definition=category_definition,
        )
    else:
        narration = file_path.read_text(encoding="utf-8")
        reasons = extract_reasons(
            model=model,
            narration=narration,
        )
        categorized_text = assign_categories(
            model=model,
            reasons=reasons,
            category_definition=category_definition,
            context_text=narration,
        )
    items = parse_categorized_lines(categorized_text)
    return FileAnalysisResult(
        file_path=file_path,
        narration=narration,
        categorized_text=categorized_text,
        items=items,
    )


def run_analysis_for_directory(
    root_dir: Path,
    model: str,
    system_prompt: str,
    category_definition: str,
    workers: int,
    input_kind: str,
) -> DirectoryAnalysisResult:
    if input_kind == INPUT_KIND_PAPER:
        files = discover_input_files(root_dir)
    else:
        files = discover_narrative_files(root_dir)
    successes: list[FileAnalysisResult] = []
    failures: list[FileAnalysisError] = []

    if not files:
        return DirectoryAnalysisResult(
            root_dir=root_dir,
            successes=tuple(),
            failures=tuple(),
            category_names=parse_category_names(category_definition),
        )

    logger.info("directory analysis: %d files discovered under %s", len(files), root_dir)

    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        future_map = {
            executor.submit(
                _analyze_single_file,
                file_path,
                model,
                system_prompt,
                category_definition,
                input_kind,
            ): file_path
            for file_path in files
        }
        for future in as_completed(future_map):
            file_path = future_map[future]
            try:
                result = future.result()
            except Exception as exc:
                failures.append(FileAnalysisError(file_path=file_path, error_message=str(exc)))
                logger.info("directory analysis failed: %s", file_path)
                continue
            successes.append(result)
            logger.info("directory analysis completed: %s", file_path)

    successes.sort(key=lambda r: str(r.file_path))
    failures.sort(key=lambda r: str(r.file_path))
    return DirectoryAnalysisResult(
        root_dir=root_dir,
        successes=tuple(successes),
        failures=tuple(failures),
        category_names=parse_category_names(category_definition),
    )


def format_directory_report(result: DirectoryAnalysisResult) -> str:
    from collections import defaultdict

    root_dir = result.root_dir
    per_research: dict[str, list[CategorizedReason]] = defaultdict(list)
    per_category: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    research_narrations: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for success in result.successes:
        rel = success.file_path.relative_to(root_dir)
        research_key = str(rel.parent) if str(rel.parent) != "." else rel.stem
        research_narrations[research_key].append((str(rel), success.narration))
        for item in success.items:
            per_research[research_key].append(item)
            for category in item.categories:
                per_category[category].append((research_key, str(rel), item.reason))

    lines: list[str] = []
    lines.append("# 集計結果")
    lines.append(
        f"- 対象フォルダ: {root_dir}\n"
        f"- 成功: {len(result.successes)} 件 / 失敗: {len(result.failures)} 件"
    )
    lines.append(f"- 該当研究数: {len(per_research)} 件")
    lines.append("\n## 目次")
    lines.append("- [観点別 該当研究数](#観点別-該当研究数)")
    lines.append("- [失敗ファイル](#失敗ファイル)")
    lines.append("- [研究ごとの語り](#研究ごとの語り)")
    lines.append("- [研究ごとの観点比較](#研究ごとの観点比較)")
    lines.append("- [観点ごとの評価比較](#観点ごとの評価比較)")

    lines.append("\n## 観点別 該当研究数")
    all_categories = list(result.category_names)
    for category in sorted(per_category):
        if category not in all_categories:
            all_categories.append(category)
    for category in all_categories:
        study_count = len({research_key for research_key, _, _ in per_category.get(category, [])})
        lines.append(f"- {category}: {study_count} 件")

    lines.append("\n## 失敗ファイル")
    if result.failures:
        for failure in result.failures:
            rel = failure.file_path.relative_to(root_dir)
            lines.append(f"- {rel}: {failure.error_message}")
    else:
        lines.append("- なし")

    lines.append("\n## 研究ごとの語り")
    for research in sorted(research_narrations):
        lines.append(f"\n### {research}")
        for rel_path, narration in research_narrations[research]:
            lines.append(f"- source: {rel_path}")
            lines.append("```text")
            lines.append(narration.strip())
            lines.append("```")

    lines.append("\n## 研究ごとの観点比較")
    for research in sorted(per_research):
        lines.append(f"\n### {research}")
        counts: dict[str, int] = defaultdict(int)
        for item in per_research[research]:
            for category in item.categories:
                counts[category] += 1
        if counts:
            summary = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
            lines.append(f"- 観点内訳: {summary}")
        for item in per_research[research]:
            category_label = ", ".join(item.categories)
            lines.append(f"- [{category_label}] {item.reason}")

    lines.append("\n## 観点ごとの評価比較")
    for category in all_categories:
        lines.append(f"\n### {category}")
        entries = per_category.get(category, [])
        study_count = len({research_key for research_key, _, _ in entries})
        lines.append(f"- 該当研究数: {study_count}")
        if not entries:
            lines.append("- 該当なし")
            continue
        for _, rel_path, reason in entries:
            lines.append(f"- ({rel_path}) {reason}")

    return "\n".join(lines)
