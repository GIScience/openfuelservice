from typing import Dict

import pytest

from app.misc.data_handling import check_manufacturer, flatten_dictionary


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
