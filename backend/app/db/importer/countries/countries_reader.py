import csv
import io
import logging
from pathlib import Path
from typing import Dict, List, Union

import shapefile
from shapely.geometry import MultiPolygon, shape

from app.db.importer.base_reader import BaseReader
from app.db.importer.mappings import CountriesMapping
from app.misc import file_management
from app.models import CountryData

logger = logging.getLogger(__name__)


class CountryCodesReader(BaseReader):
    def enrich_with_geometries(self, country_geometry_file: Union[Path, str]) -> None:
        geometry_file = self._download_data(country_geometry_file)
        files: List = file_management.unzip_download(
            zip_file_path=geometry_file, destination_folder=self._tempfolder
        )
        dbfname: Path = Path("")
        shpname: Path = Path("")
        shxname: Path = Path("")
        # Search for the specific extensions in the names
        for file in files:
            file_descriptor = file.rsplit(".", 1)[-1]
            if file_descriptor == "dbf":
                dbfname = Path(file)
            if file_descriptor == "shp":
                shpname = Path(file)
            elif file_descriptor == "shx":
                shxname = Path(file)
        shape_file = shapefile.Reader(
            shp=io.BytesIO(shpname.read_bytes()),
            dbf=io.BytesIO(dbfname.read_bytes()),
            shx=io.BytesIO(shxname.read_bytes()),
            encoding="cp1252",
        )
        if shape_file.shapeType != 5:
            logger.warning(
                f"Error. The file {country_geometry_file} doesn't contain Polygons"
            )
            return
        columns: Dict = {}
        counter: int = 0
        for h in shape_file.fields:
            column_name = h[0]
            column = CountriesMapping.from_value(column_name)
            if column:
                columns[column] = counter
            counter += 1
        # Access the single shape_record objects
        shape_record: shapefile.ShapeRecord
        for shape_record in shape_file.shapeRecords():
            record = shape_record.record
            shape_iso_a2: str = record[columns[CountriesMapping.COUNTRY_ALPHA_2]]
            shape_iso_a3: str = record[columns[CountriesMapping.COUNTRY_ALPHA_2]]
            country: CountryData
            for country in self.objects_list:
                if (
                    shape_iso_a2 == country.country_alpha_2
                    or shape_iso_a3 == country.country_alpha_3
                ):
                    geom: Union[
                        MultiPolygon, Dict
                    ] = shape_record.shape.__geo_interface__
                    if geom["type"] == "Polygon":
                        geom = shape(MultiPolygon([shape(geom)]))

                    else:
                        geom = shape(geom)
                    country.geom = "SRID=4326;" + geom.__str__()

    def _process_data(self, data_file: Path) -> None:
        with open(data_file, newline="", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=",", quotechar='"')
            header_row = next(reader)
            headers: Dict = {}
            counter: int = 0
            for h in header_row:
                mapping = CountriesMapping.from_value(h)
                if mapping is not None:
                    headers[mapping] = counter
                counter += 1
            for row in reader:
                country_object = CountryData()
                country_object.set_data(data=row, headers=headers)
                country_object.id = row[headers[CountriesMapping.COUNTRY_ALPHA_2]]
                if (
                    not country_object.country_name
                    and not country_object.country_alpha_2
                    and not country_object.country_alpha_3
                ):
                    # Alpha 2 and 3 are the absolute minimum.
                    logger.debug(f"Skipping country with not enough information: {row}")
                else:
                    self.objects_list.append(country_object)
