from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "default.toml"
PROMPT_DIR = PROJECT_ROOT / "src" / "prompt"
SYSTEM_INSTRUCTION_PATH = PROMPT_DIR / "system-instruction.txt"
REC_DEMO_EXPLANATION_PATH = PROMPT_DIR / "rec-demo-explanation.txt"
CATEGORY_DEFINITION_PATH = PROMPT_DIR / "category-definition.txt"
DEFAULT_LOG_PATH = PROJECT_ROOT / "outputs" / "eval_results.jsonl"
DOTENV_PATH = PROJECT_ROOT / ".env"
