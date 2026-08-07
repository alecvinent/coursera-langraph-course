import re
from unittest import TestCase

from module_2_multiagents.agents.prompts import (
    RESEARCHER_PROMPT,
    SEO_PROMPT,
    WRITER_PROMPT,
)

PLACEHOLDER_RE = re.compile(r"\{[a-z_]+\}")


class TestPromptTemplates(TestCase):
    def test_each_prompt_has_exactly_one_placeholder(self):
        for name, prompt in [
            ("RESEARCHER", RESEARCHER_PROMPT),
            ("WRITER", WRITER_PROMPT),
            ("SEO", SEO_PROMPT),
        ]:
            with self.subTest(name=name):
                placeholders = PLACEHOLDER_RE.findall(prompt)
                self.assertEqual(len(placeholders), 1, f"{name} must have exactly one placeholder")

    def test_researcher_placeholder_is_topic(self):
        placeholders = PLACEHOLDER_RE.findall(RESEARCHER_PROMPT)
        self.assertEqual(placeholders, ["{topic}"])

    def test_writer_placeholder_is_outline(self):
        placeholders = PLACEHOLDER_RE.findall(WRITER_PROMPT)
        self.assertEqual(placeholders, ["{outline}"])

    def test_seo_placeholder_is_draft(self):
        placeholders = PLACEHOLDER_RE.findall(SEO_PROMPT)
        self.assertEqual(placeholders, ["{draft}"])

    def test_writer_prompt_has_handoff_sentence(self):
        self.assertIn("point", WRITER_PROMPT.lower())
        self.assertIn("outline", WRITER_PROMPT.lower())

    def test_seo_prompt_has_handoff_sentence_and_output_schema(self):
        self.assertIn("article", SEO_PROMPT.lower())
        self.assertIn("SEO Title Options:", SEO_PROMPT)
        self.assertIn("Relevant Keywords:", SEO_PROMPT)

    def test_prompts_format_to_concrete_strings(self):
        outline = "- Point 1\n- Point 2"
        draft = "Para one.\n\nPara two."
        got = [
            RESEARCHER_PROMPT.format(topic="The Future of AI"),
            WRITER_PROMPT.format(outline=outline),
            SEO_PROMPT.format(draft=draft),
        ]
        self.assertIn("The Future of AI", got[0])
        self.assertIn("- Point 1", got[1])
        self.assertIn("Para one.", got[2])