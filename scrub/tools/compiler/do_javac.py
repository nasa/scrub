import os
import logging
import traceback
from scrub.tools.compiler import get_javac_warnings
from scrub.utils import scrub_utilities

VALID_TAGS = ['compiler', 'cmp', 'javac']


def initialize_analysis(tool_conf_data):
    """The purpose of this function is to prepare the tool to perform analysis.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Initialize the derived variables
    javac_log_file = os.path.normpath(tool_conf_data.get('scrub_log_dir') + '/javac.log')
    compiler_analysis_dir = os.path.normpath(tool_conf_data.get('scrub_working_dir') + '/compiler_analysis')
    javac_output_file = os.path.normpath(compiler_analysis_dir + '/javac_build.log')
    compiler_raw_warning_file = os.path.normpath(tool_conf_data.get('raw_results_dir') + '/javac_compiler_raw.scrub')
    compiler_filtered_warning_file = os.path.normpath(tool_conf_data.get('scrub_working_dir') + '/compiler.scrub')

    # Add derived values to the dictionary
    tool_conf_data.update({'compiler_analysis_dir': compiler_analysis_dir})
    tool_conf_data.update({'javac_log_file': javac_log_file})
    tool_conf_data.update({'javac_output_file': javac_output_file})
    tool_conf_data.update({'compiler_raw_warning_file': compiler_raw_warning_file})
    tool_conf_data.update({'compiler_filtered_warning_file': compiler_filtered_warning_file})

    # Remove the existing artifacts
    if os.path.exists(javac_log_file):
        os.remove(javac_log_file)

    # Check to make sure the language is Java
    if tool_conf_data.get('source_lang').lower() != 'j':
        tool_conf_data.update({'javac_warnings': False})

    # Make sure all the needed variables are present
    if not (tool_conf_data.get('javac_build_cmd') and tool_conf_data.get('javac_clean_cmd')):
        # Update the analysis flag if necessary
        if tool_conf_data.get('javac_warnings'):
            tool_conf_data.update({'javac_warnings': False})

            # Print a status message
            print('\nWARNING: Unable to perform JAVAC analysis. Required configuration inputs are missing.\n')


def perform_analysis(tool_conf_data):
    """This function runs the analysis tool.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Change directory if necessary
    if tool_conf_data.get('javac_build_dir') != os.getcwd():
        # Navigate to the compilation directory
        logging.info('\tChanging directory: %s', tool_conf_data.get('javac_build_dir'))
        os.chdir(tool_conf_data.get('javac_build_dir'))

    # Clean the previous build
    call_string = tool_conf_data.get('javac_clean_cmd')
    scrub_utilities.execute_command(call_string, os.environ.copy())

    # Run the build command
    call_string = tool_conf_data.get('javac_build_cmd')
    scrub_utilities.execute_command(call_string, os.environ.copy(), tool_conf_data.get('javac_output_file'))

    # Update the permissions of the log file
    os.chmod(tool_conf_data.get('javac_output_file'), 438)


def post_process_analysis(tool_conf_data):
    """This function post-processes results from the analysis tool.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Get the warnings from the log file
    get_javac_warnings.parse_warnings(tool_conf_data.get('javac_output_file'),
                                      tool_conf_data.get('compiler_raw_warning_file'))


def run_analysis(baseline_conf_data, override=False):
    """This function handles performing javac compiler analysis.

    Inputs:
        - baseline_conf_data: Dictionary of raw scrub.cfg configuration parameters [dict]
        - override: Override the automatic checks to see if analysis should be performed? [optional] [bool]

    Outputs:
        - compiler_analysis/javac_build.log: File containing raw output from javac compilation
        - log_files/javac.log: File containing the log information from javac compiler analysis
        - raw_results/javac_compiler_raw.scrub: SCRUB-formatted results file containing raw javac compiler results
        - raw_results/javac_compiler_raw.sarif: SARIF-formatted results file containing raw javac compiler results
    """

    # Import the config data
    tool_conf_data = baseline_conf_data.copy()
    initialize_analysis(tool_conf_data)

    # Initialize variables
    javac_exit_code = 2
    initial_dir = os.getcwd()
    attempt_analysis = tool_conf_data.get('javac_warnings') or override

    # Run JAVAC analysis?
    if attempt_analysis:
        try:
            # Create the analysis directory if it doesn't exist
            if not os.path.exists(tool_conf_data.get('compiler_analysis_dir')):
                os.mkdir(tool_conf_data.get('compiler_analysis_dir'))

            # Create the logger
            scrub_utilities.create_logger(tool_conf_data.get('javac_log_file'))

            # Print a status message
            logging.info('')
            logging.info('Perform JAVAC compiler analysis...')

            # Perform the analysis
            perform_analysis(tool_conf_data)

            # Post-process the analysis
            post_process_analysis(tool_conf_data)

            # Set the exit code
            javac_exit_code = 0

        except scrub_utilities.CommandExecutionError:
            # Print a warning message
            logging.warning('JAVAC analysis could not be performed. Please see log file {} for '
                            'more information.'.format(tool_conf_data.get('javac_log_file')))

            # Print the exception traceback
            logging.warning(traceback.format_exc())

            # Set the exit code
            javac_exit_code = 1

        except:     # lgtm [py/catch-base-exception]
            # Print a warning message
            logging.error('A SCRUB error has occurred. Please see log file {} for more '
                          'information.'.format(tool_conf_data.get('javac_log_file')))

            # Print the exception traceback
            logging.error(traceback.format_exc())

            # Set the exit code
            javac_exit_code = 100

        finally:
            # Change back to the initial dir if necessary
            if os.getcwd() != initial_dir:
                logging.info('\tChanging directory: %s', initial_dir)
                os.chdir(initial_dir)

            # Close the loggers
            logging.getLogger().handlers = []

    # Return the exit code
    return javac_exit_code
