#!/usr/bin/env python3
"""Tokenize, tag and parse Swedish plain text data.

This was originally the pipeline by Filip Salomonsson for the Swedish
Treebank (using hunpos for tagging), later modified by Robert Östling to use
efselab and Python 3.
"""

import os
import shutil
import sys
import tempfile
from optparse import OptionParser
from subprocess import Popen

from conll import tagged_to_tagged_conll
from lemmatize import SUCLemmatizer
from tagger import SucTagger, UDTagger
from tokenize import build_sentences

__authors__ = """
Filip Salomonsson <filip.salomonsson@gmail.com>
Robert Östling <robert.ostling@helsinki.fi>
Aaron Smith <aaron.smith@lingfil.uu.se>
"""

# Set some sensible defaults
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
MODEL_DIR = os.path.join(SCRIPT_DIR, "swe-pipeline")
TAGGING_MODEL = os.path.join(MODEL_DIR, "suc.bin")
UD_TAGGING_MODEL = os.path.join(MODEL_DIR, "suc-ud.bin")
LEMMATIZATION_MODEL = os.path.join(MODEL_DIR, "suc-saldo.lemmas")
PARSING_MODEL = os.path.join(MODEL_DIR, "maltmodel-UD_Swedish")
MALT = os.path.join(MODEL_DIR, "maltparser-1.8.1/maltparser-1.8.1.jar")

def main():
    options, args = parse_options()
    validate_options(options, args)
    run_pipeline(options, args)

def parse_options():
    # Set up and parse command-line options
    usage = "usage: %prog --output-dir=DIR [options] FILENAME [...]"
    op = OptionParser(usage=usage)
    op.add_option("-o", "--output-dir", dest="output_dir", metavar="DIR",
                  help="set target directory for output (Required.)")
    op.add_option("--skip-tokenization", dest="skip_tokenization",
                  action="store_true", help="Assume tokenized input")
    op.add_option("--tokenized", dest="tokenized", action="store_true",
                  help="Generate tokenized output file(s) (*.tok)")
    op.add_option("--tagged", dest="tagged", action="store_true",
                  help="Generate tagged output file(s) (*.tag)")
    op.add_option("--lemmatized", dest="lemmatized", action="store_true",
                  help="Also lemmatize the tagged output file(s) (*.tag)")
    op.add_option("--parsed", dest="parsed", action="store_true",
                  help="Generate parsed output file(s) (*.conll)")
    op.add_option("--all", dest="all", action="store_true",
                  help="Equivalent to --tokenized --tagged --lemmatized --parsed")
    op.add_option("-m", "--tagging-model", dest="tagging_model",
                  default=TAGGING_MODEL, metavar="FILENAME",
                  help="Model for PoS tagging")
    op.add_option("-u", "--ud-tagging-model", dest="ud_tagging_model",
                  default=UD_TAGGING_MODEL, metavar="FILENAME",
                  help="Model for PoS tagging (UD wrapper)")
    op.add_option("-l", "--lemmatization-model", dest="lemmatization_model",
                  default=LEMMATIZATION_MODEL, metavar="MODEL",
                  help="MaltParser model file for parsing")
    op.add_option("-p", "--parsing-model", dest="parsing_model",
                  default=PARSING_MODEL, metavar="MODEL",
                  help="MaltParser model file for parsing")
    op.add_option("--malt", dest="malt", default=MALT, metavar="JAR",
                  help=".jar file of MaltParser")
    op.add_option("--no-delete", dest="no_delete", action="store_true",
                  help="Don't delete temporary working directory.")
    return op.parse_args()

def validate_options(options, args):
    if options.all:
        options.tokenized = True
        options.tagged = True
        options.lemmatized = True
        options.parsed = True

    if not (options.tokenized or options.tagged or options.parsed):
        sys.exit("Nothing to do! Please use --tokenized, --tagged, --lemmatized and/or --parsed (or --all)")

    # If no target directory was given: write error message and exit.
    if not options.output_dir:
        sys.exit("No target directory specified. Use --output-dir=DIR")

    if not args:
        sys.exit("Please specify at least one filename as input.")

    # Set up (part of) command lines
    jarfile = os.path.expanduser(options.malt)

    # Make sure we have all we need
    if options.tagged and not os.path.exists(options.tagging_model):
        sys.exit("Can't find tagging model: %s" % options.tagging_model)
    if options.lemmatized and not options.tagged:
        sys.exit("Can't lemmatize without tagging.")
    if options.lemmatized and not os.path.exists(options.lemmatization_model):
        sys.exit("Can't find lemmatizer model file %s." % options.lemmatization_model)
    if options.parsed and not os.path.exists(jarfile):
        sys.exit("Can't find MaltParser jar file %s." % jarfile)
    if options.parsed and not os.path.exists(options.parsing_model + ".mco"):
        sys.exit("Can't find parsing model: %s" % options.parsing_model + ".mco")

