"""
Reset project to a clean state, with safety checks.
"""
import shutil
from pathlib import Path

import click

from odp_platform.common.logging_utils import get_logger
from odp_platform.common.paths import get_dirs_to_reset, is_protected

logger = get_logger(__name__)


@click.command()
@click.option(
    "--force",
    is_flag=True,
    help="Skip confirmation prompt",
)
def main(force: bool) -> None:
    """
    Reset the project to a clean state.

    Deletes generated files and directories while protecting critical ones.
    """
    project_root = Path.cwd()

    # Get list of dirs that are safe to delete
    dirs_to_reset = get_dirs_to_reset()

    if not dirs_to_reset:
        logger.warning("No directories marked for reset.")
        return

    # Show what will be deleted
    logger.info("Directories that will be reset:")
    for dir_name in dirs_to_reset:
        logger.info(f"  - {dir_name}")

    if not force:
        click.confirm("Continue?", abort=True)

    # Delete each directory
    for dir_name in dirs_to_reset:
        dir_path = project_root / dir_name

        # Double-check it's not protected
        if is_protected(dir_path):
            logger.error(f"Skipping protected directory: {dir_path}")
            continue

        if dir_path.exists():
            logger.info(f"Deleting {dir_path}...")
            shutil.rmtree(dir_path)
        else:
            logger.debug(f"Directory not found: {dir_path}")

    logger.info("✓ Reset complete")


if __name__ == "__main__":
    main()