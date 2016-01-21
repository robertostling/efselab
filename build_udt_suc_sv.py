# Tagger configuration for the Swedish version of the Universal Dependencies
# Treebank, with SUC tags given as input. The purpose of this is to convert
# SUC-tagged data to UD tags, as part of the Swedish annotation pipeline.

from options import args
from configuration import Configuration
from form import *
from tagset import Tagset
from taglexicon import TagLexicon
from tools import read_dict

# There are plenty of other configuration options (see configuration.py), the
# only mandatory one is the name of the model, which will be used for the C
# file generated.
config = Configuration('udt_suc_sv', args)

# Read tagset and tag lexicon (coarse SUC -> UD) from corpus
udt_sv_tags, udt_sv_suc_tags = read_dict('data/sv-ud-train.tab', 1, 3)
udt_sv_tags.add('X')

# Create a Tagset object from the tags we have read
UDT_SV = Tagset(udt_sv_tags, config)

lemma_field     = 0
suc_field       = 1
suc_full_field  = 2
tag_field       = 3

# UD tag (this is not really a sequence model, so we don't depend on history)
this_tag        = UDT_SV.tag(tag_field, 0)

# Word form features (lemmas)
this_word       = TextField(lemma_field, 0)

# Coarse SUC tags (given as input)
#
# The reason we apply normalization (= lower-casing) to these tags is because
# they're also used in the tag dictionary, which requires normalized inputs.
this_suc        = normalize(TextField(suc_field, 0))
last_suc        = normalize(TextField(suc_field, -1))
next_suc        = normalize(TextField(suc_field, 1))
last_last_suc   = normalize(TextField(suc_field, -2))
next_next_suc   = normalize(TextField(suc_field, 2))

# Full SUC tags
this_suc_full   = TextField(suc_full_field, 0)

# Each tuple below represents a single feature template.
fs = FeatureSet([
        # SUC full tag features
        (this_tag, this_suc_full),
        (this_tag, this_suc_full, last_suc),
        (this_tag, this_suc_full, next_suc),
        # SUC tag features
        (this_tag, this_suc),
        (this_tag, this_suc, last_suc),
        (this_tag, this_suc, next_suc),
        (this_tag, this_suc, next_suc, next_next_suc),
        (this_tag, this_suc, last_suc, last_last_suc),
        (this_tag, this_suc, last_suc, next_suc),
        # Word form features
        (this_tag, this_word),
        #(this_tag, this_suc, this_word),
    ], config)

# For tags not seen in the training material, assume UD tag X.
open_tags = sorted(
        UDT_SV.tag_idx[tag]
        for tag in ['X'])

# Create a TagLexicon object from the tag lexicon we loaded with read_dict()
# above.
tl = TagLexicon('UDT_SV_lexicon', suc_field, 0x1000, open_tags, config)
for suc, tags in udt_sv_suc_tags.items():
    tl[suc] = [UDT_SV.tag_idx[tag] for tag in tags]

# Generate C code and (optionally) compile.
config.build()

