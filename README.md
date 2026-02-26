# Re:commend-demo Simulation
# 機能
```
uv run src/cli.py eval P --llm L
```

1. LLM$L$に`./src/system-instruction.txt`をシステムプロンプトとして入力する。
   1. litellmを使用する
2. ユーザプロンプトとして、論文$P$の内容を入れる。ただし、`.pdf`の場合は`pymupdf4llm.to_markdown`を用いてテキスト化を行うこと。(pymupdf.layoutを併用)
3. $L$から得た出力のうち、応答のみを抜き出してstdoutに返答する。
出てきた結果を集積し、グラフを形成する。
生のRe:commend-demoとの違いを見比べる。それぞれの評価観点カテゴリに入った評価を見比べる。

## このコードベースでの慣習
### プロンプトについて
- プロンプト行での`% `から始まる冒頭行は、プロンプトに含めない。プロンプトに対するコメント行とする。
- `${variable}`は、後からテキストが埋め込まれることを示す。