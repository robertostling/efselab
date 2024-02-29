def convert(conllu, tab):
    with open(conllu, 'r', encoding='utf-8') as inf, \
         open(tab, 'w', encoding='utf-8') as outf:
        for line in inf:
            line = line.strip()
            if line.startswith('#'):
                pass
            elif not line:
                print(file=outf)
            else:
                fields = line.split('\t')
                if fields[0].isnumeric():
                    print(fields[1] + '\t' + fields[3], file=outf)


if __name__ == '__main__':
    import glob, sys, os.path

    ud_path, out_path = sys.argv[1:]

    if os.path.basename(ud_path) == 'ud-test-v2.0-conll2017':
        for conllu in glob.glob(os.path.join(
                ud_path,'gold', 'conll17-ud-test-2017-05-09', '*.conllu')):
            lang = os.path.splitext(os.path.basename(conllu))[0]
            tab = os.path.join(out_path, lang + '-ud-test.tab')
            if os.path.exists(tab):
                print('Refusing to overwrite %s' % tab, flush=True)
            else:
                print('Converting %s...' % lang, flush=True)
                convert(conllu, tab)
    else:
        for conllu in glob.glob(os.path.join(ud_path, '*/*-ud-*.conllu')):
            base = os.path.splitext(os.path.basename(conllu))[0]
            tab = os.path.join(out_path, base + '.tab')
            if os.path.exists(tab):
                print('Refusing to overwrite %s' % tab, flush=True)
            else:
                print('Converting %s...' % base, flush=True)
                convert(conllu, tab)

