import math
import itertools


class Tagset:
    def __init__(self, tags, config):
        config.tagset = self

        self._frozen = False
        self.tags = sorted(tags)
        self.name = config.name
        self.config = config
        self.n_bits = math.ceil(math.log2(len(tags)))
        self.subsets = set()
        self.tag_idx = {tag: i for i, tag in enumerate(self.tags)}
        self.tag_fields = set()

        self.c_n_tags = "%s_N_TAGS" % self.name
        self.c_n_bits = "%s_N_BITS" % self.name
        self.c_tag_subsets = "%s_tag_subsets" % self.name
        self.c_tag_str = "%s_tag_str" % self.name

    def c_emit(self, f):
        assert len(self.tag_fields) == 1, "Can only have one field with tags"
        f.write("#define COL_TAG %d\n" % (list(self.tag_fields)[0]))
        f.write("#define %s %d\n" % (self.c_n_tags, len(self.tags)))
        f.write("#define %s %d\n" % (self.c_n_bits, self.n_bits))
        f.write("#define N_TAGS %s\n" % self.c_n_tags)
        f.write("#define tag_str %s\n" % self.c_tag_str)
        body = "\n".join(
            '    "%s"%s' % (tag, "" if i == len(self.tags) - 1 else ",")
            for i, tag in enumerate(self.tags)
        )
        f.write(
            "\nstatic const char *%s[%s] = {\n%s\n};\n\n"
            % (self.c_tag_str, self.c_n_tags, body)
        )

        f.write(
            """
static const int %s_from_str(const char *s) {
    int i;
    for (i=0; i<%s; i++) if (!strcmp(s, %s[i])) return i;
    return -1;
}

#define tagset_from_str %s
"""
            % (self.name, self.c_n_tags, self.c_tag_str, self.name + "_from_str")
        )

        if self.subsets:
            f.write(self._subset_table())

    def register_mapping(self, fun):
        """Register a function mapping tags to some other set"""
        assert not self._frozen
        self.subsets.add(tuple(fun(tag) for tag in self.tags))

    def _subset_compute(self):
        def index_list(xs):
            idx = {x: i for i, x in enumerate(sorted(set(xs)))}
            return tuple(idx[x] for x in xs)

        self._frozen = True
        self._subset_idx = {subset: i for i, subset in enumerate(sorted(self.subsets))}
        self._indexed_subsets = [index_list(xs) for xs in sorted(self.subsets)]
        self._subset_n_bits = [
            math.ceil(math.log2(len(set(trans)))) for trans in self._indexed_subsets
        ]
        self._subset_shifts = list(itertools.accumulate([0] + self._subset_n_bits))[:-1]

    def _get_subset_shift(self, fun):
        idx = self._subset_idx[tuple(fun(tag) for tag in self.tags)]
        return self._subset_shifts[idx]

    def get_subset_mask(self, fun):
        idx = self._subset_idx[tuple(fun(tag) for tag in self.tags)]
        return ((1 << self._subset_n_bits[idx]) - 1) << self._subset_shifts[idx]

    def _subset_table(self):
        self._subset_compute()

        sum_bits = sum(self._subset_n_bits)
        assert sum_bits <= 64
        dtype = "uint32_t" if sum_bits <= 32 else "uint64_t"
        table = [
            sum(x << b for b, x in zip(self._subset_shifts, xs))
            for xs in zip(*self._indexed_subsets)
        ]
        body = "\n".join(
            ("    0x%08xUL%s" if sum_bits <= 32 else "    0x%16xULL%s")
            % (value, "" if i == len(self.tags) - 1 else ",")
            for i, value in enumerate(table)
        )
        return "static const %s %s[%s] = {\n%s\n};\n\n" % (
            dtype,
            self.c_tag_subsets,
            self.c_n_tags,
            body,
        )

    def tag(self, field, position):
        return Tag(field, position, self)


class Tag:
    def __init__(self, field, position, tagset):
        self.field = field
        self.position = position
        self.tagset = tagset
        tagset.tag_fields.add(field)

    def c_value(self):
        if self.position == 0:
            return "tag"
        else:
            return "((i>=%d)? history[i-%d] : %s)" % (
                -self.position,
                -self.position,
                self.tagset.c_n_tags,
            )


class TransformedTag(Tag):
    def __init__(self, tag, fun):
        self.tagset = tag.tagset
        self.tag = tag
        self.fun = fun

    def c_value(self):
        return "(%s[%s] & 0x%x)" % (
            self.tagset.c_tag_subsets,
            self.tag.c_value(),
            self.tagset.get_subset_mask(self.fun),
        )


def tag_mapping(fun):
    def register(tag):
        tag.tagset.register_mapping(fun)
        return TransformedTag(tag, fun)

    return register
