# Script to convert CoNLL files with tag+morphology into the simple two-column
# format assumed by efselab.
#
# If only the tag is required, conversion can more easily be done like this:
#
# cut -f 2,4 file.conll >file.tab

import sys

for line in sys.stdin:
    fields = line.rstrip('\n').split('\t')
    if len(fields) >= 6:
        word = fields[1]
        tag = fields[3]+'|'+fields[5] if (fields[5] and fields[5] != '_') else fields[3]
        print(word+'\t'+tag)
    else:
        print()

