import csv
import logging
import time
from enum import Enum
from pathlib import Path
from typing import List

from app.db.importer.base_reader import BaseReader
from app.db.importer.carfueldata.cfd_objects import CFDImportCar
from app.db.importer.mappings import CFDHeaderMapping
from app.misc import file_management
from app.misc.data_handling import check_manufacturer

logger = logging.getLogger(__name__)


class CarFuelDataReader(BaseReader):
    def __init__(self) -> None:
        super().__init__()
        self.cfd_objects_list: List = []

    def _process_data(self, zip_file: Path) -> None:
        files: list = file_management.unzip_download(
            zip_file_path=zip_file, destination_folder=self.tempfolder
        )
        for cs_file in files:
            if cs_file.rsplit(".", 1)[-1] == "csv":
                with open(cs_file, encoding="cp1252") as f:
                    reader = csv.reader(f, dialect="excel")
                    header_row = reader.__next__()
                    headers: dict = {}
                    counter = 0
                    for h in header_row:
                        mapping = CFDHeaderMapping.from_value(h)
                        if mapping is not None:
                            headers[mapping] = counter
                        counter += 1
                    for row in reader:
                        manufacturer = row[headers[CFDHeaderMapping.MANUFACTURER]]
                        real_manufacturer = check_manufacturer(
                            manufacturer_to_check=manufacturer
                        )
                        if not real_manufacturer or not len(real_manufacturer):
                            continue
                        cfd_object = CFDImportCar()
                        setattr(
                            cfd_object,
                            CFDHeaderMapping.MANUFACTURER.name.lower(),
                            real_manufacturer,
                        )
                        key: Enum
                        value: int
                        for key, value in headers.items():
                            setattr(cfd_object, key.value.casefold(), row[value])
                        self.cfd_objects_list.append(cfd_object)

    def _fetch_data(self) -> None:
        # Todo reanable after development
        # data_file = file_management.download_file_with_name(
        #     url=settings.CARFUELDATA_URL,
        #     file_name="latest_cfd_data.zip",
        #     output_folder=self.tempfolder,
        # )
        data_file = Path(
            "/home/jules/workspace/HeiGIT/openfuelservice/backend/files/Euro_6_latest_22-12-2021.zip"
        )
        self._process_data(zip_file=data_file)

    def fetch_data(self) -> None:
        start_time: float = time.time()
        print("Crawl Latest Car Fuel Data Objects")
        self._fetch_data()
        end_time: float = time.time()
        logger.info(
            f"Crawl-Result: {self.cfd_objects_list.__sizeof__()} Car Fuel Data Objects | {end_time - start_time} Seconds"
        )
