import re
import glob
import pathlib
import logging
import traceback
from scrub.utils import scrub_utilities


def distribute_warnings(warning_file, source_dir):
    """This function moves warnings to be co-located with the source file of interest.

    Inputs:
        - warning_file: Full path to the file containing SCRUB-formatted warnings [string]
        - source_dir: Full path to the top-level directory of the source code [string]

    Outputs:
        - A series of .scrub directories and output files will be created as necessary
    """

    # Initialize the variables
    warning_type = warning_file.stem

    # Print a status message
    logging.info('')
    logging.info('\tMoving results...')
    logging.info('\t>> Executing command: do_gui.distribute_warnings(%s, %s)', str(warning_file), str(source_dir))
    logging.info('\t>> From directory: %s', str(pathlib.Path().absolute()))

    # Import the warning file
    with open(warning_file, 'r') as input_fh:
        input_data = input_fh.readlines()

    # Update the source root to make it absolute
    source_dir = source_dir.resolve()

    # Iterate through every line of the file
    for i in range(0, len(input_data)):
        # Set the line
        line = input_data[i]

        # Check to see if the line contains a warning
        if re.search(r'<.*>.*:.*:.*:', line):
            # Add the line to the warning text
            warning = line

            # Get the warning file
            warning_file = pathlib.Path(line.split(":")[1].strip())
            warning_file_absolute = source_dir.joinpath(warning_file)

            # Make sure the warning file is within the source root, but not at the source root
            if warning_file_absolute.exists() and (source_dir != warning_file_absolute.parent):
                # Get the rest of the warning text
                j = i + 1
                while input_data[j].strip() != '':
                    warning = warning + input_data[j]

                    # Increment the line
                    j = j + 1

                # Get the warning directory
                warning_directory = warning_file_absolute.parent

                # Create the scrub output paths
                local_scrub_directory = warning_directory.joinpath('.scrub')
                local_scrub_warning_file = local_scrub_directory.joinpath(warning_type)

                # Create a .scrub directory if it doesn't already exists
                if not local_scrub_directory.exists():
                    local_scrub_directory.mkdir(mode=511)

                # Write the warning to the output file
                with open(local_scrub_warning_file, 'a') as output_fh:
                    output_fh.write('%s\n' % warning_file.name)

                # Change the permissions of the output file
                local_scrub_warning_file.chmod(0o666)


def initialize_analysis(tool_conf_data):
    """The purpose of this function is to prepare the tool to perform analysis.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Initialize the derived variables
    gui_log_file = tool_conf_data.get('scrub_log_dir').joinpath('gui.log')

    # Add derived values to the dictionary
    tool_conf_data.update({'gui_log_file': gui_log_file})


def run_analysis(baseline_conf_data, console_logging=logging.INFO, override=False):
    """This function runs this module based on input from the scrub.cfg file

    Inputs:
        - baseline_conf_data: Dictionary of raw scrub.cfg configuration parameters [dict]
        - console_logging: Level of console logging information to print to console [optional] [enum]
        - override: Force tool execution? [optional] [bool]
    """

    # Import the config file data
    tool_conf_data = baseline_conf_data.copy()
    initialize_analysis(tool_conf_data)

    # Initialize variables
    gui_exit_code = 2
    attempt_analysis = tool_conf_data.get('scrub_gui_export') or override

    # Determine if GUI export can be run
    if attempt_analysis:
        try:
            # Create the logging file, if it doesn't already exist
            scrub_utilities.create_logger(tool_conf_data.get('gui_log_file'), console_logging)

            # Print a status message
            logging.info('')
            logging.info('Perform GUI export...')

            # Get a list of the filtered SCRUB output files
            filtered_output_files = tool_conf_data.get('scrub_analysis_dir').glob('*.scrub')

            # Move the warnings to the appropriate directories
            for filtered_output_file in filtered_output_files:
                distribute_warnings(filtered_output_file, tool_conf_data.get('source_dir'))

            # Set the exit code
            gui_exit_code = 0

        except:     # lgtm [py/catch-base-exception]
            # Print a warning message
            logging.warning('GUI export could not be performed. Please see log file %s for more information.',
                            str(tool_conf_data.get('gui_log_file')))

            # Print the exception traceback
            logging.warning(traceback.format_exc())

            # Set the exit code
            gui_exit_code = 1

        finally:
            # Close the loggers
            logging.getLogger().handlers = []

            # Update the permissions of the log file if it exists
            if tool_conf_data.get('gui_log_file').exists():
                tool_conf_data.get('gui_log_file').chmod(0o666)

    # Return the exit code
    return gui_exit_code
