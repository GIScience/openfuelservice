# Deactivated for now!
# TODO find a good way to implement db access rights without destroying the db data that is already there!
import os

from openfuelservice.server import create_app
from openfuelservice.server.utils.database.database_tools import database
from openfuelservice.tests import logger

def clean_db(db):
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())


class BaseTestCase:
    db = None

    @classmethod
    def setUpClass(cls):
        if os.environ == 'TESTING':
            super(BaseTestCase, cls).setUpClass()
            cls.app = create_app()
            cls.db = database.db
            cls.db.app = cls.app
            cls.db.create_all()
        else:
            logger.log("Testing not in os.environ Skipping Database tests.")

    @classmethod
    def tearDownClass(cls):
        if os.environ == 'TESTING':
            cls.db.drop_all()
            super(BaseTestCase, cls).tearDownClass()
        else:
            logger.log("Testing not in os.environ Skipping Database tests.")

    def setUp(self):
        if os.environ == 'TESTING':
            super(BaseTestCase, self).setUp()

            self.client = self.app.test_client()
            self.app_context = self.app.app_context()
            self.app_context.push()
            clean_db(self.db)
        else:
            logger.log("Testing not in os.environ Skipping Database tests.")

    def tearDown(self):
        if os.environ == 'TESTING':
            self.db.session.rollback()
            self.app_context.pop()

            super(BaseTestCase, self).tearDown()
        else:
            logger.log("Testing not in os.environ Skipping Database tests.")
