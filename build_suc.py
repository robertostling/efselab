# Tagger configuration for SUC (Stockholm-Umeå Corpus)
#
# This depends on data files that require a signed license agreement.
# http://www.ling.su.se/suc

from options import args
from configuration import Configuration
from form import *
from tagset import Tagset
from taglexicon import TagLexicon
from wclexicon import WCLexicon
from tools import read_dict

import sys

config = Configuration('suc', args)

if config.skip_generate:
    config.build()
    sys.exit(0)

# Read tagset and tag lexicon from corpus
suc_tags, suc_norm_tags = read_dict('suc-data/suc-blogs.tab', 0, 1)

with open('suc-data/extra.txt', 'r', encoding='utf-8') as f:
    for line in f:
        token, tag = line.rstrip('\n').split('\t')
        suc_norm_tags[token.lower()].add(tag)
        suc_tags.add(tag)

with open('suc-data/saldo.txt', 'r', encoding='utf-8') as f:
    for line in f:
        token, _, tag, _ = line.rstrip('\n').split('\t')
        suc_norm_tags[token.lower()].add(tag)
        suc_tags.add(tag)

# Create a Tagset object from the tags we have read
SUC = Tagset(suc_tags, config)

# Load a file with word classes
WC = WCLexicon.from_file('brown', 'suc-data/swe-brown100.txt', config)

text_field  = 0
tag_field   = 1

# Define tags (relative to the current position during a search)
this_tag        = SUC.tag(tag_field, 0)
last_tag        = SUC.tag(tag_field, -1)
last_last_tag   = SUC.tag(tag_field, -2)

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
        SUC.tag_idx[tag]
        for tag in SUC.tags
        if tag[:2] in 'AB JJ NN VB PC RG RO PM UO'.split())

# Create a TagLexicon object from the tag lexicon we loaded with read_dict()
# above.
tl = TagLexicon('SUC_lexicon', text_field, len(suc_norm_tags), open_tags, config)
for norm, tags in suc_norm_tags.items():
    tl[norm] = [SUC.tag_idx[tag] for tag in tags]

config.build()

