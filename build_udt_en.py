# Tagger configuration for the English version of the Universal Dependencies
# Treebank. Data is included in the repository for convenience, so to generate
# an Englis PoS tagger you can simply execute this file:
#
#   python3 udt_en.py
#
# This could easily be generalized to create taggers for each of the languages
# in the treebank, but that is left as an exercise to the reader (for now).

from options import args
from configuration import Configuration
from form import *
from tagset import Tagset
from taglexicon import TagLexicon
from wclexicon import WCLexicon
from tools import read_dict

# There are plenty of other configuration options (see configuration.py), the
# only mandatory one is the name of the model, which will be used for the C
# file generated.
config = Configuration('udt_en', args)
# For debugging purposes, you may want to disable optimizations:
#config = Configuration('udt_en', cflags=['-g', '-O0'])

# On 64-bit systems the following might be better, if the dictionaries are
# large enough to cause many collisions.
#config = Configuration('udt_en', partial_hash_bits=64, feat_hash_bits=64, lexicon_hash_bits=64)

# Read tagset and tag lexicon from corpus
udt_en_tags, udt_en_norm_tags = read_dict('data/udt-en-train.tab', 0, 1)

# Create a Tagset object from the tags we have read
UDT_EN = Tagset(udt_en_tags, config)

# Load a file with word clusters
# This is taken from Turian et al.:
#   http://metaoptimize.com/projects/wordreprs/
# and has been converted using the brown2wcl.py script.
WC = WCLexicon.from_file('brown', 'data/en-brown320.txt', config)

text_field  = 0
tag_field   = 1

# Define tags (relative to the current position during a search)
this_tag        = UDT_EN.tag(tag_field, 0)
last_tag        = UDT_EN.tag(tag_field, -1)
last_last_tag   = UDT_EN.tag(tag_field, -2)

# Define words (relative to the current position during a search)
this_word       = TextField(text_field, 0)
last_word       = TextField(text_field, -1)
next_word       = TextField(text_field, 1)
next_next_word  = TextField(text_field, 2)

# Use case-sensitive word clusters
this_wc         = WC.lookup(this_word)
last_wc         = WC.lookup(last_word)
next_wc         = WC.lookup(next_word)
next_next_wc    = WC.lookup(next_next_word)

# If we wanted case-insensitive word clusters, it would look like this:
#this_wc         = WC.lookup(normalize(this_word))
# ...

# Each tuple below represents a single feature template.
fs = FeatureSet([
        # Tag bigram and trigram features
        (this_tag, last_tag),
        (this_tag, last_tag, last_last_tag),
       
        # Word class features
        (this_tag, last_wc),
        (this_tag, this_wc),
        (this_tag, next_wc),
        (this_tag, next_wc, next_next_wc),
        (this_tag, last_wc, next_wc),

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

        # Lower-cased prefix features.
        (this_tag, prefix(normalize(this_word), 1)),
        (this_tag, prefix(normalize(this_word), 2)),
        (this_tag, prefix(normalize(this_word), 3)),
        (this_tag, prefix(normalize(this_word), 4)),

        # Lower-cased suffix features.
        (this_tag, suffix(normalize(this_word), 1)),
        (this_tag, suffix(normalize(this_word), 2)),
        (this_tag, suffix(normalize(this_word), 3)),
        (this_tag, suffix(normalize(this_word), 4))
    ], config)

# These tags will be tried for unknown words (i.e. words not in the training
# data)
open_tags = sorted(
        UDT_EN.tag_idx[tag]
        for tag in 'ADJ ADV INTJ NOUN PROPN VERB SYM X'.split())

# Create a TagLexicon object from the tag lexicon we loaded with read_dict()
# above.
# NOTE: although items are added one by one below, we must give the number of
# items in the constructor: len(udt_en_norm_tags)
tl = TagLexicon('UDT_EN_lexicon', len(udt_en_norm_tags), open_tags, config)
for norm, tags in udt_en_norm_tags.items():
    tl[norm] = [UDT_EN.tag_idx[tag] for tag in tags]


# Generate C code and (optionally) compile.
config.build()

