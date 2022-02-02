import concurrent
import logging
from concurrent.futures import Future, ThreadPoolExecutor
from threading import local
from typing import List, Union

import requests
from requests import Response
from tqdm import tqdm

from app.core.config import settings

logger = logging.getLogger(__name__)


def initialize_session(session: requests.Session) -> requests.Session:
    """Helper Function to initialize threaded and non-threaded sessions. """
    session.headers.update(settings.GLOBAL_HEADERS)
    return session


class ThreadedRequests:
    def __init__(self) -> None:
        self.thread_local: local = local()

    def _download_link(self, url: str) -> Response:
        if not hasattr(self.thread_local, "session"):
            session = requests.Session()
            session = initialize_session(session)
            self.thread_local.session = session
        else:
            session = self.thread_local.session

        with session.get(url) as response:
            return response

    def get_urls_threaded(
        self,
        urls: list,
        workers: Union[int, None] = None,
        description: str = " Downloading URLs",
        download_unit: str = " URLs",
    ) -> List:
        results: List = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            with tqdm(
                total=len(urls), desc=description, unit=download_unit
            ) as progress:
                futures: List = []
                for url in urls:
                    future: Future[Response] = executor.submit(self._download_link, url)
                    future.add_done_callback(lambda p: progress.update())
                    futures.append(future)
                for future in concurrent.futures.as_completed(futures):
                    try:
                        results.append(future.result())
                    except Exception as exc:
                        logger.warning(f"{future} generated an exception: {exc}")
        return results
