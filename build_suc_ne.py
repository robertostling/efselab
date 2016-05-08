# Tagger configuration for named entities using the SUC corpus + the Stockholm
# Internet Corpus (SIC). It requires SUC-tagged and lemmatized data as input,
# and is intended for use with the Swedish annotation pipeline.

from options import args
from configuration import Configuration
from form import *
from tagset import Tagset
from taglexicon import TagLexicon
from wclexicon import WCLexicon
from tools import read_dict

import sys

assert args.n_train_fields == 4

config = Configuration('suc_ne', args)

if config.skip_generate:
    config.build()
    sys.exit(0)

# Read tagset and tag lexicon (coarse SUC -> UD) from corpus
suc_ne_tags, suc_norm_ne_tags = read_dict(
    'suc-data/suc-blogs-ne-train.tab', 1, 3)

# Create a Tagset object from the tags we have read
SUC_NE = Tagset(suc_ne_tags, config)

text_field      = 0
lemma_field     = 1
suc_full_field  = 2
tag_field       = 3

Names = WCLexicon.from_file('names', 'suc-data/names.txt', config)

WC = WCLexicon.from_file('brown', 'suc-data/swe-brown100.txt', config)

# Define tags (relative to the current position during a search)
this_tag        = SUC_NE.tag(tag_field, 0)
last_tag        = SUC_NE.tag(tag_field, -1)
last_last_tag   = SUC_NE.tag(tag_field, -2)

# POS tags (+ morphology)
this_pos        = TextField(suc_full_field, 0)
last_pos        = TextField(suc_full_field, -1)
next_pos        = TextField(suc_full_field, 2)

# Define lemmas (relative to the current position during a search)
this_lemma      = TextField(lemma_field, 0)
last_lemma      = TextField(lemma_field, -1)
next_lemma      = TextField(lemma_field, 1)
next_next_lemma = TextField(lemma_field, 2)

# Define words (relative to the current position during a search)
this_word       = TextField(text_field, 0)
last_word       = TextField(text_field, -1)
next_word       = TextField(text_field, 1)
next_next_word  = TextField(text_field, 2)

# Use name lexicon
this_name       = Names.lookup(this_lemma)
last_name       = Names.lookup(last_lemma)
next_name       = Names.lookup(next_lemma)

# Use case-sensitive word clusters
this_wc         = WC.lookup(this_word)
last_wc         = WC.lookup(last_word)
next_wc         = WC.lookup(next_word)
next_next_wc    = WC.lookup(next_next_word)

# Each tuple below represents a single feature template.
fs = FeatureSet([
        (this_tag, last_tag),
        (this_tag, last_tag, last_last_tag),

        (this_tag, last_pos),
        (this_tag, this_pos),
        (this_tag, next_pos),

        (this_tag, last_name),
        (this_tag, this_name),
        (this_tag, next_name),
        (this_tag, this_name, last_name),
        (this_tag, this_name, next_name),

        (this_tag, last_wc),
        (this_tag, this_wc),
        (this_tag, next_wc),
        (this_tag, next_wc, next_next_wc),
        (this_tag, last_wc, next_wc),

        (this_tag, delexicalize(this_word)),
        (this_tag, abstract(this_word)),

        (this_tag, this_lemma),
        (this_tag, this_lemma, last_lemma),
        (this_tag, this_lemma, next_lemma),
        (this_tag, next_lemma),
        (this_tag, last_lemma),
        
        # This is actually required for the tag lexicon to work properly
        (this_tag, normalize(this_lemma)),

        (this_tag, prefix(normalize(this_word), 1)),
        (this_tag, prefix(normalize(this_word), 2)),
        (this_tag, prefix(normalize(this_word), 3)),
        (this_tag, prefix(normalize(this_word), 4)),

        (this_tag, suffix(normalize(this_word), 1)),
        (this_tag, suffix(normalize(this_word), 2)),
        (this_tag, suffix(normalize(this_word), 3)),
        (this_tag, suffix(normalize(this_word), 4))
    ], config)

open_tags = sorted(SUC_NE.tag_idx[tag] for tag in SUC_NE.tags)

# Create a TagLexicon object from the tag lexicon we loaded with read_dict()
# above.
tl = TagLexicon('SUC_NE_lexicon', lemma_field, len(suc_norm_ne_tags),
                open_tags, config)
for norm, tags in suc_norm_ne_tags.items():
    tl[norm] = [SUC_NE.tag_idx[tag] for tag in tags]

# Generate C code and (optionally) compile.
config.build()