def run_pipeline(options, args):
    suc_tagger = None
    ud_tagger = None
    if options.tagged or options.parsed:
        suc_tagger = SucTagger(options.tagging_model)

        if options.lemmatized:
            ud_tagger = UDTagger(options.ud_tagging_model)

    # Set up the working directory
    tmp_dir = tempfile.mkdtemp("-stb-pipeline")
    if options.parsed:
        shutil.copy(os.path.join(SCRIPT_DIR, options.parsing_model + ".mco"),
                    tmp_dir)

    lemmatizer = None
    if options.lemmatized:
        lemmatizer = SUCLemmatizer()
        lemmatizer.load(options.lemmatization_model)

    # Process each input file
    for filename in args:
        process_file(options, filename, tmp_dir, lemmatizer, suc_tagger, ud_tagger)

    cleanup(options, tmp_dir)

def process_file(options, filename, tmp_dir, lemmatizer, suc_tagger, ud_tagger):
    print("Processing %s..." % (filename), file=sys.stderr)

    tokenized_filename = output_filename(tmp_dir, filename, "tok")
    tagged_filename = output_filename(tmp_dir, filename, "tag")

    with open(tokenized_filename, "w", encoding="utf-8") as tokenized, \
            open(tagged_filename, "w", encoding="utf-8") as tagged:

        sentences = run_tokenization(options, filename)

        # Run only one pass over sentences for writing to both files
        for sentence in sentences:
            write_to_file(tokenized, sentence)

            if options.tagged or options.parsed:
                lemmas, ud_tags_list, suc_tags_list = run_tagging_and_lemmatization(sentence, lemmatizer, suc_tagger, ud_tagger)

                ud_tag_list = [ud_tags[:ud_tags.find("|")] for ud_tags in ud_tags_list]
                if lemmas and ud_tags_list:
                    lines = ["\t".join(line) for line in zip(sentence, suc_tags_list, ud_tag_list, lemmas)]
                else:
                    lines = ["\t".join(line) for line in zip(sentence, suc_tags_list)]

                write_to_file(tagged, lines)

    parsed_filename = ""
    if options.parsed:
        parsed_filename = parse(options, filename, tmp_dir)

    write_to_output(options, tokenized_filename, tagged_filename, parsed_filename)

    print("done.", file=sys.stderr)

def run_tokenization(options, filename):
    with open(filename, "r", encoding="utf-8") as input_file:
        data = input_file.read()

        if options.skip_tokenization:
            sentences = [
                sentence.split('\n')
                for sentence in data.split('\n\n')
                if sentence.strip()]
        else:
            sentences = build_sentences(data)

    return sentences

def run_tagging_and_lemmatization(sentence, lemmatizer, suc_tagger, ud_tagger):
    lemmas = []
    ud_tags_list = []
    suc_tags_list = suc_tagger.tag(sentence)

    if lemmatizer:
        lemmas = [lemmatizer.predict(token, tag) for token, tag in zip(sentence, suc_tags_list)]
        ud_tags_list = ud_tagger.tag(sentence, lemmas, suc_tags_list)

    return lemmas, ud_tags_list, suc_tags_list

def parse(options, filename, tmp_dir):
    tagged_filename = output_filename(tmp_dir, filename, "tag")
    tagged_conll_filename = output_filename(tmp_dir, filename, "tag.conll")
    parsed_filename = output_filename(tmp_dir, filename, "conll")
    log_filename = output_filename(tmp_dir, filename, "log")

    # The parser command line is dependent on the input and
    # output files, so we build that one for each data file
    parser_cmdline = ["java", "-Xmx2000m",
                      "-jar", os.path.expanduser(options.malt),
                      "-m", "parse",
                      "-i", tagged_conll_filename,
                      "-o", parsed_filename,
                      "-w", tmp_dir,
                      "-c", os.path.basename(options.parsing_model)]

    # Conversion from .tag file to tagged.conll (input format for the parser)
    tagged_conll_file = open(tagged_conll_filename, "w", encoding="utf-8")
    tagged_to_tagged_conll(open(tagged_filename, "r", encoding="utf-8"), tagged_conll_file)
    tagged_conll_file.close()

    # Run the parser
    with open(log_filename, "w", encoding="utf-8") as log_file:
        returncode = Popen(parser_cmdline, stdout=log_file, stderr=log_file).wait()

    if returncode:
        sys.exit("Parsing failed! Log file may contain more information: %s" % log_filename)

    return parsed_filename

def write_to_file(file, lines):
    for line in lines:
        print(line, file=file)
    print(file=file)

def write_to_output(options, tokenized_filename, tagged_filename, parsed_filename):
    if options.tokenized:
        shutil.copy(tokenized_filename, options.output_dir)

    if options.tagged:
        shutil.copy(tagged_filename, options.output_dir)

    if options.parsed:
        shutil.copy(parsed_filename, options.output_dir)

def cleanup(options, tmp_dir):
    if not options.no_delete:
        shutil.rmtree(tmp_dir)
    else:
        print("Leaving working directory as is: %s" % tmp_dir, file=sys.stderr)

def output_filename(tmp_dir, filename, suffix):
    directory, _ = os.path.splitext(filename)
    basename = os.path.basename(directory)
    return os.path.join(tmp_dir, "%s.%s" % (basename, suffix))

if __name__ == '__main__':
    main()
