from unittest import TestCase

from pydantic import ValidationError

from module_2_multiagents.state import BlogState


class TestBlogStateValidation(TestCase):
    def test_valid_topic_defaults(self):
        state = BlogState(topic="The Future of AI in Marketing")
        self.assertEqual(state.topic, "The Future of AI in Marketing")
        self.assertIsNone(state.outline)
        self.assertIsNone(state.draft)
        self.assertIsNone(state.seo_feedback)
        self.assertEqual(state.processing_outcome, "full")
        self.assertEqual(state.error_records, [])

    def test_topic_is_stripped(self):
        state = BlogState(topic="  Remote Work Benefits  ")
        self.assertEqual(state.topic, "Remote Work Benefits")

    def test_empty_topic_raises_value_error(self):
        with self.assertRaises(ValidationError):
            BlogState(topic="")

    def test_whitespace_topic_raises_value_error(self):
        with self.assertRaises(ValidationError):
            BlogState(topic="   ")

    def test_serialization_roundtrip(self):
        state = BlogState(topic="t", outline="o", draft="d", seo_feedback="s")
        restored = BlogState.model_validate(state.model_dump())
        self.assertEqual(restored.draft, "d")
        self.assertEqual(restored.seo_feedback, "s")
