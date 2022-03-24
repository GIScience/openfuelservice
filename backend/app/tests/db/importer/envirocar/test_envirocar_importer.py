from typing import List, Tuple

import pytest
import responses
from sqlalchemy.orm import Session

from app.db.importer.envirocar.envirocar_reader import EnvirocarReader
from app.models import (
    EnvirocarPhenomenon,
    EnvirocarSensor,
    EnvirocarSensorStatistic,
    EnvirocarTrack,
    EnvirocarTrackMeasurement,
    EnvirocarTrackMeasurementPhenomenon,
    WikiCar,
    WikiCarCategory,
    WikicarEnvirocar,
)


@pytest.mark.asyncio
async def test_envirocar_importer(
    db: Session,
    mock_wikipedia_objects: Tuple[List[WikiCarCategory], List[WikiCar]],
    mock_all_responses: responses.RequestsMock,
) -> None:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        db=db,
        file_or_url=None,
        envirocar_base_url="https://envirocar.org/api/stable",
        threads=None,
    )
    await envirocar_reader.fetch_process_and_import_data(import_data=True)
    unique_ids_phenomenons = list(
        set(
            [
                phenomenon.name
                for phenomenon in envirocar_reader.phenomenons
                if type(phenomenon) == EnvirocarPhenomenon
            ]
        )
    )
    unique_ids_sensors = list(
        set(
            [
                sensor.id
                for sensor in envirocar_reader.sensors
                if type(sensor) == EnvirocarSensor
            ]
        )
    )
    unique_ids_tracks = list(
        set(
            [
                track.id
                for track in envirocar_reader.tracks
                if type(track) == EnvirocarTrack
            ]
        )
    )
    unique_ids_track_measurements = list(
        set(
            [
                track.id
                for track in envirocar_reader.track_measurements
                if type(track) == EnvirocarTrackMeasurement
            ]
        )
    )
    unique_ids_track_measurements_phenomenons = list(
        set(
            [
                tuple([track.id, track.name])
                for track in envirocar_reader.track_measurements_phenomenons
                if type(track) == EnvirocarTrackMeasurementPhenomenon
            ]
        )
    )
    unique_ids_wikicar_envirocar = list(
        set(
            [
                tuple([match.envirocar_sensor_id, match.wikicar_id])
                for match in envirocar_reader.wikicar_envirocar_matches
                if type(match) == WikicarEnvirocar
            ]
        )
    )
    sensor_statistic: EnvirocarSensorStatistic
    unique_ids_sensor_statistics = list(
        set(
            [
                sensor_statistic.id
                for sensor_statistic in envirocar_reader.sensor_statistics
                if type(sensor_statistic) == EnvirocarSensorStatistic
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
    sensor_statistics_in_db = EnvirocarSensorStatistic.get_all_by_filter(
        db=db, filter_ids=unique_ids_sensor_statistics, id_only=True
    )
    assert len(phenomenons_in_db)
    assert len(sensors_in_db)
    assert len(tracks_in_db)
    assert len(track_measurements_in_db)
    assert len(sensor_statistics_in_db)
    assert len(unique_ids_phenomenons) == len(phenomenons_in_db)
    assert len(unique_ids_sensors) == len(sensors_in_db)
    assert len(unique_ids_tracks) == len(tracks_in_db)
    assert len(unique_ids_tracks) == len(tracks_in_db)
    assert len(unique_ids_track_measurements_phenomenons) == len(
        track_measurement_phenomenons_in_db
    )
    assert len(unique_ids_wikicar_envirocar) == len(wikicar_envirocars_in_db)
    assert len(unique_ids_sensor_statistics) == len(sensor_statistics_in_db)

    for sensor_object in envirocar_reader.sensors:
        try:
            db.delete(sensor_object)
        except Exception:
            pass
    db.commit()
    for phenomenon_object in envirocar_reader.phenomenons:
        try:
            db.delete(phenomenon_object)
        except Exception:
            pass
    db.commit()

    assert len(db.query(WikicarEnvirocar).all()) <= 0
    assert len(db.query(EnvirocarTrackMeasurementPhenomenon).all()) <= 0
    assert len(db.query(EnvirocarTrackMeasurement).all()) <= 0
    assert len(db.query(EnvirocarTrack).all()) <= 0
