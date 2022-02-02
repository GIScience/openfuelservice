import json
import logging
from copy import deepcopy

import requests
import responses
from requests import Response
from responses import GET

from app.core.config import settings
from app.misc.requests_tools import ThreadedRequests, initialize_session

logger = logging.getLogger(__name__)


def test_initialize_session() -> None:
    session: requests.Session = requests.Session()
    headers_copy = deepcopy(session.headers)
    assert headers_copy == session.headers
    assert not session.headers.get("From")
    session = initialize_session(session)
    assert session != headers_copy
    assert session.headers.get("User-Agent") == settings.GLOBAL_HEADERS.get(
        "User-Agent"
    )
    assert session.headers.get("From") == settings.GLOBAL_HEADERS.get("From")


def test_threaded_requests(envirocar_mocked_responses: responses.RequestsMock) -> None:
    with open(settings.TEST_ENVIROCAR_TRACKS_RESPONSE) as f:
        tracks_response = json.load(f)
    urls_to_download = [
        "https://test.com/tracks/?limit=10&page=1",
        "https://test.com/tracks/?limit=10&page=2",
        "https://test.com/tracks/?limit=10&page=3",
        "https://test.com/tracks/?limit=10&page=4",
    ]
    for url in urls_to_download:
        envirocar_mocked_responses.add(
            method=GET,
            url=url,
            json=tracks_response,
            status=200,
            content_type="application/json",
        )

    threaded_requests = ThreadedRequests()
    responses = threaded_requests.get_urls_threaded(urls=urls_to_download, workers=4)
    response: Response
    for response in responses:
        assert response.ok
        assert response.status_code == 200
        assert response.json() == tracks_response
