import requests
from requests import Session

from app.misc.requests_tools import initialize_session

requestsSession: Session = requests.Session()
requestsSession = initialize_session(requestsSession)
