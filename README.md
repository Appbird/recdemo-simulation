# Re:commend-demo Simulation

ECシンポジウムの Re:commend-demo を対象に、語り生成と評価観点分析を行うCLIツール。

## Re:commend-demo とは？

[情報処理学会 エンタテインメントコンピューティング(EC)研究会](https://sig.entcomp.org)のシンポジウムにて開かれるイベントの一つです。
ECシンポジウムでは毎年大量のコンテンツがデモ発表されます。
[Re:commend-demo](https://ec2023.entcomp.org/cfp.html#h-re-commend-demo%E5%B0%82%E9%96%80%E7%A0%94%E7%A9%B6%E8%80%85%E6%8E%A8%E8%96%A6%E3%83%AC%E3%83%93%E3%83%A5%E3%83%BC)とは、これらの作品を審査員が実際に体験し、
その上でその人にとって主観的に好ましいと思われたコンテンツを一つ選んで、
学会の最後にて審査員がその作品をビブリオバトルのように「推し語る」制度です。

この制度はエンタテインメントの「面白さ」を評価する観点を多角的に捉えるための実践として実施されています。
実際に語り手自身の経験・価値観と結びつけ、「なぜ刺さったか」を分析する手掛かりになることを期待して、これらの語りが蓄積され続けています。

c.f. [エンタテインメントシンポジウム2025におけるRe:commend-demoトーク録](https://dl.mtstlab.org/papers/468)

## このツールの狙い

近年の大規模言語モデルの発展をうけ、EC領域のコンテンツ分析においてどのように利活用できるか、という議論が巻き起こっています。
例えばコンテンツの仕様が載った論文をLLMに流せば、そのコンテンツで起こりうる体験を言語化することができます。
その体験の関連に基づいて整理するなど、[EC分野全体の整理手段](https://appbird.github.io/entertainment-design-catalog/)などに活用できるでしょう。

Re:commend-demo の本質は「語り手の経験に基づく語り」にあるため、
LLM が語れるからといって、Re:commend-demoを直接自動化できるわけではありません。
しかし、これらがうまく利活用できれば、例えばRe:commend-demoでの言語化するための支援ツールとして、LLMを活用したり
語りで明瞭に言語化されなかったコンテンツの仕掛けと起こった「面白さ」との対応関係を調べることも可能になると考えられます。

以上のことを踏まえ、本リポジトリでは次の問いに取り組むことを目標に掲げています：
- 論文を与え、Re:commend-demo の説明付きプロンプトで自由に「刺さり」を語らせたとき、
  人手の語りにどこまで迫れるか？逆に不適当な部分はどこか？

実験手順の整理は [experiments-explanation.md](./experiments-explanation.md) を参照。
実験結果の `.md` は `results/` 配下:
- [actual-talk.md](./results/actual-talk.md)
- [llm-simulation.md](./results/llm-simulation.md)
- [compare.md](./results/compare.md)

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

`analysis` の入力は `--input-kind` で切り替え:
- `paper` (default): PDF
- `narrative`: `narrative_*.txt`

`--input-kind narrative` を指定すると、`narrative_*.txt` を入力として
「主張ポイント抽出 -> カテゴリ割り当て」の2段で処理。

結果をファイル保存する場合:

```bash
uv run src/cli.py analysis P --llm L --output result.md
```

フォルダを指定した場合:

```bash
uv run src/cli.py analysis PDF/EC2024 --llm L --workers 8
uv run src/cli.py analysis PDF/EC2024 --llm L --workers 8 --output result.md
uv run src/cli.py analysis PDF/EC2024 --llm L --input-kind paper
uv run src/cli.py analysis PDF/EC2024 --llm L --input-kind narrative
```

- `--input-kind paper`: フォルダ配下の `.pdf` を再帰探索
- `--input-kind narrative`: フォルダ配下の `narrative_*.txt` を再帰探索
- 各ファイルを input-kind に応じて並列実行
  - paper: 3段分析（語り生成 -> 抽出 -> カテゴリ）
  - narrative: 2段分析（抽出 -> カテゴリ）
- 最後に以下をまとめて出力
  - 研究ごとの観点比較
  - 観点ごとの評価比較
  - 失敗ファイル一覧（あれば）

`--workers` を省略した場合は `configs/default.toml` の `[analysis].workers` を利用。
`--input-kind` を省略した場合は `[analysis].input_kind` を利用。
`--output` を省略した場合は `[analysis].output` を利用（空文字なら無効）。

### 3. analysis の各ステップを単体実行

```bash
# step1: 入力コンテンツから語り生成（= eval）
uv run src/cli.py analysis-step1 P --llm L

# step2: 語りテキストから評価根拠の箇条書き抽出
uv run src/cli.py analysis-step2 narration.txt --llm L

# step3: 根拠箇条書きにカテゴリ割り当て
uv run src/cli.py analysis-step3 reasons.txt --llm L
```

短い別名コマンド:

```bash
uv run src/cli.py eval P --llm L
uv run src/cli.py bullet-points narration.txt --llm L
uv run src/cli.py categorize reasons.txt --llm L
```

### 4. 2つの集計結果を比較

```bash
uv run src/cli.py compare-results results/actual-talk.md results/llm-simulation.md
uv run src/cli.py compare-results results/actual-talk.md results/llm-simulation.md --output results/compare.md
```

出力内容:
- 観点別 該当研究数の比較表
- 観点ごとの差分（B-A）
- 増減サマリ
- 研究ごとの評価観点比較（`[カテゴリ] 理由` の共通 / 差分）

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
  - `batch_analysis.py`: ディレクトリ一括分析と集計レポート

依存・呼び出し関係の詳細は [docs/module-dependencies.md](/Users/rkawaguchi/Documents/Projects/katayose-lab/interaction-2026/recdemo-simulation/docs/module-dependencies.md) を参照。
