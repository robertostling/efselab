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

    @patch("swe_pipeline.build_sentences")
    def test_tagging_and_lemmatization(self, build_sentences_mock):
        options = self._default_options(tagged=True, lemmatized=True)
        sentence = ["Hej", "mitt", "namn", "är"]
        suc_tags = ["IN", "PS|NEU|SIN|DEF", "NN|NEU|SIN|IND|NOM", "VB|PRS|AKT"]
        ud_tags = [
            "INTJ|_",
            "DET|Definite=Def|Gender=Neut|Number=Sing|Poss=Yes",
            "NOUN|Case=Nom|Definite=Ind|Gender=Neut|Number=Sing",
            "AUX|Mood=Ind|Tense=Pres|VerbForm=Fin|Voice=Act",
        ]
        lemmas = ["hej", "min", "namn", "vara"]

        suc_tagger = MagicMock()
        suc_tagger.tag.return_value = suc_tags
        ud_tagger = MagicMock()
        ud_tagger.tag.return_value = ud_tags
        lemmatizer = MagicMock()
        lemmatizer.predict.side_effect = lemmas

        models = self._default_models(
            suc_tagger=suc_tagger,
            ud_tagger=ud_tagger,
            lemmatizer=lemmatizer,
        )

        self.assertEqual(
            run_tagging_and_lemmatization(options, sentence, models),
            (lemmas, ud_tags, suc_tags, [])
        )

    @patch("swe_pipeline.build_sentences")
    def test_tagging_and_lemmatization_and_ner(self, build_sentences_mock):
        options = self._default_options(tagged=True, lemmatized=True, ner=True)
        sentence = ["Hej", "mitt", "namn", "är"]
        suc_tags = ["IN", "PS|NEU|SIN|DEF", "NN|NEU|SIN|IND|NOM", "VB|PRS|AKT"]
        ud_tags = [
            "INTJ|_",
            "DET|Definite=Def|Gender=Neut|Number=Sing|Poss=Yes",
            "NOUN|Case=Nom|Definite=Ind|Gender=Neut|Number=Sing",
            "AUX|Mood=Ind|Tense=Pres|VerbForm=Fin|Voice=Act",
        ]
        lemmas = ["hej", "min", "namn", "vara"]
        ner_tags = ["O", "O", "O", "O"]

        suc_tagger = MagicMock()
        suc_tagger.tag.return_value = suc_tags
        ud_tagger = MagicMock()
        ud_tagger.tag.return_value = ud_tags
        lemmatizer = MagicMock()
        lemmatizer.predict.side_effect = lemmas
        suc_ne_tagger = MagicMock()
        suc_ne_tagger.tag.return_value = ner_tags

        models = self._default_models(
            suc_tagger=suc_tagger,
            ud_tagger=ud_tagger,
            lemmatizer=lemmatizer,
            suc_ne_tagger=suc_ne_tagger,
        )

        self.assertEqual(
            run_tagging_and_lemmatization(options, sentence, models),
            (lemmas, ud_tags, suc_tags, ner_tags)
        )
