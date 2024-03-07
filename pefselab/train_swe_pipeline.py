from . import build_suc
from . import build_suc_ne
from . import build_udt_suc_sv
from .tools import get_data_dir

import shutil
import requests
import subprocess
import tarfile
import tempfile
from pathlib import Path

SWEDATA_URL: str = "https://dali.ling.su.se/projects/efselab/swe-pipeline-ud2.tar.gz"


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
    modeldir: Path = get_data_dir().joinpath("models")
    if not modeldir.exists():
        modeldir.mkdir()
    response = requests.get(SWEDATA_URL, stream=True)
    print(f"Accessing {SWEDATA_URL}...")
    if response.status_code != 200:
        raise requests.RequestException("Can't access URL. Check manually.")
    print(f"Downloading and extracting {SWEDATA_URL}. This can take a few minutes...")
    file = tarfile.open(fileobj=response.raw, mode="r|gz")
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
