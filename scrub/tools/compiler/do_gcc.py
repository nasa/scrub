import os
import logging
import traceback
from scrub.tools.compiler import get_gcc_warnings
from scrub.utils import scrub_utilities

VALID_TAGS = ['compiler', 'cmp', 'gcc']


def initialize_analysis(tool_conf_data):
    """The purpose of this function is to prepare the tool to perform analysis.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Initialize the derived variables
    gcc_log_file = os.path.normpath(tool_conf_data.get('scrub_log_dir') + '/gcc.log')
    compiler_analysis_dir = os.path.normpath(tool_conf_data.get('scrub_working_dir') + '/compiler_analysis')
    gcc_output_file = os.path.normpath(compiler_analysis_dir + '/gcc_build.log')
    compiler_raw_warning_file = os.path.normpath(tool_conf_data.get('raw_results_dir') + '/gcc_compiler_raw.scrub')
    compiler_filtered_warning_file = os.path.normpath(tool_conf_data.get('scrub_working_dir') + '/compiler.scrub')

    # Add derived values to the dictionary
    tool_conf_data.update({'compiler_analysis_dir': compiler_analysis_dir})
    tool_conf_data.update({'gcc_log_file': gcc_log_file})
    tool_conf_data.update({'gcc_output_file': gcc_output_file})
    tool_conf_data.update({'compiler_raw_warning_file': compiler_raw_warning_file})
    tool_conf_data.update({'compiler_filtered_warning_file': compiler_filtered_warning_file})

    # Make the compilation directory absolute
    if tool_conf_data.get('gcc_build_dir') == '':
        tool_conf_data.update({'gcc_build_dir': tool_conf_data.get('source_dir')})
    elif not tool_conf_data.get('gcc_build_dir').startswith(tool_conf_data.get('source_dir')):
        tool_conf_data.update({'gcc_build_dir': os.path.abspath(tool_conf_data.get('source_dir') + '/' +
                                                                tool_conf_data.get('gcc_build_dir'))})

    # Check to make sure the language is C
    if tool_conf_data.get('source_lang').lower() != 'c':
        tool_conf_data.update({'gcc_warnings': False})

    # Make sure all the needed variables are present
    if not (tool_conf_data.get('gcc_build_cmd') and tool_conf_data.get('gcc_clean_cmd')):
        # Update the analysis flag if necessary
        if tool_conf_data.get('gcc_warnings'):
            tool_conf_data.update({'gcc_warnings': False})

            # Print a status message
            print('\nWARNING: Unable to perform GCC analysis. Required configuration inputs are missing.\n')


def perform_analysis(tool_conf_data):
    """This function runs the analysis tool.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Change directory if necessary
    if tool_conf_data.get('gcc_build_dir') != os.getcwd():
        # Navigate to the compilation directory
        logging.info('\tChanging directory: %s', tool_conf_data.get('gcc_build_dir'))
        os.chdir(tool_conf_data.get('gcc_build_dir'))

    # Clean the previous build
    call_string = tool_conf_data.get('gcc_clean_cmd')
    scrub_utilities.execute_command(call_string, os.environ.copy())

    # Run the build command
    call_string = tool_conf_data.get('gcc_build_cmd')
    scrub_utilities.execute_command(call_string, os.environ.copy(), tool_conf_data.get('gcc_output_file'))

    # Update the permissions of the output file
    os.chmod(tool_conf_data.get('gcc_output_file'), 438)


def post_process_analysis(tool_conf_data):
    """This function post-processes results from the analysis tool.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Get the warnings from the log file
    get_gcc_warnings.parse_warnings(tool_conf_data.get('gcc_output_file'),
                                    tool_conf_data.get('compiler_raw_warning_file'))


def run_analysis(baseline_conf_data, override=False):
    """This function handles performing gcc compiler analysis.

    Inputs:
        - baseline_conf_data: Dictionary of raw scrub.cfg configuration parameters [dict]
        - override: Override the automatic checks to see if analysis should be performed? [optional] [bool]

    Outputs:
        - compiler_analysis/gcc_build.log: File containing raw output from gcc compilation
        - log_files/gcc.log: File containing the log information from gcc compiler analysis
        - raw_results/gcc_compiler_raw.scrub: SCRUB-formatted results file containing raw gcc compiler results
        - raw_results/gcc_compiler_raw.sarif: SARIF-formatted results file containing raw gcc compiler results
    """

    # Import the config file data
    tool_conf_data = baseline_conf_data.copy()
    initialize_analysis(tool_conf_data)

    # Initialize variables
    initial_dir = os.getcwd()
    gcc_exit_code = 2
    attempt_analysis = tool_conf_data.get('gcc_warnings') or override

    # Run GCC analysis?
    if attempt_analysis:
        try:
            # Create the analysis directory if it doesn't exist
            if not os.path.exists(tool_conf_data.get('compiler_analysis_dir')):
                os.mkdir(tool_conf_data.get('compiler_analysis_dir'))

            # Create the logger
            scrub_utilities.create_logger(tool_conf_data.get('gcc_log_file'))

            # Print a status message
            logging.info('')
            logging.info('Perform GCC compiler analysis...')

            # Perform the analysis
            perform_analysis(tool_conf_data)

            # Post-process the analysis
            post_process_analysis(tool_conf_data)

            # Set the exit code
            gcc_exit_code = 0

        except scrub_utilities.CommandExecutionError:
            # Print a warning message
            logging.warning('GCC analysis could not be performed. Please see log file {} for '
                            'more information.'.format(tool_conf_data.get('gcc_log_file')))

            # Print the exception traceback
            logging.warning(traceback.format_exc())

            # Set the exit code
            gcc_exit_code = 1

        except:     # lgtm [py/catch-base-exception]
            # Print a warning message
            logging.error('A SCRUB error has occurred. Please see log file {} for more '
                          'information.'.format(tool_conf_data.get('gcc_log_file')))

            # Print the exception traceback
            logging.error(traceback.format_exc())

            # Set the exit code
            gcc_exit_code = 100

        finally:
            # Change back to the initial dir if necessary
            if os.getcwd() != initial_dir:
                logging.info('\tChanging directory: %s', tool_conf_data.get('source_dir'))
                os.chdir(tool_conf_data.get('source_dir'))

            # Close the loggers
            logging.getLogger().handlers = []

    # Return the exit code
    return gcc_exit_code
