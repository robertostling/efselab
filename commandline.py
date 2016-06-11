import os
import sys
from optparse import OptionParser

# Set some sensible defaults
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
MODEL_DIR = os.path.join(SCRIPT_DIR, "swe-pipeline")
TAGGING_MODEL = os.path.join(MODEL_DIR, "suc.bin")
NER_MODEL = os.path.join(MODEL_DIR, "suc-ne.bin")
UD_TAGGING_MODEL = os.path.join(MODEL_DIR, "suc-ud.bin")
LEMMATIZATION_MODEL = os.path.join(MODEL_DIR, "suc-saldo.lemmas")
PARSING_MODEL = os.path.join(MODEL_DIR, "maltmodel-UD_Swedish")
MALT = os.path.join(MODEL_DIR, "maltparser-1.8.1/maltparser-1.8.1.jar")

class AttrDict:
    def __init__(self, d):
        self.__dict__ = d

ERROR_MESSAGES = AttrDict({
    "no_action": "Nothing to do! Please use --tokenized, --tagged, --lemmatized --ner and/or --parsed (or --all)",
    "no_target": "No target directory specified. Use --output-dir=DIR",
    "no_filename": "Please specify at least one filename as input.",
    "not_found_tagging_model": "Can't find tagging model: %s",
    "lemmatized_without_tagged": "Can't lemmatize without tagging.",
    "ner_without_tagged_and_lemmatized": "Can't do NER without tagging and lemmatization.",
    "not_found_lemmatizer_model": "Can't find lemmatizer model file %s.",
    "not_found_maltparser": "Can't find MaltParser jar file %s.",
    "not_found_parsing_model": "Can't find parsing model: %s",
})

def create_parser():
    # Set up and parse command-line options
    usage = "usage: %prog --output-dir=DIR [options] FILENAME [...]"
    parser = OptionParser(usage=usage)
    parser.add_option("-o", "--output-dir", dest="output_dir", metavar="DIR",
                  help="set target directory for output (Required.)")
    parser.add_option("--skip-tokenization", dest="skip_tokenization",
                  action="store_true", help="Assume tokenized input")
    parser.add_option("--tokenized", dest="tokenized", action="store_true",
                  help="Generate tokenized output file(s) (*.tok)")
    parser.add_option("--tagged", dest="tagged", action="store_true",
                  help="Generate tagged output file(s) (*.tag)")
    parser.add_option("--lemmatized", dest="lemmatized", action="store_true",
                  help="Also lemmatize the tagged output file(s) (*.tag)")
    parser.add_option("--parsed", dest="parsed", action="store_true",
                  help="Generate parsed output file(s) (*.conll)")
    parser.add_option("--ner", dest="ner", action="store_true",
                  help="Generate named entity file(s) (*.ne)")
    parser.add_option("--all", dest="all", action="store_true",
                  help="Equivalent to --tokenized --tagged --lemmatized --ner --parsed")
    parser.add_option("-m", "--tagging-model", dest="tagging_model",
                  default=TAGGING_MODEL, metavar="FILENAME",
                  help="Model for PoS tagging")
    parser.add_option("-u", "--ud-tagging-model", dest="ud_tagging_model",
                  default=UD_TAGGING_MODEL, metavar="FILENAME",
                  help="Model for PoS tagging (UD wrapper)")
    parser.add_option("-l", "--lemmatization-model", dest="lemmatization_model",
                  default=LEMMATIZATION_MODEL, metavar="MODEL",
                  help="MaltParser model file for parsing")
    parser.add_option("-n", "--ner-model", dest="ner_model",
                  default=NER_MODEL, metavar="FILENAME",
                  help="Model for named entity recognizer")
    parser.add_option("-p", "--parsing-model", dest="parsing_model",
                  default=PARSING_MODEL, metavar="MODEL",
                  help="MaltParser model file for parsing")
    parser.add_option("--malt", dest="malt", default=MALT, metavar="JAR",
                  help=".jar file of MaltParser")
    parser.add_option("--no-delete", dest="no_delete", action="store_true",
                  help="Don't delete temporary working directory.")
    return parser

def validate_options(options, args):
    if options.all:
        options.tokenized = True
        options.tagged = True
        options.lemmatized = True
        options.parsed = True
        options.ner = True

    if not (options.tokenized or options.tagged or options.parsed or options.ner):
        sys.exit(ERROR_MESSAGES.no_action)

    # If no target directory was given: write error message and exit.
    if not options.output_dir:
        sys.exit(ERROR_MESSAGES.no_target)

    if not args:
        sys.exit(ERROR_MESSAGES.no_filename)

    # Set up (part of) command lines
    jarfile = os.path.expanduser(options.malt)

    # Make sure we have all we need
    if options.tagged and not os.path.exists(options.tagging_model):
        sys.exit(ERROR_MESSAGES.not_found_tagging_model % options.tagging_model)

    if options.lemmatized and not options.tagged:
        sys.exit(ERROR_MESSAGES.lemmatized_without_tagged)

    if options.ner and not (options.tagged and options.lemmatized):
        sys.exit(ERROR_MESSAGES.ner_without_tagged_and_lemmatized)

    if options.lemmatized and not os.path.exists(options.lemmatization_model):
        sys.exit(ERROR_MESSAGES.not_found_lemmatizer_model % options.lemmatization_model)

    if options.parsed and not os.path.exists(jarfile):
        sys.exit(ERROR_MESSAGES.not_found_maltparser % jarfile)

    if options.parsed and not os.path.exists(options.parsing_model + ".mco"):
        sys.exit(ERROR_MESSAGES.not_found_parsing_model % (options.parsing_model + ".mco"))
