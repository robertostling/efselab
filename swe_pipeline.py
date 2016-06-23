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
from subprocess import Popen

from commandline import create_parser, validate_options
from conll import tagged_to_tagged_conll
from lemmatize import SUCLemmatizer
from tagger import SucTagger, SucNETagger, UDTagger
from tokenizer import build_sentences

__authors__ = """
Filip Salomonsson <filip.salomonsson@gmail.com>
Robert Östling <robert.ostling@helsinki.fi>
Aaron Smith <aaron.smith@lingfil.uu.se>
"""

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

def main():
    parser = create_parser()
    options, args = parser.parse_args()
    validate_options(options, args)
    run_pipeline(options, args)

def run_pipeline(options, args):
    models = {
        "suc_ne_tagger": None,
        "suc_tagger": None,
        "ud_tagger": None,
        "lemmatizer": None,
    }
    if options.tagged or options.ner or options.parsed:
        models["suc_tagger"] = SucTagger(options.tagging_model)

        if options.lemmatized:
            models["ud_tagger"] = UDTagger(options.ud_tagging_model)

    if options.ner:
        models["suc_ne_tagger"] = SucNETagger(options.ner_model)

    # Set up the working directory
    tmp_dir = tempfile.mkdtemp("-stb-pipeline")
    if options.parsed:
        shutil.copy(
            os.path.join(SCRIPT_DIR, options.parsing_model + ".mco"),
            tmp_dir
        )

    if options.lemmatized:
        models["lemmatizer"] = SUCLemmatizer()
        models["lemmatizer"].load(options.lemmatization_model)

    # Process each input file
    for filename in args:
        process_file(
            options,
            filename,
            tmp_dir,
            models,
        )

    cleanup(options, tmp_dir)

def process_file(options, filename, tmp_dir, models):
    print("Processing %s..." % filename, file=sys.stderr)

    tokenized_filename = output_filename(tmp_dir, filename, "tok")
    tagged_filename = output_filename(tmp_dir, filename, "tag")
    ner_filename = output_filename(tmp_dir, filename, "ne")

    sentences = run_tokenization(options, filename)
    annotated_sentences = []

    with open(tokenized_filename, "w", encoding="utf-8") as tokenized, \
            open(tagged_filename, "w", encoding="utf-8") as tagged, \
            open(ner_filename, "w", encoding="utf-8") as ner:

        # Run only one pass over sentences for writing to both files
        for sentence in sentences:
            write_to_file(tokenized, sentence)

            if options.tagged or options.parsed or options.ner:
                lemmas, ud_tags_list, suc_tags_list, suc_ne_list = \
                    run_tagging_and_lemmatization(options, sentence, models)

                annotated_sentences.append(
                    zip(sentence, lemmas, ud_tags_list, suc_tags_list)
                )

                ud_tag_list = [
                    ud_tags[:ud_tags.find("|")]
                    for ud_tags in ud_tags_list
                ]

                if lemmas and ud_tags_list:
                    line_tokens = sentence, suc_tags_list, ud_tag_list, lemmas
                else:
                    line_tokens = sentence, suc_tags_list

                lines = ["\t".join(line) for line in zip(*line_tokens)]

                write_to_file(tagged, lines)

                if options.ner:
                    ner_lines = [
                        "\t".join(line)
                        for line in zip(sentence, suc_ne_list)
                    ]

                    write_to_file(ner, ner_lines)

    parsed_filename = ""
    if options.parsed:
        parsed_filename = parse(
            options, filename, annotated_sentences, tmp_dir
        )

    write_to_output([
        (options.tokenized, tokenized_filename, options.output_dir),
        (options.tagged, tagged_filename, options.output_dir),
        (options.parsed, parsed_filename, options.output_dir),
        (options.ner, ner_filename, options.output_dir),
    ])

    print("done.", file=sys.stderr)

def run_tokenization(options, filename):
    with open(filename, "r", encoding="utf-8") as input_file:
        data = input_file.read()

        if options.skip_tokenization:
            sentences = [
                sentence.split('\n')
                for sentence in data.split('\n\n')
                if sentence.strip()
            ]
        else:
            sentences = build_sentences(data)

    return sentences

def run_tagging_and_lemmatization(options, sentence, models):
    lemmas = []
    ud_tags_list = []
    suc_tags_list = models["suc_tagger"].tag(sentence)

    if options.lemmatized:
        lemmas = [
            models["lemmatizer"].predict(token, tag)
            for token, tag in zip(sentence, suc_tags_list)
        ]
        ud_tags_list = models["ud_tagger"].tag(sentence, lemmas, suc_tags_list)

        if options.ner:
            suc_ne_list = models["suc_ne_tagger"].tag(
                list(zip(sentence, lemmas, suc_tags_list))
            )
        else:
            suc_ne_list = []

    return lemmas, ud_tags_list, suc_tags_list, suc_ne_list

def parse(options, filename, annotated_sentences, tmp_dir):
    tagged_conll_filename = output_filename(tmp_dir, filename, "tag.conll")
    parsed_filename = output_filename(tmp_dir, filename, "conll")
    log_filename = output_filename(tmp_dir, filename, "log")

    # The parser command line is dependent on the input and
    # output files, so we build that one for each data file
    parser_cmdline = [
        "java",
        "-Xmx2000m",
        "-jar", os.path.expanduser(options.malt),
        "-m", "parse",
        "-i", tagged_conll_filename,
        "-o", parsed_filename,
        "-w", tmp_dir,
        "-c", os.path.basename(options.parsing_model)
    ]

    # Conversion from .tag file to tagged.conll (input format for the parser)
    tagged_conll_file = open(tagged_conll_filename, "w", encoding="utf-8")
    tagged_to_tagged_conll(annotated_sentences, tagged_conll_file)
    tagged_conll_file.close()

    # Run the parser
    with open(log_filename, "w", encoding="utf-8") as log_file:
        returncode = Popen(
            parser_cmdline, stdout=log_file, stderr=log_file
        ).wait()

    if returncode:
        sys.exit("Parsing failed! See log file: %s" % log_filename)

    return parsed_filename

def write_to_file(file, lines):
    for line in lines:
        print(line, file=file)
    print(file=file)

def write_to_output(filename_mapping):
    for should_copy, filename, output_dir in filename_mapping:
        if should_copy:
            shutil.copy(filename, output_dir)

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
