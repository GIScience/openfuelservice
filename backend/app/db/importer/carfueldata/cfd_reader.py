import csv
import logging
from pathlib import Path
from typing import List, Union

from app.db.importer.base_reader import BaseReader
from app.db.importer.mappings import CFDHeaderMapping
from app.misc import file_management
from app.misc.data_handling import check_manufacturer
from app.models import CarFuelDataCar

logger = logging.getLogger(__name__)


class CarFuelDataReader(BaseReader):
    def __init__(self, file_to_read: Union[str, Path]) -> None:
        super().__init__(file_to_read)

    def _process_data(self, data_file: Path) -> None:
        files: list = file_management.unzip_download(
            zip_file_path=data_file, destination_folder=self._tempfolder
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
                        else:
                            logger.warning(
                                f"Found Column name in CarFuelData dataset not known: {h}"
                            )
                        counter += 1
                    row: List[str]
                    for row in reader:
                        manufacturer: str = row[headers[CFDHeaderMapping.MANUFACTURER]]
                        real_manufacturer: Union[str, None] = check_manufacturer(
                            manufacturer_to_check=manufacturer
                        )
                        if not real_manufacturer or not len(real_manufacturer):
                            continue
                        row[headers[CFDHeaderMapping.MANUFACTURER]] = real_manufacturer
                        cfd_object = CarFuelDataCar()
                        cfd_object.set_data(data=row, headers=headers)
                        self.objects_list.append(cfd_object)
