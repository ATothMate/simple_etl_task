#!/usr/bin/env python3

import argparse
from datetime import datetime
from dateutil import tz
from hashlib import md5
import json
from pathlib import Path
from typing import Dict, List, NewType, Optional, Set, Union

import pandas as pd
from sqlalchemy import create_engine, Engine

from sdu_qm_task.connect import PSQLConnection
from sdu_qm_task.logger_conf import get_logger
from sdu_qm_task.etl.archiver import Archiver
from sdu_qm_task.queries import pre_loader_queries as pl_queries
from sdu_qm_task.queries import table_names as tables

# Define a new type for the structure of the delta pre-load data.
DeltaPreLoadType = NewType(
    'DeltaPreLoadType',
    Dict[str, List[Dict[str, Union[int, str, float]]]]
)

logger = get_logger(__file__)

# Define the base folder path relative to this script's location.
BASE_FOLDER = Path(__file__).parents[2]

# Define date/time formats for parsing.
DT_WO_TZ_FORMAT = "%a %b %d %H:%M:%S %Y"
DT_WITH_TZ_FORMAT = "%a %b %d %H:%M:%S %Z %Y"

# Define a mapping of known and handled timezones.
TIMEZONES = {" IST ": tz.gettz('Europe/Dublin')}


def parse_arguments() -> str:
    """Parses command line arguments to retrieve the folder path.

    Returns:
        str: path to the folder containing source files to load into the database.
    """
    parser = argparse.ArgumentParser(
        description="A script to handle the processing of source files in the database.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-f", "--folder",
        type=str,
        default=Path(BASE_FOLDER, "data_folder_monitor").as_posix(),
        help="/path/to/folder; to load source file(s) to the Database."
    )
    args = parser.parse_args()

    return args.folder


