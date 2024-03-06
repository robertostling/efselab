"""Tokenize, tag and parse Swedish plain text data.

This was originally the pipeline by Filip Salomonsson for the Swedish
Treebank (using hunpos for tagging), later modified by Robert Östling to use
efselab and Python 3.
"""

import shutil
import sys
import tempfile
import re
import gzip
from pathlib import Path

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

class SwedishPipeline:
    def __init__(
        self,
        filenames: list[str],
        tagger: str | None = None,
        udtagger: str | None = None,
        ner_tagger: str | None = None,
        lemmatizer: bool | None = None,
        output_dir: Path | str = Path("./output"),
        parse_compability: bool = False,
        non_capitalization: bool = False,
        skip_tokenization: bool = False,
        skip_segmentation: bool = False,
        delete_tmp_dir: bool = True,
    ):
        if isinstance(output_dir, str):
            self.output_dir: Path = Path(output_dir)
        else:
            self.output_dir: Path = output_dir
        if self.output_dir.exists() and not self.output_dir.is_dir():
            raise FileExistsError("Output dir exists and is not a directory!")
        if not self.output_dir.exists():
            self.output_dir.mkdir()

        self.models: dict = {}
        modeldir: Path = get_data_dir().joinpath("models")
        if tagger and any((ner_tagger, parse_compability)):
            self.models["suc_tagger"] = SucTagger(modeldir.joinpath(tagger + ".bin"))
            if lemmatizer:
                assert udtagger
                self.models["ud_tagger"] = UDTagger(modeldir.joinpath(udtagger + ".bin"))
        if ner_tagger:
            self.models["suc_ne_tagger"] = SucNETagger(modeldir.joinpath(ner_tagger + ".bin"))

        # FIX: not elegant; but there is no other lemmatizer as of now?
        if lemmatizer:
            self.models["lemmatizer"] = SUCLemmatizer()
            self.models["lemmatizer"].load(str(modeldir.joinpath("suc-saldo.lemmas")))

        self.parse_compability: bool | None = parse_compability
        self.non_capitalization: bool = non_capitalization
        self.skip_tokenization: bool = skip_tokenization
        self.skip_segmentation: bool = skip_segmentation

        self.tmpdir: Path = Path(tempfile.gettempdir()).joinpath("pefselabswpipe")
        if not self.tmpdir.exists():
            self.tmpdir.mkdir()

        for filename in filenames:
            self.__process_file(Path(filename))

        # cleanup temporary directory
        if delete_tmp_dir:
            shutil.rmtree(self.tmpdir)
            del self.tmpdir

    def __process_file(self, filename: Path) -> None:
        print("Processing %s..." % filename, file=sys.stderr)
        tokenized_filename: Path = self.tmpdir.joinpath(
            filename.with_suffix(".tok").name
        )
        tagged_filename: Path = self.tmpdir.joinpath(filename.with_suffix(".tag").name)
        ner_filename: Path = self.tmpdir.joinpath(filename.with_suffix(".ne").name)

        sentences: list = self.__run_tokenization(filename)
        annotated_sentences: list = []

        with (
            open(tokenized_filename, "w", encoding="utf-8") as tokenized,
            open(tagged_filename, "w", encoding="utf-8") as tagged,
            open(ner_filename, "w", encoding="utf-8") as ner,
        ):
            for sentence in sentences:
                self.__write_to_file(tokenized, sentence)

                if not any(
                    [
                        self.models.get("suc_tagger"),
                        self.models.get("suc_ne_tagger"),
                    ]
                ):
                    continue

                (
                    lemmas,
                    ud_tags_list,
                    suc_tags_list,
                    suc_ne_list,
                ) = self.__tag_and_lemmatize(sentence)

                annotated_sentences.append(
                    zip(sentence, lemmas, ud_tags_list, suc_tags_list)
                )

                ud_tag_list = [ud_tags[: ud_tags.find("|")] for ud_tags in ud_tags_list]

                if lemmas and ud_tags_list:
                    line_tokens = sentence, suc_tags_list, ud_tag_list, lemmas
                else:
                    line_tokens = sentence, suc_tags_list

                lines = ["\t".join(line) for line in zip(*line_tokens)]

                self.__write_to_file(tagged, lines)

                if self.models.get("suc_ne_tagger"):
                    ner_lines = ["\t".join(line) for line in zip(sentence, suc_ne_list)]

                    self.__write_to_file(ner, ner_lines)

        # write all results to output folder
        if not self.skip_tokenization:
            shutil.copy(tokenized_filename, self.output_dir)
        if self.models.get("suc_tagger"):
            shutil.copy(tagged_filename, self.output_dir)
        if self.models.get("suc_ne_tagger"):
            shutil.copy(ner_filename, self.output_dir)

        # TODO: data structure for parsing using stanza

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

    def __run_tokenization(
        self, filename: Path
    ) -> list:
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
