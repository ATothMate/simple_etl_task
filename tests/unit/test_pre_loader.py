from datetime import datetime
from pathlib import Path

import pytest

from sdu_qm_task.etl.pre_loader import PreLoader


@pytest.fixture(scope="function")
def folder():
    return Path(Path(__file__).parents[1], "data").resolve().as_posix()


@pytest.fixture
def pre_loader(folder):
    return PreLoader(folder)


@pytest.fixture
def entry():
    return {
        "UserId": 325794,
        "TransactionId": 6365337,
        "TransactionTime": "Tue Feb 05 13:10:00 XAB 2019",
        "ItemCode": 472731,
        "ItemDescription": "RETROSPOT BABUSHKA DOORSTOP",
        "NumberOfItemsPurchased": 6,
        "CostPerItem": 5.18,
        "Country": "United Kingdom"
    }


@pytest.fixture
def hash_id():
    return "8873eda206710fe16793055907649a32"


@pytest.fixture
def source_file():
    return "source_file_1.csv"


@pytest.fixture
def valid_ts():
    return "Tue Feb 05 13:10:00 IST 2019"


@pytest.fixture
def valid_utc_ts():
    return "Tue Feb 05 13:10:00 UTC 2019"


@pytest.fixture
def valid_gmt_ts():
    return "Tue Feb 05 13:10:00 GMT 2019"


@pytest.fixture
def invalid_ts():
    return "Tue Feb 05 13:10:00 XAB 2019"


@pytest.fixture
def created_at():
    return datetime.now()


def test_get_md5_hash(pre_loader, entry, hash_id):
    assert pre_loader._get_md5_hash(entry) == hash_id


def test_get_transformed_entry(pre_loader, entry, hash_id, source_file, valid_ts, created_at):
    assert pre_loader._get_transformed_entry(
        entry, hash_id, source_file, valid_ts, created_at
    ) == {
        "hash_id": hash_id,
        "source_file": source_file,
        "transaction_id": entry.get("TransactionId"),
        "user_id": entry.get("UserId"),
        "transaction_time": valid_ts,
        "item_code": entry.get("ItemCode"),
        "item_description": entry.get("ItemDescription"),
        "item_quantity": entry.get("NumberOfItemsPurchased"),
        "cost_per_item": entry.get("CostPerItem"),
        "country": entry.get("Country"),
        "created_at": created_at
    }


def test_has_known_timezone(pre_loader, valid_ts, valid_gmt_ts, valid_utc_ts, invalid_ts):
    assert pre_loader._has_known_timezone(valid_gmt_ts) is True
    assert pre_loader._has_known_timezone(valid_utc_ts) is True

    # Valid, but not by the scope of the function!
    assert pre_loader._has_known_timezone(valid_ts) is False

    assert pre_loader._has_known_timezone(invalid_ts) is False
