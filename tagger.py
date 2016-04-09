import udt_suc_sv
import suc

def suc_tag(tagger_weights, sentence):
    tags = suc.tag(tagger_weights, sentence)
    return tags

def udt_tag(sentence, lemmas, suc_tags, ud_tagger_weights):
    suc_sentence = [(lemma, tag[:2], tag) for lemma, tag in zip(lemmas, suc_tags)]
    ud_tags = udt_suc_sv.tag(ud_tagger_weights, suc_sentence)
    ud_tags = ud_verb_heuristics(ud_tags, sentence, lemmas)
    return zip(sentence, suc_tags, ud_tags, lemmas)

def ud_verb_heuristics(ud_tags, tokens, lemmas):
    """Heuristics to improve accuracy of UD tags, return modified ud_tags"""
    ud_tags = list(ud_tags)
    n = len(ud_tags)
    for i in range(n):
        if ud_tags[i] == 'AUX' and lemmas[i] != 'vara':
            for j in range(i+1, n):
                if ud_tags[j] in ('AUX', 'VERB'):
                    # If followed by AUX or VERB, do nothing
                    break
                if (ud_tags[j] in ('SCONJ', 'PUNCT')) \
                        or tokens[j].lower() == 'som' or j == n-1:
                    # If no AUX/VERB before SCONJ, PUNCT, "som" or end of
                    # sentence, change to VERB
                    ud_tags[i] = 'VERB'
                    break
    return ud_tags
