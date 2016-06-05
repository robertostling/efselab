import os
import tagger
import unittest

unittest.util._MAX_LENGTH = 300

class TestUDTagger(unittest.TestCase):
    def setUp(self):
        weights = os.path.join("swe-pipeline", "suc.bin")
        self.tagger = tagger.UDTagger(weights)

    def test_empty_sentence(self):
        test = [[], [], []]
        expected = tuple()
        self.assertEqual(self.tagger.tag(*test), expected)

    def test_sentence_list(self):
        test = (
            ["Jag", "har", "en", "dröm", "."],
            ["jag", "ha", "en", "dröm", "."],
            ['PN|UTR|SIN|DEF|SUB', 'VB|PRS|AKT', 'DT|UTR|SIN|IND', 'NN|UTR|SIN|IND|NOM', 'MAD'],
        )
        expected = (
            'PRON|Case=Nom|Definite=Def|Gender=Com|Number=Sing',
            'VERB|Mood=Ind|Tense=Pres|VerbForm=Fin|Voice=Act',
            'DET|Definite=Ind|Gender=Com|Number=Sing',
            'NOUN|Case=Nom|Definite=Ind|Gender=Com|Number=Sing',
            'PUNCT|_'
        )
        self.assertEqual(self.tagger.tag(*test), expected)

    def test_sentence_tuple(self):
        test = (
            ("Jag", "har", "en", "dröm", "."),
            ["jag", "ha", "en", "dröm", "."],
            ['PN|UTR|SIN|DEF|SUB', 'VB|PRS|AKT', 'DT|UTR|SIN|IND', 'NN|UTR|SIN|IND|NOM', 'MAD'],
        )
        expected = (
            'PRON|Case=Nom|Definite=Def|Gender=Com|Number=Sing',
            'VERB|Mood=Ind|Tense=Pres|VerbForm=Fin|Voice=Act',
            'DET|Definite=Ind|Gender=Com|Number=Sing',
            'NOUN|Case=Nom|Definite=Ind|Gender=Com|Number=Sing',
            'PUNCT|_'
        )
        self.assertEqual(self.tagger.tag(*test), expected)

    def test_incorrect_string_input(self):
        test = (
            "Jag har en dröm.",
            ["jag", "ha", "en", "dröm", "."],
            ['PN|UTR|SIN|DEF|SUB', 'VB|PRS|AKT', 'DT|UTR|SIN|IND', 'NN|UTR|SIN|IND|NOM', 'MAD'],
        )
        with self.assertRaises(TypeError):
            self.tagger.tag(*test)
