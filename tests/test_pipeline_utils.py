import os
from swe_pipeline import write_to_file, write_to_output, cleanup, output_filename
import sys
from textwrap import dedent
import unittest
from unittest.mock import call, patch, MagicMock, mock_open

class TestUtils(unittest.TestCase):
    def test_write_to_file(self):
        file = MagicMock()
        write_to_file(file, ["first line", "second line"])

        data = "".join([call[0][0] for call in file.write.call_args_list])
        self.assertEqual(data, dedent("""
            first line
            second line

        """).lstrip())

    @patch("swe_pipeline.shutil")
    def test_write_to_output(self, shutil_mock):
        write_to_output([
            (True, "file1", "/tmp1"),
            (False, "file2", "/tmp2"),
            (True, "file3", "/tmp3"),
        ])
        self.assertEqual(
            shutil_mock.copy.call_args_list,
            [call('file1', '/tmp1'), call('file3', '/tmp3')]
        )

    @patch("swe_pipeline.shutil")
    def test_cleanup_delete(self, shutil_mock):
        options = MagicMock()
        options.no_delete = False
        cleanup(options, "/tmp")
        self.assertEqual(
            shutil_mock.rmtree.call_args_list,
            [call('/tmp')]
        )

    @patch("swe_pipeline.shutil")
    def test_cleanup_without_delete(self, shutil_mock):
        options = MagicMock()
        options.no_delete = True
        with open(os.devnull, 'w') as sys.stderr:
            cleanup(options, "/tmp")

        self.assertEqual(shutil_mock.rmtree.call_args_list, [])

    def test_output_filename(self):
        self.assertEqual(
            output_filename("/tmp", "file", "txt"),
            "/tmp/file.txt"
        )
        self.assertEqual(
            output_filename("/tmp/", "file", "txt"),
            "/tmp/file.txt"
        )
        self.assertEqual(
            output_filename("/tmp/", "file.bin", "txt"),
            "/tmp/file.txt"
        )
        self.assertEqual(
            output_filename("/tmp", "/home/file.bin", "txt"),
            "/tmp/file.txt"
        )
