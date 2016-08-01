import os
import sys
from swe_pipeline import process_file
from textwrap import dedent
import unittest
from unittest.mock import patch, MagicMock, mock_open

class TestProcessFile(unittest.TestCase):
    maxDiff = 800

    def _default_options(
        self, tagged=False, ner=False, parsed=False, lemmatized=False
    ):
        options = MagicMock()
        options.tagged = tagged
        options.ner = ner
        options.parsed = parsed
        options.lemmatized = lemmatized

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

    @patch("swe_pipeline.write_to_output")
    @patch("swe_pipeline.open", mock_open(), create=True)
    @patch("swe_pipeline.parse")
    @patch("swe_pipeline.run_tagging_and_lemmatization")
    @patch("swe_pipeline.run_tokenization")
    def test_empty_options(
        self, run_tokenization_mock, run_tagging_mock, parse_mock,
        open_mock, *args
    ):
        options = self._default_options()
        models = self._default_models()
        with open(os.devnull, 'w') as sys.stderr:
            process_file(options, "file.txt", "", models)

        self.assertEqual(open_mock().write.call_count, 0)

    @patch("swe_pipeline.write_to_output")
    @patch("swe_pipeline.parse")
    @patch("swe_pipeline.run_tagging_and_lemmatization")
    @patch("swe_pipeline.run_tokenization")
    def test_only_tokenization(
        self, run_tokenization_mock, run_tagging_mock, parse_mock, *args
    ):
        options = self._default_options()
        models = self._default_models()
        run_tokenization_mock.return_value = [
            ["Hej", "mitt", "namn", "är"],
            ["Hej", "mitt", "namn", "är", "Slim", "Shady"],
        ]
        with open(os.devnull, 'w') as sys.stderr:
            open_mock = mock_open()
            with patch("swe_pipeline.open", open_mock, create=True):
                process_file(options, "file.txt", "", models)

        written_to_file = "".join([
            call[0][0]
            for call in open_mock().write.call_args_list
        ])
        self.assertEqual(
            written_to_file,
            dedent("""
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

            """).lstrip("\n")
        )

    @patch("swe_pipeline.write_to_output")
    @patch("swe_pipeline.parse")
    @patch("swe_pipeline.run_tagging_and_lemmatization")
    @patch("swe_pipeline.run_tokenization")
    def test_only_tagging(
        self, run_tokenization_mock, run_tagging_mock, parse_mock, *args
    ):
        options = self._default_options(tagged=True)
        models = self._default_models()
        run_tokenization_mock.return_value = [
            ["Hej", "mitt", "namn", "är"],
            ["Hej", "mitt", "namn", "är", "Slim", "Shady"],
        ]
        run_tagging_mock.side_effect = [
            (
                [],
                [],
                ["IN", "PS|NEU|SIN|DEF", "NN|NEU|SIN|IND|NOM", "VB|PRS|AKT"],
                [],
            ),
            (
                [],
                [],
                [
                    "IN", "PS|NEU|SIN|DEF", "NN|NEU|SIN|IND|NOM", "VB|PRS|AKT",
                    "PM|NOM", "PM|NOM"
                ],
                [],
            ),
        ]
        with open(os.devnull, 'w') as sys.stderr:
            open_mock = mock_open()
            with patch("swe_pipeline.open", open_mock, create=True):
                process_file(options, "file.txt", "", models)

        written_to_file = "".join([
            call[0][0]
            for call in open_mock().write.call_args_list
        ])
        self.assertEqual(
            written_to_file,
            dedent("""
                Hej
                mitt
                namn
                är

                Hej\tIN
                mitt\tPS|NEU|SIN|DEF
                namn\tNN|NEU|SIN|IND|NOM
                är\tVB|PRS|AKT

                Hej
                mitt
                namn
                är
                Slim
                Shady

                Hej\tIN
                mitt\tPS|NEU|SIN|DEF
                namn\tNN|NEU|SIN|IND|NOM
                är\tVB|PRS|AKT
                Slim\tPM|NOM
                Shady\tPM|NOM

            """).lstrip("\n")
        )

    @patch("swe_pipeline.write_to_output")
    @patch("swe_pipeline.parse")
    @patch("swe_pipeline.run_tagging_and_lemmatization")
    @patch("swe_pipeline.run_tokenization")
    def test_tagging_and_lemmatization(
        self, run_tokenization_mock, run_tagging_mock, parse_mock, *args
    ):
        options = self._default_options(tagged=True, lemmatized=True)
        models = self._default_models()
        run_tokenization_mock.return_value = [
            ["Hej", "mitt", "namn", "är"],
            ["Hej", "mitt", "namn", "är", "Slim", "Shady"],
        ]
        run_tagging_mock.side_effect = [
            (
                ["hej", "min", "namn", "vara"],
                [
                    "INTJ|_",
                    "DET|Definite=Def|Gender=Neut|Number=Sing|Poss=Yes",
                    "NOUN|Case=Nom|Definite=Ind|Gender=Neut|Number=Sing",
                    "AUX|Mood=Ind|Tense=Pres|VerbForm=Fin|Voice=Act",
                ],
                ["IN", "PS|NEU|SIN|DEF", "NN|NEU|SIN|IND|NOM", "VB|PRS|AKT"],
                [],
            ),
            (
                ["hej", "min", "namn", "vara", "Slim", "Shady"],
                [
                    "INTJ|_",
                    "DET|Definite=Def|Gender=Neut|Number=Sing|Poss=Yes",
                    "NOUN|Case=Nom|Definite=Ind|Gender=Neut|Number=Sing",
                    "AUX|Mood=Ind|Tense=Pres|VerbForm=Fin|Voice=Act",
                    "PROPN|Case=Nom",
                    "PROPN|Case=Nom",
                ],
                [
                    "IN", "PS|NEU|SIN|DEF", "NN|NEU|SIN|IND|NOM", "VB|PRS|AKT",
                    "PM|NOM", "PM|NOM"
                ],
                [],
            ),
        ]
        with open(os.devnull, 'w') as sys.stderr:
            open_mock = mock_open()
            with patch("swe_pipeline.open", open_mock, create=True):
                process_file(options, "file.txt", "", models)

        written_to_file = "".join([
            call[0][0]
            for call in open_mock().write.call_args_list
        ])
        self.assertEqual(
            written_to_file,
            dedent("""
                Hej
                mitt
                namn
                är

                Hej\tIN\tINTJ\thej
                mitt\tPS|NEU|SIN|DEF\tDET\tmin
                namn\tNN|NEU|SIN|IND|NOM\tNOUN\tnamn
                är\tVB|PRS|AKT\tAUX\tvara

                Hej
                mitt
                namn
                är
                Slim
                Shady

                Hej\tIN\tINTJ\thej
                mitt\tPS|NEU|SIN|DEF\tDET\tmin
                namn\tNN|NEU|SIN|IND|NOM\tNOUN\tnamn
                är\tVB|PRS|AKT\tAUX\tvara
                Slim\tPM|NOM\tPROPN\tSlim
                Shady\tPM|NOM\tPROPN\tShady

            """).lstrip("\n")
        )

    @patch("swe_pipeline.write_to_output")
    @patch("swe_pipeline.parse")
    @patch("swe_pipeline.run_tagging_and_lemmatization")
    @patch("swe_pipeline.run_tokenization")
    def test_tagging_and_lemmatization_and_ner(
        self, run_tokenization_mock, run_tagging_mock, parse_mock, *args
    ):
        options = self._default_options(tagged=True, lemmatized=True, ner=True)
        models = self._default_models()
        run_tokenization_mock.return_value = [
            ["Hej", "mitt", "namn", "är"],
            ["Hej", "mitt", "namn", "är", "Slim", "Shady"],
        ]
        run_tagging_mock.side_effect = [
            (
                ["hej", "min", "namn", "vara"],
                [
                    "INTJ|_",
                    "DET|Definite=Def|Gender=Neut|Number=Sing|Poss=Yes",
                    "NOUN|Case=Nom|Definite=Ind|Gender=Neut|Number=Sing",
                    "AUX|Mood=Ind|Tense=Pres|VerbForm=Fin|Voice=Act",
                ],
                ["IN", "PS|NEU|SIN|DEF", "NN|NEU|SIN|IND|NOM", "VB|PRS|AKT"],
                ["O", "O", "O", "O"],
            ),
            (
                ["hej", "min", "namn", "vara", "Slim", "Shady"],
                [
                    "INTJ|_",
                    "DET|Definite=Def|Gender=Neut|Number=Sing|Poss=Yes",
                    "NOUN|Case=Nom|Definite=Ind|Gender=Neut|Number=Sing",
                    "AUX|Mood=Ind|Tense=Pres|VerbForm=Fin|Voice=Act",
                    "PROPN|Case=Nom",
                    "PROPN|Case=Nom",
                ],
                [
                    "IN", "PS|NEU|SIN|DEF", "NN|NEU|SIN|IND|NOM", "VB|PRS|AKT",
                    "PM|NOM", "PM|NOM"
                ],
                ["O", "O", "O", "O", "B-person", "I-person"],
            ),
        ]
        with open(os.devnull, 'w') as sys.stderr:
            open_mock = mock_open()
            with patch("swe_pipeline.open", open_mock, create=True):
                process_file(options, "file.txt", "", models)

        written_to_file = "".join([
            call[0][0]
            for call in open_mock().write.call_args_list
        ])
        self.assertEqual(
            written_to_file,
            dedent("""
                Hej
                mitt
                namn
                är

                Hej\tIN\tINTJ\thej
                mitt\tPS|NEU|SIN|DEF\tDET\tmin
                namn\tNN|NEU|SIN|IND|NOM\tNOUN\tnamn
                är\tVB|PRS|AKT\tAUX\tvara

                Hej\tO
                mitt\tO
                namn\tO
                är\tO

                Hej
                mitt
                namn
                är
                Slim
                Shady

                Hej\tIN\tINTJ\thej
                mitt\tPS|NEU|SIN|DEF\tDET\tmin
                namn\tNN|NEU|SIN|IND|NOM\tNOUN\tnamn
                är\tVB|PRS|AKT\tAUX\tvara
                Slim\tPM|NOM\tPROPN\tSlim
                Shady\tPM|NOM\tPROPN\tShady

                Hej\tO
                mitt\tO
                namn\tO
                är\tO
                Slim\tB-person
                Shady\tI-person

            """).lstrip("\n")
        )

    @patch("swe_pipeline.write_to_output")
    @patch("swe_pipeline.parse")
    @patch("swe_pipeline.run_tagging_and_lemmatization")
    @patch("swe_pipeline.run_tokenization")
    def test_parsing(
        self, run_tokenization_mock, run_tagging_mock, parse_mock, *args
    ):
        options = self._default_options(parsed=True)
        models = self._default_models()
        run_tokenization_mock.return_value = [
            ["Hej", "mitt", "namn", "är"],
            ["Hej", "mitt", "namn", "är", "Slim", "Shady"],
        ]
        run_tagging_mock.side_effect = [
            (
                ["hej", "min", "namn", "vara"],
                [
                    "INTJ|_",
                    "DET|Definite=Def|Gender=Neut|Number=Sing|Poss=Yes",
                    "NOUN|Case=Nom|Definite=Ind|Gender=Neut|Number=Sing",
                    "AUX|Mood=Ind|Tense=Pres|VerbForm=Fin|Voice=Act",
                ],
                ["IN", "PS|NEU|SIN|DEF", "NN|NEU|SIN|IND|NOM", "VB|PRS|AKT"],
                [],
            ),
            (
                ["hej", "min", "namn", "vara", "Slim", "Shady"],
                [
                    "INTJ|_",
                    "DET|Definite=Def|Gender=Neut|Number=Sing|Poss=Yes",
                    "NOUN|Case=Nom|Definite=Ind|Gender=Neut|Number=Sing",
                    "AUX|Mood=Ind|Tense=Pres|VerbForm=Fin|Voice=Act",
                    "PROPN|Case=Nom",
                    "PROPN|Case=Nom",
                ],
                [
                    "IN", "PS|NEU|SIN|DEF", "NN|NEU|SIN|IND|NOM", "VB|PRS|AKT",
                    "PM|NOM", "PM|NOM"
                ],
                [],
            ),
        ]
        with open(os.devnull, 'w') as sys.stderr:
            open_mock = mock_open()
            with patch("swe_pipeline.open", open_mock, create=True):
                process_file(options, "file.txt", "", models)

        self.assertEqual(run_tagging_mock.call_count, 2)
        self.assertEqual(parse_mock.call_count, 1)
