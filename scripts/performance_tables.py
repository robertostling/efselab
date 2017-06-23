import re
import os.path
import glob
import sys
from collections import defaultdict


def get_ud_names(ud_path):
    names = {}
    for filename in glob.glob(os.path.join(ud_path, 'UD_*/*-ud-train.conllu')):
        name = os.path.basename(os.path.dirname(filename))[3:]
        name = name.replace('_', ' ')
        if '-' in name: name = name.replace('-', ' (') + ')'
        code = os.path.basename(filename)[:-16]
        names[code] = name
    return names

UD_NAMES = get_ud_names('/home/corpora/ud/ud-treebanks-v2.0')

def bilty_dev_error(filename):
    best_err = 2.0
    with open(filename) as f:
        for line in f:
            m = re.match(r'dev accuracy:\s+(0\.\d+)', line)
            if m:
                err = 1 - float(m.group(1))
                if err < best_err: best_err = err
    return None if best_err > 1.0 else best_err

def bilty_dev_table(path):
    table = {}
    for filename in glob.glob(os.path.join(path, '*.err')):
        err = bilty_dev_error(filename)
        if err is not None:
            lang = os.path.basename(filename)[:-4]
            table[lang] = err
    return table

def efselab_table(filename):
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
    bilty_table = bilty_dev_table(sys.argv[1])
    efselab_table = efselab_table(sys.argv[2])['dev']

    common_codes = set(bilty_table.keys()) & set(efselab_table.keys())
    table = [(UD_NAMES[code], bilty_table[code], efselab_table[code])
             for code in common_codes]
    for name, bilty_err, efselab_err in sorted(table):
        print(r'%s & %.1f & %.1f \\' % (name, 100*bilty_err, 100*efselab_err))

