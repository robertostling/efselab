from . import build_suc
from . import build_suc_ne
from . import build_udt_suc_sv
from .tools import get_data_dir

import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path


def pipeline_is_available() -> bool:
    """checks whether the swedish pipeline is available"""
    if not get_data_dir().joinpath("models").exists():
        return False

    all_modules: list[str] = [
        x.name for x in get_data_dir().joinpath("models").iterdir()
    ]
    so_modules: list[str] = [
        x.name.split(".")[0]
        for x in get_data_dir().joinpath("models").iterdir()
        if x.suffix in [".so", ".pyd"]
    ]
    required_modules: list[str] = [
        "udt_suc_sv",
        "suc_ne.PLATFORM.so",
        "udt_suc_sv.PLATFORM.so",
        "suc.PLATFORM.so",
    ]
    for rqm in required_modules:
        if rqm.split(".")[-1] in ["so", "pyd"]:
            if rqm.split(".")[0] not in so_modules:
                return False
        else:
            if rqm not in all_modules:
                return False
    return True


def build_pipeline():
    build_suc.build(skip_generate=True, n_train_fields=2)
    build_suc_ne.build(skip_generate=True)
    build_udt_suc_sv.build(n_train_fields=4, skip_generate=False, beam_size=1)
    if Path("./build").exists():
        shutil.rmtree("build")


def train_pipeline():
    subprocess.run(
        [
            get_data_dir().joinpath("models", "udt_suc_sv"),
            "train",
            Path(__file__).parent.joinpath("data", "sv-ud-train.tab"),
            Path(__file__).parent.joinpath("data", "sv-ud-dev.tab"),
            get_data_dir().joinpath("models", "suc-ud.bin"),
        ]
    )
    # create empty file to make it easier to check if pipeline is available
    open(get_data_dir().joinpath("models", "pipeline_built"), "w").close()


def preprocessing_for_pipeline():
    """extracts pipeline data to the correct folder"""

    modeldir: Path = get_data_dir().joinpath("models")
    if not modeldir.exists():
        modeldir.mkdir(parents=True)
    datadir: Path = Path(__file__).parent.joinpath("data")

    with open(datadir.joinpath("swe-pipeline-ud2.tar.gz"), "rb") as archive:
        with tarfile.open(fileobj=archive, mode="r|gz") as file:
            dl_path: Path = Path(tempfile.gettempdir()).joinpath("spipe")
            file.extractall(path=dl_path)

    for i in dl_path.iterdir():
        if i.suffix != ".c":
            continue
        if modeldir.joinpath(i.name).exists():
            continue
        shutil.move(i, modeldir)

    for i in dl_path.joinpath("swe-pipeline").iterdir():
        if i.suffix != ".bin" and i.suffix != ".lemmas":
            continue
        if modeldir.joinpath(i.name).exists():
            continue
        shutil.move(i, modeldir)


def create_pipeline():
    preprocessing_for_pipeline()
    build_pipeline()
    train_pipeline()
