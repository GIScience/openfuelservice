from typing import Generator

import responses
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.import_data import import_all_data
from app.models import (
    CarFuelDataCar,
    CountryData,
    EnvirocarPhenomenon,
    EnvirocarSensor,
    EnvirocarTrack,
    EnvirocarTrackMeasurement,
    EnvirocarTrackMeasurementPhenomenon,
    EurostatCountryPrice,
    EurostatGeneralPrice,
    WikiCar,
    WikiCarCategory,
    WikicarEnvirocar,
    WikiCarPageText,
)


def test_import_all_data(
    db: Session,
    mock_all_responses: Generator[responses.RequestsMock, None, None],
) -> None:
    db.query(CarFuelDataCar).delete()
    db.query(EnvirocarTrackMeasurementPhenomenon).delete()
    db.query(EnvirocarTrackMeasurement).delete()
    db.query(EnvirocarTrack).delete()
    db.query(EnvirocarSensor).delete()
    db.query(EnvirocarPhenomenon).delete()
    db.query(WikiCar).delete()
    db.query(WikiCarPageText).delete()
    db.query(WikiCarCategory).delete()
    db.query(CountryData).delete()
    db.query(EurostatCountryPrice).delete()
    db.query(EurostatGeneralPrice).delete()
    db.query(CountryData).delete()

    assert len(db.query(CarFuelDataCar).all()) == 0
    assert len(db.query(EnvirocarTrackMeasurementPhenomenon).all()) == 0
    assert len(db.query(EnvirocarTrackMeasurement).all()) == 0
    assert len(db.query(EnvirocarTrack).all()) == 0
    assert len(db.query(EnvirocarSensor).all()) == 0
    assert len(db.query(EnvirocarPhenomenon).all()) == 0
    assert len(db.query(WikiCar).all()) == 0
    assert len(db.query(WikiCarCategory).all()) == 0
    assert len(db.query(CountryData).all()) == 0
    assert len(db.query(EurostatCountryPrice).all()) == 0
    assert len(db.query(EurostatGeneralPrice).all()) == 0
    assert len(db.query(CountryData).all()) == 0

    db.commit()
    test_car_category = {
        "car_categories": {
            "a": {
                "category_names": [
                    "Kategorie:Kleinstwagen",
                    "Kategorie:Leichtfahrzeug",
                    "Category:Microcars",
                ],
                "de": "Kleinstwagen",
                "en": "mini cars",
                "single_cars": [],
                "tank_capacity": 15,
            }
        }
    }
    settings.CAR_CATEGORIES = test_car_category
    import_all_data(db=db)

    assert len(db.query(WikicarEnvirocar).all()) > 0
    assert len(db.query(CarFuelDataCar).all()) > 0
    assert len(db.query(EnvirocarTrackMeasurementPhenomenon).all()) > 0
    assert len(db.query(EnvirocarTrackMeasurement).all()) > 0
    assert len(db.query(EnvirocarTrack).all()) > 0
    assert len(db.query(EnvirocarSensor).all()) > 0
    assert len(db.query(EnvirocarPhenomenon).all()) > 0
    assert len(db.query(WikiCar).all()) > 0
    assert len(db.query(WikiCarCategory).all()) > 0
    assert len(db.query(CountryData).all()) > 0
    assert len(db.query(EurostatCountryPrice).all()) > 0
    assert len(db.query(EurostatGeneralPrice).all()) > 0
    assert len(db.query(CountryData).all()) > 0

    db.query(CarFuelDataCar).delete()
    db.query(EnvirocarTrackMeasurementPhenomenon).delete()
    db.query(EnvirocarTrackMeasurement).delete()
    db.query(EnvirocarTrack).delete()
    db.query(EnvirocarSensor).delete()
    db.query(EnvirocarPhenomenon).delete()
    db.commit()
    # Test cascade ondelete
    assert len(db.query(WikicarEnvirocar).all()) == 0
    db.query(WikiCar).delete()
    db.query(WikiCarPageText).delete()
    db.query(WikiCarCategory).delete()
    db.query(EurostatCountryPrice).delete()
    db.query(EurostatGeneralPrice).delete()
    db.query(CountryData).delete()

    db.commit()
