#!/usr/bin/env python3

import os

import psycopg2

from sdu_qm_task.logger_conf import get_logger

logger = get_logger(__file__)


class PSQLConnection():
    """Context manager class for managing connections to a PostgreSQL database.
    """
    def __init__(
            self,
            dbname: str=None,
            user: str=None,
            password: str=None,
            host: str=None,
            port: str=None
        ) -> None:
        """Initializes the PSQLConnection class with database connection parameters.

        Args:
            dbname (str, optional): name of the database. Defaults to None.
            user (str, optional): database user. Defaults to None.
            password (str, optional): database password. Defaults to None.
            host (str, optional): database host. Defaults to None.
            port (str, optional): database port. Defaults to None.
        """
        logger.debug(f"Initiated {self.__class__.__name__} class.")

        self.dbname = dbname if dbname else os.environ.get("POSTGRES_DB")
        self.user = user if user else os.environ.get("POSTGRES_USER")
        self.password = password if password else os.environ.get("POSTGRES_PASSWORD")
        self.host = host if host else os.environ.get("POSTGRES_HOST")
        self.port = port if port else os.environ.get("POSTGRES_PORT")

        self.config = {
            "dbname": self.dbname,
            "user": self.user,
            "password": self.password,
            "host": self.host,
            "port": self.port
        }

    def __enter__(self) -> psycopg2.extensions.connection:
        """Establishes a connection to the PostgreSQL database when entering the context.

        Returns:
            psycopg2.extensions.connection: database connection object.
        """
        logger.info(f"Connecting to PostgreSQL database: {self.dbname}")
        return self.connect()

    def __exit__(self, exception_type, exception_value, exception_traceback) -> None:
        """Handles cleanup upon exiting the context.
        Commits any pending transactions and closes the connection.
        Logs the exception details if any occurred.

        Args:
            exception_type (_type_): type of exception, if occured.
            exception_value (_type_): value of exception, if occured.
            exception_traceback (_type_): trceback of exception, if occured.
        """
        if exception_type is not None:
            raise exception_type(
                f"{exception_type.__name__}: {exception_value}.\nTraceback: {exception_traceback}."
            )

        logger.info(f"Committing and closing connection for database: {self.dbname}")
        self.close()

    def _get_connection(self) -> psycopg2.extensions.connection:
        """Retrieves the current database connection.

        Returns:
            psycopg2.extensions.connection: current database connection.
        """
        return self.connection

    def connect(self) -> psycopg2.extensions.connection:
        """Establishes a connection to the PostgreSQL database.

        Returns:
            psycopg2.extensions.connection: established database connection.
        """
        self.connection = psycopg2.connect(**self.config)
        return self.connection

    def close(self) -> None:
        """Commits any pending transactions and closes the database connection.
        """
        connection = self._get_connection()
        connection.commit()
        connection.close()

    def get_connection_string(self) -> str:
        """Generates a PostgreSQL connection string.

        Returns:
            str: connection string formatted for PostgreSQL.
        """
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"
