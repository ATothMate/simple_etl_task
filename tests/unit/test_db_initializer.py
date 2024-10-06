import pytest

from sdu_qm_task.db_init.db_initializer import DBInitializer
from sdu_qm_task.queries import create_table_queries as ct_queries

@pytest.fixture
def expected_command_list():
    return [
        ct_queries.CREATE_PRELOAD_TRANSACTION,
        ct_queries.CREATE_DIM_DATE,
        ct_queries.CREATE_DIM_ITEM,
        ct_queries.CREATE_DIM_LOCATION,
        ct_queries.CREATE_FACT_TRANSCTION
    ]

def test_get_commands(expected_command_list):
    assert DBInitializer()._get_commands() == expected_command_list
