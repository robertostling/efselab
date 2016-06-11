import unittest
from commandline import (
    create_parser, validate_options, ERROR_MESSAGES,
    TAGGING_MODEL, NER_MODEL, LEMMATIZATION_MODEL, PARSING_MODEL, MALT,
)

def _validate_args(args):
    parser = create_parser()
    options, args = parser.parse_args(args)
    validate_options(options, args)
    return options, args

class TestCommandlineFailiures(unittest.TestCase):
    def test_empty(self):
        with self.assertRaises(SystemExit) as manager:
            _validate_args([])

        self.assertEqual(str(manager.exception), ERROR_MESSAGES.no_action)

    def test_no_target(self):
        with self.assertRaises(SystemExit) as manager:
            _validate_args(["--tokenized"])

        self.assertEqual(str(manager.exception), ERROR_MESSAGES.no_target)

        with self.assertRaises(SystemExit) as manager:
            _validate_args(["--all"])

        self.assertEqual(str(manager.exception), ERROR_MESSAGES.no_target)

    def test_no_filename(self):
        with self.assertRaises(SystemExit) as manager:
            _validate_args(["--tokenized", "--output=DIR"])

        self.assertEqual(str(manager.exception), ERROR_MESSAGES.no_filename)

        with self.assertRaises(SystemExit) as manager:
            _validate_args(["--all", "--output=DIR"])

        self.assertEqual(str(manager.exception), ERROR_MESSAGES.no_filename)

    def test_incorrect_tagging_model(self):
        with self.assertRaises(SystemExit) as manager:
            _validate_args(["--tagged", "--output=DIR", "--tagging-model=MODEL", "out.txt"])

        self.assertEqual(str(manager.exception), ERROR_MESSAGES.not_found_tagging_model % "MODEL")

    def test_lemmatized_without_tagged(self):
        with self.assertRaises(SystemExit) as manager:
            _validate_args(["--tokenized", "--lemmatized", "--output=DIR", "out.txt"])

        self.assertEqual(str(manager.exception), ERROR_MESSAGES.lemmatized_without_tagged)

    def test_ner_without_tagged_and_lemmatized(self):
        with self.assertRaises(SystemExit) as manager:
            _validate_args(["--ner", "--tagged", "--output=DIR", "out.txt"])

        self.assertEqual(str(manager.exception), ERROR_MESSAGES.ner_without_tagged_and_lemmatized)

    def test_incorrect_lemmatizer_model(self):
        with self.assertRaises(SystemExit) as manager:
            _validate_args(["--tokenized", "--tagged", "--lemmatized", "--output=DIR", "--lemmatization-model=MODEL", "out.txt"])

        self.assertEqual(str(manager.exception), ERROR_MESSAGES.not_found_lemmatizer_model % "MODEL")

    def test_incorrect_maltparser(self):
        with self.assertRaises(SystemExit) as manager:
            _validate_args(["--parsed", "--output=DIR", "--malt=JARFILE", "out.txt"])

        self.assertEqual(str(manager.exception), ERROR_MESSAGES.not_found_maltparser % "JARFILE")

    def test_incorrect_parsing_model(self):
        with self.assertRaises(SystemExit) as manager:
            _validate_args(["--parsed", "--output=DIR", "--parsing-model=MODEL", "out.txt"])

        self.assertEqual(str(manager.exception), ERROR_MESSAGES.not_found_parsing_model % "MODEL.mco")

class TestCommandlineSuccesses(unittest.TestCase):
    def test_all(self):
        options, args = _validate_args(["--all", "--output=DIR", "out.txt"])
        self.assertEqual(options.tokenized, True)
        self.assertEqual(options.tagged, True)
        self.assertEqual(options.lemmatized, True)
        self.assertEqual(options.parsed, True)
        self.assertEqual(options.ner, True)
        self.assertEqual(options.output_dir, "DIR")
        self.assertEqual(args, ["out.txt"])

    def test_single_commands(self):
        _validate_args(["--tokenized", "--output=DIR", "out.txt"])
        _validate_args(["--tagged", "--output=DIR", "out.txt"])
        _validate_args(["--tagged", "--lemmatized", "--output=DIR", "out.txt"])
        _validate_args(["--parsed", "--output=DIR", "out.txt"])
        _validate_args(["--ner", "--tagged", "--lemmatized", "--output=DIR", "out.txt"])

    def test_multiple_filenames(self):
        options, args = _validate_args(["--tokenized", "--output=DIR", "out1.txt", "out2.txt"])
        self.assertEqual(args, ["out1.txt", "out2.txt"])

    def test_custom_models(self):
        _validate_args(["--tagged", "--output=DIR", "--tagging-model=" + TAGGING_MODEL, "out.txt"])
        _validate_args(["--tagged", "--lemmatized", "--output=DIR", "--lemmatization-model=" + LEMMATIZATION_MODEL, "out.txt"])
        _validate_args(["--parsed", "--output=DIR", "--parsing-model=" + PARSING_MODEL, "out.txt"])
        _validate_args(["--ner", "--tagged", "--lemmatized", "--output=DIR", "--ner-model=" + NER_MODEL, "out.txt"])

    def test_custom_malt_jar(self):
        _validate_args(["--tagged", "--output=DIR", "--malt=" + MALT, "out.txt"])
