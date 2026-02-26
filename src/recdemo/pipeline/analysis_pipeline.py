import logging

from recdemo.llm.client import generate_response

logger = logging.getLogger(__name__)

ANALYSIS_SYSTEM_PROMPT = """あなたは、Re:commend-demo の語りを評価軸に沿って構造化する分析者です。
与えられた指示に従い、過不足なく、形式を厳密に守って出力してください。"""


def extract_reasons(model: str, narration: str) -> str:
    user_prompt = f"""以下の語りを分析してください。

# 語り
{narration}

# タスク
- 語りの中から、コンテンツを「良い」と判断した評価根拠を抽出する。
- 各根拠を、重複なく1項目ずつ箇条書きにする。

# 出力形式（厳守）
- 根拠1
- 根拠2

# 制約
- 見出しや前置きは不要。
- 箇条書き以外の形式は使わない。
- 各項目は1文で簡潔に書く。
"""
    return generate_response(
        model=model,
        system_prompt=ANALYSIS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )


def assign_categories(model: str, reasons: str, category_definition: str) -> str:
    user_prompt = f"""以下の評価根拠にカテゴリを割り当ててください。

# 評価根拠（箇条書き）
{reasons}

# 評価観点カテゴリ定義
{category_definition}

# タスク
- 各評価根拠に対して、該当する評価観点カテゴリを割り当てる。
- 該当カテゴリがない場合は「その他」を割り当てる。

# 出力形式（厳守）
[カテゴリ1] 評価理由1
[カテゴリ1, カテゴリ2] 評価理由2

# 制約
- 見出しや前置きは不要。
- 1行に1つの評価理由のみを書く。
- カテゴリ名は定義文の表記に合わせる。
- 評価理由部分は、入力の根拠を改変しすぎずに使う。
"""
    return generate_response(
        model=model,
        system_prompt=ANALYSIS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )


def run_analysis(model: str, system_prompt: str, source_content: str, category_definition: str) -> str:
    logger.info("analysis step 1/3: generating narrative")
    narration = generate_response(
        model=model,
        system_prompt=system_prompt,
        user_prompt=source_content,
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
    )
    logger.info("analysis step 3/3 completed")

    return f"# 語りの内容\n{narration}\n\n# 評価観点\n{categorized_reasons}".strip()
