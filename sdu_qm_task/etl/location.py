#!/usr/bin/env python3

from typing import Tuple

import pycountry as pyc
import pycountry_convert as pyc_c

from sdu_qm_task.logger_conf import get_logger

logger = get_logger(__file__)


class Location():
    """Class to represent a geographical location and retrieve its details
    based on a provided country name.
    """
    def __init__(self, country_name: str) -> None:
        """Initializes the Location object.

        Args:
            country_name (str): name of the country to look up.
        """
        logger.debug(f"Initiated {self.__class__.__name__} class.")

        self.country_name_arg = country_name

        self.country_name, self.country_code, self.continent = self.get_location_info()

    @staticmethod
    def _code_to_continent(country_code_a2: str) -> str:
        """Converts a two-letter country code to its corresponding continent name.

        Args:
            country_code_a2 (str): two-letter country code (ISO 3166-1 alpha-2).

        Returns:
            str: name of the continent corresponding to the provided country code.
        """
        country_continent_code = pyc_c.country_alpha2_to_continent_code(country_code_a2)
        return pyc_c.convert_continent_code_to_continent_name(country_continent_code)

    def get_location_info(self) -> Tuple[str, str, str]:
        """Retrieves location information including the country name, country code, and continent.

        Returns:
            Tuple[str, str, str]: tuple of the country name, country code, and continent name.
        """
        try:
            info = pyc.countries.lookup(self.country_name_arg)
            country_code = info.alpha_3
            continent = self._code_to_continent(info.alpha_2)
            country_name = self.country_name_arg

        except LookupError:
            country_name = "UNKNOWN"
            country_code = "N/A"
            continent = "UNKNOWN"

            logger.warning(
                f"Lookup failed for country: '{self.country_name_arg}', marking it as 'UNKNOWN'"
            )

        return country_name, country_code, continent
