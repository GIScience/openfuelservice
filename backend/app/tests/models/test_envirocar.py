from typing import List

from app.models import EnvirocarPhenomenon


def test_envirocar_phenomenon() -> None:
    test_data: List = [
        {"unit": "CO2", "value": "g/km"},
        {"unit": "NOx", "value": "g/km"},
    ]
    test_data_objects = [
        EnvirocarPhenomenon(**test_data_dict) for test_data_dict in test_data
    ]
    assert len(test_data_objects) == 2
    assert test_data_objects[0].unit in test_data[0]["unit"]
    assert test_data_objects[0].value in test_data[0]["value"]

    assert test_data_objects[1].unit in test_data[1]["unit"]
    assert test_data_objects[1].value in test_data[1]["value"]
