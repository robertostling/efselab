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

# for filename in `ls *-train.tab`; do echo `grep -v "^$" $filename | wc -l` $filename | sort -n | sed 's/-ud-train.tab//'; done | tee ../datasize.txt

TRAIN_SIZE = {s.split()[1]:int(s.split()[0]) for s in '''
590819 ar_nyuad
223881 ar
3975 be
124336 bg
417587 ca
6804 cop
472608 cs_cac
16400 cs_cltt
1173282 cs
37432 cu
80378 da
269626 de
41212 el
50095 en_lines
25871 en_partut
204585 en
444617 es_ancora
382436 es
22525 et
72974 eu
121064 fa
127602 fi_ftb
162621 fi
6396 fr_partut
50561 fr_sequoia
356464 fr
3183 ga
4855 gl_treegal
79329 gl
35024 got
184382 grc_proiel
159895 grc
137680 he
281057 hi
169283 hr
20166 hu
97531 id
28844 it_partut
270703 it
161902 ja
52328 ko
270403 la_ittb
147044 la_proiel
8018 la
3210 lt
34667 lv
81243 nl_lassysmall
186467 nl
243887 no_bokmaal
245330 no_nynorsk
62501 pl
255755 pt_br
206740 pt
185113 ro
870033 ru_syntagrus
75964 ru
695 sa
80575 sk
9487 sl_sst
112530 sl
48325 sv_lines
66645 sv
6329 ta
38082 tr
478 uk
108690 ur
20285 vi
98608 zh'''.strip().split('\n')}

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
            (code,
             bilty_table[code], udpipe_table[code], efselab_table[code])
            for code in common_codes)

    def process_row(row):
        if all(x is None for x in row): return ['' for _ in row]
        name = UD_NAMES[row[0]]
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

    import matplotlib.pyplot as plt
    #table = sorted(
    #        (UD_NAMES[code],
    #         bilty_table[code], udpipe_table[code], efselab_table[code])
    #        for code in common_codes)

    from matplotlib.font_manager import FontProperties
    import matplotlib.patches as mpatches
    prop = FontProperties()
    prop.set_family('serif')
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('n: size of training data (tokens)', fontproperties=prop)
    plt.ylabel('e: PoS tagging error rate (%)', fontproperties=prop)
    table = [row for row in table if not None in row]
    train_sizes = [TRAIN_SIZE[code] for code,_,_,_ in table]
    bilty_acc = [100*bilty for _,bilty,_,_ in table]
    efselab_acc = [100*efselab for _,_,_,efselab in table]
    bilty_ax = plt.scatter(train_sizes, bilty_acc, marker='o', edgecolors='b',
            facecolors=['b' if x<=y else 'none'
                        for x,y in zip(bilty_acc,efselab_acc)])
    efselab_ax = plt.scatter(train_sizes, efselab_acc, marker='s',
            edgecolors='r', facecolors=[
                'r' if x>=y else 'none'
                for x,y in zip(bilty_acc,efselab_acc)])
    #red_patch = mpatches.Patch(color='red', label='efselab (ours)')
    #blue_patch = mpatches.Patch(color='blue', label='bilty (Plank et al., 2016)')
    #plt.legend(handles=[blue_patch, red_patch], prop=prop)
    red_square, = plt.plot(0, "rs")
    blue_dot, = plt.plot(0, "bo")
    plt.legend([blue_dot, red_square],
               ['bilty (Plank et al., 2016)', 'efselab (ours)'],
               prop=prop)
    #plt.legend([bilty_ax, efselab_ax],
    #           ['bilty (Plank et al., 2016)', 'efselab (ours)'],
    #           prop=prop)
    from scipy.stats import linregress
    a, b, _, _, _ = linregress(np.log10(train_sizes), np.log10(bilty_acc))
    print(r'bilty: e = %.2f \cdot n^{%.2f})' % (
        np.power(10, b), a), file=sys.stderr)
    plt.plot([200, 2000000], np.power(10, np.log10([200, 2000000])*a+b), 'b--')
    a, b, _, _, _ = linregress(np.log10(train_sizes), np.log10(efselab_acc))
    print(r'efselab: e = %.2f \cdot n^{%.2f})' % (
        np.power(10, b), a), file=sys.stderr)
    plt.plot([200, 2000000], np.power(10, np.log10([200, 2000000])*a+b), 'r-.')
    plt.axis((200, 2000000, 1, 100))
    plt.savefig('datasize.pdf')
    plt.show()

