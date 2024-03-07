# Script to convert CoNLL files with tag+morphology into the simple two-column
# format assumed by efselab.
#
# If only the tag is required, conversion can more easily be done like this:
#
# cut -f 2,4 file.conll >file.tab

"""
cat /home/corpora/SUC3.0/corpus/conll/blogs.conll /home/corpora/SUC3.0/corpus/conll/suc-train.conll | python3 conll2tab.py ne >../suc-data/suc-blogs-ne-train.tab
cat /home/corpora/SUC3.0/corpus/conll/suc-dev.conll | python3 conll2tab.py ne >../suc-data/suc-ne-dev.tab
cat /home/corpora/SUC3.0/corpus/conll/suc-test.conll | python3 conll2tab.py ne >../suc-data/suc-ne-test.tab
"""

import sys

include_ne = "ne" in sys.argv[1:]

for line in sys.stdin:
    fields = line.rstrip("\n").split("\t")
    if len(fields) >= 6:
        word = fields[1]
        pos = fields[3]
        if pos == "LE":
            pos = "IN"
        tag = pos + "|" + fields[5] if (fields[5] and fields[5] != "_") else pos
        if include_ne and len(fields) >= 12:
            ne = (
                fields[10]
                if fields[11] == "_"
                else ("%s-%s" % (fields[10], fields[11]))
            )
            lemma = fields[2]
            print(word + "\t" + lemma + "\t" + tag + "\t" + ne)
        else:
            print(word + "\t" + tag)
    else:
        print()
