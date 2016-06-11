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
    op.add_option("--ner", dest="ner", action="store_true",
                  help="Generate named entity file(s) (*.ne)")
    op.add_option("--all", dest="all", action="store_true",
                  help="Equivalent to --tokenized --tagged --lemmatized --ner --parsed")
    op.add_option("-m", "--tagging-model", dest="tagging_model",
                  default=TAGGING_MODEL, metavar="FILENAME",
                  help="Model for PoS tagging")
    op.add_option("-u", "--ud-tagging-model", dest="ud_tagging_model",
                  default=UD_TAGGING_MODEL, metavar="FILENAME",
                  help="Model for PoS tagging (UD wrapper)")
    op.add_option("-l", "--lemmatization-model", dest="lemmatization_model",
                  default=LEMMATIZATION_MODEL, metavar="MODEL",
                  help="MaltParser model file for parsing")
    op.add_option("-n", "--ner-model", dest="ner_model",
                  default=NER_MODEL, metavar="FILENAME",
                  help="Model for named entity recognizer")
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
        options.ner = True

    if not (   options.tokenized or options.tagged or options.parsed
            or options.ner):
        sys.exit("Nothing to do! Please use --tokenized, --tagged, --lemmatized --ner and/or --parsed (or --all)")

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
    if options.ner and not (options.tagged and options.lemmatized):
        sys.exit("Can't do NER without tagging and lemmatization.")
    if options.lemmatized and not os.path.exists(options.lemmatization_model):
        sys.exit("Can't find lemmatizer model file %s." % options.lemmatization_model)
    if options.parsed and not os.path.exists(jarfile):
        sys.exit("Can't find MaltParser jar file %s." % jarfile)
    if options.parsed and not os.path.exists(options.parsing_model + ".mco"):
        sys.exit("Can't find parsing model: %s" % options.parsing_model + ".mco")
