import os
import logging
import traceback
import shutil
from scrub.utils import scrub_utilities

VALID_TAGS = ['custom', 'cust']


def initialize_analysis(tool_conf_data):
    """The purpose of this function is to prepare the tool to perform analysis.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Initialize the derived variables
    custom_log_file = os.path.normpath(tool_conf_data.get('scrub_log_dir') + '/custom.log')
    custom_analysis_dir = os.path.normpath(tool_conf_data.get('scrub_working_dir') + '/custom_analysis')
    custom_raw_warning_file = os.path.normpath(tool_conf_data.get('raw_results_dir') + '/custom_raw.scrub')
    custom_filtered_warning_file = os.path.normpath(tool_conf_data.get('scrub_working_dir') + '/custom.scrub')

    # Create the custom output file if necessary
    if tool_conf_data.get('custom_output_file') == '':
        custom_output_file = os.path.normpath(custom_analysis_dir + '/custom.txt')
        tool_conf_data.update({'custom_output_file': custom_output_file})

    # Add derived values to the dictionary
    tool_conf_data.update({'custom_analysis_dir': custom_analysis_dir})
    tool_conf_data.update({'custom_log_file': custom_log_file})
    tool_conf_data.update({'custom_raw_warning_file': custom_raw_warning_file})
    tool_conf_data.update({'custom_filtered_warning_file': custom_filtered_warning_file})

    # Make the compilation directory absolute
    if tool_conf_data.get('custom_build_dir') == '':
        tool_conf_data.update({'custom_build_dir': tool_conf_data.get('source_dir')})
    elif not tool_conf_data.get('custom_build_dir').startswith(tool_conf_data.get('source_dir')):
        tool_conf_data.update({'custom_build_dir': os.path.abspath(tool_conf_data.get('source_dir') + '/' +
                                                                   tool_conf_data.get('custom_build_dir'))})

    # Make sure all the needed variables are present
    if not tool_conf_data.get('custom_cmd'):
        # Update the analysis flag if necessary
        if tool_conf_data.get('custom_warnings'):
            tool_conf_data.update({'custom_warnings': False})

            # Print a status message
            print('\nWARNING: Unable to perform custom analysis. Required configuration inputs are missing.\n')


def perform_analysis(tool_conf_data):
    """This function runs the analysis tool.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Change directory if necessary
    if tool_conf_data.get('custom_build_dir') != os.getcwd():
        # Navigate to the compilation directory
        logging.info('\tChanging directory: %s', tool_conf_data.get('custom_build_dir'))
        os.chdir(tool_conf_data.get('custom_build_dir'))

    # Execute the custom check command
    call_string = tool_conf_data.get('custom_cmd')
    scrub_utilities.execute_command(call_string, os.environ.copy(), tool_conf_data.get('custom_output_file'))


def post_process_analysis(tool_conf_data):
    """This function post-processes results from the analysis tool.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Copy the results to the proper directory
    if os.path.exists(tool_conf_data.get('custom_output_file')):
        shutil.copy(tool_conf_data.get('custom_output_file'), tool_conf_data.get('custom_raw_warning_file'))
    else:
        raise UserWarning


def run_analysis(baseline_conf_data, override=False):
    """This function handles performing custom analysis.

    Inputs:
        - baseline_conf_data: Dictionary of raw scrub.cfg configuration parameters [dict]
        - override: Force tool execution? [optional] [bool]

    Outputs:
        - log_file/custom.log: SCRUB log file for the custom analysis
        - raw_results/custom_raw.scrub: SCRUB-formatted results file containing raw custom results
        - raw_results/custom_raw.sarif: SARIF-formatted results file containing raw custom results
    """

    # Import the config data
    tool_conf_data = baseline_conf_data.copy()
    initialize_analysis(tool_conf_data)

    # Initialize the config file data
    custom_exit_code = 2
    initial_dir = os.getcwd()
    attempt_analysis = tool_conf_data.get('custom_warnings') or override

    if attempt_analysis:
        try:
            # Create the analysis directory if it doesn't exist
            if not os.path.exists(tool_conf_data.get('custom_analysis_dir')):
                os.mkdir(tool_conf_data.get('custom_analysis_dir'))

            # Create the logger
            scrub_utilities.create_logger(tool_conf_data.get('custom_log_file'))

            # Print a status message
            logging.info('')
            logging.info('Perform custom analysis...')

            # Perform the analysis
            perform_analysis(tool_conf_data)

            # Post-process the analysis
            post_process_analysis(tool_conf_data)

            # Set the exit code
            custom_exit_code = 0

        except scrub_utilities.CommandExecutionError:
            # Print a warning message
            logging.warning('Custom analysis could not be performed. Please see log file {} for '
                            'more information.'.format(tool_conf_data.get('custom_log_file')))

            # Print the exception traceback
            logging.warning(traceback.format_exc())

            # Set the exit code
            custom_exit_code = 1

        except:     # lgtm [py/catch-base-exception]
            # Print a warning message
            logging.error('A SCRUB error has occurred. Please see log file {} for more '
                          'information.'.format(tool_conf_data.get('custom_log_file')))

            # Print the exception traceback
            logging.error(traceback.format_exc())

            # Set the exit code
            custom_exit_code = 100

        finally:
            # Change back to the initial dir if necessary
            if os.getcwd() != initial_dir:
                logging.info('\tChanging directory: %s', initial_dir)
                os.chdir(initial_dir)

            # Close the loggers
            logging.getLogger().handlers = []

    # Return the exit code
    return custom_exit_code
