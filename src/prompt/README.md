# Prompt Testing Quickstart

## 1) Render a simple template example

```bash
uv run src/prompt_demo.py \
  --template src/prompt/examples/simple-template.txt \
  --vars-json src/prompt/examples/simple-vars.json
```

## 2) Override a value from CLI

```bash
uv run src/prompt_demo.py \
  --template src/prompt/examples/simple-template.txt \
  --vars-json src/prompt/examples/simple-vars.json \
  --var topic=評価観点の分類
```

## 3) Run unit tests for prompt helpers

```bash
uv run python -m unittest -q tests.test_prompt_builders
```

Notes:
- Lines starting with `% ` are treated as comments and removed.
- `${variable}` placeholders are replaced by provided values.
- Missing variables raise `PromptTemplateError`.
