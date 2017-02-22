"""Convert the sv-ud-*.tab files from UD 1 to UD 2 format

These are in a 4-column format:
    lemma form (lowercase)
    SUC tag
    SUC features
    UD tag
"""

import sys

# "verka" needs to be manually disambiguated
copulas = set('vara bli heta förbli'.split())

def translate(lemma, suc_tag, suc_feats, ud1_tag):
    if ud1_tag == 'CONJ':
        return 'CCONJ'
    elif ud1_tag == 'VERB' and lemma in copulas:
        return 'AUX'
    else:
        return ud1_tag

for lineno,line in enumerate(sys.stdin):
    fields = line.rstrip('\n').split('\t')
    if len(fields) == 1:
        print()
    elif len(fields) == 4:
        print('\t'.join(fields[:3] + [translate(*fields)]))
    else:
        print('WARNING: line %d: %d columns (4 or 0 expected)' % (
            lineno, len(fields)), file=sys.stderr)

