import pathlib
import shutil


def clean_subdirs(root_dir):
    """This function cleans all sub-directories under the specified root directory.

    Inputs:
        - root_dir: Absolute path to the root directory of interest [string]
    """

    # Find all the files and directories of interest
    for scrub_dir in list(root_dir.rglob('.scrub')):
        if scrub_dir != root_dir.joinpath('.scrub'):
            shutil.rmtree(scrub_dir)


def clean_directory(directory):
    """This function removes previous SCRUB data products.

    Inputs:
        - directory: Full path to the top-level source code directory [string]
    """

    # Print a status message
    print('\tRemoving previous SCRUB results from source tree...\n')

    # Remove the root directory
    if directory.joinpath('.scrub').exists():
        shutil.rmtree(directory.joinpath('.scrub'))

    # Remove all of the sub-directories
    clean_subdirs(directory)
