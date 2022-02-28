from typing import Generator, List

import responses
from sqlalchemy.orm import Session

from app.db.importer.base_importer import BaseImporter
from app.db.importer.envirocar.envirocar_reader import EnvirocarReader
from app.models import (
    EnvirocarPhenomenon,
    EnvirocarSensor,
    EnvirocarTrack,
    EnvirocarTrackMeasurement,
    EnvirocarTrackMeasurementPhenomenon,
    WikiCar,
    WikicarEnvirocar,
)


def test_envirocar_importer(
    db: Session,
    mock_wikipedia_cars: Generator[WikiCar, None, None],
    envirocar_mocked_responses: responses.RequestsMock,
) -> None:
    # Clean the database
    db.query(WikicarEnvirocar).delete()
    db.query(EnvirocarTrackMeasurementPhenomenon).delete()
    db.query(EnvirocarTrackMeasurement).delete()
    db.query(EnvirocarTrack).delete()
    db.query(EnvirocarSensor).delete()
    db.query(EnvirocarPhenomenon).delete()
    db.commit()

    unique_ids_phenomenons = []
    unique_ids_sensors = []
    unique_ids_tracks = []
    unique_ids_track_measurements = []
    unique_ids_track_measurements_phenomenons = []
    unique_ids_wikicar_envirocar = []

    envirocar_reader: EnvirocarReader = EnvirocarReader(
        db=db,
        file_or_url=None,
        envirocar_base_url="https://envirocar.org/api/stable",
        threads=None,
    )
    envirocar_reader.fetch_and_process_data()
    for index, object_collection in envirocar_reader.objects_ordered.items():
        BaseImporter(db=db).import_data(db_objects=object_collection)
        if index == 0:
            unique_ids_phenomenons = list(
                set(
                    [
                        phenomenon.name
                        for phenomenon in object_collection
                        if type(phenomenon) == EnvirocarPhenomenon
                    ]
                )
            )
        if index == 1:
            unique_ids_sensors = list(
                set(
                    [
                        sensor.id
                        for sensor in object_collection
                        if type(sensor) == EnvirocarSensor
                    ]
                )
            )
        elif index == 2:
            unique_ids_tracks = list(
                set(
                    [
                        track.id
                        for track in object_collection
                        if type(track) == EnvirocarTrack
                    ]
                )
            )
        elif index == 3:
            unique_ids_track_measurements = list(
                set(
                    [
                        track.id
                        for track in object_collection
                        if type(track) == EnvirocarTrackMeasurement
                    ]
                )
            )
        elif index == 4:
            unique_ids_track_measurements_phenomenons = list(
                set(
                    [
                        tuple([track.id, track.name])
                        for track in object_collection
                        if type(track) == EnvirocarTrackMeasurementPhenomenon
                    ]
                )
            )
        elif index == 5:
            unique_ids_wikicar_envirocar = list(
                set(
                    [
                        tuple([match.envirocar_sensor_id, match.wikicar_id])
                        for match in object_collection
                        if type(match) == WikicarEnvirocar
                    ]
                )
            )
    phenomenons_in_db: List = EnvirocarPhenomenon.get_all_by_filter(
        db=db, filter_ids=unique_ids_phenomenons, id_only=True
    )
    sensors_in_db: List = EnvirocarSensor.get_all_by_filter(
        db=db, filter_ids=unique_ids_sensors, id_only=True
    )
    tracks_in_db: List = EnvirocarTrack.get_all_by_filter(
        db=db, filter_ids=unique_ids_tracks, id_only=True
    )
    track_measurements_in_db: List = EnvirocarTrackMeasurement.get_all_by_filter(
        db=db, filter_ids=unique_ids_track_measurements, id_only=True
    )
    track_measurement_phenomenons_in_db = (
        EnvirocarTrackMeasurementPhenomenon.get_all_by_filter(
            db=db, filter_ids=unique_ids_track_measurements_phenomenons, id_only=True
        )
    )
    wikicar_envirocars_in_db = WikicarEnvirocar.get_all_by_filter(
        db=db, filter_ids=unique_ids_wikicar_envirocar, id_only=True
    )
    assert len(phenomenons_in_db)
    assert len(sensors_in_db)
    assert len(tracks_in_db)
    assert len(track_measurements_in_db)
    assert len(unique_ids_phenomenons) == len(phenomenons_in_db)
    assert len(unique_ids_sensors) == len(sensors_in_db)
    assert len(unique_ids_tracks) == len(tracks_in_db)
    assert len(unique_ids_tracks) == len(tracks_in_db)
    assert len(unique_ids_track_measurements_phenomenons) == len(
        track_measurement_phenomenons_in_db
    )
    assert len(unique_ids_wikicar_envirocar) == len(wikicar_envirocars_in_db)
    db.query(WikicarEnvirocar).delete()
    db.query(EnvirocarTrackMeasurementPhenomenon).delete()
    db.query(EnvirocarTrackMeasurement).delete()
    db.query(EnvirocarTrack).delete()
    db.query(EnvirocarSensor).delete()
    db.query(EnvirocarPhenomenon).delete()
    db.commit()
