import argparse

parser = argparse.ArgumentParser(description="Build a tagger module")
parser.add_argument("--python", action="store_true", help="also build Python module")
parser.add_argument(
    "--name", dest="name", type=str, default=None, help="name of the module/executable"
)
parser.add_argument(
    "--cc", dest="cc", type=str, default="cc", help="C compiler (default: cc)"
)
parser.add_argument(
    "--cflags",
    dest="cflags",
    type=str,
    default="-Wall -Wno-unused-function -Ofast",
    help="C compiler flags",
)
parser.add_argument(
    "--train",
    dest="train",
    type=str,
    help="training file (only used with generic model)",
)
parser.add_argument(
    "--n-train-fields",
    dest="n_train_fields",
    type=int,
    default=2,
    help="number of tab-separated fields in training data (default: 2)",
)
parser.add_argument(
    "--beam-size",
    dest="beam_size",
    type=int,
    default=4,
    help="beam size of the decoder (recommended interval: 1--4)",
)
parser.add_argument(
    "--hash-bits",
    dest="feat_hash_bits",
    type=int,
    default=32,
    help="number of bits for hashes (default: 32)",
)
parser.add_argument(
    "--skip-generate",
    action="store_true",
    help="compile Python module but do not generate C code (assumed to exist)",
)
parser.add_argument(
    "--skip-compile", action="store_true", help="generate C code but do not compile it"
)
args = parser.parse_args()
