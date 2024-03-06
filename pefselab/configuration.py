from io import TextIOWrapper
import os
import sys
from pathlib import Path
from setuptools import setup, Extension
from Cython.Build import cythonize
import subprocess

from . import translation
from .tools import get_data_dir


class Configuration:
    def __init__(
        self,
        name: str,
        custom_cflags: str = "-Wall -Wno-unused-function -Ofast",
        n_train_fields: int = 2,
        beam_size: int = 4,
        hash_bits: int = 32,
    ):
        feat_hash_bits = hash_bits
        partial_hash_bits = feat_hash_bits
        lexicon_hash_bits = partial_hash_bits
        n_train_fields = n_train_fields
        beam_size = beam_size
        n_tag_fields = None
        cflags: list[str] = custom_cflags.replace(r"\-", "-").split()

        # Only these values are (currently) supported
        assert partial_hash_bits in (32, 64)
        assert feat_hash_bits in (32, 64)
        assert lexicon_hash_bits == partial_hash_bits

        self.name = name
        # use_unicode doesn't currently change anything
        self.use_unicode = True
        self.skip_generate = False
        self.generate_python = True
        self.cc = "cc"
        self.cflags = cflags

        self.tagset = None
        self.lexicon = None
        self.feature_set = None
        self.wclexicons = []

        self.beam_size = beam_size
        self.partial_hash_bits = partial_hash_bits
        self.feat_hash_bits = feat_hash_bits
        self.lexicon_hash_bits = lexicon_hash_bits
        self.n_train_fields = n_train_fields
        self.n_tag_fields = n_tag_fields if n_tag_fields else n_train_fields - 1
        print("Building tagger...", file=sys.stderr)

    def build(self):
        # generate and compile native version
        generated_c_fp: Path = (
            get_data_dir().joinpath("models").joinpath(self.name + ".c")
        )
        if not self.skip_generate:
            with open(generated_c_fp, "w") as f:
                print("Generating C code to %s..." % f.name, file=sys.stderr)
                self.c_emit(f, build_python=False)
                f.flush()

            subprocess.run(
                ["cc"]  # TODO: implement config file with custom C compiler
                + self.cflags
                + ["-I", str(get_data_dir().joinpath("models"))]
                + ["-o", str(get_data_dir().joinpath("models", self.name)), str(get_data_dir().joinpath("models", self.name + ".c"))]
            )

        # generate and compile Python interface
        generated_cpy_fp: Path = (
            get_data_dir().joinpath("models").joinpath("py" + self.name + ".c")
        )
        if not self.skip_generate:
            with open(generated_cpy_fp, "w") as f:
                print("Generating C code to %s..." % f.name, file=sys.stderr)
                self.c_emit(f, build_python=True)
                f.flush()
        if not self.generate_python:
            return
        tagger = Extension(
            self.name,
            sources=[str(generated_cpy_fp)],
            extra_compile_args=self.cflags,
        )
        setup(
            name=self.name,
            ext_modules=cythonize(
                [tagger], build_dir=get_data_dir().joinpath("models")
            ),
            script_args=[
                "build_ext",
                "--build-lib",
                f"{get_data_dir().joinpath('models')}",
            ],
        )

    def c_emit(self, f: TextIOWrapper, build_python=False):
        def c_include(filename: str):
            """internal wrapper for including a prewritten C file"""
            with open(os.path.join(Path(__file__).parent, "c", filename)) as cf:
                code = cf.read()
                f.write(code)

        f.write(
            """
#define N_TRAIN_FIELDS  %d
#define N_TAG_FIELDS    %d
#define BEAM_SIZE       %d
#define TAGGER_NAME     "%s"
#define PyInit_TAGGER_NAME PyInit_%s

#include <stdint.h>

typedef uint%d_t   partial_hash_t;
typedef uint%d_t   feat_hash_t;
typedef uint32_t   label;

"""
            % (
                self.n_train_fields,
                self.n_tag_fields,
                self.beam_size,
                self.name,
                self.name,
                self.partial_hash_bits,
                self.feat_hash_bits,
            )
        )

        c_include("hash.c")
        c_include("headers.h")

        translation.c_emit(f, self)

        self.tagset.c_emit(f)
        if self.lexicon:
            self.lexicon.c_emit(f)
        for wcl in self.wclexicons:
            wcl.c_emit(f)
        self.feature_set.c_emit(f)

        c_include("seq.c")
        c_include("search.c")
        c_include("tag.c")
        c_include("train.c")
        c_include("run.c")
        c_include("main.c")
        if build_python:
            c_include("pytagger.c")
