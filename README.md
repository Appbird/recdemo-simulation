# Re:commend-demo Simulation

Re:commend-demo の語り生成と評価観点分析を行うCLIツール。

## できること

### 1. eval

```bash
uv run src/cli.py eval P --llm L
```

1. `src/prompt/system-instruction.txt` をシステムプロンプトとして使用
2. 入力 `P` をユーザプロンプトとして使用
3. `P` が `.pdf` の場合は `pymupdf.layout` と `pymupdf4llm.to_markdown` でテキスト化
4. LiteLLM で応答を生成し、本文のみを stdout に出力
5. 既定で `outputs/eval_results.jsonl` に結果を追記（`--no-log` で無効化）

### 2. analysis

```bash
uv run src/cli.py analysis P --llm L
```

3段のLLMパイプラインで実行:

1. 語り生成
2. 「良いと判断した根拠」の箇条書き化
3. 各根拠へのカテゴリ割り当て（該当なしは「その他」）

出力形式:

```text
# 語りの内容
{語りの内容}

# 評価観点
[カテゴリ1] 評価理由1
[カテゴリ1, カテゴリ2] 評価理由2
```

実行中は `INFO` ログで進捗（step 1/3〜3/3）を表示。

## プロンプトファイル

`src/prompt/` 配下で管理:

- `system-instruction.txt`
- `rec-demo-explanation.txt`
- `category-definition.txt`
- `analysis-system.txt`
- `analysis-extract-reasons.txt`
- `analysis-assign-categories.txt`

### 記法ルール

- `% ` で始まる行はコメントとして除外
- `${variable}` はテンプレート埋め込み

## プロンプトを手早く試す

```bash
uv run src/prompt_demo.py --template src/prompt/examples/simple-template.txt --vars-json src/prompt/examples/simple-vars.json
```

詳細は [src/prompt/README.md](/Users/rkawaguchi/Documents/Projects/katayose-lab/interaction-2026/recdemo-simulation/src/prompt/README.md) を参照。

## テスト

```bash
uv run python -m unittest -q tests.test_prompt_builders
```

## モジュール構成

機能別に `src/recdemo/` を分割:

- `cli`: 引数解釈とコマンド振り分け
- `core`: パス定義、型、設定読み込み
- `runtime`: ログ設定、`.env` 読み込み
- `prompt`: プロンプトテンプレートの構築
- `io`: 入出力（PDF読み込み、結果保存）
- `llm`: LiteLLMクライアント
- `pipeline`: `eval`/`analysis` の実行フロー

依存・呼び出し関係の詳細は [docs/module-dependencies.md](/Users/rkawaguchi/Documents/Projects/katayose-lab/interaction-2026/recdemo-simulation/docs/module-dependencies.md) を参照。
