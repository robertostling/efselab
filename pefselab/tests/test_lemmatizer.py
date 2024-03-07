import pefselab.lemmatize
import tempfile


def build_lemmatizer(rules):
    lemmatizer = pefselab.lemmatize.SUCLemmatizer()
    with tempfile.NamedTemporaryFile() as file:
        file.write(rules.encode("utf-8"))
        file.seek(0)
        lemmatizer.load(file.name)
    return lemmatizer


def test_verb():
    lemmatizer = build_lemmatizer("rasade\trasa\tVB|PRT|AKT")
    test = ("rasade", "VB|PRT|AKT")
    expected = "rasa"
    assert lemmatizer.predict(*test) == expected


def test_adjective():
    lemmatizer = build_lemmatizer("stora\tstor\tJJ|POS|UTR/NEU|PLU|IND/DEF|NOM")
    test = ("stora", "JJ|POS|UTR/NEU|PLU|IND/DEF|NOM")
    expected = "stor"
    assert lemmatizer.predict(*test) == expected


def test_noun():
    lemmatizer = build_lemmatizer("värden\tvärde\tNN|NEU|PLU|IND|NOM")
    test = ("värden", "NN|NEU|PLU|IND|NOM")
    expected = "värde"
    assert lemmatizer.predict(*test) == expected
