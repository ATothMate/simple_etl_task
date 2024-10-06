import pytest

from pathlib import Path
import tempfile


from sdu_qm_task.feeder import feeder


@pytest.fixture(scope="function")
def folder():
    return Path(Path(__file__).parents[1], "data").resolve().as_posix()


@pytest.fixture(scope="module")
def empty_folder():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture(scope="module")
def temp_file():
    with tempfile.NamedTemporaryFile(suffix='.csv') as tf:
        yield Path(tf.name)


@pytest.fixture(scope="module")
def temp_file_2():
    with tempfile.NamedTemporaryFile(suffix='.csv') as tf:
        yield Path(tf.name)


def test_get_available_files(folder, empty_folder):
    assert feeder.get_available_files(folder) == sorted(Path(folder).glob("*.csv"))

    assert feeder.get_available_files(empty_folder.as_posix()) == []


def test_get_next_file(folder, empty_folder):
    assert feeder.get_next_file(folder) == Path(folder, "sample_df.csv")

    assert feeder.get_next_file(empty_folder.as_posix()) is None


def test_move_file(temp_file, empty_folder):
    assert temp_file.exists()

    expected_file = Path(empty_folder, temp_file.name)
    feeder.move_file(temp_file, empty_folder)

    assert not temp_file.exists()
    assert expected_file.exists()


def test_main(temp_file_2, empty_folder):
    assert temp_file_2.exists()

    feeder.main(temp_file_2.parent.as_posix(), empty_folder.as_posix())

    assert not temp_file_2.exists()
    assert Path(empty_folder, temp_file_2.name).exists()

    not_available_folder = Path(temp_file_2.parent, "unavailable_folder")
    with pytest.raises(ValueError):
        feeder.main(not_available_folder.as_posix(), empty_folder.as_posix())
