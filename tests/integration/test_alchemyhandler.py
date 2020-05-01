from networkx import Graph
from sqlalchemy import MetaData
from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import OperationalError
from pathlib import Path
from pdm_utils.functions import querying
from pdm_utils.classes.alchemyhandler import AlchemyHandler
from unittest.mock import patch, Mock, PropertyMock
import sys
import unittest

# Import helper functions to build mock database
unittest_file = Path(__file__)
test_dir = unittest_file.parent.parent
if str(test_dir) not in set(sys.path):
    sys.path.append(str(test_dir))
import test_db_utils

# pdm_anon, pdm_anon, and pdm_test_db
user = test_db_utils.USER
pwd = test_db_utils.PWD
db = test_db_utils.DB

class TestAlchemyHandler(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        test_db_utils.create_filled_test_db()

    def setUp(self):
        self.alchemist = AlchemyHandler()

    def test_validate_database_1(self):
        """Verify validate_database() detects good database access.
        """
        self.alchemist.username = user
        self.alchemist.password = pwd
        self.alchemist.build_engine()

        self.alchemist.database = db
        self.alchemist.validate_database()

    def test_validate_database_2(self):
        """Verify validate_database() detects bad database access.
        """
        self.alchemist.username = user
        self.alchemist.password = pwd
        self.alchemist.build_engine()

        self.alchemist.database = "not_database"
        with self.assertRaises(ValueError):
            self.alchemist.validate_database()

    def test_build_engine_1(self):
        """Verify build_engine() creates and stores Engine object.
        """
        self.alchemist.username = user
        self.alchemist.password = pwd
        self.alchemist.build_engine()

        self.assertTrue(isinstance(self.alchemist.engine, Engine))
        self.assertTrue(self.alchemist.connected)

    def test_build_engine_2(self):
        """Verify build_engine() connects to database if has_database.
        """
        self.alchemist.username = user
        self.alchemist.password = pwd
        self.alchemist.database = db

        self.alchemist.build_engine()

        self.assertTrue(self.alchemist.connected_database)

    def connect_to_pdm_test_db(self):
        """Sets alchemist credentials and database to connect to pdm_test_db.
        """
        self.alchemist.username = user
        self.alchemist.password = pwd
        self.alchemist.database = db
        self.alchemist.build_graph()

    def test_build_metadata_1(self):
        """Verify build_metadata() creates and stores MetaData and Engine.
        """
        self.connect_to_pdm_test_db()

        self.assertTrue(isinstance(self.alchemist.metadata, MetaData))
        self.assertTrue(isinstance(self.alchemist.engine, Engine))

    def test_build_graph_1(self):
        """Verify build_graph() creates and stores, Graph, MetaData, and Engine.
        """
        self.connect_to_pdm_test_db()

        self.assertTrue(isinstance(self.alchemist.graph, Graph))
        self.assertTrue(isinstance(self.alchemist.metadata, MetaData))
        self.assertTrue(isinstance(self.alchemist.engine, Engine))

    def test_execute_1(self):
        """Verify execute() returns values in expected data types.
        """
        self.connect_to_pdm_test_db()

        PhageID = querying.get_column(self.alchemist.metadata, "phage.PhageID")
        query = querying.build_select(self.alchemist.graph, PhageID)

        results = self.alchemist.execute(query)

        self.assertTrue(isinstance(results, list))
        for result in results:
            self.assertTrue(isinstance(result, dict))

    def test_execute_2(self):
        """Verify execute() returns expected values in dictionaries.
        """
        self.connect_to_pdm_test_db()

        PhageID = querying.get_column(self.alchemist.metadata, "phage.PhageID")
        query = querying.build_select(self.alchemist.graph, PhageID)

        results = self.alchemist.execute(query)

        values = []
        for result in results:
            with self.subTest(result_dict=result):
                self.assertTrue("PhageID" in result.keys())
                values.append(result["PhageID"])

        self.assertTrue("Trixie" in values)
        self.assertTrue("D29" in values)
        self.assertTrue("Myrna" in values)
        self.assertTrue("Alice" in values)

    def test_execute_3(self):
        """Verify execute() returns expected values in tuples.
        """
        self.connect_to_pdm_test_db()

        PhageID = querying.get_column(self.alchemist.metadata, "phage.PhageID")
        query = querying.build_select(self.alchemist.graph, PhageID)

        results = self.alchemist.execute(query, return_dict=False)

        values = []
        for result in results:
            with self.subTest(result_tuple=result):
                self.assertTrue(len(result) == 1)
                values.append(result[0])

        self.assertTrue("Trixie" in values)
        self.assertTrue("D29" in values)
        self.assertTrue("Myrna" in values)
        self.assertTrue("Alice" in values)

    def test_scalar_1(self):
        """Verify scalar() returns expected value.
        """
        self.connect_to_pdm_test_db()

        PhageID = querying.get_column(self.alchemist.metadata, "phage.PhageID")
        query = querying.build_select(self.alchemist.graph, PhageID)

        value = self.alchemist.scalar(query)

        self.assertEqual(value, "Alice")

    def test_first_column_1(self):
        """Verify first_column() returns expected value.
        """
        self.connect_to_pdm_test_db()

        PhageID = querying.get_column(self.alchemist.metadata, "phage.PhageID")
        query = querying.build_distinct(self.alchemist.graph, PhageID)

        values = self.alchemist.first_column(query)

        self.assertTrue("Trixie" in values)
        self.assertTrue("D29" in values)
        self.assertTrue("Myrna" in values)
        self.assertTrue("Alice" in values)

    @classmethod
    def tearDownClass(self):
        test_db_utils.remove_db()

if __name__ == "__main__":
    unittest.main()