from collections import defaultdict, Counter


cdef class TabReader:
    cdef object f

    def __init__(self, filename):
        self.f = open(filename, 'r', encoding='utf-8')


    cdef list read_sentence(self):
        cdef list buf, fields
        cdef str line

        buf = []
        while True:
            line = self.f.readline().rstrip('\n')
            if not line: return buf
            fields = line.split('\t')
            buf.append(fields)


cdef list from_conll(list sent):
    cdef list flt
    flt = [(
        fields[1],
        fields[2],
        fields[3]+'|'+fields[5] if fields[5] else fields[3])
        for fields in sent]
    return flt


cdef str capitalize(str lemma, str form, str tag):
    cdef list upper
    cdef str c

    if tag.endswith('AN'):
        if form.isupper(): return lemma.upper()
    elif form and (tag[:2] in ('NN', 'JJ', 'VB')) and not form[1:].islower():
        upper = [c.isupper() for c in form]
        return ''.join([(c.upper() if b else c)
                        for b,c in zip(upper, lemma)])
    elif tag.startswith('PM'):
        if form.isupper() and not lemma[1:].islower(): return lemma.upper()
        else: return lemma[0].upper() + lemma[1:].lower()
    return lemma.lower()


cdef class SUCLemmatizer:
    cdef dict lexicon

    def __init__(self):
        self.lexicon = {}


    cpdef str predict(self, str form, str tag):
        cdef str lemma, suffix, form_lower
        cdef tuple form_tag
        cdef int i

        form_lower = form.lower()
        form_tag = (form_lower, tag)
        lemma = self.lexicon.get(form_tag)
        if not lemma is None:
            return capitalize(lemma, form, tag).replace(' ', '_')
        if tag == 'PM|GEN' and form_lower.endswith('s'):
            return capitalize(form[:-1], form, tag).replace(' ', '_')
        for i in range(1, len(form)-2):
            suffix = form[i:]
            form_tag = (suffix, tag)
            lemma = self.lexicon.get(form_tag)
            if not lemma is None:
                return capitalize(form[:i] + lemma, form, tag).replace(' ', '_')
        return capitalize(form, form, tag).replace(' ', '_')


    cpdef float evaluate(self, str filename):
        cdef TabReader r
        cdef list sent
        cdef str form, lemma, tag, pred_lemma
        cdef int n_correct, n_tokens

        n_correct = 0
        n_tokens = 0
        r = TabReader(filename)
        while True:
            sent = r.read_sentence()
            if not sent: break
            for form, lemma, tag in from_conll(sent):
                pred_lemma = self.predict(form, tag)
                n_tokens += 1
                if pred_lemma == lemma: n_correct += 1
                else:
                    print(form, tag, lemma, pred_lemma)

        return float(n_correct) / float(n_tokens)


    cpdef save(self, str filename):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(
                ['\t'.join((form, lemma, tag))
                 for (form, tag), lemma in self.lexicon.items()]))


    cpdef load(self, str filename):
        with open(filename, 'r', encoding='utf-8') as f:
            self.lexicon = { (form, tag): lemma for form, lemma, tag in
                             [line.rstrip('\n').split('\t') for line in f] }


cpdef train(list conll_files, list lexicon_files):
    """Return a trained SUCLemmatizer object

    conll_files -- list of filenames containing SUC-format CoNLL files
    lexicon_files -- list of filenames containing tag dictionaries (mostly
                     extracted from SALDO, taken from the old Stagger data
    """
    cdef str filename, line, form, lemma, tag, form_lower
    cdef tuple form_tag
    cdef TabReader r
    cdef list sent
    cdef dict pc_prf_lemma, pc_prs_lemma

    lemma_count = defaultdict(Counter)

    for filename in lexicon_files:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                form, lemma, tag, _ = line.rstrip('\n').split('\t')
                form_lower = form.lower()
                form_tag = (form_lower, tag)
                lemma_count[form_tag][lemma] += 1

    pc_prf_lemma = {}
    pc_prs_lemma = {}

    for (form, tag), counts in lemma_count.items():
        if tag == 'PC|PRF|UTR|SIN|IND|NOM':
            pc_prf_lemma[counts.most_common(1)[0][0]] = form
        if tag == 'PC|PRS|UTR/NEU|SIN/PLU|IND/DEF|NOM':
            pc_prs_lemma[counts.most_common(1)[0][0]] = form

    for (form, tag), counts in lemma_count.items():
        if tag.startswith('PC|PRF'):
            for lemma in list(counts.keys()):
                counts[lemma] -= 1
                counts[pc_prf_lemma.get(lemma, lemma)] += 1
        elif tag.startswith('PC|PRS'):
            for lemma in list(counts.keys()):
                counts[lemma] -= 1
                counts[pc_prs_lemma.get(lemma, lemma)] += 1

    for filename in conll_files:
        r = TabReader(filename)
        while True:
            sent = r.read_sentence()
            if not sent: break
            for form, lemma, tag in from_conll(sent):
                form_lower = form.lower()
                form_tag = (form_lower, tag)
                lemma_count[form_tag][lemma] += 1

    l = SUCLemmatizer()
    l.lexicon = { form_tag: counts.most_common(1)[0][0]
                  for form_tag, counts in lemma_count.items() }

    return l

