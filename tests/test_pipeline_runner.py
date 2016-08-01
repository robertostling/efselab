from swe_pipeline import run_pipeline
import tempfile
import unittest
from unittest.mock import patch, MagicMock

class TestRunner(unittest.TestCase):
    def setUp(self):
        self.file = tempfile.NamedTemporaryFile()

    def tearDown(self):
        self.file.close()

    def _default_options(
        self, tagged=False, ner=False, parsed=False, lemmatized=False
    ):
        options = MagicMock()
        options.tagged = tagged
        options.tagging_model = self.file.name
        options.ud_tagging_model = self.file.name
        options.ner = ner
        options.ner_model = self.file.name
        options.parsed = parsed
        options.parsing_model = self.file.name
        options.lemmatized = lemmatized
        options.lemmatization_model = self.file.name

        return options

    @patch("swe_pipeline.cleanup")
    @patch("swe_pipeline.tempfile")
    @patch("swe_pipeline.process_file")
    def test_empty_options(self, process_file_mock, *args):
        options = self._default_options()
        run_pipeline(options, [])

        self.assertEqual(process_file_mock.call_count, 0)

    @patch("swe_pipeline.cleanup")
    @patch("swe_pipeline.tempfile")
    @patch("swe_pipeline.process_file")
    def test_one_file(self, process_file_mock, tempfile_mock, *args):
        options = self._default_options()
        tempfile_mock.mkdtemp.return_value = "/tmp/dir"

        run_pipeline(options, ["file.txt"])

        arguments = process_file_mock.call_args_list[0][0]
        self.assertEqual(arguments[1], "file.txt")
        self.assertEqual(arguments[3]['suc_ne_tagger'], None)
        self.assertEqual(arguments[3]['suc_tagger'], None)
        self.assertEqual(arguments[3]['ud_tagger'], None)
        self.assertEqual(arguments[3]['lemmatizer'], None)

    @patch("swe_pipeline.cleanup")
    @patch("swe_pipeline.tempfile")
    @patch("swe_pipeline.process_file")
    def test_one_with_tagger(self, process_file_mock, tempfile_mock, *args):
        options = self._default_options(tagged=True)
        tempfile_mock.mkdtemp.return_value = "/tmp/dir"

        run_pipeline(options, ["file.txt"])

        arguments = process_file_mock.call_args_list[0][0]
        self.assertEqual(arguments[1], "file.txt")
        self.assertEqual(arguments[3]['suc_ne_tagger'], None)
        self.assertEqual(
            arguments[3]['suc_tagger'].__class__.__name__,
            "SucTagger",
        )
        self.assertEqual(arguments[3]['ud_tagger'], None)
        self.assertEqual(arguments[3]['lemmatizer'], None)

    @patch("swe_pipeline.cleanup")
    @patch("swe_pipeline.tempfile")
    @patch("swe_pipeline.process_file")
    def test_one_with_ner(self, process_file_mock, tempfile_mock, *args):
        options = self._default_options(ner=True)
        tempfile_mock.mkdtemp.return_value = "/tmp/dir"

        run_pipeline(options, ["file.txt"])

        arguments = process_file_mock.call_args_list[0][0]
        self.assertEqual(arguments[1], "file.txt")
        self.assertEqual(
            arguments[3]['suc_ne_tagger'].__class__.__name__,
            "SucNETagger"
        )
        self.assertEqual(
            arguments[3]['suc_tagger'].__class__.__name__,
            "SucTagger"
        )
        self.assertEqual(arguments[3]['ud_tagger'], None)
        self.assertEqual(arguments[3]['lemmatizer'], None)

    @patch("swe_pipeline.cleanup")
    @patch("swe_pipeline.tempfile")
    @patch("swe_pipeline.shutil")
    @patch("swe_pipeline.process_file")
    def test_one_with_parsed(
        self, process_file_mock, shutil_mock, tempfile_mock, *args
    ):
        options = self._default_options(parsed=True)
        tempfile_mock.mkdtemp.return_value = "/tmp/dir"

        run_pipeline(options, ["file.txt"])

        arguments = process_file_mock.call_args_list[0][0]
        self.assertEqual(arguments[1], "file.txt")
        self.assertEqual(arguments[3]['suc_ne_tagger'], None)
        self.assertEqual(
            arguments[3]['suc_tagger'].__class__.__name__,
            "SucTagger"
        )
        self.assertEqual(arguments[3]['ud_tagger'], None)
        self.assertEqual(arguments[3]['lemmatizer'], None)

        self.assertEqual(shutil_mock.copy.call_count, 1)

    @patch("swe_pipeline.cleanup")
    @patch("swe_pipeline.tempfile")
    @patch("swe_pipeline.process_file")
    def test_tagger_and_lemma(self, process_file_mock, tempfile_mock, *args):
        options = self._default_options(tagged=True, lemmatized=True)
        tempfile_mock.mkdtemp.return_value = "/tmp/dir"

        run_pipeline(options, ["file.txt"])

        arguments = process_file_mock.call_args_list[0][0]
        self.assertEqual(arguments[1], "file.txt")
        self.assertEqual(arguments[3]['suc_ne_tagger'], None)
        self.assertEqual(
            arguments[3]['suc_tagger'].__class__.__name__,
            "SucTagger"
        )
        self.assertEqual(
            arguments[3]['ud_tagger'].__class__.__name__,
            "UDTagger"
        )
        self.assertEqual(
            arguments[3]['lemmatizer'].__class__.__name__,
            "SUCLemmatizer"
        )

    @patch("swe_pipeline.cleanup")
    @patch("swe_pipeline.tempfile")
    @patch("swe_pipeline.process_file")
    def test_two_files(self, process_file_mock, tempfile_mock, *args):
        options = self._default_options()
        tempfile_mock.mkdtemp.return_value = "/tmp/dir"

        run_pipeline(options, ["file1.txt", "file2.txt"])

        arguments = process_file_mock.call_args_list[0][0]
        self.assertEqual(arguments[1], "file1.txt")
        self.assertEqual(arguments[3]['suc_ne_tagger'], None)
        self.assertEqual(arguments[3]['suc_tagger'], None)
        self.assertEqual(arguments[3]['ud_tagger'], None)
        self.assertEqual(arguments[3]['lemmatizer'], None)

        arguments = process_file_mock.call_args_list[1][0]
        self.assertEqual(arguments[1], "file2.txt")
        self.assertEqual(arguments[3]['suc_ne_tagger'], None)
        self.assertEqual(arguments[3]['suc_tagger'], None)
        self.assertEqual(arguments[3]['ud_tagger'], None)
        self.assertEqual(arguments[3]['lemmatizer'], None)
