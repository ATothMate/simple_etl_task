#!/usr/bin/env python3

from datetime import date

import pandas as pd
import psycopg2

from sdu_qm_task.connect import PSQLConnection
from sdu_qm_task.logger_conf import get_logger
from sdu_qm_task.queries import delta_loader_queries as dl_queries
from sdu_qm_task.queries import table_names as tables
from sdu_qm_task.etl.location import Location

logger = get_logger(__file__)


class DeltaLoader():
    """Class responsible for loading delta data into the PostgreSQL database.
    It follows the Extract-Transform-Load (ETL) pattern; extracting new entries 
     from a source table, transforming the data as needed, and loading
     it into the target tables.
    """
    def __init__(self) -> None:
        """Initializes the DeltaLoader class.
        """
        logger.debug(f"Initiated {self.__class__.__name__} class.")

        self.psql_connection = PSQLConnection()

    def run(self) -> None:
        """Executes the ETL process.
        """
        delta_loc_df = self.extract()
        unique_loc_df = self.transform(delta_loc_df)
        self.load(unique_loc_df)

    @staticmethod
    def _get_dateid_from_date(date: date) -> int:
        """Converts a date object to an integer in the format YYYYMMDD.

        Args:
            date (date): date to convert.

        Returns:
            int: date in YYYYMMDD format as an integer.
        """
        return int(str(date).replace("-", ""))

    @staticmethod
    def _get_delta_load_count(cur: psycopg2.extensions.cursor) -> int:
        """Retrieves the count of new entries in the delta table.

        Args:
            cur (psycopg2.extensions.cursor): database cursor for executing queries.

        Returns:
            int: count of new entries found.
        """
        cur.execute(dl_queries.COUNT_DELTA_QUERY)
        delta_count = cur.fetchone()[0]
        logger.info(
            f"Found {delta_count} new entries in '{tables.PRELOAD_TRANSACTION_TABLE}' table."
        )

        return delta_count

    def extract(self) -> pd.DataFrame:
        """Extracts new location entries to be transformed from the PostgreSQL database.

        Returns:
            pd.DataFrame: DataFrame containing the new location entries.
        """
        logger.info(f"Extracting '{tables.PRELOAD_TRANSACTION_TABLE}' for new entries.")

        with self.psql_connection as conn:
            with conn.cursor() as cur:
                cur.execute(dl_queries.LOCATION_QUERY)
                delta_loc_extract = [item for item in cur.fetchall()]
                delta_loc_cols = [desc[0] for desc in cur.description]

        if delta_loc_extract == []:
            logger.info(f"Extracted 0 new location entry.")
        else:
            logger.info(f"Extracted {len(delta_loc_extract)} new location entries.")

        delta_loc_df = pd.DataFrame(data=delta_loc_extract, columns=delta_loc_cols)

        return delta_loc_df

    def transform(self, delta_loc_df: pd.DataFrame) -> pd.DataFrame:
        """Transforms the extracted DataFrame, if applicable.

        Args:
            delta_loc_df (pd.DataFrame): DataFrame containing extracted location entries.

        Returns:
            pd.DataFrame: DataFrame with transformed, unique location entries.
        """
        if delta_loc_df.empty:
            logger.info(f"No location entry to be transformed.")
            return pd.DataFrame()

        else:
            logger.info(f"Transforming new location entries.")

            location_data = []
            for _, row in delta_loc_df.iterrows():
                location = Location(row.country)

                location_data.append({
                    "country_code": location.country_code,
                    "country_name": location.country_name,
                    "continent": location.continent
                })

            loc_df = pd.DataFrame(data=location_data, columns=list(location_data[0].keys()))
            unique_loc_df = loc_df[loc_df.duplicated() == False]

            logger.info(f"Transformed {len(unique_loc_df)} new, unique location entries.")

            return unique_loc_df.reindex()

    def load(self, unique_loc_df: pd.DataFrame) -> None:
        """Loads the transformed DataFrame into the PostgreSQL database.

        Args:
            unique_loc_df (pd.DataFrame): DataFrame containing unique location entries to load.
        """
        unique_countries = unique_loc_df[unique_loc_df.duplicated() == False]

        with self.psql_connection as conn:
            with conn.cursor() as cur:
                # Check for new entries before loading.
                if self._get_delta_load_count(cur) == 0:
                    logger.info(f"Skipping insertion as there is no new entry.")
                else:
                    logger.info(f"Starting insertion into tables.")

                    logger.info(f"\t'{tables.DIM_LOCATION_TABLE}'")
                    for _, row in unique_countries.iterrows():
                        cur.execute(dl_queries.LOCATION_INSERT_CMD.format(
                            columns=f"{', '.join(unique_countries.columns)}",
                            values=f"{"', '".join([t for t in row.values])}",
                            country_name=row.country_name
                        ))

                    logger.info(f"\t'{tables.DIM_ITEM_TABLE}'")
                    cur.execute(dl_queries.ITEM_INSERT_CMD)

                    logger.info(f"\t'{tables.DIM_DATE_TABLE}'")
                    cur.execute(dl_queries.DATE_INSERT_CMD)

                    # Commit changes to be available for the fact table.
                    conn.commit()

                    logger.info(f"\t'{tables.FACT_TRANSLATION_TABLE}'")
                    cur.execute(dl_queries.FACT_INSERT_CMD)

                    logger.info(f"Insertion finished.")

def main():
    """Main entry point for the script.
    Creates an instance of DeltaLoader and runs the ETL process.
    """
    DeltaLoader().run()

if __name__ == "__main__":
    main()
