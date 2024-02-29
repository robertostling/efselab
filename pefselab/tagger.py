import udt_suc_sv
import suc
import suc_ne
import collections

# Tags a sentence with SUC tags based on a trained model
class SucTagger():

    def __init__(self, tagging_model):
        with open(tagging_model, 'rb') as f:
            self.tagger_weights = f.read()

    def tag(self, sentence):
        tags_list = suc.tag(self.tagger_weights, sentence)
        return tags_list

# Tags a sentence with SUC-style named entity tags based on a trained model
class SucNETagger():

    def __init__(self, tagging_model):
        with open(tagging_model, 'rb') as f:
            self.tagger_weights = f.read()

    def tag(self, sentence):
        tags_list = suc_ne.tag(self.tagger_weights, sentence)
        return tags_list


# Tags a sentence with UD tags based on a model trained on SUC tags
class UDTagger():
    FEATURE_MAPPING = {
        "AKT": ["Voice=Act"],
        "DEF": ["Definite=Def"],
        "GEN": ["Case=Gen"],
        "IND": ["Definite=Ind"],
        "INF": ["VerbForm=Inf"],
        "IMP": ["VerbForm=Fin", "Mood=Imp"],
        "KOM": ["Degree=Cmp"],
        "KON": ["Mood=Sub"],
        "NEU": ["Gender=Neut"],
        "NOM": ["Case=Nom"],
        "MAS": ["Gender=Masc"],
        "OBJ": ["Case=Acc"],
        "PLU": ["Number=Plur"],
        "POS": ["Degree=Pos"],
        "PRF": ["VerbForm=Part", "Tense=Past"],
        "PRT": ["VerbForm=Fin", "Tense=Past"],
        "PRS": ["VerbForm=Fin", "Tense=Pres"],
        "SFO": ["Voice=Pass"],
        "SIN": ["Number=Sing"],
        "SMS": [],
        "SUB": ["Case=Nom"],
        "SUP": ["VerbForm=Sup"],
        "SUV": ["Degree=Sup"],
        "UTR": ["Gender=Com"],
        "AN": ["Abbr=Yes"],
        "-": [],
    }

    # Words that should have the feature Polarity=Neg
    NEGATIVE = {
        ('inte', 'AB'),
        ('icke', 'AB'),
        ('aldrig', 'AB'),
        ('knappast', 'AB'),
        ('näppeligen', 'AB'),
        ('varken', 'AB'),
        ('föga', 'AB'),
        ('igalunda', 'AB'),
        ('ej', 'AB'),
        #('nej', 'IN'),
        #('nehej', 'IN'),
        #('nejdå', 'IN'),
        #('nix', 'IN'),
    }

    # Words that should have the feature Polarity=Pos
    # NOTE: this is currently not used in the Swedish version
    #POSITIVE = {
    #    ('ja', 'IN'),
    #    ('jaa', 'IN'),
    #    ('jadå', 'IN'),
    #    ('jajamen', 'IN'),
    #    ('jajamän', 'IN'),
    #    ('jajamensan', 'IN'),
    #}

    def __init__(self, tagging_model):
        with open(tagging_model, 'rb') as f:
            self.tagger_weights = f.read()

    def _is_nonstring_iterable(self, value):
        if not isinstance(value, collections.Iterable) or isinstance(value, str):
            raise TypeError("Argument is not of the correct type")

    def tag(self, sentence, lemmas, suc_tags_list):
        self._is_nonstring_iterable(sentence)
        self._is_nonstring_iterable(lemmas)
        self._is_nonstring_iterable(suc_tags_list)

        suc_sentence = [(lemma, tag.split('|',1)[0], tag)
                        for lemma, tag in zip(lemmas, suc_tags_list)]
        tag_list = udt_suc_sv.tag(self.tagger_weights, suc_sentence)
        tag_list = self.ud_verb_heuristics(tag_list, sentence, lemmas)
        features = self.ud_features(suc_tags_list, lemmas)
        return tuple(["|".join(t) for t in zip(tag_list, features)])

    def ud_verb_heuristics(self, ud_tags, tokens, lemmas):
        """Heuristics to improve accuracy of UD tags, return modified ud_tags"""
        ud_tags = list(ud_tags)
        n = len(ud_tags)
        for i in range(n):
            if ud_tags[i] == 'AUX':
                if lemmas[i] == 'vara':
                    # Trust the copula classifier
                    continue
                for j in range(i + 1, n):
                    if ud_tags[j] in ('AUX', 'VERB'):
                        # If followed by AUX or VERB, do nothing
                        break
                    if (ud_tags[j] in ('SCONJ', 'PUNCT')) \
                            or tokens[j].lower() == 'som' or j == n - 1:
                        # If no AUX/VERB before SCONJ, PUNCT, "som" or end of
                        # sentence, change to VERB
                        ud_tags[i] = 'VERB'
                        break
        return ud_tags

    def ud_features(self, suc_tags_list, lemmas):
        ud_features = []

        for suc_tags, lemma in zip(suc_tags_list, lemmas):
            # Apparently incorrect code from the UD 1 version:
            #if "|" not in suc_tags:
            #    ud_features.append("_")
            #    continue

            if "|" in suc_tags:
                fields = suc_tags.split("|")
                suc_tag = fields[0]
                suc_features = fields[1:]
            else:
                suc_tag = suc_tags
                suc_features = []

            ud_feature_list = []
            for suc_feature in suc_features:
                # Don't include suc_features with multiple options in the UD suc_features
                if "/" not in suc_feature:
                    ud_feature_list += self.FEATURE_MAPPING[suc_feature]

            if "VerbForm=Fin" in ud_feature_list and "Mood=Imp" not in ud_feature_list and "Mood=Sub" not in ud_feature_list:
                ud_feature_list += ["Mood=Ind"]

            if suc_tag in ["HA", "HD", "HP", "HS"]:
                ud_feature_list += ["PronType=Int,Rel"]

            if suc_tag in ["HS", "PS"]:
                ud_feature_list += ["Poss=Yes"]  # Test this!

            if suc_tag == "UO":
                ud_feature_list += ["Foreign=Yes"]

            if (lemma, suc_tag) in self.NEGATIVE:
                ud_feature_list += ["Polarity=Neg"]
            # Currently not used in the Swedish UD treebank:
            #elif (lemma, suc_tag) in self.POSITIVE:
            #    ud_feature_list += ["Polarity=Pos"]

            ud_features.append("|".join(sorted(ud_feature_list)) or "_")

        return ud_features
