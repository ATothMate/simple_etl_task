#!/usr/bin/env python3

import psycopg2
from typing import List

from sdu_qm_task.connect import PSQLConnection
from sdu_qm_task.logger_conf import get_logger
from sdu_qm_task.queries import create_table_queries as ct_queries

logger = get_logger(__file__)


class DBInitializer():
    """Class responsible for initializing the PostgreSQL database by creating
     the necessary tables.
    It executes a set of predefined SQL commands to set up the schema.
    """
    def __init__(self) -> None:
        """Initializes the DBInitializer class.
        """
        logger.debug(f"Initiated {self.__class__.__name__} class.")

        self.psql_connection = PSQLConnection()

    def _get_commands(self) -> List[str]:
        """Returns a list of predefined SQL commands to create the necessary tables.
        """
        return [
            ct_queries.CREATE_PRELOAD_TRANSACTION,
            ct_queries.CREATE_DIM_DATE,
            ct_queries.CREATE_DIM_ITEM,
            ct_queries.CREATE_DIM_LOCATION,
            ct_queries.CREATE_FACT_TRANSCTION
        ]

    def create_tables(self) -> None:
        """Executes the table creation commands in the PostgreSQL database.
        """
        commands = self._get_commands()

        try:
            with self.psql_connection as conn:
                with conn.cursor() as cur:
                    for command in commands:
                        logger.debug(command)
                        cur.execute(command)

        except (psycopg2.DatabaseError, Exception) as e:
            logger.exception(e)


def main():
    """Main entry point for the script.
    Creates an instance of DBInitializer and runs the create_tables method
     to set up the database schema.
    """
    DBInitializer().create_tables()


if __name__ == '__main__':
    main()
