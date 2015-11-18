import unicodedata


def get_normalize_table(start, stop):
    def normalize(i):
        if i == 0: return 0
        return ord(unicodedata.normalize('NFC', chr(i).lower())[0])
    return [normalize(i) for i in range(start, stop)]

def get_delex_table(start, stop):
    categories = sorted(set(unicodedata.category(chr(i))
                            for i in range(start, stop)))
    category_idx = { x: i for i, x in enumerate(categories) }
    return [category_idx[unicodedata.category(chr(i))]
            for i in range(start, stop)]


def c_emit(f, config):
    def make_table(name, xs, bits):
        body = '\n'.join('    %d%s' % (x, '' if i == len(xs)-1 else ',')
                         for i,x in enumerate(xs))
        f.write('static const uint%d_t %s[] = {\n%s\n};\n\n' % (
            bits, name, body))

    if config.use_unicode:
        normalize_stop = 0x530
        delex_stop = 0x10000

        make_table('normalize_tab', get_normalize_table(0, normalize_stop), 32)

        delex_tab = get_delex_table(0, delex_stop)
        make_table('delex_tab', delex_tab, 8)

        f.write('''
static inline void unicode_translate_normalize(
        uint32_t *dest,
        size_t *dest_len,
        const uint32_t *src,
        size_t src_len)
{
    size_t i;
    for (i=0; i<src_len; i++) {
        if (likely(src[i] < 0x%x)) dest[i] = normalize_tab[src[i]];
        else dest[i] = src[i];
    }
    *dest_len = src_len;
}

static inline void unicode_translate_delexicalize(
        uint32_t *dest,
        size_t *dest_len,
        const uint32_t *src,
        size_t src_len)
{
    size_t i;
    for (i=0; i<src_len; i++) {
        if (likely(src[i] < 0x%x)) dest[i] = delex_tab[src[i]];
        else dest[i] = %d;
    }
    *dest_len = src_len;
}

static inline void unicode_translate_abstract(
        uint32_t *dest,
        size_t *dest_len,
        const uint32_t *src,
        size_t src_len)
{
    size_t i, n = 0;
    uint8_t last = 0xff;

    for (i=0; i<src_len; i++) {
        const uint8_t c = (likely(src[i] < 0x%x))? delex_tab[src[i]] : %d;
        if (c != last) {
            dest[n++] = c;
            last = c;
        }
    }
    *dest_len = n;
}

''' % (normalize_stop, delex_stop, max(delex_tab) + 1,
       delex_stop, max(delex_tab) + 1))

