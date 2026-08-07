from unittest import TestCase

from module_2_multiagents.agents.prompts import (
    RESEARCHER_PROMPT,
    SEO_PROMPT,
    WRITER_PROMPT,
)
from module_2_multiagents.export import build_analysis_doc, build_prompts_doc


class TestBuildPromptsDoc(TestCase):
    def test_contains_all_three_prompt_texts_verbatim(self):
        doc = build_prompts_doc()
        self.assertIn("## Researcher", doc)
        self.assertIn("## Writer", doc)
        self.assertIn("## SEO Analyst", doc)
        for prompt in (RESEARCHER_PROMPT, WRITER_PROMPT, SEO_PROMPT):
            self.assertIn(prompt.strip(), doc)

    def test_sections_have_one_justification_sentence_each(self):
        doc = build_prompts_doc()
        self.assertIn("How it transforms input for the next agent:", doc)
        # one justification sentence per section: count the heading marker
        self.assertEqual(doc.count("How it transforms input for the next agent:"), 3)

    def test_justifications_name_input_and_output(self):
        doc = build_prompts_doc()
        self.assertIn("topic", doc.lower())
        self.assertIn("outline", doc.lower())
        self.assertIn("draft", doc.lower())
        self.assertIn("next agent", doc.lower())


class TestBuildAnalysisDoc(TestCase):
    def test_word_count_within_150_to_200(self):
        md, count = build_analysis_doc()
        self.assertTrue(150 <= count <= 200, f"word count {count} out of range")

    def test_mentions_advantage_and_limitation(self):
        md, _ = build_analysis_doc()
        self.assertIn("advantage", md.lower())
        self.assertIn("limitation", md.lower())

    def test_identifies_handoff_consideration(self):
        md, _ = build_analysis_doc()
        self.assertIn("prompt", md.lower())
        self.assertIn("handoff", md.lower())

    def test_out_of_range_explicit_count_raises(self):
        with self.assertRaises(ValueError):
            build_analysis_doc(word_count=120)


if __name__ == "__main__":
    import unittest

    unittest.main()