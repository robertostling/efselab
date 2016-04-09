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

if __name__ == '__main__':
    # Set some sensible defaults
    SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
    MODEL_DIR = os.path.join(SCRIPT_DIR, "swe-pipeline")
    TAGGING_MODEL = os.path.join(MODEL_DIR, "suc.bin")
    UD_TAGGING_MODEL = os.path.join(MODEL_DIR, "suc-ud.bin")
    LEMMATIZATION_MODEL = os.path.join(MODEL_DIR, "suc-saldo.lemmas")
    PARSING_MODEL = os.path.join(MODEL_DIR, "maltmodel-UD_Swedish")
    MALT = os.path.join(MODEL_DIR, "maltparser-1.8.1/maltparser-1.8.1.jar")

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

    options, args = op.parse_args()
    if options.all:
        options.tokenized = True
        options.tagged = True
        options.lemmatized = True
        options.parsed = True

    if not (options.tokenized or options.tagged or options.parsed):
        op.error("Nothing to do! Please use --tokenized, --tagged, --lemmatized and/or --parsed (or --all)")

    # If no target directory was given: write error message and exit.
    if not options.output_dir:
        op.error("No target directory specified. Use --output-dir=DIR")

    if not args:
        op.error("Please specify at least one filename as input.")

    # Set up (part of) command lines
    jarfile = os.path.expanduser(options.malt)

    # Make sure we have all we need
    if options.tagged and not os.path.exists(options.tagging_model):
        sys.exit("Can't find tagging model: %s" % options.tagging_model)
    if options.lemmatized and not options.tagged:
        sys.exit("Can't lemmatize without tagging.")
    if options.lemmatized and not os.path.exists(options.lemmatization_model):
        sys.exit("Can't find lemmatizer model file %s." %
                 options.lemmatization_model)
    if options.parsed and not os.path.exists(jarfile):
        sys.exit("Can't find MaltParser jar file %s." % jarfile)
    if options.parsed and not os.path.exists(options.parsing_model+".mco"):
        sys.exit("Can't find parsing model: %s" % options.parsing_model+".mco")

    if options.tagged or options.parsed:
        suc_tagger = SucTagger(options.tagging_model)

        if options.lemmatized:
            ud_tagger = UDTagger(options.ud_tagging_model)

    # Set up the working directory
    tmp_dir = tempfile.mkdtemp("-stb-pipeline")
    if options.parsed:
        shutil.copy(os.path.join(SCRIPT_DIR, options.parsing_model+".mco"),
                    tmp_dir)

    lemmatizer = None
    if options.lemmatized:
        lemmatizer = SUCLemmatizer()
        lemmatizer.load(options.lemmatization_model)

    # Process each input file
    for filename in args:
        name_root, ext = os.path.splitext(filename)
        basename = os.path.basename(name_root)

        def output_filename(suffix):
            return os.path.join(tmp_dir, "%s.%s" % (basename, suffix))

        # Set up output filenames
        tokenized_filename = output_filename("tok")
        tagged_filename = output_filename("tag")
        tagged_conll_filename = output_filename("tag.conll")
        parsed_filename = output_filename("conll")
        log_filename = output_filename("log")


        # The parser command line is dependent on the input and
        # output files, so we build that one for each data file
        parser_cmdline = ["java", "-Xmx2000m",
                          "-jar", jarfile,
                          "-m", "parse",
                          "-i", tagged_conll_filename,
                          "-o", parsed_filename,
                          "-w", tmp_dir,
                          "-c", os.path.basename(options.parsing_model)]


        # Open the log file for writing
        log_file = open(log_filename, "w")

        print("Processing %s..."% (filename), file=sys.stderr)

        # Read input data file
        data = open(filename, "r", encoding="utf-8").read()


        #########################################
        # Tokenization, tagging and lemmatization

        if options.skip_tokenization:
            sentences = [
                    sentence.split('\n')
                    for sentence in data.split('\n\n')
                    if sentence.strip()]
        else:
            sentences = build_sentences(data)

        # Write tokenized data to output dir, optionally tag as well
        tokenized = None
        if options.tokenized or options.tagged:
            tokenized = open(tokenized_filename, "w", encoding="utf-8")

        tagged = None
        if options.tagged or options.parsed:
            tagged = open(tagged_filename, "w")

        for s_id, sentence in enumerate(sentences):
            for t_id, token in enumerate(sentence):
                print(token, file=tokenized)
            print(file=tokenized)

            if tagged:
                suc_tags = suc_tagger.tag(sentence)
                if lemmatizer:
                    lemmas = [lemmatizer.predict(token, tag) for token, tag in zip(sentence, suc_tags)]
                    ud_tags = ud_tagger.tag(sentence, lemmas, suc_tags)
                    for row in zip(sentence, suc_tags, ud_tags, lemmas):
                        print("\t".join(row), file=tagged)
                else:
                    for token, tag in zip(sentence, suc_tags):
                        print(token + '\t' + tag, file=tagged)
                print(file=tagged)

        if tokenized: tokenized.close()
        if tagged: tagged.close()

        if options.tokenized:
            shutil.copy(tokenized_filename, options.output_dir)

        if options.tagged:
            shutil.copy(tagged_filename, options.output_dir)

        #########
        # Parsing

        if options.parsed:
            # Conversion from .tag file to tagged.conll (input format for the parser)
            tagged_conll_file = open(tagged_conll_filename, "w", encoding="utf-8")
            tagged_to_tagged_conll(open(tagged_filename, "r", encoding="utf-8"),
                                   tagged_conll_file)
            tagged_conll_file.close()

            # Run the parser
            returncode = Popen(parser_cmdline,
                               stdout=log_file, stderr=log_file).wait()
            if returncode:
                sys.exit("Parsing failed! Log file may contain "
                         "more information: %s" % log_filename)

            if options.parsed:
                shutil.copy(parsed_filename, options.output_dir)

        # end: if options.parsed

        log_file.close()

        print("done.", file=sys.stderr)


    ##########
    # Clean up

    if not options.no_delete:
        shutil.rmtree(tmp_dir)
    else:
        print("Leaving working directory as is: %s" % tmp_dir, file=sys.stderr)
