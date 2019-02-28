import logging

from openfuelservice.server import create_app

app = create_app()
client = app.test_client()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
