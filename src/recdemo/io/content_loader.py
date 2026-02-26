from pathlib import Path

import pymupdf
import pymupdf.layout
import pymupdf4llm


def load_user_prompt_from_input(input_path: Path) -> str:
    if input_path.suffix.lower() == ".pdf":
        pymupdf.layout.activate()
        doc = pymupdf.open(input_path)
        try:
            return pymupdf4llm.to_markdown(doc, force_text=True)
        finally:
            doc.close()
    return input_path.read_text(encoding="utf-8")
