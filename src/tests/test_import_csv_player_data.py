import unittest
from unittest.mock import patch, mock_open
from io import StringIO

from ..app.Player import import_csv_player_data


class TestImportCSVPlayerData(unittest.TestCase):
    @patch('builtins.open', new_callable=mock_open, read_data="first_name,last_name,sport,team,position\nJohn,Doe,Basketball,Lakers,Forward\nJane,Smith,Soccer,United,Midfielder")
    @patch('..orm.Player')
    def test_import_csv_player_data(self, mock_player, mock_file):
        # Mock the Player class and its save method
        mock_player_instance = mock_player.return_value
        mock_player_instance.save.return_value = True

        # Call the function with the mock file data
        file_data = StringIO("first_name,last_name,sport,team,position\nJohn,Doe,Basketball,Lakers,Forward\nJane,Smith,Soccer,United,Midfielder")
        result = import_csv_player_data(file_data)

        # Check if the save method was called twice (once for each player)
        self.assertEqual(mock_player_instance.save.call_count, 2)

        # Check if the data was correctly passed to the Player instance
        calls = [
            unittest.mock.call({"first_name": "John", "last_name": "Doe", "sport": "Basketball", "team": "Lakers", "position": "Forward"}),
            unittest.mock.call({"first_name": "Jane", "last_name": "Smith", "sport": "Soccer", "team": "United", "position": "Midfielder"})
        ]
        mock_player.assert_has_calls(calls, any_order=True)

if __name__ == '__main__':
    unittest.main()