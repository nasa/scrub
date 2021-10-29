import re
import os
import glob
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
    warning_type = warning_file.split(os.sep)[-1].strip()

    # Print a status message
    logging.info('')
    logging.info('\tMoving results...')
    logging.info('\t>> Executing command: do_gui.distribute_warnings(%s, %s)', warning_file, source_dir)
    logging.info('\t>> From directory: %s', os.getcwd())

    # Import the warning file
    with open(warning_file, 'r') as input_fh:
        input_data = input_fh.readlines()

    # Update the source root to make it absolute
    source_dir = os.path.abspath(source_dir)

    # Iterate through every line of the file
    for i in range(0, len(input_data)):
        # Set the line
        line = input_data[i]

        # Check to see if the line contains a warning
        if re.search(r'<.*>.*:.*:.*:', line):
            # Add the line to the warning text
            warning = line

            # Get the warning file
            warning_file = line.split(":")[1].strip()
            warning_file_absolute = os.path.normpath(source_dir + '/' + warning_file)

            # Make sure the warning file is within the source root, but not at the source root
            if os.path.exists(warning_file_absolute) and (source_dir != os.path.dirname(warning_file_absolute)):
                # Get the rest of the warning text
                j = i + 1
                while input_data[j].strip() != '':
                    warning = warning + input_data[j]

                    # Increment the line
                    j = j + 1

                # Get the warning directory
                warning_directory = os.path.dirname(warning_file_absolute)

                # Create the scrub output paths
                local_scrub_directory = os.path.normpath(warning_directory + '/.scrub')
                local_scrub_warning_file = os.path.normpath(local_scrub_directory + '/' + warning_type)

                # Create a .scrub directory if it doesn't already exists
                if not os.path.exists(local_scrub_directory):
                    os.mkdir(local_scrub_directory)
                    os.chmod(local_scrub_directory, 511)

                # Write the warning to the output file
                with open(local_scrub_warning_file, 'a') as output_fh:
                    output_fh.write('%s\n' % (warning.replace(warning_file, os.path.basename(warning_file))))

                # Change the permissions of the output file
                os.chmod(local_scrub_warning_file, 438)


def initialize_analysis(tool_conf_data):
    """The purpose of this function is to prepare the tool to perform analysis.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Initialize the derived variables
    gui_log_file = os.path.normpath(tool_conf_data.get('scrub_log_dir') + '/gui.log')

    # Add derived values to the dictionary
    tool_conf_data.update({'gui_log_file': gui_log_file})


def run_analysis(baseline_conf_data, override=False):
    """This function runs this module based on input from the scrub.cfg file

    Inputs:
        - baseline_conf_data: Dictionary of raw scrub.cfg configuration parameters [dict]
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
            scrub_utilities.create_logger(tool_conf_data.get('gui_log_file'))

            # Print a status message
            logging.info('')
            logging.info('Perform GUI export...')

            # Get a list of the filtered SCRUB output files
            filtered_output_files = glob.glob(tool_conf_data.get('scrub_analysis_dir') + '/*.scrub')

            # Move the warnings to the appropriate directories
            for filtered_output_file in filtered_output_files:
                distribute_warnings(filtered_output_file, tool_conf_data.get('source_dir'))

            # Set the exit code
            gui_exit_code = 0

        except:     # lgtm [py/catch-base-exception]
            # Print a warning message
            logging.warning('GUI export could not be performed. Please see log file %s for more information.',
                            tool_conf_data.get('gui_log_file'))

            # Print the exception traceback
            logging.warning(traceback.format_exc())

            # Set the exit code
            gui_exit_code = 1

        finally:
            # Close the loggers
            logging.getLogger().handlers = []

            # Update the permissions of the log file if it exists
            if os.path.exists(tool_conf_data.get('gui_log_file')):
                os.chmod(tool_conf_data.get('gui_log_file'), 438)

    # Return the exit code
    return gui_exit_code
