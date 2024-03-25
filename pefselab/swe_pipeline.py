"""Tokenize, tag and parse Swedish plain text data.

This was originally the pipeline by Filip Salomonsson for the Swedish
Treebank (using hunpos for tagging), later modified by Robert Östling to use
efselab and Python 3.
"""

import sys
import re
import gzip
from pathlib import Path
from dataclasses import asdict, dataclass, field
import json

from pefselab.tools import get_data_dir

from .lemmatize import SUCLemmatizer
from .tagger import SucTagger, SucNETagger, UDTagger
from .tokenizer import build_sentences

__authors__ = """
Filip Salomonsson <filip.salomonsson@gmail.com>
Robert Östling <robert.ostling@helsinki.fi>
Aaron Smith <aaron.smith@lingfil.uu.se>
"""

MAX_TOKEN = 256

@dataclass
class ParseEntry:
    """dataclass for returning Stanza parse compatible list"""

    idx: int
    text: str
    upos: str
    xpos: str
    feats: str


@dataclass
class Document:
    """dataclass for storing documents in Pipeline.
    VARIABLES:
        path:       Path object to file
        tokens:     list of tokens
        ud_tags:    list of universal dependency tags (index matches with tokens above)
        suc_tags:   list of SUC tags (index matches with tokens above)
        ner_tags:   list of NER tags (index matches with tokens above)
    """

    path: str
    tokens: list[str] = field(default_factory=list)
    lemmas: list[str] = field(default_factory=list)
    ud_tags: list[str] = field(default_factory=list)
    suc_tags: list[str] = field(default_factory=list)
    ner_tags: list[str] = field(default_factory=list)


class SwedishPipeline:
    def __init__(
        self,
        filenames: list[str],
        tagger: bool = True,
        ud_tagger: bool = True,
        ner_tagger: bool = True,
        lemmatizer: bool = True,
        non_capitalization: bool = False,
        skip_tokenization: bool = False,
        skip_segmentation: bool = False,
    ):
        self.documents: dict[str, Document] = {}

        self.models: dict = {}
        modeldir: Path = get_data_dir().joinpath("models")
        if tagger:
            self.models["suc_tagger"] = SucTagger(modeldir.joinpath("suc.bin"))
        if ud_tagger:
            self.models["ud_tagger"] = UDTagger(modeldir.joinpath("suc-ud.bin"))
        if ner_tagger:
            self.models["suc_ne_tagger"] = SucNETagger(modeldir.joinpath("suc-ne.bin"))
        if lemmatizer:  # FIX: not elegant; but there is no other lemmatizer as of now?
            assert ud_tagger
            self.models["lemmatizer"] = SUCLemmatizer()
            self.models["lemmatizer"].load(str(modeldir.joinpath("suc-saldo.lemmas")))

        self.skip_tokenization: bool = skip_tokenization
        self.skip_segmentation: bool = skip_segmentation
        self.non_capitalization: bool = non_capitalization

        for filename in filenames:
            self.documents[Path(filename).name] = Document(filename)
            self.process_file(Path(filename))

    def save(self, output_dir: Path | str = Path("./output")):
        """saves processed data to json given an output directory path"""
        if isinstance(output_dir, str):
            self.output_dir: Path = Path(output_dir)
        else:
            self.output_dir: Path = output_dir
        if self.output_dir.exists() and not self.output_dir.is_dir():
            raise FileExistsError("Output dir exists and is not a directory!")
        if not self.output_dir.exists():
            self.output_dir.mkdir()

        for filename, doc in self.documents.items():
            with open(
                self.output_dir.joinpath(Path(filename).with_suffix(".json").name), "w"
            ) as f:
                json.dump(asdict(doc), f)

    def as_stanza_parse_struct(self, name: str) -> list[ParseEntry]:
        """given a filename returns a list of stanza compatible parse entries"""
        doc: Document = self.documents[name]
        parse_entries: list[ParseEntry] = []
        if not (doc.ud_tags and doc.tokens and doc.suc_tags):
            raise ValueError(
                """Document lacks necessary values. Rerun pipeline
            with all components in order to generate parse struct."""
            )
        for i, token in enumerate(doc.tokens):
            ud_tags: list[str] = doc.ud_tags[i].split("|")
            upos: str = ud_tags[0]
            xpos: str = doc.suc_tags[i].split("|")[0]
            feats: str = ("|").join(ud_tags[1:])
            parse_entries.append(
                ParseEntry(
                    i + 1,  # since they're 1 indexed
                    text=token,
                    xpos=xpos,  # TODO: how to get xpos?
                    upos=upos,
                    feats=feats,
                )
            )
        return parse_entries

    def process_file(self, filename: Path) -> None:
        print("Processing %s..." % filename, file=sys.stderr)
        for sentence in self.__run_tokenization(filename):
            self.documents[filename.name].tokens += sentence

            if not any(
                [self.models.get("suc_tagger"), self.models.get("suc_ne_tagger")]
            ):
                continue

            lemmas, ud_tags, suc_tags, ner_tags = self.__tag_and_lemmatize(sentence)

            self.documents[filename.name].lemmas += lemmas
            self.documents[filename.name].ud_tags += ud_tags
            self.documents[filename.name].suc_tags += suc_tags
            self.documents[filename.name].ner_tags += ner_tags
        print("Finished processing files.", file=sys.stderr)

    def __tag_and_lemmatize(self, sentence: str) -> tuple:
        lemmas = []
        ud_tags_list = []
        assert self.models.get("suc_tagger")
        suc_tags_list = self.models["suc_tagger"].tag(sentence)
        suc_ne_list = []

        if self.models.get("lemmatizer"):
            lemmas = [
                self.models["lemmatizer"].predict(token, tag)
                for token, tag in zip(sentence, suc_tags_list)
            ]
            ud_tags_list = self.models["ud_tagger"].tag(sentence, lemmas, suc_tags_list)

            if self.models.get("suc_ne_tagger"):
                suc_ne_list = self.models["suc_ne_tagger"].tag(
                    list(zip(sentence, lemmas, suc_tags_list))
                )

        return lemmas, ud_tags_list, suc_tags_list, suc_ne_list

    def __run_tokenization(self, filename: Path) -> list:
        with (
            gzip.open(filename, "rt", encoding="utf-8")
            if filename.suffix == ".gz"
            else open(filename, "r", encoding="utf-8")
        ) as input_file:
            data = input_file.read()
        if self.skip_tokenization:
            sentences = [
                sentence.split("\n")
                for sentence in data.split("\n\n")
                if sentence.strip()
            ]
        elif self.skip_segmentation:
            sentences = [
                build_sentences(line, segment=False)
                for line in data.split("\n")
                if line.strip()
            ]
        else:
            if self.non_capitalization:
                n_capitalized = len(re.findall(r"[\.!?] +[A-ZÅÄÖ]", data))
                n_non_capitalized = len(re.findall(r"[\.!?] +[a-zåäö]", data))
                self.non_capitalization = n_non_capitalized > 5 * n_capitalized
            sentences = build_sentences(data, non_capitalized=self.non_capitalization)
        sentences = list(
            filter(
                bool,
                [
                    [token for token in sentence if len(token) <= MAX_TOKEN]
                    for sentence in sentences
                ],
            )
        )
        return sentences

    def __write_to_file(self, file, lines):
        for line in lines:
            print(line, file=file)
        print(file=file)
