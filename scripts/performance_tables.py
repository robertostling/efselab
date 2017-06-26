import re
import os.path
import glob
import sys
from collections import defaultdict

import numpy as np

def get_ud_names(ud_path):
    names = {}
    for filename in glob.glob(os.path.join(ud_path, 'UD_*/*-ud-train.conllu')):
        name = os.path.basename(os.path.dirname(filename))[3:]
        name = name.replace('_', ' ')
        if '-' in name: name = name.replace('-', ' (') + ')'
        code = os.path.basename(filename)[:-16]
        name = name.replace('Ancient Greek', r'Anc.\ Greek')
        names[code] = name
    return names

UD_NAMES = get_ud_names('/home/corpora/ud/ud-treebanks-v2.0')

def read_table(filename, scale):
    with open(filename) as f:
        data = [line.split() for line in f]
    return {t[0]:1-float(t[1])*scale for t in data if len(t) == 2}

def read_efselab_table(filename):
    lang, part = None, None
    part_table = defaultdict(dict)
    with open(filename) as f:
        for line in f:
            m = re.match(r'(\S+)\s+(dev|test)', line)
            if m:
                lang, part = m.group(1), m.group(2)
                continue
            m = re.match(r'Error rate: (\d+\.\d+)%', line)
            if m:
                err = float(m.group(1)) / 100.0
                part_table[part][lang] = err
                continue
            raise ValueError(line)
    return part_table

if __name__ == '__main__':
    if len(sys.argv[1:]) != 3:
        print('Usage: %s bilty.txt udpipe.txt efselab.txt' % sys.argv[0])
        sys.exit(1)
    bilty_table = read_table(sys.argv[1], scale=1.0)
    udpipe_table = read_table(sys.argv[2], scale=0.01)
    efselab_table = read_efselab_table(sys.argv[3])['test']

    common_codes = set(bilty_table.keys()) & set(efselab_table.keys()) & \
                   set(udpipe_table.keys())
    union_codes = set(bilty_table.keys()) | set(efselab_table.keys()) | \
                   set(udpipe_table.keys())
    table = sorted(
            (UD_NAMES[code],
             bilty_table[code], udpipe_table[code], efselab_table[code])
            for code in common_codes)

    def process_row(row):
        if all(x is None for x in row): return ['' for _ in row]
        name = row[0]
        err = row[1:]
        err = [round(100*x, 1) for x in err]
        min_err = min(err)
        res = [(r'\textbf{%.1f}' if x == min_err else '%.1f') % x for x in err]
        return [name] + res

    table_err = np.array([row[1:] for row in table])

    if len(table) % 2 != 0: table.append([None]*len(table[0]))

    for col1, col2 in zip(table[:round(len(table)/2)],
                          table[round(len(table)/2):]):
        print(' & '.join(process_row(col1) + process_row(col2)) + r' \\')

    #for row in sorted(table):
    #    name = row[0]
    #    err = row[1:]
    #    err = [round(100*x, 1) for x in err]
    #    min_err = min(err)
    #    res = [(r'\textbf{%.1f}' if x == min_err else '%.1f') % x for x in err]
    #    print(r'%s & %s \\' % (name, ' & '.join(res)))

    best_count = np.sum(
            (np.round(table_err*100, 1) == 
             np.min(np.round(table_err*100, 1), axis=1, keepdims=True)),
            axis=0).flatten()

    print(r'\midrule')
    print((r'\multicolumn{8}{c}{Summary statistics below refer to all %d '
           r'treebanks, in both columns above} \\') % len(common_codes))
    print(r'\midrule')
    print(r'Mean error rate & %s & No.\ of (shared) top ranks & %s \\' % (
        ' & '.join('%.1f' % x for x in np.mean(table_err*100, axis=0)),
        ' & '.join(map(str, best_count))))


    languages = {code.split('_')[0] for code in common_codes}
    print('%d treebanks in %d languages evaluated' % (
        len(common_codes), len(languages)), file=sys.stderr)

    print('bilty is missing: %s' % ' '.join(
        union_codes - set(bilty_table.keys())), file=sys.stderr)
    print('udpipe is missing: %s' % ' '.join(
        union_codes - set(udpipe_table.keys())), file=sys.stderr)
    print('efselab is missing: %s' % ' '.join(
        union_codes - set(efselab_table.keys())), file=sys.stderr)

