import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from recdemo.prompt.builders import (
    PromptTemplateError,
    render_prompt_template,
    strip_prompt_comment_lines,
)


class PromptBuildersTest(unittest.TestCase):
    def test_strip_prompt_comment_lines(self) -> None:
        text = "% c1\nline1\n% c2\nline2\n"
        self.assertEqual(strip_prompt_comment_lines(text), "line1\nline2")

    def test_render_prompt_template(self) -> None:
        template = "hello ${name}, topic=${topic}"
        rendered = render_prompt_template(template, {"name": "A", "topic": "T"})
        self.assertEqual(rendered, "hello A, topic=T")

    def test_render_prompt_template_missing_variable(self) -> None:
        template = "hello ${name}"
        with self.assertRaises(PromptTemplateError):
            render_prompt_template(template, {})


if __name__ == "__main__":
    unittest.main()
