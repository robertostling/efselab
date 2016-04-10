import udt_suc_sv
import suc


class SucTagger():

    def __init__(self, tagging_model):
        with open(tagging_model, 'rb') as f:
            self.tagger_weights = f.read()

    def tag(self, sentence):
        tags = suc.tag(self.tagger_weights, sentence)
        return tags


class UDTagger():

    def __init__(self, tagging_model):
        with open(tagging_model, 'rb') as f:
            self.tagger_weights = f.read()

    def tag(self, sentence, lemmas, suc_tags):
        suc_sentence = [(lemma, tag[:2], tag)
                        for lemma, tag in zip(lemmas, suc_tags)]
        ud_tags = udt_suc_sv.tag(self.tagger_weights, suc_sentence)
        ud_tags = self.ud_verb_heuristics(ud_tags, sentence, lemmas)
        return ud_tags

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
