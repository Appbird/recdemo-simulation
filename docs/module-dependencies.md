# Module Dependencies

この文書は `src/recdemo/` のモジュール依存と、`eval` / `analysis` 実行時の呼び出しフローを整理したものです。

## パッケージ単位の責務

- `recdemo.cli`
  - CLI引数を定義し、コマンドごとのハンドラに振り分ける。
- `recdemo.core`
  - 共通パス、設定読み込み、型定義。
- `recdemo.runtime`
  - ログ初期化、`.env` 読み込み。
- `recdemo.prompt`
  - プロンプトテンプレート読込、コメント除去、`${...}` 埋め込み。
- `recdemo.io`
  - 入出力（PDF→テキスト変換、JSONL保存）。
- `recdemo.llm`
  - LiteLLM呼び出しと応答テキスト抽出。
- `recdemo.pipeline`
  - ユースケースの処理フロー（`eval` / `analysis`）。

## 依存関係（モジュール）

- `recdemo.cli.app`
  - depends on: `recdemo.core.paths`, `recdemo.runtime.env`, `recdemo.runtime.logging`, `recdemo.cli.handlers`
- `recdemo.cli.handlers`
  - depends on: `recdemo.core.config`, `recdemo.core.paths`, `recdemo.core.types`, `recdemo.io.content_loader`, `recdemo.pipeline.eval_pipeline`, `recdemo.pipeline.analysis_pipeline`, `recdemo.prompt.builders`
- `recdemo.pipeline.eval_pipeline`
  - depends on: `recdemo.core.types`, `recdemo.io.result_store`, `recdemo.llm.client`
- `recdemo.pipeline.analysis_pipeline`
  - depends on: `recdemo.llm.client`, `recdemo.prompt.builders`
- `recdemo.pipeline.batch_analysis`
  - depends on: `recdemo.io.content_loader`, `recdemo.pipeline.analysis_pipeline`
- `recdemo.prompt.builders`
  - depends on: `recdemo.core.paths`
- `recdemo.io.content_loader`
  - external: `pymupdf`, `pymupdf.layout`, `pymupdf4llm`
- `recdemo.llm.client`
  - external: `litellm`

## 実行フロー

### `eval` の呼び出し

1. `src/cli.py` → `recdemo.cli.app.main()`
2. `configure_logging()` / `load_dotenv_if_exists()`
3. `handle_eval()`
4. `load_default_model()`
5. `build_system_prompt()`
   - `system-instruction.txt` + `${rec_demo_explanation}` 展開
6. `load_user_prompt_from_input()`
   - PDFなら `pymupdf4llm.to_markdown()`
7. `run_eval()`
   - `generate_response()`
   - `append_eval_result()`（`--no-log`で無効）
8. stdoutへ応答本文を出力

### `analysis` の呼び出し

1. `src/cli.py` → `recdemo.cli.app.main()`
2. `configure_logging()` / `load_dotenv_if_exists()`
3. `handle_analysis()`
4. `load_default_model()`
5. `build_system_prompt()`
6. `load_user_prompt_from_input()`
7. `build_category_definition()`
8. `run_analysis()`
   1. step 1/3: 語り生成（`generate_response`）
   2. step 2/3: 根拠箇条書き（`build_extract_reasons_prompt` → `generate_response`）
   3. step 3/3: カテゴリ割当（`build_assign_categories_prompt` → `generate_response`）
9. stdoutへ整形済み結果を出力

フォルダ入力時:
1. `run_analysis_for_directory()` で入力種別に応じて再帰収集
   - `input-kind=paper`: `.pdf`
   - `input-kind=narrative`: `narrative_*.txt`
2. スレッド並列で各ファイルを分析
   - paper: 3段（語り生成 -> 根拠抽出 -> カテゴリ割当）
   - narrative: 2段（根拠抽出 -> カテゴリ割当）
3. `format_directory_report()` で以下を比較表示
   - 研究ごとの観点比較
   - 観点ごとの評価比較
   - 失敗ファイル

### `analysis-step1/2/3` の呼び出し

1. `src/cli.py` → `recdemo.cli.app.main()`
2. `configure_logging()` / `load_dotenv_if_exists()`
3. `handle_analysis_stepX()` を実行
4. 各stepで `recdemo.pipeline.analysis_pipeline` の対応関数を実行
   - step1: `generate_narration`
   - step2: `extract_reasons`
   - step3: `assign_categories`

補足:
- `eval` は実質 step1 相当の生成コマンド。
- `bullet-points` は `analysis-step2` のエイリアス。
- `categorize` は `analysis-step3` のエイリアス。

## 補足

- プロンプトテンプレートでは `% ` コメント行を除去し、`${variable}` を置換する。
- テンプレート動作確認は `src/prompt_demo.py` と `tests/test_prompt_builders.py` で行える。
