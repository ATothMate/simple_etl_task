import pytest

import pycountry as pyc
import pycountry_convert as pyc_c

from sdu_qm_task.etl.location import Location


@pytest.fixture
def valid_location(valid_country_name):
    return Location(valid_country_name)

@pytest.fixture
def valid_country_name():
    return "United Kingdom"

@pytest.fixture
def valid_alpha2():
    return "GB"

@pytest.fixture
def invalid_location(invalid_country_name):
    return Location(invalid_country_name)

@pytest.fixture
def invalid_country_name():
    return "Atlantis"

@pytest.fixture
def invalid_alpha2():
    return "XY"

def test_code_to_continent(valid_location, invalid_location, valid_alpha2, invalid_alpha2):
    assert valid_location._code_to_continent(valid_alpha2) == "Europe"

    with pytest.raises(KeyError):
        invalid_location._code_to_continent(invalid_alpha2)

def test_get_location_info(
        valid_location,
        invalid_location,
        valid_country_name
    ):
    assert valid_location.get_location_info() == (valid_country_name, "GBR", "Europe")

    assert invalid_location.get_location_info() == ("UNKNOWN", "N/A", "UNKNOWN")
