import unittest
import tokenizer

class TestTokenizer(unittest.TestCase):
    def test_empty_string(self):
        test = ""
        expected = []
        self.assertEqual(list(tokenizer.build_sentences(test)), expected)

    def test_single_word(self):
        test = "hej"
        expected = [["hej"]]
        self.assertEqual(list(tokenizer.build_sentences(test)), expected)

    def test_two_words(self):
        test = "hej hopp"
        expected = [["hej", "hopp"]]
        self.assertEqual(list(tokenizer.build_sentences(test)), expected)

    def test_sentence(self):
        test = "hej hopp."
        expected = [["hej", "hopp", "."]]
        self.assertEqual(list(tokenizer.build_sentences(test)), expected)

    def test_two_sentences(self):
        test = "Jag skriver text. Och mer text."
        expected = [["Jag", "skriver", "text", "."], ["Och", "mer", "text", "."]]
        self.assertEqual(list(tokenizer.build_sentences(test)), expected)

    def test_paragraphs_without_punctuation(self):
        test = """Första meningen

        Andra meningen"""
        expected = [["Första", "meningen"], ["Andra", "meningen"]]
        self.assertEqual(list(tokenizer.build_sentences(test)), expected)

    def test_abbreviations(self):
        test = "Jag skickar räkningen p.g.a. ditt inköp"
        expected = [["Jag", "skickar", "räkningen", "p.g.a.", "ditt", "inköp"]]
        self.assertEqual(list(tokenizer.build_sentences(test)), expected)

        test = "Vi har bl a svamp"
        expected = [["Vi", "har", "bl.a.", "svamp"]]
        self.assertEqual(list(tokenizer.build_sentences(test)), expected)

    def test_smileys(self):
        test = "Jag säger :) och :( samtidigt"
        expected = [["Jag", "säger", ":)", "och", ":(", "samtidigt"]]
        self.assertEqual(list(tokenizer.build_sentences(test)), expected)

    def test_numeric(self):
        test = "Temperatur: 21.0 grader"
        expected = [["Temperatur", ":", "21.0", "grader"]]
        self.assertEqual(list(tokenizer.build_sentences(test)), expected)
