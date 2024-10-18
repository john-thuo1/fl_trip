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
from unittest.mock import MagicMock, mock_open, patch


from scribe_data.cli.convert import (
    convert_to_sqlite,
    convert_to_json,
)


class TestConvert(unittest.TestCase):

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


    @patch('scribe_data.cli.convert.language_map', autospec=True)  
    @patch('scribe_data.cli.convert.Path', autospec=True)
    def test_convert_to_json_normalized_language(self, mock_path, mock_language_map):
        mock_language_map.get.side_effect = lambda lang:  {
            'english': {'language': 'english', 'iso': 'en', 'qid': 'Q1860', 'remove-words': ['of', 'the', 'The', 'and'], 'ignore-words': []},        
            'french': {'language': 'french', 'iso': 'fr', 'qid': 'Q150', 'remove-words': ['of', 'the', 'The', 'and'], 'ignore-words': ['XXe']}       
        }.get(lang.lower())  

        # Mocking Path object behavior
        mock_path_obj = MagicMock(spec=Path)
        mock_path.return_value = mock_path_obj

        # Set the file extension to .csv/ .tsv
        mock_path_obj.suffix = ".csv"
        mock_path_obj.exists.return_value = True


        # Call the function with 'English'
        convert_to_json(
            language='English',
            data_type="nouns",
            output_type="json",
            input_file="input.csv",
            output_dir="/output_dir",
            overwrite=True,
        )

        # Verify that the mock's get method was called with 'english' (lowercased by the function)
        mock_language_map.get.assert_called_with('english')


    @patch('scribe_data.cli.convert.language_map', autospec=True)  
    @patch('scribe_data.cli.convert.Path', autospec=True)
    def test_convert_to_json_unknown_language(self, mock_path, mock_language_map):
        mock_language_map.get.return_value = None  

     # Mock for input file and output_directory
        mock_input_file_path = MagicMock(spec=Path)
        mock_input_file_path.exists.return_value = True
        mock_path.side_effect = [mock_input_file_path, MagicMock(spec=Path)] 


        with self.assertRaises(ValueError) as context:
            convert_to_json(
                language='kazatan', 
                data_type="nouns",
                output_type="json",
                input_file="test.csv", 
                output_dir="/output_dir", 
                overwrite=True,
            )

        # Assert the error message
        self.assertEqual(str(context.exception), "Language 'Kazatan' is not recognized.")

    @patch("scribe_data.cli.convert.Path")
    def test_convert_to_json_with_input_file(self, mock_path):
        # Sample Data 
        csv_data = "key,value\na,1\nb,2"
        mock_file = StringIO(csv_data)

        mock_path_obj = MagicMock(spec=Path)
        mock_path.return_value = mock_path_obj
        mock_path_obj.suffix = ".csv"
        mock_path_obj.exists.return_value = True
        mock_path_obj.open.return_value.__enter__.return_value = mock_file

        convert_to_json(
            language='English',
            data_type="nouns",
            output_type="json",
            input_file="test.csv", 
            output_dir="/output_dir",
            overwrite=True,
        )

        mock_path_obj.exists.assert_called_once()

        # Verify the file was opened for reading
        mock_path_obj.open.assert_called_once_with("r", encoding="utf-8")

    @patch("scribe_data.cli.convert.Path")
    def test_convert_to_json_no_input_file(self, mock_path):
        mock_path_obj = MagicMock(spec=Path)
        mock_path.return_value = mock_path_obj
        mock_path_obj.exists.return_value = False  

        mock_path_obj.__str__.return_value = "Data/ecode.csv"

        with self.assertRaises(FileNotFoundError) as context:
            convert_to_json(
                language='English',
                data_type="nouns",
                output_type="json",
                input_file="Data/ecode.csv",  
                output_dir="/output_dir",
                overwrite=True,
            )

        self.assertEqual(str(context.exception), "No data found for input file 'Data/ecode.csv'.")

        mock_path_obj.exists.assert_called_once()


    @patch("scribe_data.cli.convert.Path")
    def test_convert_to_json_supported_file_extension_csv(self, mock_path):
        mock_path_obj = MagicMock(spec=Path)
        mock_path.return_value = mock_path_obj

        mock_path_obj.suffix = ".csv"
        mock_path_obj.exists.return_value = True

        convert_to_json(
            language='English',
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
            language='English',
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
                language='English',
                data_type="nouns",
                output_type="json",
                input_file="test.txt",  
                output_dir="/output_dir",
                overwrite=True,
            )
        
        self.assertIn("Unsupported file extension", str(context.exception))
        self.assertEqual(str(context.exception), "Unsupported file extension '.txt' for test.txt. Please provide a '.csv' or '.tsv' file.")
