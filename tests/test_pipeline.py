import json
from pathlib import Path
import tempfile
from pefselab.swe_pipeline import SwedishPipeline
from pefselab.train_swe_pipeline import create_pipeline


def test_pipeline_process_file():
    """test the process_file without any modifications"""
    nlp: SwedishPipeline = SwedishPipeline(
        ["tests/sample_tokenized.txt"],
        tagger=False,
        ner_tagger=False,
        lemmatizer=False,
        skip_tokenization=True,
    )

    with open("tests/sample_tokenized.txt", "r") as f:
        lines: list[str] = [x.rstrip() for x in f]
        tokens: list[str] = []
        for line in lines:
            tokens += [x for x in line.split()]

    assert tokens == nlp.documents["sample_tokenized.txt"].tokens


def test_pipeline_tokenization():
    """test tokenization without tagging"""
    nlp: SwedishPipeline = SwedishPipeline(
        ["tests/sample.txt"],
        tagger=False,
        ud_tagger=False,
        ner_tagger=False,
        lemmatizer=False,
        skip_tokenization=False,
    )

    with open("tests/sample_tokenized.txt", "r") as tokenized_file:
        tokens: list[str] = [
            token.rstrip() for token in tokenized_file if token != "\n"
        ]

    assert tokens == nlp.documents["sample.txt"].tokens


def test_pipeline_suc_tagging():
    nlp: SwedishPipeline = SwedishPipeline(
        ["tests/sample.txt"],
        tagger=True,
        ud_tagger=False,
        ner_tagger=False,
        lemmatizer=False,
    )
    with open("tests/sample.json", "r") as f:
        suc_tags: list[str] = json.load(f)["suc_tags"]
    assert nlp.documents["sample.txt"].suc_tags == suc_tags


def test_pipeline_ud_tagging():
    nlp: SwedishPipeline = SwedishPipeline(["tests/sample.txt"])
    with open("tests/sample.json", "r") as f:
        ud_tags: list[str] = json.load(f)["ud_tags"]
    assert nlp.documents["sample.txt"].ud_tags == ud_tags


def test_pipeline_save():
    with tempfile.TemporaryDirectory() as output_dir:
        SwedishPipeline(["tests/sample.txt"]).save(output_dir)
        with open(Path(output_dir).joinpath("sample.json"), "r") as f:
            lr: dict = json.load(f)
            del lr["path"]  # since the pathname k/v is not in the comparison file
        with open("tests/sample.json", "r") as f:
            rr: dict = json.load(f)
        assert lr == rr


def test_pipeline_parse_struct():
    pass
