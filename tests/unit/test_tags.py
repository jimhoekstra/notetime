from unittest import TestCase

from notetime.tags import extract_tags


class TestTags(TestCase):
    def test_extract_tags(self):
        text = "This is a test note with tags @tag1 and @tag2."
        expected_tags = ["tag1", "tag2"]

        tags = extract_tags(text)
        self.assertEqual(tags, expected_tags)

    def test_extract_tags_with_no_tags(self):
        text = "This is a test note with no tags."
        expected_tags = []

        tags = extract_tags(text)
        self.assertEqual(tags, expected_tags)

    def test_extract_tags_with_newlines(self):
        text = "This is a test note with tags @tag1 and @tag2.\nAnd another tag @tag3."
        expected_tags = ["tag1", "tag2", "tag3"]

        tags = extract_tags(text)
        self.assertEqual(tags, expected_tags)

    def test_extract_tags_applies_lowercase(self):
        text = "This is a test note with tags @Tag1 and @TAG2."
        expected_tags = ["tag1", "tag2"]

        tags = extract_tags(text)
        self.assertEqual(tags, expected_tags)
