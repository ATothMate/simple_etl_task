#!/usr/bin/env python3

import argparse
from pathlib import Path
from shutil import move
from typing import List, Optional, Tuple

from sdu_qm_task.logger_conf import get_logger

logger = get_logger(__file__)

# Define the base folder path relative to this script's location.
BASE_FOLDER = Path(__file__).parents[2]

# Log message template for moving files.
MOVE_INFO = "Moving source file: '{{src}}' to destination '{{dst}}'."


def parse_arguments() -> Tuple[str, str]:
    """Parses command line arguments to retrieve source and destination folder paths.

    Returns:
        Tuple[str, str]: paths to the source and destination folders.
    """
    parser = argparse.ArgumentParser(
        description=(
            "A script to handle the automatic relocation of the source file(s),"
            " imitating the real world."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "-s", "--source_folder",
        type=str,
        default=Path(BASE_FOLDER, "data_folder_source").as_posix(),
        help="path/to/the source folder."
    )
    parser.add_argument(
        "-d", "--destination_folder",
        type=str,
        default=Path(BASE_FOLDER, "data_folder_monitor").as_posix(),
        help="path/to/the destination folder."
    )

    args = parser.parse_args()

    return args.source_folder, args.destination_folder


def get_available_files(folder: str) -> List[Path]:
    """Retrieves a sorted list of available CSV files in the specified folder.

    Args:
        folder (str): path to the folder to search for available files.

    Returns:
        List[Path]: sorted list of Path objects representing available CSV files.
    """
    return sorted(Path(folder).glob("*.csv"))


def get_next_file(folder: str) -> Optional[Path]:
    """Retrieves the next available CSV file from the specified folder.

    Args:
        folder (str): path to the folder to search for available files.

    Returns:
        Optional[Path]: Path of the next available file, if applicable, otherwise None.
    """
    available_files = get_available_files(folder)

    if len(available_files) > 0:
        logger.info(f"Feeding the next file: {available_files[0].resolve().as_posix()}.")
        return available_files[0].resolve()
    else:
        return None


def move_file(src_file: Path, dst_folder: Path) -> None:
    """Moves the specified source file to the destination folder.

    Args:
        src_file (Path): source file to move.
        dst_folder (Path): destination folder to move the file to.
    """
    dst_file = Path(dst_folder, src_file.name).resolve()
    logger.info(MOVE_INFO.format(src=src_file.as_posix(), dst=dst_file.as_posix()))

    move(src_file, dst_file)


def main(src_folder: str, dest_folder: str) -> None:
    """Main function to handle the relocation of source files.

    Args:
        src_folder (str): path to the source folder.
        dest_folder (str): path to the destination folder.

    Raises:
        ValueError: raised if source file does not exist.
    """
    if not Path(src_folder).exists():
        raise ValueError("Source folder does not exist: '{src_folder}'!")

    if not Path(dest_folder).exists():
        logger.warning("Monitor (destination) folder does not exist!")
        Path(dest_folder).mkdir(parents=True, exist_ok=True)
        logger.info(f"Monitor (destination) folder created: {dest_folder}")

    logger.info(f"Looking for available source file in: {src_folder}")
    next_file = get_next_file(folder=src_folder)

    if next_file is not None:
        move_file(src_file=next_file, dst_folder=dest_folder)
    else:
        logger.info("Found no processable file.")


if __name__ == "__main__":
    # Parse command line arguments for source and destination folders.
    src_folder, dest_folder = parse_arguments()

    main(src_folder, dest_folder)
