from math import ceil, log2

from .taglexicon import hash32trans, hash64trans
from .fasthash import hash32, hash64
from .form import Lookup


class WCLexicon:
    def __init__(self, name, items, config):
        config.wclexicons.append(self)

        self.items = items
        self.lower = False
        self.name = name
        self.config = config

        self.c_size = "%s_size" % name
        self.c_table = name

    def make_table(self):
        n_items = len(self.items)
        size = 1 << (ceil(log2(n_items) + 0.5))
        table = [None] * size
        if self.lower:
            fun = (
                (lambda s: hash32trans(s.lower()))
                if self.config.lexicon_hash_bits == 32
                else (lambda s: hash64trans(s.lower()))
            )
        else:
            fun = (
                (lambda s: hash32(1, s.encode("utf-8")))
                if self.config.lexicon_hash_bits == 32
                else (lambda s: hash64(1, s.encode("utf-8")))
            )
        for key, value in self.items:
            key_hash = fun(key)
            i = key_hash % size
            while not table[i] is None:
                if table[i][0] == key_hash:
                    break
                i = (i + 1) % size
            if table[i] is None:
                table[i] = (key_hash, value + 1)
        return table

    def lookup(self, form):
        if "normalize" in form.get_translations():
            self.lower = True
        return Lookup(form, self)

    @staticmethod
    def from_file(name, filename, config):
        with open(filename, "r", encoding="utf-8") as f:
            items = [tuple(line.rstrip("\n").split("\t")) for line in f]
            assert all(len(t) == 2 for t in items)
        return WCLexicon(name, [(key, int(s)) for key, s in items], config)

    def c_emit(self, f):
        table = self.make_table()

        f.write("#define %s 0x%x\n\n" % (self.c_size, len(table)))

        def c_kv(entry):
            if entry is None:
                return "{ 0, 0 }"
            key_hash, value = entry
            return "{ 0x%x, %d }" % (key_hash, value + 1)

        body = "\n".join(
            "    %s%s" % (c_kv(t), "" if i == len(table) - 1 else ",")
            for i, t in enumerate(table)
        )

        f.write(
            "static const hash%d_kv_label %s[%s] = {\n%s\n};\n\n"
            % (self.config.lexicon_hash_bits, self.c_table, self.c_size, body)
        )

        f.write(
            """
static inline label %s_get_wc(uint%d_t key) {
    size_t i = key & 0x%x;
    for (;;) {
        if (%s[i].hash == key) return %s[i].value;
        if (%s[i].value == 0) return 0;
        i = (i + 1) & 0x%x;
    }
}
"""
            % (
                self.name,
                self.config.lexicon_hash_bits,
                len(table) - 1,
                self.c_table,
                self.c_table,
                self.c_table,
                len(table) - 1,
            )
        )

    def c_lookup(self, c_key):
        return "%s_get_wc(%s)" % (self.name, c_key)
