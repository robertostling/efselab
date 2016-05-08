import sys
from collections import defaultdict
import hashlib, math

from tagset import Tag


def fixed_hash(seed, bits):
   return '0x'+hashlib.sha256(
               seed.encode('ascii')).hexdigest()[:math.ceil(bits/4)]


class Form:
    def get_field(self):
        return self.parent.get_field() if self.parent else None
    
    def get_position(self):
        return self.parent.get_position() if self.parent else None

    def get_affix(self):
        return self.parent.get_affix() if self.parent else None

    def get_translations(self):
        return self.parent.get_translations() if self.parent else ()

    def get_wclexicon(self):
        return None

    def get_ident(self):
        field = str(self.get_field())
        #position = str(self.get_position()).replace('-', 'm')
        affix = self.get_affix()
        translations = self.get_translations()
        wclexicon = self.get_wclexicon()
        return '_'.join((
            field,
            #position,
            (('%s%d' % ('pre' if affix[0] else 'suf', affix[1]))
             if affix else 'x'),
            ('_'.join(translations) if translations else 'x')) +
            ((wclexicon.name,) if wclexicon else ()))


class TextField(Form):
    def __init__(self, field, position):
        self.field = field
        self.position = position
        self.parent = None

    def get_field(self): return self.field

    def get_position(self): return self.position


class Affix(Form):
    def __init__(self, parent, is_prefix, n):
        self.parent = parent
        self.is_prefix = is_prefix
        self.n = n

    def get_affix(self): return (self.is_prefix, self.n)


class Translation(Form):
    def __init__(self, parent, translation):
        assert not parent.get_affix()
        assert translation in ['normalize', 'abstract', 'delexicalize']
        self.parent = parent
        self.translation = translation

    def get_translations(self):
        return self.parent.get_translations() + (self.translation,)


class Lookup(Form):
    def __init__(self, parent, wclexicon):
        self.parent = parent
        self.wclexicon = wclexicon

    def get_wclexicon(self):
        return self.wclexicon


