import pytest

from app.misc.data_handling import check_manufacturer


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
