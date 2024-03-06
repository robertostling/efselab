"""
contains code for creating a POS tagger using Universal Treebanks data.
"""

import tarfile
import tempfile
from pathlib import Path
from Cython.Build.Dependencies import subprocess
import requests

from .wrappers import Info
from .configuration import Configuration
from .tools import get_data_dir, conll2tab, read_dict
from .tagset import Tagset
from .form import (
    TextField,
    FeatureSet,
    suffix,
    prefix,
    normalize,
    abstract,
    delexicalize,
)
from .taglexicon import TagLexicon

UDT_URL: str = "https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-5287/ud-treebanks-v2.13.tgz"


def get_udt(include_ne: bool = False) -> None:
    """downloads and converts universal treebanks to TAB format."""
    print(f"Accessing {UDT_URL}...")
    response = requests.get(UDT_URL, stream=True)
    if response.status_code != 200:
        raise requests.RequestException("Can't access URL. Check manually.")
    print(f"Downloading and extracting {UDT_URL}. This can take a few minutes...")
    file = tarfile.open(fileobj=response.raw, mode="r|gz")
    dl_path: Path = Path(tempfile.gettempdir()).joinpath("udt")
    file.extractall(path=dl_path)
    print("Converting UDT to TAB format...")
    udt_filepath: Path = get_data_dir().joinpath("udt")
    if not udt_filepath.exists():
        udt_filepath.mkdir()
    # since the exact folder will change depending on the version number
    dl_path: Path = list(dl_path.iterdir())[0]

    # FIX: this will fail if one tries to run the script again with a different
    # version, since it will always default to the first one. Uncertain if
    # necessary to fix?
    for folder in dl_path.iterdir():
        lang_folder: Path = udt_filepath.joinpath(folder.name)
        files: list[Path] = [x for x in folder.iterdir() if x.suffix == ".conllu"]

        # NOTE: add to model selection rather than extraction conditional
        # if not any("train" in x.name for x in files):
        #     continue
        # if not any("test" in x.name for x in files):
        #     continue
        # if not any("dev" in x.name for x in files):
        #     continue

        if not lang_folder.exists():
            lang_folder.mkdir()
        for file in files:
            with open(
                lang_folder.joinpath(Path(file.name).with_suffix(".tab")), "w"
            ) as f:
                f.write(conll2tab([file], include_ne))


class TrainerUdt:
    def __init__(self, lang: str, datapath: Path):
        self.lang: str = lang
        self.config: Configuration = Configuration("ud" + self.lang)

        trainpath: Path = datapath.joinpath(f"{self.lang}-ud-train.tab")
        testpath: Path = datapath.joinpath(f"{self.lang}-ud-test.tab")
        devpath: Path = datapath.joinpath(f"{self.lang}-ud-dev.tab")
        assert trainpath.exists() # I'm not crazy...
        assert testpath.exists() or devpath.exists() # must have one or the other
        self.data: dict[str, Path] = {
            "test": testpath if testpath.exists() else devpath,
            "dev": devpath if devpath.exists() else testpath,
            "train": trainpath
        }
        self.udt_tags, self.udt_norm_tags = read_dict(self.data["train"], 0, 1)
        UDT = Tagset(self.udt_tags, self.config)

        text_field = 0
        tag_field = 1

        this_tag = UDT.tag(tag_field, 0)
        last_tag = UDT.tag(tag_field, -1)
        last_last_tag = UDT.tag(tag_field, -2)

        # Define words (relative to the current position during a search)
        this_word = TextField(text_field, 0)
        last_word = TextField(text_field, -1)
        next_word = TextField(text_field, 1)

        # Each tuple below represents a single feature template.
        self.fs = FeatureSet(
            [
                # Tag bigram and trigram features
                (this_tag, last_tag),
                (this_tag, last_tag, last_last_tag),
                # Word with each letter mapped to its unicode character class, so that
                # e.g. "Fish" and "Make" become equivalent, but not "Fish" and
                # "Fishing" (different length).
                (this_tag, delexicalize(this_word)),
                # Same as above, but where repetitions are ignored, so that e.g.
                # "Fish123" and "Making7" become equivalent (upper+lower+digit).
                (this_tag, abstract(this_word)),
                # Lower-cased words.
                (this_tag, normalize(this_word)),
                (this_tag, normalize(next_word)),
                (this_tag, normalize(last_word)),
                # Lower-cased word bigrams.
                (this_tag, normalize(last_word), normalize(this_word)),
                (this_tag, normalize(next_word), normalize(this_word)),
                # Lower-cased prefix features.
                (this_tag, prefix(normalize(this_word), 1)),
                (this_tag, prefix(normalize(this_word), 2)),
                (this_tag, prefix(normalize(this_word), 3)),
                (this_tag, prefix(normalize(this_word), 4)),
                (this_tag, prefix(normalize(this_word), 5)),
                # Lower-cased suffix features.
                (this_tag, suffix(normalize(this_word), 1)),
                (this_tag, suffix(normalize(this_word), 2)),
                (this_tag, suffix(normalize(this_word), 3)),
                (this_tag, suffix(normalize(this_word), 4)),
                (this_tag, suffix(normalize(this_word), 5)),
            ],
            self.config,
        )

        # These tags will be tried for unknown words (i.e. words not in the training
        # data)
        # NOTE: currently this is not right! see original implementation
        open_tags = sorted(UDT.tag_idx[tag] for tag in UDT.tags)

        # Create a TagLexicon object from the tag lexicon we loaded with read_dict()
        # above.
        # NOTE: although items are added one by one below, we must give the number of
        # items in the constructor: len(udt_norm_tags)
        self.tl = TagLexicon(
            "UDT_lexicon", text_field, len(self.udt_norm_tags), open_tags, self.config
        )
        for norm, tags in self.udt_norm_tags.items():
            self.tl[norm] = [UDT.tag_idx[tag] for tag in tags]

    def fit(self):
        """train model"""
        self.config.build()
        subprocess.run([
            f"{get_data_dir().joinpath('models', 'ud' + self.lang)}",
            "train",
            self.data["train"],
            self.data["dev"],
            f"{get_data_dir().joinpath('models', 'ud' + str(Path(self.lang).with_suffix('.bin')))}"
        ])


def udt_pipeline(lang: str) -> None:
    """POS tagger pipeline for universal dependencies and efselab"""
    udt_path: Path = Path(get_data_dir()).joinpath("udt")
    if not udt_path.exists():
        while True:
            print("Universal Dependencies Treebank not found. Download (y/n)?")
            print("[About ~1GB]")
            match input("> "):
                case "y":
                    break
                case "n":
                    return
        get_udt()

    langpath: Path = udt_path.joinpath(lang)
    assert langpath.exists()
    langid: str = Info().udt_langs[lang]
    trainer: TrainerUdt = TrainerUdt(
        lang=langid,
        datapath=langpath
    )
    trainer.fit()
