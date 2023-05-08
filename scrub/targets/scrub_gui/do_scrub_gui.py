import re
import pathlib
import logging
import traceback
from scrub.utils import scrub_utilities
from scrub.tools.parsers import translate_results


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
    distributed_files_list = []

    # Print a status message
    logging.info('')
    logging.info('\tMoving results...')
    logging.info('\t>> Executing command: do_gui.distribute_warnings(%s, %s)', str(warning_file), str(source_dir))
    logging.info('\t>> From directory: %s', str(pathlib.Path().absolute()))

    # Update the source root to make it absolute
    source_dir = source_dir.resolve()

    # Parse all the findings from the warning file
    warnings = translate_results.parse_scrub(warning_file, source_dir)

    # Iterate through everything warning
    for warning in warnings:
        # Make sure the warning file is within the source root, but not at the source root
        if warning['file'].exists() and (source_dir != warning['file'].parent):
            # Get the warning directory
            warning_directory = warning['file'].parent

            # Create the scrub output paths
            local_scrub_directory = warning_directory.joinpath('.scrub')
            local_scrub_warning_file = local_scrub_directory.joinpath(warning_type + '.scrub')

            # Create a .scrub directory if it doesn't already exists
            if not local_scrub_directory.exists():
                local_scrub_directory.mkdir()
                local_scrub_directory.chmod(0o755)

            # Write the warning to the output file
            with open(local_scrub_warning_file, 'a') as output_fh:
                output_fh.write('%s' % translate_results.format_scrub_warning(warning))

            # Add the file to the list if it hasn't been added already
            if local_scrub_warning_file not in distributed_files_list:
                distributed_files_list.append(local_scrub_warning_file)

            # Change the permissions of the output file
            local_scrub_warning_file.chmod(0o644)

    return distributed_files_list


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
                distributed_files = distribute_warnings(filtered_output_file, tool_conf_data.get('source_dir'))

                # Check each of the generated files for formatting
                for distributed_file in distributed_files:
                    if len(translate_results.parse_scrub(distributed_file, tool_conf_data.get('source_dir'))) == 0:
                        raise AssertionError

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
                tool_conf_data.get('gui_log_file').chmod(0o644)

    # Return the exit code
    return gui_exit_code
