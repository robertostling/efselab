from swe_pipeline import run_tagging_and_lemmatization
import unittest
from unittest.mock import patch, MagicMock

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

    def _default_models(
        self, suc_ne_tagger=None, suc_tagger=None,
        ud_tagger=None, lemmatizer=None
    ):
        return {
            "suc_ne_tagger": suc_ne_tagger,
            "suc_tagger": suc_tagger,
            "ud_tagger": ud_tagger,
            "lemmatizer": lemmatizer,
        }

    @patch("swe_pipeline.build_sentences")
    def test_tagging(self, build_sentences_mock):
        options = self._default_options(tagged=True)
        sentence = ["Hej", "mitt", "namn", "är"]
        tags = ["IN", "PS|NEU|SIN|DEF", "NN|NEU|SIN|IND|NOM", "VB|PRS|AKT"]

        tagger = MagicMock()
        tagger.tag.return_value = tags
        models = self._default_models(suc_tagger=tagger)

        self.assertEqual(
            run_tagging_and_lemmatization(options, sentence, models),
            (
                [],
                [],
                ['IN', 'PS|NEU|SIN|DEF', 'NN|NEU|SIN|IND|NOM', 'VB|PRS|AKT'],
                []
            )
        )
