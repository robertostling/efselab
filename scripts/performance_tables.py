import re
import os.path
import glob
import sys

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


if __name__ == '__main__':
    bilty_table = bilty_dev_table(sys.argv[1])

    table = sorted([(UD_NAMES[code], err)
                    for code, err in bilty_table.items()])
    for name, err in table:
        print(r'%s & %.1f \\' % (name, 100*err))

