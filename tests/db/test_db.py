import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from dapi.db import DSDatabase


class MockRowProxy:
    def __init__(self, row_data, column_names):
        self._row_data = row_data
        self._column_names = column_names

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._row_data[key]
        elif isinstance(key, str):
            return self._row_data[self._column_names.index(key)]


class TestDSDatabase(unittest.TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.db = DSDatabase(dbname="ngl")
        self.db.engine.connect = MagicMock(return_value=self.mock_connection)

    @patch.dict(
        "os.environ", {"NGL_DB_USER": "ngl_user", "NGL_DB_PASSWORD": "ngl_pass"}
    )
    def test_init_with_valid_dbname_ngl(self):
        db = DSDatabase(dbname="ngl")
        self.assertEqual(db.user, "ngl_user")
        self.assertEqual(db.password, "ngl_pass")
        self.assertEqual(db.db, "sjbrande_ngl_db")

    @patch.dict("os.environ", {"VP_DB_USER": "vp_user", "VP_DB_PASSWORD": "vp_pass"})
    def test_init_with_valid_dbname_vp(self):
        db = DSDatabase(dbname="vp")
        self.assertEqual(db.user, "vp_user")
        self.assertEqual(db.password, "vp_pass")
        self.assertEqual(db.db, "sjbrande_vpdb")

    @patch.dict("os.environ", {"EQ_DB_USER": "eq_user", "EQ_DB_PASSWORD": "eq_pass"})
    def test_init_with_valid_dbname_eq(self):
        db = DSDatabase(dbname="eq")
        self.assertEqual(db.user, "eq_user")
        self.assertEqual(db.password, "eq_pass")
        self.assertEqual(db.db, "post_earthquake_recovery")

    def test_init_with_invalid_dbname(self):
        with self.assertRaises(ValueError):
            DSDatabase(dbname="invalid")

    @patch("pandas.read_sql_query")
    def test_read_sql_returns_dataframe(self, mock_read_sql_query):
        sql = "SELECT * FROM table"
        mock_df = pd.DataFrame([{"id": 1, "name": "Test"}])
        mock_read_sql_query.return_value = mock_df
        result = self.db.read_sql(sql)
        self.assertIsInstance(result, pd.DataFrame)
        pd.testing.assert_frame_equal(result, mock_df)


if __name__ == "__main__":
    unittest.main()
