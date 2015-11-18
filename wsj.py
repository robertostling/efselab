# Tagger configuration for the Wall Street Journal texts from the Penn
# Treebank. The data itself must be licensed from LDC.
# Brown clusters from Turian et al. are used:
# http://metaoptimize.com/projects/wordreprs/

from configuration import Configuration
from form import *
from tagset import Tagset
from taglexicon import TagLexicon
from wclexicon import WCLexicon
from tools import read_dict

import sys

config = Configuration('wsj')

# Read tagset and tag lexicon from corpus
wsj_tags, wsj_norm_tags = read_dict('data/wsj-train.txt', 0, 1)

# Create a Tagset object from the tags we have read
WSJ = Tagset(wsj_tags, config)

# Load a file with word classes
WC = WCLexicon.from_file('brown', 'data/eng-brown320.txt', config)

text_field  = 0
tag_field   = 1

# Define tags (relative to the current position during a search)
this_tag        = WSJ.tag(tag_field, 0)
last_tag        = WSJ.tag(tag_field, -1)
last_last_tag   = WSJ.tag(tag_field, -2)

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
        (this_tag, last_tag),
        (this_tag, last_tag, last_last_tag),
       
        (this_tag, last_wc),
        (this_tag, this_wc),
        (this_tag, next_wc),
        (this_tag, next_wc, next_next_wc),
        (this_tag, last_wc, next_wc),

        (this_tag, delexicalize(this_word)),
        (this_tag, abstract(this_word)),
        (this_tag, normalize(this_word)),
        (this_tag, normalize(next_word)),
        (this_tag, normalize(last_word)),

        (this_tag, prefix(normalize(this_word), 1)),
        (this_tag, prefix(normalize(this_word), 2)),
        (this_tag, prefix(normalize(this_word), 3)),
        (this_tag, prefix(normalize(this_word), 4)),

        (this_tag, suffix(normalize(this_word), 1)),
        (this_tag, suffix(normalize(this_word), 2)),
        (this_tag, suffix(normalize(this_word), 3)),
        (this_tag, suffix(normalize(this_word), 4))
    ], config)

# These tags will be tried for unknown words (i.e. words not in the training
# data)
open_tags = sorted(
        WSJ.tag_idx[tag]
        for tag in ('CD FW JJ JJR JJS NN NNP NNPS NNS RB RBR RBS SYM UH ' +
                    'VB VBD VBG VBN VBP VBZ').split())

# Create a TagLexicon object from the tag lexicon we loaded with read_dict()
# above.
tl = TagLexicon('WSJ_lexicon', len(wsj_norm_tags), open_tags, config)
for norm, tags in wsj_norm_tags.items():
    tl[norm] = [WSJ.tag_idx[tag] for tag in tags]

config.generate()

