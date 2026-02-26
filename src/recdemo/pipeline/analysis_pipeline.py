import logging

from recdemo.llm.client import generate_response
from recdemo.prompt.builders import (
    build_analysis_system_prompt,
    build_assign_categories_prompt,
    build_extract_reasons_prompt,
)

logger = logging.getLogger(__name__)


def generate_narration(model: str, system_prompt: str, source_content: str) -> str:
    return generate_response(
        model=model,
        system_prompt=system_prompt,
        user_prompt=source_content,
    )


def extract_reasons(model: str, narration: str) -> str:
    system_prompt = build_analysis_system_prompt()
    user_prompt = build_extract_reasons_prompt(narration=narration)
    return generate_response(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )


def assign_categories(model: str, reasons: str, category_definition: str, context_text: str) -> str:
    system_prompt = build_analysis_system_prompt()
    user_prompt = build_assign_categories_prompt(
        reasons=reasons,
        category_definition=category_definition,
        context_text=context_text,
    )
    return generate_response(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )


def run_analysis(model: str, system_prompt: str, source_content: str, category_definition: str) -> str:
    narration, categorized_reasons = run_analysis_structured(
        model=model,
        system_prompt=system_prompt,
        source_content=source_content,
        category_definition=category_definition,
    )
    return f"# 語りの内容\n{narration}\n\n# 評価観点\n{categorized_reasons}".strip()


def run_analysis_structured(
    model: str,
    system_prompt: str,
    source_content: str,
    category_definition: str,
) -> tuple[str, str]:
    logger.info("analysis step 1/3: generating narrative")
    narration = generate_narration(
        model=model,
        system_prompt=system_prompt,
        source_content=source_content,
    )
    logger.info("analysis step 1/3 completed")

    logger.info("analysis step 2/3: extracting reasons")
    reasons = extract_reasons(
        model=model,
        narration=narration,
    )
    logger.info("analysis step 2/3 completed")

    logger.info("analysis step 3/3: assigning categories")
    categorized_reasons = assign_categories(
        model=model,
        reasons=reasons,
        category_definition=category_definition,
        context_text=narration,
    )
    logger.info("analysis step 3/3 completed")

    return narration, categorized_reasons
