#!/usr/bin/env python3

"""Script to compute and print confusion matrices from tab-separated data

Usage: python3 confusion.py <filename1> <filename2> <column>

Where <column> is a 0-based index of the column to be considered.
"""

import sys
from collections import defaultdict, Counter
from pprint import pprint
import numpy as np

name1, name2 = sys.argv[1:3]
field_idx = int(sys.argv[3])


def print_aligned(ss):
    n_rows = len(ss)
    n_cols = len(ss[0])
    col_formats = [
        "%%%ds" % max(len(ss[i][j]) for i in range(n_rows)) for j in range(n_cols)
    ]
    rows = [[f % s for s, f in zip(row, col_formats)] for row in ss]
    for row in rows:
        print(" ".join(row))


m = defaultdict(Counter)
labels = set()

with open(name1, "r", encoding="utf-8") as f1, open(name2, "r", encoding="utf-8") as f2:
    for line1, line2 in zip(f1, f2):
        fields1 = line1.rstrip("\n").split("\t")
        fields2 = line2.rstrip("\n").split("\t")
        if len(fields1) > field_idx and len(fields2) > field_idx:
            x, y = fields1[field_idx], fields2[field_idx]
            labels.add(x)
            labels.add(y)
            m[x][y] += 1

labels = sorted(labels)
sm = [[""] + labels] + [[x] + [str(m[x][y]) for y in labels] for x in labels]

print_aligned(sm)
