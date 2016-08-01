from swe_pipeline import run_tokenization
from textwrap import dedent
import unittest
from unittest.mock import patch, MagicMock, mock_open

class TestRunTokenization(unittest.TestCase):
    def _default_options(
        self, tagged=False, ner=False, parsed=False,
        lemmatized=False, skip_tokenization=False
    ):
        options = MagicMock()
        options.tagged = tagged
        options.ner = ner
        options.parsed = parsed
        options.lemmatized = lemmatized
        options.skip_tokenization = skip_tokenization

        return options

    @patch("swe_pipeline.build_sentences")
    def test_empty_options(self, build_sentences_mock):
        options = self._default_options()
        build_sentences_mock.return_value = []

        open_mock = mock_open()
        with patch("swe_pipeline.open", open_mock, create=True):
            self.assertEqual(run_tokenization(options, "file.txt"), [])

    @patch("swe_pipeline.build_sentences")
    def test_sentences(self, build_sentences_mock):
        options = self._default_options()
        build_sentences_mock.return_value = [
            ["Hej", "mitt", "namn", "är"],
            ["Hej", "mitt", "namn", "är", "Slim", "Shady"],
        ]

        text = dedent("""
            Hej mitt namn är
            Hej mitt namn är Slim Shady
        """).strip()

        open_mock = mock_open(read_data=text)
        with patch("swe_pipeline.open", open_mock, create=True):
            self.assertEqual(run_tokenization(options, "file.txt"), [
                ["Hej", "mitt", "namn", "är"],
                ["Hej", "mitt", "namn", "är", "Slim", "Shady"],
            ])

    @patch("swe_pipeline.build_sentences")
    def test_sentences_without_tokenization(self, build_sentences_mock):
        options = self._default_options(skip_tokenization=True)
        text = dedent("""
            Hej
            mitt
            namn
            är

            Hej
            mitt
            namn
            är
            Slim
            Shady

        """).strip()

        open_mock = mock_open(read_data=text)
        with patch("swe_pipeline.open", open_mock, create=True):
            self.assertEqual(run_tokenization(options, "file.txt"), [
                ["Hej", "mitt", "namn", "är"],
                ["Hej", "mitt", "namn", "är", "Slim", "Shady"],
            ])
