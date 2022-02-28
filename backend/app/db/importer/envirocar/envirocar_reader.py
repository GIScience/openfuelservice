import asyncio
import json
import logging
import multiprocessing
import time
import urllib.parse
from pathlib import Path
from typing import Any, Coroutine, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import parse_qs, urlparse

import geojson
import tqdm
from geojson import Feature
from requests import Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.importer.base_reader import BaseReader
from app.matching.envirocar_matcher import EnvirocarMatcher
from app.misc import data_handling
from app.misc.requests_tools import ThreadedRequests
from app.models import (
    EnvirocarPhenomenon,
    EnvirocarSensor,
    EnvirocarTrack,
    EnvirocarTrackMeasurement,
    EnvirocarTrackMeasurementPhenomenon,
    WikicarEnvirocar,
)

logger = logging.getLogger(__name__)


class EnvirocarReader(BaseReader):
    def __init__(
        self,
        db: Session,
        file_or_url: Union[str, Path, None] = None,
        envirocar_base_url: str = "https://envirocar.org/api/stable",
        threads: Union[int, None] = None,
    ):
        super().__init__(file_or_url)
        self.phenomenons_url = f"{envirocar_base_url}/phenomenons"
        self.sensors_url = f"{envirocar_base_url}/sensors"
        self.tracks_url = f"{envirocar_base_url}/tracks"
        self._headers = settings.GLOBAL_HEADERS
        if not threads:
            self._threads = 1
            if multiprocessing.cpu_count() > 1:
                self._threads = multiprocessing.cpu_count() - 1
        else:
            self._threads = threads
        self._threaded_requests = ThreadedRequests()
        self._envirocar_matcher: EnvirocarMatcher = EnvirocarMatcher(
            models_path=settings.UNCOMPRESSED_MATCHING_DATA, db=db
        )

    @property
    def matched_sensors(self) -> Union[List, None]:
        if 1 in self.objects_ordered:
            return self.objects_ordered.get(1)
        return None

    def get_phenomenons(self) -> List:
        phenomenons: List = []
        start_time = time.time()
        try:
            responses = self.__crawl_urls(
                urls_to_crawl=[self.phenomenons_url],
                description=" Download Phenomenons",
                download_unit=" Phenomenons",
            )
            response: Dict
            for response in responses:
                content = response["phenomenons"] if "phenomenons" in response else None
                object_data: Dict
                phenomenons.extend(
                    [EnvirocarPhenomenon(**object_data) for object_data in content]
                )
        except Exception as err:
            logger.error(f"Error fetching envirocar phenomenons with error {err}")
            raise err
        finally:
            end_time = time.time()
            logger.info(
                f"{len(phenomenons)} Phenomenons crawled in {end_time - start_time} Seconds"
            )
            return phenomenons

    def get_sensors(self) -> List:
        sensors: List = []
        start_time = time.time()
        try:
            responses: List = self.__crawl_urls(
                urls_to_crawl=[self.sensors_url],
                description=" Get Sensors",
                download_unit=" Sensors",
            )
            for response in responses:
                content: List = response["sensors"] if "sensors" in response else None
                data: Dict
                object_data: Dict
                sensors.extend(
                    [
                        EnvirocarSensor(**data_handling.flatten_dictionary(data))
                        for data in content
                    ]
                )
        except Exception as err:
            logger.error(f"Error fetching envirocar phenomenons with error {err}")
            raise err
        finally:
            end_time = time.time()
            logger.info(
                f"{len(sensors)} Sensors crawled in {end_time - start_time} Seconds"
            )
        return sensors

    def __crawl_urls(
        self,
        urls_to_crawl: List,
        threads: int = None,
        skip_next_pages: bool = False,
        description: str = " Downloading URLs",
        download_unit: str = " URLs",
    ) -> List:
        response_objects: List = []
        thread_responses = self._threaded_requests.get_urls_threaded(
            urls=urls_to_crawl,
            workers=threads,
            description=description,
            download_unit=download_unit,
        )
        response: Response
        sub_urls_to_crawl: List = []
        for response in thread_responses:
            if response.status_code != 200:
                continue
            if not skip_next_pages and response.links.get("last"):
                last_link: Optional[Any] = response.links.get("last")
                if not isinstance(last_link, Dict):
                    continue
                last_url: urllib.parse.ParseResult = urlparse(last_link["url"])
                original_base_url = response.url.rsplit("?")[0] + "/"
                query_strings = parse_qs(last_url.query)
                if "page" not in query_strings or "limit" not in query_strings:
                    continue
                # limit: int = int(query_strings.pop('limit')[0])
                total_pages: int = int(query_strings.pop("page")[0])
                sub_urls_to_crawl.extend(
                    [
                        Request("GET", original_base_url, params=query_strings)  # type: ignore
                        .prepare()
                        .url
                        + f"&page={i}"  # type: ignore
                        for i in range(2, total_pages + 1)
                    ]
                )
            response_json = response.json()
            if not response_json:
                continue
            response_objects.append(response.json())
        if not len(sub_urls_to_crawl):
            return response_objects
        thread_responses = self._threaded_requests.get_urls_threaded(
            urls=sub_urls_to_crawl,
            workers=threads,
            description=description,
            download_unit=download_unit,
        )
        for response in thread_responses:
            if response.status_code != 200:
                continue
            response_json = response.json()
            if not response_json:
                continue
            response_objects.append(response.json())
        return response_objects

    def get_track_ids_and_sensors(
        self,
    ) -> Tuple[List[EnvirocarSensor], List[EnvirocarTrack], List[int]]:
        logger.info("Get track ids and sensors.")
        tracks_and_sensors: List = self.__crawl_urls(
            [self.tracks_url],
            threads=self._threads,
            skip_next_pages=False,
            description=" Get Tracks and Sensors",
            download_unit=" Tracks and Sensors",
        )

        if not len(tracks_and_sensors):
            return [], [], []
        tracks_and_sensors_flattened = []
        for tracks in tracks_and_sensors:
            if isinstance(tracks, dict) and "tracks" in tracks:
                tracks_and_sensors_flattened.extend(tracks["tracks"])
        track_ids: Set = set()
        sensor_ids: Set = set()
        sensors_return: List = []
        tracks_return: List = []
        track: Dict
        for track in tracks_and_sensors_flattened:
            if (
                any(key not in track.keys() for key in ["id", "sensor"])
                or track["id"] in track_ids
                or any(
                    key not in track["sensor"].keys() for key in ["properties", "type"]
                )
            ):
                continue
            sensor_object = EnvirocarSensor(
                **data_handling.flatten_dictionary(track.pop("sensor"))
            )
            track_object: EnvirocarTrack = EnvirocarTrack(**track)
            track_ids.add(track_object.id)
            if sensor_object.id not in sensor_ids:
                sensors_return.append(sensor_object)
                sensor_ids.add(sensor_object.id)
            track_object.sensor_id = sensor_object.id
            tracks_return.append(track_object)
        logger.info(
            f"Successfully crawled {len(sensors_return)} sensors and {len(track_ids)} tracks."
        )
        return sensors_return, tracks_return, list(track_ids)

    @staticmethod
    def process_track_measurements(track_measurement_input: Dict) -> Tuple[List, List]:
        track_measurements: List = []
        track_measurement_phenomenons: List = []
        if any(
            key not in track_measurement_input.keys() for key in ["type", "features"]
        ):
            return track_measurements, track_measurement_phenomenons
        for feature in track_measurement_input["features"]:
            # Is valid GeoJSON
            measurement_geojson: Feature = geojson.loads(json.dumps(feature))
            if any(
                key not in measurement_geojson.keys()
                for key in ["type", "properties", "geometry"]
            ):
                continue
            track_measurement_properties: Dict = measurement_geojson.pop("properties")
            if any(
                key not in track_measurement_properties.keys()
                for key in ["track", "phenomenons", "sensor"]
            ):
                continue
            track_measurement_properties["track_id"] = track_measurement_properties.pop(
                "track"
            )
            track_measurement_phenomenons_raw = track_measurement_properties.pop(
                "phenomenons"
            )
            track_measurement_properties = {
                key: value
                for key, value in track_measurement_properties.items()
                if key in EnvirocarTrackMeasurement.__dict__.keys()
            }
            track_measurement_properties["geom"] = measurement_geojson
            track_measurement = EnvirocarTrackMeasurement(
                **track_measurement_properties
            )
            for key, value in track_measurement_phenomenons_raw.items():
                value["name"] = key
                value["id"] = track_measurement.id
                track_measurement_phenomenons.append(
                    EnvirocarTrackMeasurementPhenomenon(**value)
                )
            track_measurements.append(track_measurement)
        return track_measurements, track_measurement_phenomenons

    def fetch_track_measurements_and_phenomenons(
        self, track_ids: List
    ) -> Tuple[List, List]:
        track_measurements: List = []
        track_measurements_phenomenons: List = []
        tracks_to_fetch: List = [
            Request("GET", self.tracks_url + "/" + track_id + "/measurements")
            .prepare()
            .url
            for track_id in track_ids
        ]
        logger.info("Crawling track measurements.")
        fetched_track_measurements = self.__crawl_urls(
            tracks_to_fetch,
            threads=self._threads,
            description=" Getting track measurements",
            download_unit=" Track Measurements",
        )
        for track_measurements_raw in fetched_track_measurements:
            (
                temp_track_measurements,
                temp_track_measurements_phenomenons,
            ) = self.process_track_measurements(track_measurements_raw)
            track_measurements.extend(temp_track_measurements)
            track_measurements_phenomenons.extend(temp_track_measurements_phenomenons)
        logger.info(f"Successfully crawled and processed {len(track_measurements)}")
        return track_measurements, track_measurements_phenomenons

    async def match_sensors_to_wikicar(
        self, sensors: List[EnvirocarSensor], accuracy: Union[float, None] = None
    ) -> List[WikicarEnvirocar]:
        manufacturer_names: List = list(
            set([sensor.manufacturer for sensor in sensors])
        )
        loader_task = self._envirocar_matcher.initialize_models(manufacturer_names)
        sensor: EnvirocarSensor
        tasks = [
            self._envirocar_matcher.match(car=matched_sensor, accuracy=accuracy)
            # creating task starts coroutine
            for matched_sensor in sensors
        ]
        pbar = tqdm.tqdm(
            total=len(tasks), position=0, ncols=90, desc=" Matching Sensors to WikiCars"
        )
        matches: List[WikicarEnvirocar] = []
        await loader_task
        for f in asyncio.as_completed(tasks):
            value: Union[List[WikicarEnvirocar], None] = await f
            if value is not None:
                matches.extend(value)
            pbar.update()
        return matches

    def _process_data(self, data_file: Union[Path, None]) -> None:
        phenomenons: List = self.get_phenomenons()
        self.objects_ordered[0] = phenomenons
        # sensors: List = self.get_sensors()
        sensors, tracks, track_ids = self.get_track_ids_and_sensors()
        self.objects_ordered[1] = sensors
        self.objects_ordered[2] = tracks
        (
            track_measurements,
            track_measurements_phenomenons,
        ) = self.fetch_track_measurements_and_phenomenons(track_ids=track_ids)
        self.objects_ordered[3] = track_measurements
        self.objects_ordered[4] = track_measurements_phenomenons
        loop = asyncio.get_event_loop()
        coro: Coroutine[
            Any, Any, List[WikicarEnvirocar]
        ] = self.match_sensors_to_wikicar(sensors, accuracy=0.2)
        wikicar_envirocar_matches: List[WikicarEnvirocar] = loop.run_until_complete(
            coro
        )
        self.objects_ordered[5] = wikicar_envirocar_matches
