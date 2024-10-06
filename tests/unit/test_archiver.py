from datetime import datetime
from pathlib import Path
import shutil

import pandas as pd
import pytest

from sdu_qm_task.etl.archiver import Archiver, DT_FILE_FORMAT


@pytest.fixture
def timestamp():
    return datetime.now()


@pytest.fixture
def archiver(timestamp):
    return Archiver(timestamp)


@pytest.fixture(scope="function")
def archive_folder():
    archive_folder = Path(Path(__file__).parent, "archive_temp").resolve()

    yield archive_folder

    shutil.rmtree(archive_folder, ignore_errors=True)


@pytest.fixture(scope="function")
def archive_file(archive_folder: Path, timestamp: datetime):
    archive_folder.mkdir(parents=True, exist_ok=True)
    formatted_ts = timestamp.strftime(DT_FILE_FORMAT)

    archive_file = Path(archive_folder, f"{formatted_ts}_unconvertibles.csv").resolve()

    yield archive_file

    archive_file.unlink(missing_ok=True)


@pytest.fixture(scope="module")
def entries() -> pd.DataFrame:
    return pd.read_csv(Path(Path(__file__).parents[1], "data", "sample_df.csv"))


def test_create_archive_folder(archiver, archive_folder):
    archiver._create_archive_folder(archive_folder)
    assert Path(archive_folder).exists()

    archiver._create_archive_folder(archive_folder)


def test_save_to_archive(archiver, archive_file, entries):
    archiver._save_to_archive(archive_file, entries)
    assert Path(archive_file).exists()


def test_create_file_name(archiver, timestamp):
    formatted_ts = timestamp.strftime(DT_FILE_FORMAT)
    assert archiver._create_file_name() == f"{formatted_ts}_unconvertibles.csv"


def test_get_archive_file_name(monkeypatch, archiver, archive_folder, archive_file):
    monkeypatch.setattr('sdu_qm_task.etl.archiver.ARCHIVE_FOLDER', archive_folder)
    assert archiver._get_archive_file_name() == archive_file


def test_archive(monkeypatch, archiver, archive_folder, archive_file, entries):
    monkeypatch.setattr('sdu_qm_task.etl.archiver.ARCHIVE_FOLDER', archive_folder)
    archiver.archive(entries)

    assert archive_file.exists()
    assert pd.read_csv(archive_file).to_dict() == entries.to_dict()
