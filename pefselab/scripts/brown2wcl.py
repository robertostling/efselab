# Tool to convert Brown clusters from Percy Liang's tool into a format usable
# by the WCLexicon class.

import sys

LIMIT = 10


def parse_line(s):
    fields = s.rstrip("\n").split("\t")
    return (fields[0], fields[1], int(fields[2]))


cluster_idx = {}
lines = [parse_line(line) for line in sys.stdin]
lines = [t for t in lines if t[2] >= LIMIT]
lines = sorted(lines, key=lambda t: -t[2])

for cluster, word, _ in lines:
    print("%s\t%d" % (word, cluster_idx.setdefault(cluster, len(cluster_idx))))
