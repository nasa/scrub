import os
import logging
import traceback
from scrub.tools.compiler import get_gbuild_warnings
from scrub.utils import scrub_utilities

VALID_TAGS = ['gbuild', 'dblchk', 'doublecheck']


def initialize_analysis(tool_conf_data):
    """The purpose of this function is to prepare the tool to perform analysis.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Initialize the derived variables
    gbuild_log_file = os.path.normpath(tool_conf_data.get('scrub_log_dir') + '/gbuild.log')
    compiler_analysis_dir = os.path.normpath(tool_conf_data.get('scrub_working_dir') + '/compiler_analysis')
    gbuild_output_file = os.path.normpath(compiler_analysis_dir + '/gbuild_build.log')
    compiler_raw_warning_file = os.path.normpath(tool_conf_data.get('raw_results_dir') + '/gbuild_compiler_raw.scrub')
    compiler_filtered_warning_file = os.path.normpath(tool_conf_data.get('scrub_working_dir') + '/compiler.scrub')

    # Add derived values to the dictionary
    tool_conf_data.update({'compiler_analysis_dir': compiler_analysis_dir})
    tool_conf_data.update({'gbuild_log_file': gbuild_log_file})
    tool_conf_data.update({'gbuild_output_file': gbuild_output_file})
    tool_conf_data.update({'compiler_raw_warning_file': compiler_raw_warning_file})
    tool_conf_data.update({'compiler_filtered_warning_file': compiler_filtered_warning_file})

    if tool_conf_data.get('source_lang').lower() != 'c':
        tool_conf_data.update({'gbuild_warnings': False})

    # Make sure all the needed variables are present
    if not (tool_conf_data.get('gbuild_build_cmd') and tool_conf_data.get('gbuild_clean_cmd')):
        # Update the analysis flag if necessary
        if tool_conf_data.get('gbuild_warnings'):
            tool_conf_data.update({'gbuild_warnings': False})

            # Print a status message
            print('\nWARNING: Unable to perform GBUILD analysis. Required configuration inputs are missing.\n')


def perform_analysis(tool_conf_data):
    """This function runs the analysis tool.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Change directory if necessary
    if tool_conf_data.get('gbuild_build_dir') != os.getcwd():
        # Navigate to the compilation directory
        logging.info('\tChanging directory: %s', tool_conf_data.get('gbuild_build_dir'))
        os.chdir(tool_conf_data.get('gbuild_build_dir'))

    # Clean the previous build
    call_string = tool_conf_data.get('gbuild_clean_cmd')
    scrub_utilities.execute_command(call_string, os.environ.copy())

    # Run the build command
    call_string = tool_conf_data.get('gbuild_build_cmd')
    scrub_utilities.execute_command(call_string, os.environ.copy(), tool_conf_data.get('gbuild_output_file'))

    # Update the permissions of the log file
    os.chmod(tool_conf_data.get('gbuild_log_file'), 438)


def post_process_analysis(tool_conf_data):
    """This function post-processes results from the analysis tool.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Get the warnings from the log file
    get_gbuild_warnings.parse_warnings(tool_conf_data.get('gbuild_output_file'),
                                       tool_conf_data.get('compiler_raw_warning_file'))


def run_analysis(baseline_conf_data, override=False):
    """This function handles performing gbuild compiler analysis.

    Inputs:
        - baseline_conf_data: Dictionary of raw scrub.cfg configuration parameters [dict]
        - override: Override the automatic checks to see if analysis should be performed? [optional] [bool]

    Outputs:
        - compiler_analysis/gbuild_build.log: File containing raw output from gbuild compilation
        - log_files/gbuild.log: File containing the log information from gbuild compiler analysis
        - raw_results/gbuild_compiler_raw.scrub: SCRUB-formatted results file containing raw gbuild compiler results
        - raw_results/gbuild_compiler_raw.sarif: SARIF-formatted results file containing raw gbuild compiler results
    """

    # Import the config data
    tool_conf_data = baseline_conf_data.copy()
    initialize_analysis(tool_conf_data)

    # Initialize the config file data
    attempt_analysis = tool_conf_data.get('gbuild_warnings') or override
    gbuild_exit_code = 2
    initial_dir = os.getcwd()

    # Run gbuild analysis?
    if attempt_analysis:
        try:
            # Create the analysis directory if it doesn't exist
            if not os.path.exists(tool_conf_data.get('compiler_analysis_dir')):
                os.mkdir(tool_conf_data.get('compiler_analysis_dir'))

            # Create the logger
            scrub_utilities.create_logger(tool_conf_data.get('gbuild_log_file'))

            # Print a status message
            logging.info('')
            logging.info('Perform GBUILD compiler analysis...')

            # Perform the analysis
            perform_analysis(tool_conf_data)

            # Post-process the analysis
            post_process_analysis(tool_conf_data)

            # Set the exit code
            gbuild_exit_code = 0

        except scrub_utilities.CommandExecutionError:
            # Print a warning message
            logging.warning('GBUILD analysis could not be performed. Please see log file {} for '
                            'more information.'.format(tool_conf_data.get('gbuild_log_file')))

            # Print the exception traceback
            logging.warning(traceback.format_exc())

            # Set the exit code
            gbuild_exit_code = 1

        except:     # lgtm [py/catch-base-exception]
            # Print a warning message
            logging.error('A SCRUB error has occurred. Please see log file {} for more '
                          'information.'.format(tool_conf_data.get('gbuild_log_file')))

            # Print the exception traceback
            logging.error(traceback.format_exc())

            # Set the exit code
            gbuild_exit_code = 100

        finally:
            # Change back to the initial dir if necessary
            if os.getcwd() != initial_dir:
                logging.info('\tChanging directory: %s', initial_dir)
                os.chdir(initial_dir)

            # Close the loggers
            logging.getLogger().handlers = []

    # Return the exit code
    return gbuild_exit_code
