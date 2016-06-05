import lemmatize
import unittest
import tempfile

class TestLemmatizer(unittest.TestCase):
    def _build_lemmatizer(self, rules):
        lemmatizer = lemmatize.SUCLemmatizer()
        with tempfile.NamedTemporaryFile() as file:
            file.write(rules.encode("utf-8"))
            file.seek(0)
            lemmatizer.load(file.name)

        return lemmatizer

    def test_verb(self):
        lemmatizer = self._build_lemmatizer(
            "rasade\trasa\tVB|PRT|AKT"
        )
        test = ("rasade", "VB|PRT|AKT")
        expected = "rasa"
        self.assertEqual(lemmatizer.predict(*test), expected)

    def test_adjective(self):
        lemmatizer = self._build_lemmatizer(
            "stora\tstor\tJJ|POS|UTR/NEU|PLU|IND/DEF|NOM"
        )
        test = ("stora", "JJ|POS|UTR/NEU|PLU|IND/DEF|NOM")
        expected = "stor"
        self.assertEqual(lemmatizer.predict(*test), expected)

    def test_noun(self):
        lemmatizer = self._build_lemmatizer(
            "värden\tvärde\tNN|NEU|PLU|IND|NOM"
        )
        test = ("värden", "NN|NEU|PLU|IND|NOM")
        expected = "värde"
        self.assertEqual(lemmatizer.predict(*test), expected)
