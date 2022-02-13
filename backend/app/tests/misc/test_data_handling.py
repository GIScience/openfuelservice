from typing import Dict

import pytest

from app.core.config import settings
from app.misc.data_handling import (
    check_brand_aliases,
    check_manufacturer,
    check_static_vehicles_list,
    clean_vehicle_name,
    flatten_dictionary,
    vehicle_is_ignored,
)


@pytest.mark.parametrize(
    "bare_manufacturer,real_manufacturer",
    (
        ("3 GE", "3 GE"),
        ("ACAM", "ACAM"),
        ("Opel", "Opel"),
        ("azlk", "Moskvitch"),
        ("PSA / Fiat", "Fiat"),
        ("Foobar", None),
    ),
)
def test_check_manufacturer(bare_manufacturer: str, real_manufacturer: str) -> None:
    assert real_manufacturer == check_manufacturer(
        manufacturer_to_check=bare_manufacturer
    )


@pytest.mark.parametrize(
    "input_dict,output_dict",
    (
        ({"a": "b"}, {"a": "b"}),
        ({"a": "b", "c": {"c1": "d1", "c2": "d2"}}, {"a": "b", "c1": "d1", "c2": "d2"}),
        ({}, {}),
        (None, {}),
        ("foobar", {}),
    ),
)
def test_flatten_dictionary(input_dict: Dict, output_dict: Dict) -> None:
    assert flatten_dictionary(input_dict) == output_dict


@pytest.mark.parametrize(
    "test_string,expected_result",
    (
        ("Mercedes 3 GE \\\"'#@;*<>{}`+=~|.!?,'", "Mercedes 3 GE"),
        ("Mercedes 3 GE;*<>{}`+=~|.!?,", "Mercedes 3 GE"),
        ("Mercedes +#*'3 +#*'GE", "Mercedes 3 GE"),
        ("Opel Foobar (22?=)", "Opel Foobar (22)"),
        ("PSA / Fiat Foobar", "PSA / Fiat Foobar"),
        ("Kei-Car", "Kei-Car"),
        ("Foobar", "Foobar"),
        (None, None),
    ),
)
def test_clean_vehicle_name(test_string: str, expected_result: str) -> None:
    test = clean_vehicle_name(vehicle_name=test_string)
    assert test == expected_result


@pytest.mark.parametrize(
    "test_string", [s for s in settings.CAR_BRANDS["ignore_list"]][::100]
)
def test_vehicle_is_ignored(test_string: str) -> None:
    ignored: bool = vehicle_is_ignored(car_brand_or_name=test_string)
    assert ignored


@pytest.mark.parametrize(
    "test, expected",
    (
        (["azlk", "Foo"], ["Moskvitch", "Foo"]),
        (["daimler benz", "Foo"], ["Mercedes-Benz", "Foo"]),
        (["VW-Porsche", "Foo"], ["Porsche", "Foo"]),
        (["DS", "Foo"], ["Citroën", "Foo"]),
        ([None, "Foo"], [None, None]),
        (["Foo", "Foo"], [None, None]),
        (["DS", None], [None, None]),
        ([None, None], [None, None]),
    ),
)
def test_check_brand_aliases(test: tuple, expected: tuple) -> None:
    brand, name = check_brand_aliases(short_name=test[0], car_name=test[1])
    assert brand == expected[0]
    assert name == expected[1]


@pytest.mark.parametrize(
    "car_name, expected_brand, expected_car_name",
    (
        ("DS5 LS", "Citroën", "DS 5LS"),
        ("DS 5LS", "Citroën", "DS 5LS"),
        ("Abarth 500 SS", "Abarth", "500 SS"),
        ("Foo", None, None),
        (None, None, None),
    ),
)
def test_check_static_vehicles_list(
    car_name: str, expected_brand: str, expected_car_name: str,
) -> None:
    brand, name = check_static_vehicles_list(car_name=car_name)
    assert brand == expected_brand
    assert name == expected_car_name