class FeatureSet:
    def __init__(self, terms, config):
        config.feature_set = self
        self.terms = terms
        self.config = config

        self._field_translations = defaultdict(set)
        for cons in terms:
            for con in cons:
                if isinstance(con, Form):
                    field = con.get_field()
                    translations = con.get_translations()
                    assert len(translations) <= 1
                    if translations != ():
                        self._field_translations[field].add(translations)

    def c_emit(self, f):
        pi_hashes = set()

        f.write('''
static int extract_invariant(
        const uint8_t **field_buf,
        const size_t *field_len,
        size_t n_fields,
        size_t n_items,
        partial_hash_t *pi_hashes)
{
size_t i;

for (i=0; i<n_items; i++) {
''')

        if self.config.use_unicode:

            f.write('''
    uint32_t codep_buf[MAX_STR];
    size_t codep_buf_len;

    uint32_t trans_buf[MAX_STR];
    size_t trans_buf_len;
''')

            for cons in self.terms:
                for con in cons:
                    if not isinstance(con, Form): continue
                    if con.get_translations(): continue
                    hash_name = 'hash_%s' % con.get_ident()
                    if hash_name in pi_hashes: continue
                    pi_hashes.add(hash_name)
                    field = con.get_field()
                    affix = con.get_affix()
                    if not affix:
                        if type(con) is Lookup:
                            f.write('''
    const partial_hash_t %s = %s;
''' % (hash_name, con.get_wclexicon().c_lookup(
        'hash%d_data(1, field_buf[%d], field_len[%d])' % (
        self.config.partial_hash_bits, field, field))))
                        else:
                            f.write('''
    const partial_hash_t %s = hash%d_data(1, field_buf[%d], field_len[%d]);
''' % (hash_name, self.config.partial_hash_bits, field, field))
                    else:
                        f.write('''
    const partial_hash_t %s = hash%d_utf8_%s(field_buf[%d], field_len[%d], %d, 2);
''' % (hash_name, self.config.partial_hash_bits,
       'prefix' if affix[0] else 'suffix', field, field, affix[1]))


            for field, translations in self._field_translations.items():
                if len(translations) >= 1:
                    f.write('''
    codep_buf_len = MAX_STR;
    if (utf8_decode(codep_buf, &codep_buf_len, field_buf[%d], field_len[%d]) < 0)
        return -1;
''' % (field, field))
                    for translation, in translations:
                        trans_buf = '%s_buf' % translation
                        trans_buf_len = '%s_buf_len' % translation
                        f.write('''
    trans_buf_len = MAX_STR;
    unicode_translate_%s(trans_buf, &trans_buf_len, codep_buf, codep_buf_len);
''' % translation)

                        for cons in self.terms:
                            for con in cons:
                                if not isinstance(con, Form):
                                    continue
                                if not con.get_field() == field:
                                    continue
                                if not con.get_translations() == (translation,):
                                    continue

                                hash_name = 'hash_%s' % con.get_ident()
                                if hash_name in pi_hashes: continue
                                pi_hashes.add(hash_name)

                                affix = con.get_affix()

                                if not affix:
                                    if type(con) is Lookup:
                                        f.write('''
    const partial_hash_t %s = %s;
''' % (hash_name, con.get_wclexicon().c_lookup(
        'hash%d_fmix(hash%d_partial_unicode(trans_buf, trans_buf_len))' %
        (self.config.partial_hash_bits, self.config.partial_hash_bits))))
                                    else:
                                        f.write('''
    const partial_hash_t %s =
        hash%d_partial_unicode(trans_buf, trans_buf_len);
''' % (hash_name, self.config.partial_hash_bits))
                                else:
                                    f.write('''
    const partial_hash_t %s =
        hash%d_partial_unicode_%s(trans_buf, trans_buf_len, %d, 2);
''' % (hash_name, self.config.partial_hash_bits,
       'prefix' if affix[0] else 'suffix', affix[1]))
            
        f.write('\n')

        pi_hashes = sorted(pi_hashes)

        for idx, hash_name in enumerate(pi_hashes):
            f.write('    pi_hashes[%d] = %s;\n' % (idx, hash_name))

        f.write('''
    field_buf += n_fields;
    field_len += n_fields;
    pi_hashes += %d;
}
return 0;
}

#define N_INVARIANTS    %d
#define N_FEATURES      %d
''' % (len(pi_hashes), len(pi_hashes), len(self.terms)))

        f.write('''
static void extract_features(
        const label *history,
        label tag,
        size_t i,
        size_t n_items,
        const partial_hash_t *pi_hashes,
        feat_hash_t *feature_hashes)
{
''')

        pi_hashes_idx = { s: i for i, s in enumerate(pi_hashes) }
        for idx,cons in enumerate(self.terms):
            form_cons = [con for con in cons if isinstance(con, Form)]
            tag_cons = [con for con in cons if isinstance(con, Tag)]

            def c_form_hash(pos, idx, ident):
                if pos == 0:
                    return 'pi_hashes[i*N_INVARIANTS + %d]' % idx
                elif pos < 0:
                    return ('((i >= %d)? pi_hashes[(i-%d)*N_INVARIANTS' +
                            '+ %d] : %s)') % (
                            -pos, -pos, idx,
                            fixed_hash(ident, self.config.partial_hash_bits))
                else:
                    return ('((i < n_items-%d)? pi_hashes[(i+%d)*N_INVARIANTS'+
                            ' + %d] : %s)') % (
                            pos, pos, idx,
                            fixed_hash(ident, self.config.partial_hash_bits))

            form_hashes = [
                    c_form_hash(
                        con.get_position(), 
                        pi_hashes_idx['hash_' + con.get_ident()],
                        con.get_ident())
                    for con in form_cons]

            # TODO: this should be optimized, normally multiple tags can be
            # merged into the same uintNN_t before hashing, to reduce the
            # number of mixing operations
            tag_values = [con.c_value() for con in tag_cons]

            def merge_hash(xs_full):
                def merge_partial(xs):
                    if len(xs) == 1: return xs[0]
                    else: return 'hash%d_mix(%s, %s)' % (
                            self.config.partial_hash_bits, xs[0],
                            merge_partial(xs[1:]))
                return 'hash%d_fmix(%s)' % (
                        self.config.feat_hash_bits, merge_partial(xs_full))

            f.write('    feature_hashes[%d] = %s;\n' % (
                idx, merge_hash([idx+1] + form_hashes + tag_values)))

        f.write('}\n\n')

        lexicon_field = self.config.lexicon.field
        normalize_idx = pi_hashes_idx.get('hash_%d_x_normalize' % lexicon_field)

        f.write('''
#if BEAM_SIZE == 1
static void beam_search(
        const uint8_t **field_buf,
        const size_t *field_len,
        size_t n_fields,
        size_t n_items,
        const real *weights,
        size_t weights_len,
        int use_lexicon,
        label *result)
{
    size_t i;
    feat_hash_t invariant_hashes[N_INVARIANTS*n_items];
    feat_hash_t feature_hashes[N_FEATURES];
    const label *tags;
    extract_invariant(
            field_buf, field_len, n_fields, n_items, invariant_hashes);

    for (i=0; i<n_items; i++) {
        real max_score = -REAL_MAX;
        label max_tag = 0;
''')

        if normalize_idx is None:
            print('WARNING: no normalize(TextField(n)) for tag dictionary '
                  'key, generated files may be incorrect',
                  file=sys.stderr)
        else:
            f.write('''
        if (use_lexicon) {
            size_t j;
            tags = get_tags(hash%d_fmix(invariant_hashes[N_INVARIANTS*i + %d]));
            if (tags[0] == 1) {
                //printf("Only tag available: %%d\\n", tags[1]);
                max_tag = (label)tags[1];
            } else {
                //printf("%%d tags available\\n", tags[0]);
                for (j=1; j<tags[0]+1; j++) {
                    extract_features(
                            result, tags[j], i, n_items,
                            invariant_hashes, feature_hashes);
                    const real score = get_score(
                            feature_hashes, N_FEATURES, weights, weights_len);
                    if (score > max_score) {
                        max_score = score;
                        max_tag = (label)tags[j];
                    }
                }
            }
        } else {''' % (self.config.lexicon_hash_bits, normalize_idx))
        f.write('''
            label tag;
            for (tag=0; tag<N_TAGS; tag++) {
                extract_features(
                        result, tag, i, n_items,
                        invariant_hashes, feature_hashes);
                const real score = get_score(
                        feature_hashes, N_FEATURES, weights, weights_len);
                if (score > max_score) {
                    max_score = score;
                    max_tag = (label)tag;
                }
            }''')
        if not normalize_idx is None:
            f.write('\n        }')
        f.write('''
        result[i] = max_tag;
    }
}
#endif
''')

        f.write('''
#if BEAM_SIZE > 1
static void beam_search(
        const uint8_t **field_buf,
        const size_t *field_len,
        size_t n_fields,
        size_t n_items,
        const real *weights,
        size_t weights_len,
        int use_lexicon,
        label *result)
{
    size_t i;
    feat_hash_t invariant_hashes[N_INVARIANTS*n_items];
    feat_hash_t feature_hashes[N_FEATURES];
    real beam_scores[BEAM_SIZE];
    label new_beams[BEAM_SIZE][n_items];
    label beams[BEAM_SIZE][n_items];
    // this is the actual beam size, whereas BEAM_SIZE is the maximum size
    size_t beam_size = 1;
    const label *tags;
    extract_invariant(
            field_buf, field_len, n_fields, n_items, invariant_hashes);

    beam_scores[0] = (real)0.0;

    for (i=0; i<n_items; i++) {
        size_t k;
        real max_score[BEAM_SIZE];
        label max_tag[BEAM_SIZE];
        size_t max_beam[BEAM_SIZE];
        for (k=0; k<BEAM_SIZE; k++) {
            max_score[k] = -REAL_MAX;
            max_tag[k] = 0;
            max_beam[k] = 0;
        }
''')
        # TODO: make a struct above, instead of 3 arrays
        # TODO: special cases for first and last step of main loop

        if normalize_idx is None:
            print('WARNING: no normalize(TextField(n)) for tag dictionary '
                  'key, generated files may be incorrect',
                  file=sys.stderr)
        else:
            f.write('''
        if (use_lexicon) {
            size_t j;
            tags = get_tags(hash%d_fmix(invariant_hashes[N_INVARIANTS*i + %d]));
            /* if (tags[0] == 1) {
                for (k=0; k<beam_size; k++) {
                    max_tag[k] = tags[1];
                    max_beam[k] = 0;
                    max_score[k] = beam_scores[k];
                }
            } else */ {
                for (j=1; j<tags[0]+1; j++) {
                    for (k=0; k<beam_size; k++) {
                        extract_features(
                                beams[k], tags[j], i, n_items,
                                invariant_hashes, feature_hashes);
                        const real score = beam_scores[k] + get_score(
                                feature_hashes, N_FEATURES,
                                weights, weights_len);
                        if (score > max_score[BEAM_SIZE-1]) {
                            size_t l,m;
                            for (l=0; score < max_score[l]; l++);
                            for (m=BEAM_SIZE-1; m>l; m--) {
                                max_score[m] = max_score[m-1];
                                max_tag[m] = max_tag[m-1];
                                max_beam[m] = max_beam[m-1];
                            }
                            max_score[l] = score;
                            max_tag[l] = (label)tags[j];
                            max_beam[l] = k;
                        }
                    }
                }
            }
        } else {''' % (self.config.lexicon_hash_bits, normalize_idx))
        f.write('''
            label tag;
            for (tag=0; tag<N_TAGS; tag++) {
                for (k=0; k<beam_size; k++) {
                    extract_features(
                            beams[k], tag, i, n_items,
                            invariant_hashes, feature_hashes);
                    const real score = beam_scores[k] + get_score(
                            feature_hashes, N_FEATURES, weights, weights_len);
                    if (score > max_score[BEAM_SIZE-1]) {
                        size_t l,m;
                        for (l=0; score < max_score[l]; l++);
                        for (m=BEAM_SIZE-1; m>l; m--) {
                            max_score[m] = max_score[m-1];
                            max_tag[m] = max_tag[m-1];
                            max_beam[m] = max_beam[m-1];
                        }
                        max_score[l] = score;
                        max_tag[l] = tag;
                        max_beam[l] = k;
                    }
                }
            }''')
        if not normalize_idx is None:
            f.write('\n        }')
        # TODO: this could probably be made more efficient, since some copying
        # is redundant.
        f.write('''
        for (k=0; k<BEAM_SIZE && max_score[k] != -REAL_MAX; k++) {
            beams[k][i] = max_tag[k];
            beam_scores[k] = max_score[k];
        }
        beam_size = k;
        if (i > 0) {
            for (k=0; k<beam_size; k++)
                if (max_beam[k] != k)
                    memcpy(new_beams[k], beams[max_beam[k]], i*sizeof(label));
            for (k=0; k<beam_size; k++)
                if (max_beam[k] != k)
                    memcpy(beams[k], new_beams[k], i*sizeof(label));
        }
    }
    memcpy(result, beams[0], n_items*sizeof(label));
}
#endif
''')

def abstract(form): return Translation(form, 'abstract')
def delexicalize(form): return Translation(form, 'delexicalize')
def normalize(form): return Translation(form, 'normalize')
def suffix(form, n): return Affix(form, False, n)
def prefix(form, n): return Affix(form, True, n)


