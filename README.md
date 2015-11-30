# efselab
Efficient Sequence Labeling

`efselab` is a compiler for sequence labeling tools,
aimed at producing accurate and very fast part-of-speech (PoS) taggers and
named entity recognizers (NER).

To create a PoS tagger, all you need to do is to edit a Python file which
specifies which feature templates, tag lexicons and/or word clusters to use.
`efselab` then compiles this specification into C code, which is then compiled
into an executable.

The basic algorithm used is simple: a structured perceptron using greedy
search for decoding. To maximize performance, all strings are represented as
hash sums internally. During decoding, these can then be efficiently combined
into feature hashes.

In this way, even rather complex feature templates using word clusters and
external lexicons can generate taggers capable of around a million tokens per
second.

## Installing and using efselab

`efselab` is implemented in Python/C and requires the following software to be
installed:

 * Python 3 (tested with version 3.4) and setuptools
 * gcc (tested with version 4.9) and GNU Make

There is no installation as such, all the software is (somewhat inelegantly)
contained in the root directory, where configuration files are also assumed to
be placed and executed.

First, you need to build the Python module `fasthash`, which is used to
construct lexicon hash tables. Simply type:

    make

Then, to build a tagger simply run the corresponding configuration file, e.g.:

    python3 udt_en_config.py

which will build a tagger for the English part of the Universal Dependencies
Treebank. This produces a binary file, `udt_en`, which contains everything 
except the model weights. These need to be learned in the following way:

    ./udt_en train data/udt-en-train.tab data/udt-en-dev.tab udt-en.bin

The final weights are written to the file `udt-en.bin`, and can the be used
for tagging:

    ./udt_en tag data/udt-en-test.tab udt-en.bin evaluate >/dev/null

Note that the `evaluate` option requires a tagged input, if you want to tag an
untagged file, this can also be done (in this example by stripping off the
tags using the `cut` tool, and using `-` as the input file to read from stdin):

    cut -f 1 data/udt-en-test.tab | ./udt_en tag - udt-en.bin >udt-en-retag.tab

## Python interface

To build a Python module for your tagger, pass the argument
`build_python=True` to the `Configuration.generate` method (see the bottom
of `udt_en_config.py` for an example).

Then run the configuration script, e.g.:

    python3 udt_en_config.py

After this, the tagger can be used from Python in the following way:

    >>> import udt_en
    >>> with open('udt-en.bin', 'rb') as f: weights = f.read()
    ...
    >>> udt_en.tag(weights, "A short sentence .".split())
    ('DET', 'ADJ', 'NOUN', 'PUNCT')

The second argument can be a tuple or list of either `str` objects, or a
tuple or list containing the values of the different input fields. Using a
tuple with a single `str` object is equivalent to using just the `str` object.

`weights` is a `bytes` object, containing the contents of a model
file, i.e. a binary vector of floating-point values.

## Distributing taggers

Users with access to (possibly restricted) training material will likely want
to distribute the generated C file and the model file. The end user can then
compile the C file for their own platform, and start tagging files.

## Issues

There are some things to be aware of:

 * Tokens are simply truncated at 4095 bytes, don't feed it very long strings!
 * Currently only UTF-8 input is supported.

## Third-party code and data

This repository includes a few third-party contributions:

 * The English part of the UD Treebank (licensed as CC BY-SA 4.0), see:
   https://universaldependencies.github.io/docs/
 * UTF-8 decoding code from Björn Höhrmann (under the MIT license):
   http://bjoern.hoehrmann.de/utf-8/decoder/dfa/
 * Brown clusters from Turian et al.:
   http://metaoptimize.com/projects/wordreprs/

## Credits

Thanks to Emil Stenström for useful feedback.