#---------------------------------------------------------------------------------------------------------------------------------------------------------
    @patch("scribe_data.cli.convert.Path", autospec=True)
    @patch("builtins.open", new_callable=mock_open)
    @patch("scribe_data.cli.convert.language_map", return_value={'english': {'language': 'english'}}, autospec=True)
    def test_convert_standard_csv(self, mock_language_map, mock_file, mock_path):
        # CSV and expected JSON
        csv_data = "key,value\na,1\nb,2"
        expected_json = {"a": "1", "b": "2"}
        mock_file_obj = StringIO(csv_data)

        # Mocking Path object behavior
        mock_path_obj = MagicMock(spec=Path)
        mock_path.return_value = mock_path_obj
        mock_path_obj.suffix = ".csv"
        mock_path_obj.exists.return_value = True
        mock_path_obj.open.return_value.__enter__.return_value = mock_file_obj
        mock_path_obj.mkdir.return_value = None  

        # Simulate path concatenation behavior (mock output directory)
        mock_output_file = "mocked_output_dir/English/nouns.json"
        mock_path_obj.__truediv__.return_value = Path(mock_output_file)

        # Call the function with the mocked directory
        convert_to_json(
            language='English',
            data_type="nouns",
            output_type="json",
            input_file="test.csv",
            output_dir="mocked_output_dir", 
            overwrite=True,
        )

        # Assert that the correct JSON data is being written to the mocked file
        mock_file.assert_called_once_with(mock_output_file, "w", encoding="utf-8")
        handle = mock_file()
        written_data = handle.write.call_args[0][0]  
        assert json.loads(written_data) == expected_json






    # @patch("scribe_data.cli.convert.Path")
    # @patch("builtins.open", new_callable=mock_open)
    # @patch("scribe_data.cli.convert.language_map", return_value={'english': {'language': 'english'}})
    # def test_convert_csv_with_multiple_fields(self, mock_language_map, mock_file, mock_path):
    #     csv_data = "key,value1,value2\nitem1,10,20\nitem2,30,40"
    #     expected_json = {
    #         "item1": {"value1": "10", "value2": "20"},
    #         "item2": {"value1": "30", "value2": "40"}
    #     }
    #     mock_file_obj = StringIO(csv_data)

    #     # Mocking Path object behavior
    #     mock_path_obj = MagicMock(spec=Path)
    #     mock_path.return_value = mock_path_obj
    #     mock_path_obj.suffix = ".csv"
    #     mock_path_obj.exists.return_value = True
    #     mock_path_obj.open.return_value.__enter__.return_value = mock_file_obj

    #     # Call the function
    #     convert_to_json(
    #         language='English',
    #         data_type="nouns",
    #         output_type="json",
    #         input_file="test.csv",
    #         output_dir="/output_dir",
    #         overwrite=True,
    #     )

    #     # Assert that the correct JSON data is being written
    #     mock_file.assert_called_once_with("/output_dir/English/nouns.json", "w", encoding="utf-8")
    #     handle = mock_file()
    #     written_data = handle.write.call_args[0][0]
    #     self.assertEqual(json.loads(written_data), expected_json)

    # @patch("scribe_data.cli.convert.Path")
    # @patch("builtins.open", new_callable=mock_open)
    # @patch("scribe_data.cli.convert.language_map", return_value={'english': {'language': 'english'}})
    # def test_convert_empty_csv(self, mock_language_map, mock_file, mock_path):
    #     csv_data = ""
    #     expected_json = {}  # Expecting an empty dictionary for empty CSV
    #     mock_file_obj = StringIO(csv_data)

    #     # Mocking Path object behavior
    #     mock_path_obj = MagicMock(spec=Path)
    #     mock_path.return_value = mock_path_obj
    #     mock_path_obj.suffix = ".csv"
    #     mock_path_obj.exists.return_value = True
    #     mock_path_obj.open.return_value.__enter__.return_value = mock_file_obj

    #     # Call the function
    #     convert_to_json(
    #         language='English',
    #         data_type="nouns",
    #         output_type="json",
    #         input_file="test.csv",
    #         output_dir="/output_dir",
    #         overwrite=True,
    #     )

    #     # Assert that the correct JSON data is being written
    #     mock_file.assert_called_once_with("/output_dir/English/nouns.json", "w", encoding="utf-8")
    #     handle = mock_file()
    #     written_data = handle.write.call_args[0][0]
    #     self.assertEqual(json.loads(written_data), expected_json)

    # @patch("scribe_data.cli.convert.Path")
    # @patch("builtins.open", new_callable=mock_open)
    # @patch("scribe_data.cli.convert.language_map", return_value={'english': {'language': 'english'}})
    # def test_convert_malformed_csv(self, mock_language_map, mock_file, mock_path):
    #     csv_data = "key,value\n1,2\n3"  # Missing value for key 3
    #     mock_file_obj = StringIO(csv_data)

    #     # Mocking Path object behavior
    #     mock_path_obj = MagicMock(spec=Path)
    #     mock_path.return_value = mock_path_obj
    #     mock_path_obj.suffix = ".csv"
    #     mock_path_obj.exists.return_value = True
    #     mock_path_obj.open.return_value.__enter__.return_value = mock_file_obj

    #     with self.assertRaises(Exception):  # Adjust to a specific exception if you know it
    #         convert_to_json(
    #             language='English',
    #             data_type="nouns",
    #             output_type="json",
    #             input_file="test.csv",
    #             output_dir="/output_dir",
    #             overwrite=True,
    #         )
