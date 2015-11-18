from operator import itemgetter
from math import ceil, log2

import fasthash

def hash32trans(s):
    return fasthash.hashlongs32(tuple(ord(c) for c in s))

def hash64trans(s):
    return fasthash.hashlongs64(tuple(ord(c) for c in s))

class TagLexicon:
    def __init__(self, name, n_items, open_tags, config):
        config.lexicon = self

        size = 1 << (ceil(log2(n_items) + 0.5))
        self.table = [None] * size
        self.fun = hash32trans if config.lexicon_hash_bits == 32 \
                   else hash64trans
        self.name = name
        self.value_idx = {}
        self.config = config
        self.open_tags = open_tags

        self.c_size = '%s_size' % name
        self.c_table = name

    def __setitem__(self, key, value):
        i = self.fun(key) % len(self.table)
        while not self.table[i] is None:
            if self.table[i][0] == key: return
            #assert self.table[i][0] != key, 'Collision in tag lexicon'
            i = (i + 1) % len(self.table)
        idx = self.value_idx.setdefault(tuple(value), len(self.value_idx))
        self.table[i] = (key, idx)

    def c_emit(self, f):
        f.write('static const size_t %s = 0x%x;\n\n' % (
            self.c_size, len(self.table)))
        for tags,i in sorted(self.value_idx.items(), key=itemgetter(1)):
            f.write('static const label %s_tags_%d[] = { %d, %s };\n' % (
                self.name, i, len(tags), ', '.join(map(str, tags))))
            
        f.write('static const label %s_tags_open[] = { %d, %s };\n' % (
            self.name, len(self.open_tags),
            ', '.join(map(str, sorted(self.open_tags)))))

        def c_kv(entry):
            if entry is None: return '{ 0, NULL }'
            key, idx = entry
            return '{ 0x%x, %s_tags_%d }' % (self.fun(key), self.name, idx)

        body = '\n'.join(
                '    %s%s' % (c_kv(t), '' if i == len(self.table)-1 else ',')
                for i,t in enumerate(self.table))

        f.write('static const hash%d_kv %s[%d] = {\n%s\n};\n\n' % (
            self.config.lexicon_hash_bits, self.c_table, len(self.table), body))

        f.write('''
static inline const label *%s_get_tags(uint%d_t key) {
    size_t i = key & 0x%x;
    for (;;) {
        if (%s[i].hash == key) return (const label*)%s[i].value;
        if (%s[i].value == NULL) return %s_tags_open;
        i = (i + 1) & 0x%x;
    }
}

#define get_tags %s_get_tags
''' % (self.name, self.config.lexicon_hash_bits, len(self.table)-1,
       self.c_table, self.c_table, self.c_table, self.name,
       len(self.table)-1, self.name))

