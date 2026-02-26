import json
from datetime import datetime, timezone
from pathlib import Path


def append_eval_result(log_path: Path, input_path: Path, model: str, response: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input_path": str(input_path),
        "model": model,
        "response": response,
    }
    with log_path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(record, ensure_ascii=False) + "\n")
