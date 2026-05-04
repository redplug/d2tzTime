import unittest
from unittest.mock import patch, Mock

from api.client import fetch_terror_zone


class TestClient(unittest.TestCase):
    def test_fetch_without_token_returns_error(self):
        result = fetch_terror_zone("")
        self.assertIsNotNone(result.error)

    @patch("api.client.requests.get")
    def test_fetch_list_response_parses_current_and_next(self, mock_get):
        mock_resp = Mock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = [
            {"time": 0, "end_time": 9999999999, "zone_name": ["Dark Wood"]},
            {"time": 9999999999, "end_time": 99999999999, "zone_name": ["Black Marsh"]},
        ]
        mock_get.return_value = mock_resp

        result = fetch_terror_zone("token")

        self.assertEqual(result.current_zone, "Dark Wood")
        self.assertEqual(result.next_zone, "Black Marsh")
        self.assertEqual(result.source, "d2tz")


if __name__ == "__main__":
    unittest.main()
