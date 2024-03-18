import tempfile
import pefselab.conll
import textwrap

annotated_sentences = [
    [
        (
            "Jag jag PRON|Case=Nom|Definite=Def|Gender=Com|Number=Sing PN|UTR|SIN|DEF|SUB"
        ).split(" "),
        ("har ha VERB|Mood=Ind|Tense=Pres|VerbForm=Fin|Voice=Act VB|PRS|AKT").split(
            " "
        ),
        ("en en DET|Definite=Ind|Gender=Com|Number=Sing DT|UTR|SIN|IND").split(" "),
        (
            "dröm dröm NOUN|Case=Nom|Definite=Ind|Gender=Com|Number=Sing NN|UTR|SIN|IND|NOM"
        ).split(" "),
        (". . PUNCT|_ MAD").split(" "),
    ]
]


def test_verb():
    file_data = ""
    with tempfile.TemporaryFile(mode="w+") as outfile:
        pefselab.conll.tagged_to_tagged_conll(annotated_sentences, outfile)
        outfile.seek(0)
        file_data = outfile.read()

    assert (
        file_data.splitlines()
        == textwrap.dedent(
            """
        0	Jag	jag	PRON	PN|UTR|SIN|DEF|SUB	Case=Nom|Definite=Def|Gender=Com|Number=Sing
        1	har	ha	VERB	VB|PRS|AKT	Mood=Ind|Tense=Pres|VerbForm=Fin|Voice=Act
        2	en	en	DET	DT|UTR|SIN|IND	Definite=Ind|Gender=Com|Number=Sing
        3	dröm	dröm	NOUN	NN|UTR|SIN|IND|NOM	Case=Nom|Definite=Ind|Gender=Com|Number=Sing
        4	.	.	PUNCT	MAD	_

    """
        )
        .lstrip()
        .splitlines()
    )
