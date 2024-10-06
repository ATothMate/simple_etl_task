import pytest

from datetime import date

from sdu_qm_task.etl.delta_loader import DeltaLoader


@pytest.fixture
def delta_loader():
    return DeltaLoader()

@pytest.fixture
def test_date():
    return date(2025, 1, 1)

def test_get_dateid_from_date(delta_loader, test_date):
    assert delta_loader._get_dateid_from_date(test_date) == 20250101
