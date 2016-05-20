import os, subprocess, tempfile, sys

import translation

class Configuration:
    def __init__(self, name, args):
        if not args.name is None: name = args.name
        feat_hash_bits = args.feat_hash_bits
        partial_hash_bits = feat_hash_bits
        lexicon_hash_bits = partial_hash_bits
        n_train_fields = args.n_train_fields
        beam_size = args.beam_size
        n_tag_fields = None
        use_unicode = True
        cc = args.cc
        cflags = args.cflags.replace(r'\-', '-').split()

        self.skip_compile = args.skip_compile
        self.skip_generate = args.skip_generate
        self.build_python = args.python

        # Only these values are (currently) supported
        assert partial_hash_bits in (32, 64)
        assert feat_hash_bits in (32, 64)
        assert lexicon_hash_bits == partial_hash_bits
        assert use_unicode

        self.name               = name
        self.cc                 = cc
        self.cflags             = cflags

        self.tagset             = None
        self.lexicon            = None
        self.feature_set        = None
        self.wclexicons         = []

        self.beam_size          = beam_size
        self.partial_hash_bits  = partial_hash_bits
        self.feat_hash_bits     = feat_hash_bits
        self.lexicon_hash_bits  = lexicon_hash_bits
        self.use_unicode        = use_unicode
        self.n_train_fields     = n_train_fields
        self.n_tag_fields       = n_tag_fields if n_tag_fields \
                                  else n_train_fields-1

        print('Building tagger...', file=sys.stderr)

    def build(self):
        if not self.skip_generate:
            self.generate(not self.skip_compile, False)
        if self.build_python:
            self.generate(not self.skip_compile, True, not self.skip_generate)

    def generate(self, run_cc=True, build_python=False, generate_c=True):
        filename = ('py'+self.name if build_python else self.name) + '.c'
        if generate_c:
            with open(filename, 'w') as f:
                print('Generating C code to %s...' % f.name, file=sys.stderr)
                self.c_emit(f, build_python)
                f.flush()
        if run_cc and not build_python:
            command = [self.cc] + self.cflags + [
                    '-I', os.path.realpath(os.path.dirname(sys.argv[0])),
                    '-o', self.name, filename]
            print(' '.join(command), file=sys.stderr)
            subprocess.call(command)
        elif run_cc and build_python:
            from distutils.core import setup, Extension
            tagger = Extension(
                    self.name,
                    sources = [filename],
                    libraries = [],
                    extra_compile_args = self.cflags,
                    extra_link_args = [])
            setup(name = self.name, ext_modules = [tagger],
                  script_args = ['build_ext', '--inplace'])

    def c_emit(self, f, build_python):
        def c_include(filename):
            with open(os.path.join('c', filename)) as cf:
                code = cf.read()
                f.write(code)

        f.write('''
#define N_TRAIN_FIELDS  %d
#define N_TAG_FIELDS    %d
#define BEAM_SIZE       %d
#define TAGGER_NAME     "%s"
#define PyInit_TAGGER_NAME PyInit_%s

#include <stdint.h>

typedef uint%d_t   partial_hash_t;
typedef uint%d_t   feat_hash_t;
typedef uint32_t   label;

''' % (self.n_train_fields, self.n_tag_fields, self.beam_size,
       self.name, self.name,
       self.partial_hash_bits, self.feat_hash_bits))

        c_include('headers.h')
        c_include('hash.c')

        translation.c_emit(f, self)

        self.tagset.c_emit(f)
        if self.lexicon: self.lexicon.c_emit(f)
        for wcl in self.wclexicons: wcl.c_emit(f)
        self.feature_set.c_emit(f)

        c_include('seq.c')
        c_include('search.c')
        c_include('tag.c')
        c_include('train.c')
        c_include('run.c')
        c_include('main.c')
        if build_python:
            c_include('pytagger.c')

