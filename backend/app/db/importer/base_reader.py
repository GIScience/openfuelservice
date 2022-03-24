import logging
import tempfile
import time
from asyncio import Event
from os.path import basename
from pathlib import Path
from typing import Dict, List, Union

from sqlalchemy.orm import Session

from app.db.importer.base_importer import BaseImporter
from app.misc import file_management

logger = logging.getLogger(__name__)


class BaseReader:
    def __init__(self, db: Session, file_or_url: Union[str, Path, None] = None) -> None:
        self._tempfolder: Path = Path(tempfile.mkdtemp())
        self.objects_list: List = []
        # Todo make getter and setter for every input
        self.objects_ordered: Dict = {}
        self._file_or_url: Union[Path, str, None] = file_or_url
        self.name: str = "BaseReader"
        self._db: Session = db

    def _download_data(self, file_to_read: Union[Path, str, None]) -> Union[Path, None]:
        if file_to_read is None:
            return None
        return file_management.download_file_with_name(
            url_or_path=file_to_read,
            file_name=basename(file_to_read),
            output_folder=self._tempfolder,
        )

    async def _process_data(self, data_file: Union[Path, None]) -> None:  # noqa
        logger.error("Base Reader process_data not defined. Override with a subclass.")

    async def fetch_process_and_import_data(
        self,
        import_data: bool,
        event_to_wait: Union[Event, None] = None,
        event_to_set: Union[Event, None] = None,
    ) -> None:
        if event_to_wait is not None and isinstance(event_to_wait, Event):
            await event_to_wait.wait()
        start_time: float = time.time()
        logger.info(f"Crawl Latest {self.__class__} Data Objects")
        data_file: Union[Path, None] = self._download_data(self._file_or_url)
        await self._process_data(data_file=data_file)
        if import_data:
            if len(self.objects_list) > 0:
                BaseImporter(db=self._db).import_data(db_objects=self.objects_list)
            if len(self.objects_ordered) > 0:
                BaseImporter(db=self._db).import_data_ordered(
                    db_objects_ordered=self.objects_ordered
                )
        end_time: float = time.time()
        if event_to_set is not None and isinstance(event_to_set, Event):
            event_to_set.set()
        logger.info(
            f"Crawl-Result: {self.objects_list} {self.__class__} Data Objects | {end_time - start_time} Seconds"
        )
