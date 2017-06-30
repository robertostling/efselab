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
 * Cython (only needed if you want to use the Swedish lemmatizer)

There is no installation as such, all the software is (somewhat inelegantly)
contained in the root directory, where configuration files are also assumed to
be placed and executed.

First, you need to build the Python module `fasthash`, which is used to
construct lexicon hash tables. Simply type:

    make

Each tagger specification file (`build_*.py`) also functions as a build
script. For a complete list of arguments, run e.g.:

    python3 build_udt_en.py --help

Then, to build a tagger simply run the corresponding configuration file, the
following will build a tagger for the English Universal Dependencies treebank
with the name `udt_en`, both an executable file and a Python module:

    python3 build_udt_en.py --name udt_en --python

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

## Swedish annotation pipeline

There is a Swedish annotation pipeline, adapted from the Swedish Treebank
pipeline (originally using hunpos for POS tagging) created at
Uppsala University by Filip Salomonsson. It can do the following:

 * Tokenization (using a Python tokenizer by Filip Salomonsson)
 * POS tagging (using `efselab` with a SUC + SIC model)
 * Conversion to Universal PoS tags (using `efselab` trained on Universal
   Dependencies data plus some postprocessing heuristics by Aaron Smith)
 * Lemmatization (using the lexicon-based lemmatizer in `lemmatize.pyx`)
 * Named Entity Recognition (using `efselab` with a SUC + SIC model)
 * Dependency prasing (using MaltParser by Joakim Nivre et al.) into
   Universal Dependencies format (version 2)

To start using the pipeline, you first need to execute the following
convenience script:

    scripts/install_swedish_pipeline.sh

Then you should be able to run the pipeline like this:

    mkdir output
    ./swe_pipeline.py -o output --all file.txt

For a more detailed description of the command-line options, run:

    ./swe_pipeline.py --help

## Accuracy

These evaluations are performed with the 17-element PoS tagset from Universal
Dependencies version 2. The Swedish model in the leftmost column of the first
table uses additional data, all other models use only the training part of the
corresponding Universal Dependencies treebank.

### Swedish

| Test data                   | Swedish | Generic |
|:--------------------------- | ----:| ----:|
| Swedish UD treebank         | 97.7 | 96.3 |
| Swedish (LinES) UD treebank | 91.9 | 95.0 |


### Universal Dependencies treebanks (version 2.0)

| Treebank | Accuracy |
|:-------- | --------:|
| Anc.\ Greek | 87.7 |
| Anc.\ Greek (PROIEL) | 96.5 |
| Arabic | 94.8 |
| Basque | 94.2 |
| Belarusian | 90.2 |
| Bulgarian | 98.0 |
| Catalan | 97.6 |
| Chinese | 91.0 |
| Coptic | 95.1 |
| Croatian | 96.4 |
| Czech | 98.6 |
| Czech (CAC) | 98.8 |
| Czech (CLTT) | 97.5 |
| Danish | 96.3 |
| Dutch | 92.3 |
| Dutch (LassySmall) | 97.6 |
| English | 94.8 |
| English (LinES) | 95.3 |
| English (ParTUT) | 94.7 |
| Estonian | 90.3 |
| Finnish | 95.8 |
| Finnish (FTB) | 93.2 |
| French | 96.6 |
| French (ParTUT) | 94.1 |
| French (Sequoia) | 97.4 |
| Galician | 97.4 |
| Galician (TreeGal) | 90.4 |
| German | 92.8 |
| Gothic | 95.7 |
| Greek | 96.8 |
| Hebrew | 95.5 |
| Hindi | 96.5 |
| Hungarian | 93.4 |
| Indonesian | 92.9 |
| Irish | 84.9 |
| Italian | 97.7 |
| Japanese | 96.2 |
| Korean | 94.0 |
| Latin | 84.4 |
| Latin (ITTB) | 97.3 |
| Latin (PROIEL) | 95.8 |
| Latvian | 91.1 |
| Lithuanian | 79.1 |
| Norwegian (Bokmaal) | 97.1 |
| Norwegian (Nynorsk) | 96.7 |
| Old Church Slavonic | 95.3 |
| Persian | 96.6 |
| Polish | 97.0 |
| Portuguese | 96.6 |
| Portuguese (BR) | 96.9 |
| Romanian | 97.2 |
| Russian | 95.9 |
| Sanskrit | 61.0 |
| Slovak | 95.2 |
| Slovenian | 96.8 |
| Slovenian (SST) | 89.0 |
| Spanish | 95.9 |
| Spanish (AnCora) | 97.9 |
| Swedish | 96.3 |
| Swedish (LinES) | 95.0 |
| Tamil | 86.6 |
| Turkish | 94.3 |
| Ukrainian | 61.9 |
| Urdu | 93.3 |
| Vietnamese | 88.3 |

## Performance-related options

The `--beam-size` argument of the build scripts controls the beam size of the
decoder, which is the
most important way to balance accuracy and performance. A beam size of 1 is
equivalent to a greedy search, which is the fastest option but results in
significantly higher error rates than the default beam size (4).

## Python interface

To build a Python module for your tagger, use the `--python` argument with the
configuration script:

    python3 build_udt_en.py --name udt_en --python

After this, the tagger can be used from Python in the following way:

    >>> import udt_en
    >>> with open('udt-en.bin', 'rb') as f: weights = f.read()
    ...
    >>> udt_en.tag(weights, ['A', 'short', 'sentence', '.'])
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

Thanks to [Emil Stenström](https://github.com/EmilStenstrom) for testing and
feedback.

The Swedish pipeline wrapper script (including the tokenizer) was originally
written by Filip Salomonsson (Uppsala), later modified by Robert Östling
(Stockholm/Helsinki) and Aaron Smith (Uppsala). Joakim Nivre and Jesper Näsman
(Uppsala) contributed to different parts of the Swedish pipeline.

