import os
import shutil


def clean_subdirs(root_dir):
    """This function cleans all sub-directories under the specified root directory.

    Inputs:
        - root_dir: Absolute path to the root directory of interest [string]
    """

    # Find all the files and directories of interest
    root_sub_dir = True
    for root, dir_names, file_names in os.walk(root_dir):
        # Update the dir list only the first time
        if root_sub_dir:
            # Remove .scrub from the list, if it exists
            if '.scrub' in dir_names:
                dir_names.remove('.scrub')

            # Update the flag
            root_sub_dir = False

        # Remove any .scrub directories
        for dir_name in dir_names:
            if '.scrub' in dir_name:
                dir_path = os.path.join(root, dir_name)
                shutil.rmtree(dir_path)


def clean_directory(directory):
    """This function removes previous SCRUB data products.

    Inputs:
        - directory: Full path to the top-level source code directory [string]
    """

    # Remove the root directory
    if os.path.exists(directory + '/.scrub'):
        shutil.rmtree(directory + '/.scrub')

    # Remove all of the sub-directories
    clean_subdirs(directory)
