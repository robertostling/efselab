# Generic Universal Dependencies treebank model
#
# Use scripts/conllu2tab.py to convert the CoNLL-U format to the tab format
# used by efselab.

import os.path

from .options import args
from .configuration import Configuration
from .form import (
    TextField,
    FeatureSet,
    suffix,
    prefix,
    normalize,
    abstract,
    delexicalize,
)
from .tagset import Tagset
from .taglexicon import TagLexicon
from .tools import read_dict

train_filename = args.train
lang = os.path.basename(train_filename).split("-")[0]

# There are plenty of other configuration options (see configuration.py), the
# only mandatory one is the name of the model, which will be used for the C
# file generated.
config = Configuration("udt_" + lang, args)
# For debugging purposes, you may want to disable optimizations:
# config = Configuration('udt_' + lang, cflags=['-g', '-O0'])

# Read tagset and tag lexicon from corpus
udt_tags, udt_norm_tags = read_dict(train_filename, 0, 1)
# UDv1
# udt_tags = set(('ADJ ADP PUNCT ADV AUX SYM INTJ CONJ X NOUN DET PROPN NUM ' +
#                'VERB PART PRON SCONJ').split())
# UDv2
udt_tags = set(
    (
        "ADJ ADP ADV AUX CCONJ DET INTJ NOUN NUM PART PRON PROPN "
        "PUNCT SCONJ SYM VERB X"
    ).split()
)

# Create a Tagset object from the tags we have read
UDT = Tagset(udt_tags, config)

text_field = 0
tag_field = 1

# Define tags (relative to the current position during a search)
this_tag = UDT.tag(tag_field, 0)
last_tag = UDT.tag(tag_field, -1)
last_last_tag = UDT.tag(tag_field, -2)

# Define words (relative to the current position during a search)
this_word = TextField(text_field, 0)
last_word = TextField(text_field, -1)
next_word = TextField(text_field, 1)
next_next_word = TextField(text_field, 2)

# Each tuple below represents a single feature template.
fs = FeatureSet(
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
    config,
)

# These tags will be tried for unknown words (i.e. words not in the training
# data)
open_tags = sorted(
    UDT.tag_idx[tag] for tag in "ADJ ADV INTJ NOUN NUM PROPN VERB SYM X".split()
)

# Create a TagLexicon object from the tag lexicon we loaded with read_dict()
# above.
# NOTE: although items are added one by one below, we must give the number of
# items in the constructor: len(udt_norm_tags)
tl = TagLexicon("UDT_lexicon", text_field, len(udt_norm_tags), open_tags, config)
for norm, tags in udt_norm_tags.items():
    tl[norm] = [UDT.tag_idx[tag] for tag in tags]

# Generate C code and (optionally) compile.
config.build()
