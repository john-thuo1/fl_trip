"""
Tests for the CLI convert functionality.

.. raw:: html
    <!--
    * Copyright (C) 2024 Scribe
    *
    * This program is free software: you can redistribute it and/or modify
    * it under the terms of the GNU General Public License as published by
    * the Free Software Foundation, either version 3 of the License, or
    * (at your option) any later version.
    *
    * This program is distributed in the hope that it will be useful,
    * but WITHOUT ANY WARRANTY; without even the implied warranty of
    * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    * GNU General Public License for more details.
    *
    * You should have received a copy of the GNU General Public License
    * along with this program.  If not, see <https://www.gnu.org/licenses/>.
    -->
"""

from io import StringIO
import json
from pathlib import Path
import unittest
from unittest.mock import MagicMock, Mock, mock_open, patch


from scribe_data.cli.convert import (
    convert_to_json,
    convert_to_sqlite,
    convert_to_csv_or_tsv,
)


class TestConvert(unittest.TestCase):
    # Helper Functions
    def setup_language_map(self, mock_language_map: Mock) -> None:
        """
        Set up the mock language map for testing.

        Parameters
        ---------
            mock_language_map: Mock
                Mock object representing the language map
                to be configured.

        Returns
        -------
            None
        """
        mock_language_map.get.side_effect = lambda lang: {
            "english": {
                "language": "english",
                "iso": "en",
                "qid": "Q1860",
                "remove-words": ["of", "the", "The", "and"],
                "ignore-words": [],
            },
            "french": {
                "language": "french",
                "iso": "fr",
                "qid": "Q150",
                "remove-words": ["of", "the", "The", "and"],
                "ignore-words": ["XXe"],
            },
        }.get(lang.lower())

    def normalize_line_endings(self, data: str) -> str:
        """
        Normalize line endings in a given string.

        This method replaces Windows-style line endings (`\r\n`) and
        standalone carriage return characters (`\r`) with Unix-style
        line endings (`\n`). This is useful for ensuring consistent
        line endings when comparing strings or writing to files.

        Parameters
        ----------
            data: str
                The input string whose line endings are to be normalized.

        Returns
        ---------
            data: str
                The input string with normalized line endings.
        """
        return data.replace("\r\n", "\n").replace("\r", "\n")

    # MARK: JSON Tests

    @patch("scribe_data.cli.convert.language_map", autospec=True)
    @patch("scribe_data.cli.convert.Path", autospec=True)
    def test_convert_to_json_normalized_language(self, mock_path, mock_language_map):
        self.setup_language_map(mock_language_map)

        mock_path_obj = MagicMock(spec=Path)
        mock_path.return_value = mock_path_obj

        mock_path_obj.suffix = ".csv"
        mock_path_obj.exists.return_value = True

        convert_to_json(
            language="French",
            data_type="nouns",
            output_type="json",
            input_file="input.csv",
            output_dir="/output_dir",
            overwrite=True,
        )

        mock_language_map.get.assert_called_with("french")

    @patch("scribe_data.cli.convert.language_map", autospec=True)
    @patch("scribe_data.cli.convert.Path", autospec=True)
    def test_convert_to_json_unknown_language(self, mock_path, mock_language_map):
        mock_language_map.get.return_value = None
        # Mock for input file and output_directory
        mock_input_file_path = MagicMock(spec=Path)
        mock_input_file_path.exists.return_value = True
        mock_path.side_effect = [mock_input_file_path, MagicMock(spec=Path)]

        with self.assertRaises(ValueError) as context:
            convert_to_json(
                language="kazatan",
                data_type="nouns",
                output_type="json",
                input_file="test.csv",
                output_dir="/output_dir",
                overwrite=True,
            )

        # Assert the error message
        self.assertEqual(
            str(context.exception), "Language 'Kazatan' is not recognized."
        )

    @patch("scribe_data.cli.convert.Path")
    def test_convert_to_json_with_input_file(self, mock_path):
        csv_data = "key,value\na,1\nb,2"
        mock_file = StringIO(csv_data)

        mock_path_obj = MagicMock(spec=Path)
        mock_path.return_value = mock_path_obj
        mock_path_obj.suffix = ".csv"
        mock_path_obj.exists.return_value = True
        mock_path_obj.open.return_value.__enter__.return_value = mock_file

        convert_to_json(
            language="English",
            data_type="nouns",
            output_type="json",
            input_file="test.csv",
            output_dir="/output_dir",
            overwrite=True,
        )

        mock_path_obj.exists.assert_called_once()

        mock_path_obj.open.assert_called_once_with("r", encoding="utf-8")

    @patch("scribe_data.cli.convert.Path")
    def test_convert_to_json_no_input_file(self, mock_path):
        mock_path_obj = MagicMock(spec=Path)
        mock_path.return_value = mock_path_obj
        mock_path_obj.exists.return_value = False

        mock_path_obj.__str__.return_value = "Data/ecode.csv"

        with self.assertRaises(FileNotFoundError) as context:
            convert_to_json(
                language="English",
                data_type="nouns",
                output_type="json",
                input_file="Data/ecode.csv",
                output_dir="/output_dir",
                overwrite=True,
            )

        self.assertEqual(
            str(context.exception), "No data found for input file 'Data/ecode.csv'."
        )

        mock_path_obj.exists.assert_called_once()

    @patch("scribe_data.cli.convert.Path")
    def test_convert_to_json_supported_file_extension_csv(self, mock_path):
        mock_path_obj = MagicMock(spec=Path)
        mock_path.return_value = mock_path_obj

        mock_path_obj.suffix = ".csv"
        mock_path_obj.exists.return_value = True

        convert_to_json(
            language="English",
            data_type="nouns",
            output_type="json",
            input_file="test.csv",
            output_dir="/output_dir",
            overwrite=True,
        )

    @patch("scribe_data.cli.convert.Path")
    def test_convert_to_json_supported_file_extension_tsv(self, mock_path):
        mock_path_obj = MagicMock(spec=Path)
        mock_path.return_value = mock_path_obj

        mock_path_obj.suffix = ".tsv"
        mock_path_obj.exists.return_value = True

        convert_to_json(
            language="English",
            data_type="nouns",
            output_type="json",
            input_file="test.tsv",
            output_dir="/output_dir",
            overwrite=True,
        )

    @patch("scribe_data.cli.convert.Path")
    def test_convert_to_json_unsupported_file_extension(self, mock_path):
        mock_path_obj = MagicMock(spec=Path)
        mock_path.return_value = mock_path_obj

        mock_path_obj.suffix = ".txt"
        mock_path_obj.exists.return_value = True

        with self.assertRaises(ValueError) as context:
            convert_to_json(
                language="English",
                data_type="nouns",
                output_type="json",
                input_file="test.txt",
                output_dir="/output_dir",
                overwrite=True,
            )

        self.assertIn("Unsupported file extension", str(context.exception))
        self.assertEqual(
            str(context.exception),
            "Unsupported file extension '.txt' for test.txt. Please provide a '.csv' or '.tsv' file.",
        )

    @patch("scribe_data.cli.convert.language_map", autospec=True)
    @patch("scribe_data.cli.convert.Path", autospec=True)
    def test_convert_to_json_standard_csv(self, mock_path_class, mock_language_map):
        csv_data = "key,value\na,1\nb,2"
        expected_json = {"a": "1", "b": "2"}
        mock_file_obj = StringIO(csv_data)

        self.setup_language_map(mock_language_map)

        mock_input_file_path = MagicMock(spec=Path)
        mock_input_file_path.suffix = ".csv"
        mock_input_file_path.exists.return_value = True
        mock_input_file_path.open.return_value.__enter__.return_value = mock_file_obj

        mock_path_class.side_effect = (
            lambda x: mock_input_file_path if x == "test.csv" else Path(x)
        )

        mocked_open = mock_open()

        with patch("pathlib.Path.open", mocked_open), patch(
            "pathlib.Path.mkdir"
        ) as mock_mkdir:
            mock_mkdir.return_value = None
            convert_to_json(
                language="English",
                data_type="nouns",
                output_type="json",
                input_file="test.csv",
                output_dir="/output_dir",
                overwrite=True,
            )

        mocked_open.assert_called_once_with("w", encoding="utf-8")

        mock_file_handle = mocked_open()
        written_data = "".join(
            call.args[0] for call in mock_file_handle.write.call_args_list
        )

        self.assertEqual(json.loads(written_data), expected_json)

    @patch("scribe_data.cli.convert.language_map", autospec=True)
    @patch("scribe_data.cli.convert.Path", autospec=True)
    def test_convert_to_json_with_multiple_keys(
        self, mock_path_class, mock_language_map
    ):
        csv_data = "key,value1,value2\na,1,x\nb,2,y\nc,3,z"
        expected_json = {
            "a": {"value1": "1", "value2": "x"},
            "b": {"value1": "2", "value2": "y"},
            "c": {"value1": "3", "value2": "z"},
        }
        mock_file_obj = StringIO(csv_data)

        self.setup_language_map(mock_language_map)

        mock_input_file_path = MagicMock(spec=Path)
        mock_input_file_path.suffix = ".csv"
        mock_input_file_path.exists.return_value = True
        mock_input_file_path.open.return_value.__enter__.return_value = mock_file_obj
        mock_path_class.side_effect = (
            lambda x: mock_input_file_path if x == "test.csv" else Path(x)
        )

        mocked_open = mock_open()
        with patch("pathlib.Path.open", mocked_open), patch(
            "pathlib.Path.mkdir"
        ) as mock_mkdir:
            mock_mkdir.return_value = None
            convert_to_json(
                language="English",
                data_type="nouns",
                output_type="json",
                input_file="test.csv",
                output_dir="/output_dir",
                overwrite=True,
            )

        mock_file_handle = mocked_open()
        written_data = "".join(
            call.args[0] for call in mock_file_handle.write.call_args_list
        )
        self.assertEqual(json.loads(written_data), expected_json)

    @patch("scribe_data.cli.convert.language_map", autospec=True)
    @patch("scribe_data.cli.convert.Path", autospec=True)
    def test_convert_to_json_with_complex_structure(
        self, mock_path_class, mock_language_map
    ):
        csv_data = "key,emoji,is_base,rank\na,😀,true,1\nb,😅,false,2"
        expected_json = {
            "a": [{"emoji": "😀", "is_base": True, "rank": 1}],
            "b": [{"emoji": "😅", "is_base": False, "rank": 2}],
        }
        mock_file_obj = StringIO(csv_data)

        self.setup_language_map(mock_language_map)

        mock_input_file_path = MagicMock(spec=Path)
        mock_input_file_path.suffix = ".csv"
        mock_input_file_path.exists.return_value = True
        mock_input_file_path.open.return_value.__enter__.return_value = mock_file_obj
        mock_path_class.side_effect = (
            lambda x: mock_input_file_path if x == "test.csv" else Path(x)
        )

        mocked_open = mock_open()
        with patch("pathlib.Path.open", mocked_open), patch(
            "pathlib.Path.mkdir"
        ) as mock_mkdir:
            mock_mkdir.return_value = None
            convert_to_json(
                language="English",
                data_type="nouns",
                output_type="json",
                input_file="test.csv",
                output_dir="/output",
                overwrite=True,
            )

        mock_file_handle = mocked_open()
        written_data = "".join(
            call.args[0] for call in mock_file_handle.write.call_args_list
        )
        self.assertEqual(json.loads(written_data), expected_json)

    # MARK: CSV OR TSV Tests

    @patch("scribe_data.cli.convert.language_map", autospec=True)
    @patch("scribe_data.cli.convert.Path", autospec=True)
    def test_convert_to_csv_or_json_normalized_language(
        self, mock_path, mock_language_map
    ):
        self.setup_language_map(mock_language_map)

        mock_path_obj = MagicMock(spec=Path)
        mock_path.return_value = mock_path_obj

        mock_path_obj.suffix = ".json"
        mock_path_obj.exists.return_value = True

        mock_json_data = json.dumps({"key1": "value1", "key2": "value2"})
        mock_open_function = mock_open(read_data=mock_json_data)
        mock_path_obj.open = mock_open_function

        convert_to_csv_or_tsv(
            language="English",
            data_type="nouns",
            output_type="csv",
            input_file="input.json",
            output_dir="/output_dir",
            overwrite=True,
        )

        mock_language_map.get.assert_called_with("english")

        mock_open_function.assert_called_once_with("r", encoding="utf-8")

    @patch("scribe_data.cli.convert.language_map", autospec=True)
    @patch("scribe_data.cli.convert.Path", autospec=True)
    def test_convert_to_csv_or_json_unknown_language(
        self, mock_path, mock_language_map
    ):
        self.setup_language_map(mock_language_map)

        mock_path_obj = MagicMock(spec=Path)
        mock_path.return_value = mock_path_obj

        mock_path_obj.suffix = ".json"
        mock_path_obj.exists.return_value = True

        mock_json_data = json.dumps({"key1": "value1", "key2": "value2"})
        mock_open_function = mock_open(read_data=mock_json_data)
        mock_path_obj.open = mock_open_function

        with self.assertRaises(ValueError) as context:
            convert_to_csv_or_tsv(
                language="kazatan",
                data_type="nouns",
                output_type="csv",
                input_file="input.json",
                output_dir="/output_dir",
                overwrite=True,
            )

        self.assertEqual(
            str(context.exception), "Language 'Kazatan' is not recognized."
        )

    @patch("scribe_data.cli.convert.language_map", autospec=True)
    @patch("scribe_data.cli.convert.Path", autospec=True)
    def test_convert_to_csv_or_tsv_standarddict_to_csv(
        self, mock_path_class, mock_language_map
    ):
        json_data = '{"a": "1", "b": "2"}'
        expected_csv_output = "preposition,value\n" "a,1\n" "b,2\n"

        mock_file_obj = StringIO(json_data)

        self.setup_language_map(mock_language_map)

        mock_input_file_path = MagicMock(spec=Path)
        mock_input_file_path.suffix = ".json"
        mock_input_file_path.exists.return_value = True
        mock_input_file_path.open.return_value.__enter__.return_value = mock_file_obj
        mock_path_class.side_effect = (
            lambda x: mock_input_file_path if x == "test.json" else Path(x)
        )

        mocked_open = mock_open()

        with patch("pathlib.Path.open", mocked_open), patch(
            "pathlib.Path.mkdir"
        ) as mock_mkdir:
            mock_mkdir.return_value = None

            convert_to_csv_or_tsv(
                language="English",
                data_type="prepositions",
                output_type="csv",
                input_file="test.json",
                output_dir="/output_dir",
                overwrite=True,
            )

        mock_file_handle = mocked_open()
        written_data = "".join(
            call.args[0] for call in mock_file_handle.write.call_args_list
        )

        written_data = self.normalize_line_endings(written_data)
        expected_csv_output = self.normalize_line_endings(expected_csv_output)

        self.assertEqual(written_data, expected_csv_output)

    @patch("scribe_data.cli.convert.language_map", autospec=True)
    @patch("scribe_data.cli.convert.Path", autospec=True)
    def test_convert_to_csv_or_tsv_standarddict_to_tsv(
        self, mock_path_class, mock_language_map
    ):
        json_data = '{"a": "1", "b": "2"}'

        expected_tsv_output = "preposition\tvalue\n" "a\t1\n" "b\t2\n"

        mock_file_obj = StringIO(json_data)

        self.setup_language_map(mock_language_map)

        mock_input_file_path = MagicMock(spec=Path)
        mock_input_file_path.suffix = ".json"
        mock_input_file_path.exists.return_value = True
        mock_input_file_path.open.return_value.__enter__.return_value = mock_file_obj
        mock_path_class.side_effect = (
            lambda x: mock_input_file_path if x == "test.json" else Path(x)
        )

        mocked_open = mock_open()

        with patch("pathlib.Path.open", mocked_open), patch(
            "pathlib.Path.mkdir"
        ) as mock_mkdir:
            mock_mkdir.return_value = None
            convert_to_csv_or_tsv(
                language="English",
                data_type="prepositions",
                output_type="tsv",
                input_file="test.json",
                output_dir="/output_dir",
                overwrite=True,
            )

        mock_file_handle = mocked_open()
        written_data = "".join(
            call.args[0] for call in mock_file_handle.write.call_args_list
        )

        written_data = self.normalize_line_endings(written_data)
        expected_tsv_output = self.normalize_line_endings(expected_tsv_output)

        self.assertEqual(written_data, expected_tsv_output)

    @patch("scribe_data.cli.convert.language_map", autospec=True)
    @patch("scribe_data.cli.convert.Path", autospec=True)
    def test_convert_to_csv_or_tsv_nesteddict_to_csv(
        self, mock_path_class, mock_language_map
    ):
        json_data = (
            '{"a": {"value1": "1", "value2": "x"}, "b": {"value1": "2", "value2": "y"}}'
        )
        expected_csv_output = "noun,value1,value2\n" "a,1,x\n" "b,2,y\n"
        mock_file_obj = StringIO(json_data)

        self.setup_language_map(mock_language_map)

        mock_input_file_path = MagicMock(spec=Path)
        mock_input_file_path.suffix = ".json"
        mock_input_file_path.exists.return_value = True
        mock_input_file_path.open.return_value.__enter__.return_value = mock_file_obj

        mock_path_class.side_effect = (
            lambda x: mock_input_file_path if x == "test.json" else Path(x)
        )

        mocked_open = mock_open()
        with patch("pathlib.Path.open", mocked_open), patch(
            "pathlib.Path.mkdir"
        ) as mock_mkdir:
            mock_mkdir.return_value = None
            convert_to_csv_or_tsv(
                language="English",
                data_type="nouns",
                output_type="csv",
                input_file="test.json",
                output_dir="/output_dir",
                overwrite=True,
            )

        mock_file_handle = mocked_open()
        written_data = "".join(
            call.args[0] for call in mock_file_handle.write.call_args_list
        )

        written_data = self.normalize_line_endings(written_data)
        expected_csv_output = self.normalize_line_endings(expected_csv_output)
        self.assertEqual(written_data, expected_csv_output)

    @patch("scribe_data.cli.convert.language_map", autospec=True)
    @patch("scribe_data.cli.convert.Path", autospec=True)
    def test_convert_to_csv_or_tsv_nesteddict_to_tsv(
        self, mock_path_class, mock_language_map
    ):
        json_data = (
            '{"a": {"value1": "1", "value2": "x"}, "b": {"value1": "2", "value2": "y"}}'
        )
        expected_tsv_output = "noun\tvalue1\tvalue2\n" "a\t1\tx\n" "b\t2\ty\n"

        mock_file_obj = StringIO(json_data)

        self.setup_language_map(mock_language_map)

        mock_input_file_path = MagicMock(spec=Path)
        mock_input_file_path.suffix = ".json"
        mock_input_file_path.exists.return_value = True
        mock_input_file_path.open.return_value.__enter__.return_value = mock_file_obj

        mock_path_class.side_effect = (
            lambda x: mock_input_file_path if x == "test.json" else Path(x)
        )

        mocked_open = mock_open()
        with patch("pathlib.Path.open", mocked_open), patch(
            "pathlib.Path.mkdir"
        ) as mock_mkdir:
            mock_mkdir.return_value = None
            convert_to_csv_or_tsv(
                language="English",
                data_type="nouns",
                output_type="tsv",
                input_file="test.json",
                output_dir="/output_dir",
                overwrite=True,
            )

        mock_file_handle = mocked_open()
        written_data = "".join(
            call.args[0] for call in mock_file_handle.write.call_args_list
        )

        written_data = self.normalize_line_endings(written_data)
        expected_tsv_output = self.normalize_line_endings(expected_tsv_output)

        self.assertEqual(written_data, expected_tsv_output)

    @patch("scribe_data.cli.convert.language_map", autospec=True)
    @patch("scribe_data.cli.convert.Path", autospec=True)
    def test_convert_to_csv_or_tsv_listofdicts_to_csv(
        self, mock_path_class, mock_language_map
    ):
        json_data = '{"a": [{"emoji": "😀", "is_base": true, "rank": 1}, {"emoji": "😅", "is_base": false, "rank": 2}]}'
        expected_csv_output = (
            "word,emoji,is_base,rank\n" "a,😀,True,1\n" "a,😅,False,2\n"
        )
        mock_file_obj = StringIO(json_data)

        self.setup_language_map(mock_language_map)

        mock_input_file_path = MagicMock(spec=Path)
        mock_input_file_path.suffix = ".json"
        mock_input_file_path.exists.return_value = True
        mock_input_file_path.open.return_value.__enter__.return_value = mock_file_obj

        mock_path_class.side_effect = (
            lambda x: mock_input_file_path if x == "test.json" else Path(x)
        )

        mocked_open = mock_open()
        with patch("pathlib.Path.open", mocked_open), patch(
            "pathlib.Path.mkdir"
        ) as mock_mkdir:
            mock_mkdir.return_value = None
            convert_to_csv_or_tsv(
                language="English",
                data_type="emoji-keywords",
                output_type="csv",
                input_file="test.json",
                output_dir="/output_dir",
                overwrite=True,
            )

        mock_file_handle = mocked_open()
        written_data = "".join(
            call.args[0] for call in mock_file_handle.write.call_args_list
        )

        written_data = self.normalize_line_endings(written_data)
        expected_csv_output = self.normalize_line_endings(expected_csv_output)
        self.assertEqual(written_data, expected_csv_output)

    @patch("scribe_data.cli.convert.language_map", autospec=True)
    @patch("scribe_data.cli.convert.Path", autospec=True)
    def test_convert_to_csv_or_tsv_listofdicts_to_tsv(
        self, mock_path_class, mock_language_map
    ):
        json_data = '{"a": [{"emoji": "😀", "is_base": true, "rank": 1}, {"emoji": "😅", "is_base": false, "rank": 2}]}'
        expected_tsv_output = (
            "word\temoji\tis_base\trank\n" "a\t😀\tTrue\t1\n" "a\t😅\tFalse\t2\n"
        )
        mock_file_obj = StringIO(json_data)

        self.setup_language_map(mock_language_map)

        # Mock input file path
        mock_input_file_path = MagicMock(spec=Path)
        mock_input_file_path.suffix = ".json"
        mock_input_file_path.exists.return_value = True
        mock_input_file_path.open.return_value.__enter__.return_value = mock_file_obj

        mock_path_class.side_effect = (
            lambda x: mock_input_file_path if x == "test.json" else Path(x)
        )

        mocked_open = mock_open()
        with patch("pathlib.Path.open", mocked_open), patch(
            "pathlib.Path.mkdir"
        ) as mock_mkdir:
            # Prevent actual directory creation
            mock_mkdir.return_value = None
            convert_to_csv_or_tsv(
                language="English",
                data_type="emoji-keywords",
                output_type="tsv",
                input_file="test.json",
                output_dir="/output_dir",
                overwrite=True,
            )

        mock_file_handle = mocked_open()
        written_data = "".join(
            call.args[0] for call in mock_file_handle.write.call_args_list
        )

        written_data = self.normalize_line_endings(written_data)
        expected_tsv_output = self.normalize_line_endings(expected_tsv_output)
        self.assertEqual(written_data, expected_tsv_output)

    @patch("scribe_data.cli.convert.language_map", autospec=True)
    @patch("scribe_data.cli.convert.Path", autospec=True)
    def test_convert_to_csv_or_tsv_liststrings_to_csv(
        self, mock_path_class, mock_language_map
    ):
        json_data = '{"a": ["x", "y", "z"]}'
        expected_csv_output = (
            "autosuggestion,autosuggestion_1,autosuggestion_2,autosuggestion_3\n"
            "a,x,y,z\n"
        )
        mock_file_obj = StringIO(json_data)

        self.setup_language_map(mock_language_map)

        mock_input_file_path = MagicMock(spec=Path)
        mock_input_file_path.suffix = ".json"
        mock_input_file_path.exists.return_value = True
        mock_input_file_path.open.return_value.__enter__.return_value = mock_file_obj

        mock_path_class.side_effect = (
            lambda x: mock_input_file_path if x == "test.json" else Path(x)
        )

        mocked_open = mock_open()

        with patch("pathlib.Path.open", mocked_open), patch(
            "pathlib.Path.mkdir"
        ) as mock_mkdir:
            mock_mkdir.return_value = None
            convert_to_csv_or_tsv(
                language="English",
                data_type="autosuggestions",
                output_type="csv",
                input_file="test.json",
                output_dir="/output_dir",
                overwrite=True,
            )

        mock_file_handle = mocked_open()
        written_data = "".join(
            call.args[0] for call in mock_file_handle.write.call_args_list
        )

        written_data = self.normalize_line_endings(written_data)
        expected_csv_output = self.normalize_line_endings(expected_csv_output)
        self.assertEqual(written_data, expected_csv_output)

    @patch("scribe_data.cli.convert.language_map", autospec=True)
    @patch("scribe_data.cli.convert.Path", autospec=True)
    def test_convert_to_csv_or_tsv_liststrings_to_tsv(
        self, mock_path_class, mock_language_map
    ):
        json_data = '{"a": ["x", "y", "z"]}'
        expected_tsv_output = (
            "autosuggestion\tautosuggestion_1\tautosuggestion_2\tautosuggestion_3\n"
            "a\tx\ty\tz\n"
        )
        mock_file_obj = StringIO(json_data)

        self.setup_language_map(mock_language_map)

        mock_input_file_path = MagicMock(spec=Path)
        mock_input_file_path.suffix = ".json"
        mock_input_file_path.exists.return_value = True
        mock_input_file_path.open.return_value.__enter__.return_value = mock_file_obj

        mock_path_class.side_effect = (
            lambda x: mock_input_file_path if x == "test.json" else Path(x)
        )

        mocked_open = mock_open()

        with patch("pathlib.Path.open", mocked_open), patch(
            "pathlib.Path.mkdir"
        ) as mock_mkdir:
            mock_mkdir.return_value = None
            convert_to_csv_or_tsv(
                language="English",
                data_type="autosuggestions",
                output_type="tsv",
                input_file="test.json",
                output_dir="/output_dir",
                overwrite=True,
            )

        mock_file_handle = mocked_open()
        written_data = "".join(
            call.args[0] for call in mock_file_handle.write.call_args_list
        )
        written_data = self.normalize_line_endings(written_data)
        expected_tsv_output = self.normalize_line_endings(expected_tsv_output)
        self.assertEqual(written_data, expected_tsv_output)

    # MARK: SQLITE Tests

    @patch("scribe_data.cli.convert.Path")
    @patch("scribe_data.cli.convert.data_to_sqlite")
    @patch("shutil.copy")
    def test_convert_to_sqlite(self, mock_shutil_copy, mock_data_to_sqlite, mock_path):
        mock_path.return_value.exists.return_value = True

        convert_to_sqlite(
            language="english",
            data_type="nouns",
            input_file="file",
            output_type="sqlite",
            output_dir="/output",
            overwrite=True,
        )

        mock_data_to_sqlite.assert_called_with(["english"], ["nouns"])
        mock_shutil_copy.assert_called()

    @patch("scribe_data.cli.convert.Path")
    @patch("scribe_data.cli.convert.data_to_sqlite")
    def test_convert_to_sqlite_no_output_dir(self, mock_data_to_sqlite, mock_path):
        # Create a mock for input file
        mock_input_file = MagicMock()
        mock_input_file.exists.return_value = True

        mock_path.return_value = mock_input_file

        # source and destination paths
        mock_input_file.parent = MagicMock()
        mock_input_file.parent.__truediv__.return_value = MagicMock()
        mock_input_file.parent.__truediv__.return_value.exists.return_value = False

        convert_to_sqlite(
            language="english",
            data_type="nouns",
            input_file=mock_input_file,
            output_type="sqlite",
            output_dir=None,
            overwrite=True,
        )

        mock_data_to_sqlite.assert_called_with(["english"], ["nouns"])

    @patch("scribe_data.cli.convert.Path")
    @patch("scribe_data.cli.convert.data_to_sqlite")
    @patch("scribe_data.cli.convert.get_language_iso")
    @patch("shutil.copy")
    def test_convert_to_sqlite_with_language_iso(
        self, mock_copy, mock_get_language_iso, mock_data_to_sqlite, mock_path
    ):
        mock_get_language_iso.return_value = "en"
        mock_path.return_value.exists.return_value = True

        convert_to_sqlite(
            language="English",
            data_type="data_type",
            input_file="file",
            output_type="sqlite",
            output_dir="/output",
            overwrite=True,
        )

        mock_data_to_sqlite.assert_called_with(["English"], ["data_type"])
        mock_copy.assert_called()

    def test_convert_to_sqlite_no_language(self):
        with self.assertRaises(ValueError):
            convert_to_sqlite(
                language=None,
                data_type="data_type",
                output_type="sqlite",
                output_dir="/output",
                overwrite=True,
            )
