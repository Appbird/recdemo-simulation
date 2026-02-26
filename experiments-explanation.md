# Experiments Explanation

## 目的
- `analysis` で各研究の語りと評価観点を生成し、`compare-results` で `actual-talk` と `llm-sim` を比較する。

## 記号
- `L`: 使用するLLM
- `P`: 入力論文（PDF）
- `P_sys`: `system-instruction.txt` に `rec-demo-explanation.txt` を埋め込んだシステムプロンプト

## 実験フロー（analysis -> compare-results）
1. LLM `L` に論文 `P`（PDF）を渡す。  
2. `P_sys`（Re:commend-demo説明を含むプロンプト）を使って語りを生成する。  
3. 生成された語りを主張単位の箇条書きに分割する。  
4. 各主張を10観点+「その他」でマルチラベル分類する。  
   今回は迅速化のため、この分類もLLMに任せる。  
5. 研究単位・観点単位で集計し、比較用レポートを作る。  
6. `actual-talk`（人手語り）と `llm-sim`（LLM語り）を比較し、観点ごとの違いを確認する。  

## 実行対象
- 対象は `PDF` 配下（EC2025を含む）  
- `analysis` では `paper` モードでPDFを再帰探索して処理する。

## 実行コマンド例
### 1) LLM側の集計（llm-sim）
```bash
uv run recdemo-sim analysis PDF --input-kind paper --output results/llm-simulation.md
```

### 2) 人手側の集計（actual-talk）
- 既存の `narrative_*.txt` から作る場合:
```bash
uv run recdemo-sim analysis PDF --input-kind narrative --output results/actual-talk.md
```

### 3) 比較レポート生成
- `configs/default.toml` の `[compare]` を使う場合:
```bash
uv run recdemo-sim compare-results
```

- 直接指定する場合:
```bash
uv run recdemo-sim compare-results \
  results/actual-talk.md \
  results/llm-simulation.md \
  --left-name actual-talk \
  --right-name llm-sim \
  --output results/compare.md
```

## compare-results で見ているもの
- 観点別 該当研究数 差分  
- 観点別 研究対応一覧（Aでのみ該当 / Bでのみ該当、研究リンク、サンプル主張）  
- 研究ごとの観点比較表（観点差分 + サンプル主張）  
- 研究ごとの差分詳細（Aの主張 / Bの主張）
