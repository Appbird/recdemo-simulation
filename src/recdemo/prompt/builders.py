import re
from pathlib import Path

from recdemo.core.paths import (
    CATEGORY_DEFINITION_PATH,
    REC_DEMO_EXPLANATION_PATH,
    SYSTEM_INSTRUCTION_PATH,
)


class PromptTemplateError(RuntimeError):
    pass


def strip_prompt_comment_lines(text: str) -> str:
    kept_lines = [line for line in text.splitlines() if not line.startswith("% ")]
    return "\n".join(kept_lines).strip()


def render_prompt_template(template: str, variables: dict[str, str]) -> str:
    pattern = re.compile(r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

    def replace(match: re.Match[str]) -> str:
        var_name = match.group(1)
        if var_name not in variables:
            raise PromptTemplateError(f"Missing template variable: {var_name}")
        return variables[var_name]

    return pattern.sub(replace, template)


def _read_prompt_file(primary: Path, legacy: Path) -> str:
    if primary.exists():
        return primary.read_text(encoding="utf-8")
    if legacy.exists():
        return legacy.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Prompt file not found: {primary}")


def build_system_prompt() -> str:
    system_template_raw = _read_prompt_file(
        SYSTEM_INSTRUCTION_PATH,
        SYSTEM_INSTRUCTION_PATH.parent.parent / "system-instruction.txt",
    )
    system_template = strip_prompt_comment_lines(system_template_raw)

    rec_demo_raw = _read_prompt_file(
        REC_DEMO_EXPLANATION_PATH,
        REC_DEMO_EXPLANATION_PATH.parent.parent / "rec-demo-explanation.txt",
    )
    rec_demo_text = strip_prompt_comment_lines(rec_demo_raw)

    return render_prompt_template(
        system_template,
        {
            "rec_demo_explanation": rec_demo_text,
        },
    )


def build_category_definition() -> str:
    category_raw = _read_prompt_file(
        CATEGORY_DEFINITION_PATH,
        CATEGORY_DEFINITION_PATH.parent.parent / "category-definition.txt",
    )
    return strip_prompt_comment_lines(category_raw)
