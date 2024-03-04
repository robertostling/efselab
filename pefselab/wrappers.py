"""
Wrappers allowing downloading and training of efselab models/pipelines.
"""

import argparse
from pathlib import Path
import sys
from importlib import import_module
from types import ModuleType
from typing import Iterable
from .tools import get_data_dir

class Model:
    """Wrapper around an already trained model to allow easy integration into
    other python programs"""

    def __init__(self, modelspec: str):
        self.name: str = modelspec
        self.modeldir: Path = get_data_dir().joinpath("models")
        found: bool = True
        for i in self.modeldir.iterdir():
            if self.name in i.name:
                found = True
                break
        if not found:
            raise FileNotFoundError(f"{modelspec} not found")
        sys.path.append(str(self.modeldir.absolute())) # hacky, but it works
        self.model: ModuleType = import_module(str(self.name))
        with open(self.modeldir.joinpath(self.name).with_suffix(".bin"), "rb") as f:
            self.weights = f.read()

    def tag(self, sentence: str) -> list[str]:
        """ just makes it easier to access tag method """
        return self.model.tag(self.weights, sentence.split())


class Info:
    """
    Gathers information on the locally available pefselab data.

    Attributes:
        datadir: Path              = path to datadirectory; see utils.get_data_dir()
        models: list[Path]         = list containing path objects to each
                                     available model
        udtdir: Path               = path to universal dependencies (if downloaded)
        udt_langs: dict[str, str]  = dict mapping foldernames to udt language codes
    """

    def __init__(self):
        self.datadir: Path = get_data_dir()
        if not self.datadir.exists():
            self.datadir.mkdir()

        self.modeldir: Path = self.datadir.joinpath("models")
        if not self.modeldir.exists():
            self.modeldir.mkdir()
        self.models: list[Path] = [x for x in self.modeldir.iterdir() if x.suffix == ".so"]

        self.udtdir: Path = self.datadir.joinpath("udt")
        self.udt_available: bool = True if self.udtdir.exists() else False
        if not self.udt_available:
            return
        self.udt_langs: dict[str, str] = {}
        for i in self.udtdir.iterdir():
            # FIX: unreadable line of code; but it works (it gets the language id)
            self.udt_langs[i.name] = list(i.iterdir())[0].name.split("-")[0]

    def __str__(self):
        """
        returns human readable specs for entire data directory, including
        [data_directory, efselab_models]
        """
        res: str = "= PEFSELAB SPEC =\n"
        res += f"\nDATADIR:\n\t{self.datadir}\n"

        if not self.udt_available:
            res += "\n== Universal Dependencies Not Found ==\n"
        else:
            res += "\nAVAILABLE UDT LANGUAGES\n"
            i: str
            for i in sorted(self.udt_langs.keys()):
                res += f"\t{i}\n"

        if self.models != []:
            res += "\nMODELS:\n"
            p: Path
            for p in self.models:
                res += f"{p.name.split('.')[0]}\n"
        else:
            res += "\n== No models found ==\n"

        return res


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    mode_options: list[str] = ["download", "info"]
    parser.add_argument(
        "mode", help=f"""Mode of efselab. Possible modes: {mode_options}"""
    )
    parser.add_argument("-u", "--url", help="URL for downloading model to datadir.")
    args: argparse.Namespace = parser.parse_args()
    if args.mode not in mode_options:
        parser.print_help()
        sys.exit(1)

    if args.mode == "info":
        print(Info())

    if args.mode == "download":
        if not args.url:
            print("ERROR: must provide URL if using mode 'download'\n")
            parser.print_help()
            sys.exit(1)
