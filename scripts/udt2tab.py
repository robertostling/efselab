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

    for conllu in glob.glob(os.path.join(ud_path, '*/*-ud-*.conllu')):
        base = os.path.splitext(os.path.basename(conllu))[0]
        tab = os.path.join(out_path, base + '.tab')
        print('Converting %s...' % base, flush=True)
        convert(conllu, tab)

