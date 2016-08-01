from swe_pipeline import parse
import unittest
from unittest.mock import patch, MagicMock, mock_open

class TestParse(unittest.TestCase):
    def _default_options(self):
        options = MagicMock()
        options.malt = "/dummy/maltparser.jar"
        options.parsing_model = "/dummy/maltmodel.mco"
        return options

    @patch("swe_pipeline.tagged_to_tagged_conll")
    @patch("swe_pipeline.Popen")
    def test_run_parser(self, popen_mock, *args):
        options = self._default_options()

        popen_mock().wait.return_value = 0
        data = [zip(
            ["Hej", "mitt", "namn", "är"],
            ["hej", "min", "namn", "vara"],
            [
                "INTJ|_",
                "DET|Definite=Def|Gender=Neut|Number=Sing|Poss=Yes",
                "NOUN|Case=Nom|Definite=Ind|Gender=Neut|Number=Sing",
                "AUX|Mood=Ind|Tense=Pres|VerbForm=Fin|Voice=Act",
            ],
            ["IN", "PS|NEU|SIN|DEF", "NN|NEU|SIN|IND|NOM", "VB|PRS|AKT"],
        )]

        open_mock = mock_open()
        with patch("swe_pipeline.open", open_mock, create=True):
            self.assertEqual(
                parse(options, "file.txt", data, "/tmp"),
                "/tmp/file.conll"
            )
            arguments = popen_mock.call_args_list[1][0][0]
            self.assertEqual(
                " ".join(arguments),
                (
                    "java -Xmx2000m -jar /dummy/maltparser.jar "
                    "-m parse -i /tmp/file.tag.conll -o /tmp/file.conll "
                    "-w /tmp -c maltmodel.mco"
                )
            )

    @patch("swe_pipeline.tagged_to_tagged_conll")
    @patch("swe_pipeline.Popen")
    def test_parser_error(self, popen_mock, *args):
        options = self._default_options()

        popen_mock().wait.return_value = 1
        data = []

        open_mock = mock_open()
        with patch("swe_pipeline.open", open_mock, create=True):
            with self.assertRaises(SystemExit):
                parse(options, "file.txt", data, "/tmp")
