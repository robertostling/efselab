import argparse

parser = argparse.ArgumentParser(description='Build a tagger module')
parser.add_argument('--python', action='store_true',
    help='build python interface (default: build standalone executable)')
parser.add_argument('--skip-compile', action='store_true',
    help='generate C code but do not compile it')
args = parser.parse_args()

