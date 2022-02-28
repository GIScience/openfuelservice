import logging
import shutil
import tempfile
import time
from os.path import basename
from pathlib import Path
from typing import Dict, List, Union

from app.misc import file_management

logger = logging.getLogger(__name__)


class BaseReader:
    def __init__(self, file_or_url: Union[str, Path, None] = None) -> None:
        self._tempfolder: Path = Path(tempfile.mkdtemp())
        self.objects_list: List = []
        self.objects_ordered: Dict = {}
        self._file_or_url: Union[Path, str, None] = file_or_url
        self.name = "BaseReader"

    def _download_data(self, file_to_read: Union[Path, str, None]) -> Union[Path, None]:
        if file_to_read is None:
            return None
        return file_management.download_file_with_name(
            url_or_path=file_to_read,
            file_name=basename(file_to_read),
            output_folder=self._tempfolder,
        )

    def _process_data(self, data_file: Union[Path, None]) -> None:  # noqa
        logger.error("Base Reader process_data not defined. Override with a subclass.")

    def fetch_and_process_data(self) -> None:
        start_time: float = time.time()
        logger.info(f"Crawl Latest {self.__class__} Data Objects")
        data_file: Union[Path, None] = self._download_data(self._file_or_url)
        self._process_data(data_file=data_file)
        end_time: float = time.time()
        logger.info(
            f"Crawl-Result: {self.objects_list} {self.__class__} Data Objects | {end_time - start_time} Seconds"
        )

    def close(self) -> None:
        shutil.rmtree(self._tempfolder)
