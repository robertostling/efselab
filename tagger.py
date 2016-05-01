import udt_suc_sv
import suc

# Tags a sentence with SUC tags based on a trained model
class SucTagger():

    def __init__(self, tagging_model):
        with open(tagging_model, 'rb') as f:
            self.tagger_weights = f.read()

    def tag(self, sentence):
        tags_list = suc.tag(self.tagger_weights, sentence)
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
        "AN": [],
        "-": [],
    }

    def __init__(self, tagging_model):
        with open(tagging_model, 'rb') as f:
            self.tagger_weights = f.read()

    def tag(self, sentence, lemmas, suc_tags_list):
        suc_sentence = [(lemma, tag[:2], tag) for lemma, tag in zip(lemmas, suc_tags_list)]
        tag_list = udt_suc_sv.tag(self.tagger_weights, suc_sentence)
        tag_list = self.ud_verb_heuristics(tag_list, sentence, lemmas)
        features = self.ud_features(suc_tags_list)
        return ["|".join(t) for t in zip(tag_list, features)]

    def ud_verb_heuristics(self, ud_tags, tokens, lemmas):
        """Heuristics to improve accuracy of UD tags, return modified ud_tags"""
        ud_tags = list(ud_tags)
        n = len(ud_tags)
        for i in range(n):
            if ud_tags[i] == 'AUX' and lemmas[i] != 'vara':
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

    def ud_features(self, suc_tags_list):
        ud_features = []

        for suc_tags in suc_tags_list:
            if "|" not in suc_tags:
                ud_features.append("_")
                continue

            suc_tag, suc_features = suc_tags.split("|", 1)

            ud_feature_list = []
            for suc_feature in suc_features.split("|"):
                # Don't include suc_features with multiple options in the UD suc_features
                if "/" not in suc_feature:
                    ud_feature_list += self.FEATURE_MAPPING[suc_feature]

            if "VerbForm=Fin" in ud_feature_list and "Mood=Imp" not in ud_feature_list and "Mood=Sub" not in ud_feature_list:
                ud_feature_list += ["Mood=Ind"]

            if suc_tag in ["HA", "HD", "HP", "HS"]:
                ud_feature_list += ["PronType=Int,Rel"]

            if suc_tag in ["HS", "PS"]:
                ud_feature_list += ["Poss=Yes"]  # Test this!

            ud_features.append("|".join(sorted(ud_feature_list)) or "_")

        return ud_features
