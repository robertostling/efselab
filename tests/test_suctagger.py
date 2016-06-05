import os
import tagger
import unittest

class TestSucTagger(unittest.TestCase):
    def setUp(self):
        weights = os.path.join("swe-pipeline", "suc.bin")
        self.tagger = tagger.SucTagger(weights)

    def test_empty_sentence(self):
        test = []
        expected = tuple()
        self.assertEqual(self.tagger.tag(test), expected)

    def test_sentence_list(self):
        test = ["Jag", "har", "en", "dröm", "."]
        expected = ('PN|UTR|SIN|DEF|SUB', 'VB|PRS|AKT', 'DT|UTR|SIN|IND', 'NN|UTR|SIN|IND|NOM', 'MAD')
        self.assertEqual(self.tagger.tag(test), expected)

    def test_sentence_tuple(self):
        test = ("Jag", "har", "en", "dröm", ".")
        expected = ('PN|UTR|SIN|DEF|SUB', 'VB|PRS|AKT', 'DT|UTR|SIN|IND', 'NN|UTR|SIN|IND|NOM', 'MAD')
        self.assertEqual(self.tagger.tag(test), expected)

    def test_incorrect_string_input(self):
        test = "Jag har en dröm."
        with self.assertRaises(TypeError):
            self.tagger.tag(test)
