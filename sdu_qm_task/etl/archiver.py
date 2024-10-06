#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd

from sdu_qm_task.logger_conf import get_logger

logger = get_logger(__file__)

# Define the base folder path relative to this script's location.
ARCHIVE_FOLDER = Path(Path(__file__).parents[2], "archive")

# Define date/time formats for formatting timestamps.
DT_FILE_FORMAT = "%Y-%m-%d_%H-%M-%S"


class Archiver():
    """A class for archiving unconvertible entries into a CSV file with a timestamped filename.
    """
    def __init__(self, timestamp: datetime) -> None:
        """Initializes the Archiver class with a timestamp.

        Args:
            timestamp (datetime): timestamp to generate archive filename.
        """
        logger.debug(f"Initiated {self.__class__.__name__} class.")

        self.timestamp = timestamp
    
    @staticmethod
    def _create_archive_folder(archive_folder: Path) -> None:
        """Creates the archive folder if it doesn't exist.

        Args:
            archive_folder (Path): Path to create the archive folder.
        """
        if not archive_folder.exists():
            logger.info(f"Creating archive folder: {archive_folder}.")
            archive_folder.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def _save_to_archive(archive_file: Path, entries: List[dict]) -> None:
        """Saves the list of entries to a CSV file in the archive folder.

        Args:
            archive_file (Path): file path to save the data.
            entries (List[dict]): list of unconvertible entries.
        """
        archive_df = pd.DataFrame(entries)
        archive_df.to_csv(archive_file, index=False)
        logger.info(f"Archived unconvertibles entries to: {archive_file.as_posix()}.")

    def _create_file_name(self) -> str:
        """Generates a filename for unconvertible entries based on timestamp.

        Returns:
            str: formatted filename like "YYYY-MM-DD_HH-MM-SS_unconvertibles.csv".
        """
        timestamp = self.timestamp.strftime(DT_FILE_FORMAT)
        return f"{timestamp}_unconvertibles.csv"

    def _get_archive_file_name(self) -> Path:
        """Generates the full path of the archive file, ensuring the archive folder exists.

        Returns:
            Path: path of the archive file to be created.
        """
        archive_file_name = self._create_file_name()

        self._create_archive_folder(ARCHIVE_FOLDER)

        archive_file = Path(ARCHIVE_FOLDER, archive_file_name).resolve()

        return archive_file

    def archive(self, entries: List[dict]) -> None:
        """Archives entries that could not be converted to a proper datetime format.

        Args:
            entries (List[dict]): list of unconvertible entries.
        """
        logger.warning(f"Caught {len(entries)} unconvertible entries.")

        archive_file = self._get_archive_file_name()
        self._save_to_archive(archive_file, entries)

        logger.warning(f"Archived {len(entries)} unconvertible entries.")