class PreLoader():
    """Class responsible for loading data from source files into a PostgreSQL database.
    It follows the Extract-Transform-Load (ETL) pattern; extracting data from newly available
     source files, transforming the data as needed, and loading it into the preload tables.
    """
    def __init__(self, folder: str) -> None:
        """Initializes the PreLoader with the specified folder.

        Args:
            folder (str): path to the folder containing source files.
        """
        logger.debug(f"Initiated {self.__class__.__name__} class.")

        self.folder = folder
        self.created_at = datetime.now()

        self.psql_connection = PSQLConnection()
        self.archiver = Archiver(self.created_at)

    def run(self) -> None:
        """Executes the ETL proces.
        """
        delta_load = self.extract()
        delta_df = self.transform(delta_load)
        self.load(delta_df)

    @staticmethod
    def _get_md5_hash(entry: dict) -> str:
        """Computes the MD5 hash of a given entry.

        Args:
            entry (dict): entry to hash.

        Returns:
            str: MD5 hash of the entry.
        """
        return md5(json.dumps(entry).encode()).hexdigest()

    @staticmethod
    def _get_transformed_entry(
            entry: dict,
            hash_id: str,
            source_file: str,
            transaction_time: str,
            created_at: datetime
        ) -> Dict[str, Union[int, str, float]]:
        """Transforms a single entry into the desired format.

        Args:
            entry (dict): original entry.
            hash_id (str): MD5 hash of the entry.
            source_file (str): name of the source file.
            transaction_time (str): transaction timestamp.
            created_at (datetime): timestamp of current ETL process.

        Returns:
            Dict[str, Union[int, str, float]]: transformed entry.
        """
        return {
            "hash_id": hash_id,
            "source_file": source_file,
            "transaction_id": entry.get("TransactionId"),
            "user_id": entry.get("UserId"),
            "transaction_time": transaction_time,
            "item_code": entry.get("ItemCode"),
            "item_description": entry.get("ItemDescription"),
            "item_quantity": entry.get("NumberOfItemsPurchased"),
            "cost_per_item": entry.get("CostPerItem"),
            "country": entry.get("Country"),
            "created_at": created_at
        }

    @staticmethod
    def _has_known_timezone(transaction_time: str) -> bool:
        """Checks if the transaction time string has a known timezone.

        Args:
            transaction_time (str): transaction time string.

        Returns:
            bool: True if the timezone is known; otherwise, False.
        """
        return True if (
            transaction_time.find("GMT") != -1
            or transaction_time.find("UTC") != -1
        ) else False

    @staticmethod
    def _load_to_table(
            df: pd.DataFrame, table_name: str, engine: Engine, append: str="append"
        ) -> None:
        """Loads a DataFrame into a specified SQL table.

        Args:
            df (pd.DataFrame): DataFrame to load.
            table_name (str): name of the table to load the data into.
            engine (Engine): SQLAlchemy engine for database connection.
            append (str, optional): action to take if the table already exists. Default: "append".
        """
        df.to_sql(name=table_name, con=engine, if_exists=append, index=False)

    def _assign_timezone(self, transaction_time: str) -> Optional[datetime]:
        """Converts a transaction time string to a timezone-aware datetime object.

        Args:
            transaction_time (str): transaction time string.

        Returns:
            Optional[datetime]: timezone-aware datetime object or None if conversion fails.
        """
        if self._has_known_timezone(transaction_time):
            return datetime.strptime(transaction_time, DT_WITH_TZ_FORMAT)

        else:
            for tzone in TIMEZONES.keys():
                if tzone in transaction_time:
                    untimezoned_time = transaction_time.replace(tzone, " ").strip()
                    dt_time = datetime.strptime(untimezoned_time, DT_WO_TZ_FORMAT)
                    return dt_time.astimezone(TIMEZONES.get(tzone))

        logger.error(
            f"Can not convert timestamp: '{transaction_time}', as timezone is not in "
            f"[UTC, GMT] or among the handled timezones: {list(TIMEZONES.keys())}."
        )
        return None

    def _extract_db(self) -> Set[str]:
        """Extracts the set of source files that have already been processed from the database.

        Returns:
            Set[str]: set of source file names that are already in the database.
        """
        with self.psql_connection as conn:
            with conn.cursor() as cur:
                cur.execute(pl_queries.PRELOAD_SOURCE_FILE_QUERY)
                db_source_files = [item[0] for item in cur.fetchall()]

        return set(db_source_files)

    def _send_to_archive(self, entries: List[dict]) -> None:
        """Transmits any unconvertible entries for archiving.

        Args:
            entries (List[dict]): list of unconvertible entries.
        """
        self.archiver.archive(entries)

    def extract(self) -> DeltaPreLoadType:
        """Extracts data from source CSV files in the specified folder.

        Returns:
            DeltaPreLoadType: dictionary mapping source file names to their extracted entries.
        """
        logger.info(f"Starting extraction from source folder: '{self.folder}'.")
        db_source_files = self._extract_db()

        csv_files = list(Path(self.folder).glob("*.csv"))
        logger.info(f"Found {len(csv_files)} source CSV files.")

        if csv_files:
            if db_source_files:
                delta_csv_files = [cf for cf in csv_files if cf.name not in db_source_files]
            else:
                delta_csv_files = csv_files
        else:
            delta_csv_files = []

        logger.info(f"Found {len(delta_csv_files)} new source CSV files compared to the DB.")

        delta_load = {}
        for file in delta_csv_files:
            logger.info(f"Extracting source file: '{file.name}'.")
            df = pd.read_csv(file)

            delta_file_load = []
            for _, row in df.iterrows():
                delta_file_load.append(row.to_dict())

            logger.info(f"Extracted {len(delta_file_load)} entries from: '{file.name}'.")
            delta_load[file.name] = delta_file_load

        return delta_load

    def transform(self, delta_load: DeltaPreLoadType) -> pd.DataFrame:
        """Transforms the extracted entries into the desired format.

        Args:
            delta_load (DeltaPreLoadType): extracted entries from source files.

        Returns:
            pd.DataFrame: DataFrame containing the transformed data.
        """
        delta_data = []
        unconvertible_entries = []

        for source_file, entries in delta_load.items():
            logger.info(f"Starting transformation of: '{source_file}'")

            for _, entry in enumerate(entries):

                hash_id = self._get_md5_hash(entry)
                transaction_time = self._assign_timezone(entry.get("TransactionTime"))

                if transaction_time is not None:
                    # Transform the entry and add to the delta data list.
                    transformed_entry = self._get_transformed_entry(
                        entry, hash_id, source_file, transaction_time, self.created_at
                    )
                    delta_data.append(transformed_entry)
                else:
                    # Conversion failed. Skip transformation; apend entry.
                    unconvertible_entries.append(entry)

        logger.info(f"Transformed {len(delta_data)} entries.")

        # Archive any unconvertible entries.
        if len(unconvertible_entries) > 0:
            self._send_to_archive(unconvertible_entries)

        return pd.DataFrame(delta_data)

    def load(self, delta_df: pd.DataFrame) -> None:
        """Loads the transformed data into the specified SQL table.

        Args:
            delta_df (pd.DataFrame): DataFrame containing transformed data to load.
        """
        engine = create_engine(self.psql_connection.get_connection_string())

        # Load only if there is available data.
        if not delta_df.empty:
            logger.info(f"Inserting into table '{tables.PRELOAD_TRANSACTION_TABLE}'")
            self._load_to_table(df=delta_df, table_name=tables.PRELOAD_TRANSACTION_TABLE, engine=engine)
        else:
            logger.info(f"No data to insert to '{tables.PRELOAD_TRANSACTION_TABLE}'.")

        engine.dispose()


def main(folder: str):
    """Main entry point for the script.

    Args:
        folder (str): path to the folder containing source files.
    """
    PreLoader(folder).run()


if __name__ == "__main__":
    # Parse command line argument for folder path.
    folder = parse_arguments()

    main(folder)
