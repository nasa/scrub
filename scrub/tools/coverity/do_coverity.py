import os
import shutil
import subprocess
import re
import logging
import traceback
from scrub.tools.coverity import get_coverity_warnings
from  scrub.utils import scrub_utilities

VALID_TAGS = ['coverity', 'cov']


def initialize_analysis(tool_conf_data):
    """The purpose of this function is to prepare the tool to perform analysis.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Initialize the derived variables
    coverity_log_file = os.path.normpath(tool_conf_data.get('scrub_log_dir') + '/coverity.log')
    coverity_analysis_dir = os.path.normpath(tool_conf_data.get('scrub_working_dir') + '/coverity_analysis')
    coverity_output_file = os.path.normpath(coverity_analysis_dir + '/coverity.out')
    coverity_raw_warning_file = os.path.normpath(tool_conf_data.get('raw_results_dir') + '/coverity_raw.scrub')
    coverity_filtered_warning_file = os.path.normpath(tool_conf_data.get('scrub_working_dir') + '/coverity.scrub')

    # Add derived values to the dictionary
    tool_conf_data.update({'coverity_log_file': coverity_log_file})
    tool_conf_data.update({'coverity_analysis_dir': coverity_analysis_dir})
    tool_conf_data.update({'coverity_output_file': coverity_output_file})
    tool_conf_data.update({'coverity_raw_warning_file': coverity_raw_warning_file})
    tool_conf_data.update({'coverity_filtered_warning_file': coverity_filtered_warning_file})

    # Remove any existing Coverity results
    if os.path.exists(coverity_analysis_dir):
        shutil.rmtree(coverity_analysis_dir)

    # Remove any existing raw Coverity data
    if os.path.exists(coverity_output_file):
        os.remove(coverity_output_file)

    # Determine if Coverity can be run
    if not (tool_conf_data.get('coverity_build_cmd') and tool_conf_data.get('coverity_clean_cmd')):
        # Update the analysis flag if necessary
        if tool_conf_data.get('coverity_warnings'):
            tool_conf_data.update({'coverity_warnings': False})

            # Print a status message
            print('\nWARNING: Unable to perform Coverity analysis. Required configuration inputs are missing.\n')


def perform_analysis(tool_conf_data):
    """This function runs the analysis tool.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Change directory if necessary
    if tool_conf_data.get('coverity_build_dir') != os.getcwd():
        # Navigate to the compilation directory
        logging.info('\tChanging directory: %s', tool_conf_data.get('coverity_build_dir'))
        os.chdir(tool_conf_data.get('coverity_build_dir'))

    # Perform a clean
    call_string = tool_conf_data.get('coverity_clean_cmd')
    scrub_utilities.execute_command(call_string, os.environ.copy())

    # Examine the cov-configure flag values
    if not tool_conf_data.get('coverity_covconfigure_flags'):
        if tool_conf_data.get('source_lang') == 'c':
            tool_conf_data.update({'coverity_covconfigure_flags': '--gcc'})
        elif tool_conf_data.get('source_lang') == 'j':
            tool_conf_data.update({'coverity_covconfigure_flags': '--java'})

    # Configure Coverity to perform analysis
    cov_configure(tool_conf_data.get('coverity_path'),
                  tool_conf_data.get('coverity_covconfigure_flags'))

    # Examine the cov-build flag values
    required_covbuild_flags = ('--dir ' + tool_conf_data.get('coverity_analysis_dir') + ' '
                               + tool_conf_data.get('coverity_build_cmd'))
    tool_conf_data.update({'coverity_covbuild_flags': tool_conf_data.get('coverity_covbuild_flags') + ' ' +
                           required_covbuild_flags})

    # Build the analysis dir
    cov_build(tool_conf_data.get('coverity_path'),
              tool_conf_data.get('coverity_covbuild_flags'))

    # Examine the cov-analyze flag values
    if tool_conf_data.get('source_lang') == 'c':
        cov_analysis_options = "--enable-constraint-fpp " \
                               "--concurrency " \
                               "--security " \
                               "-en STACK_USE " \
                               "--checker-option STACK_USE:note_indirect_recursion:true " \
                               "--checker-option STACK_USE:note_direct_recursion:true " \
                               "--checker-option PASS_BY_VALUE:size_threshold:256 " \
                               "-en INFINITE_LOOP " \
                               "-en ASSERT_SIDE_EFFECT " \
                               "-en CHECKED_RETURN " \
                               "--checker-option CHECKED_RETURN:stat_threshold:0 " \
                               "-en ARRAY_VS_SINGLETON " \
                               "-en ATOMICITY " \
                               "-en BAD_ALLOC_ARITHMETIC " \
                               "-en BAD_ALLOC_STRLEN " \
                               "-en DELETE_VOID " \
                               "-en INTEGER_OVERFLOW " \
                               "-en MISSING_BREAK " \
                               "-en MISSING_LOCK " \
                               "-en READLINK " \
                               "-en USER_POINTER"
    else:
        cov_analysis_options = ''
    required_covanalyze_flags = '--dir ' + tool_conf_data.get('coverity_analysis_dir') + ' ' + cov_analysis_options
    tool_conf_data.update({'coverity_covanalyze_flags': tool_conf_data.get('coverity_covanalyze_flags') + ' ' +
                           required_covanalyze_flags})

    # Perform the analysis
    cov_analyze(tool_conf_data.get('coverity_path'),
                tool_conf_data.get('coverity_covanalyze_flags'))

    # Examine the cov-format-errors flag values
    required_covformaterrors_flags = ('--dir ' + tool_conf_data.get('coverity_analysis_dir') +
                                      ' -x -X --emacs-style > ' + tool_conf_data.get('coverity_output_file'))
    tool_conf_data.update({'coverity_covformaterrors_flags': tool_conf_data.get('coverity_covformaterrors_flags') +
                           ' ' + required_covformaterrors_flags})

    # Format the output
    cov_format_errors(tool_conf_data.get('coverity_path'),
                      tool_conf_data.get('coverity_covformaterrors_flags'))

    # Change the permissions of the Coverity output file
    os.chmod(tool_conf_data.get('coverity_output_file'), 438)


def post_process_analysis(tool_conf_data):
    """This function post-processes results from the analysis tool.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Post process the results
    get_coverity_warnings.parse_warnings(tool_conf_data.get('coverity_output_file'),
                                         tool_conf_data.get('coverity_raw_warning_file'),
                                         tool_conf_data.get('coverity_version'))


def cov_configure(bin_dir, coverity_covconfigure_flags):
    """This function configures Coverity based on the source code language.

    Inputs:
        - bin_dir: Absolute path to the 'bin' directory of the Coverity installation [string]
        - coverity_covconfigure_flags: Command flags to be passed to Coverity command "cov-configure" [string]
    """

    # Perform the build
    if bin_dir == '':
        call_string = "cov-configure " + coverity_covconfigure_flags
    else:
        call_string = bin_dir + "/cov-configure " + coverity_covconfigure_flags
    scrub_utilities.execute_command(call_string, os.environ.copy())


def cov_build(bin_dir, coverity_covbuild_flags):
    """This function performs the Coverity build capture process.

    Inputs:
        - bin_dir: Absolute path to the 'bin' directory of the Coverity installation [string]
        - coverity_covbuild_flags: Command flags to be passed to Coverity command "cov-build" [string]
    """

    # Initialize variables
    coverity_output_dir = get_argument_value(coverity_covbuild_flags, "--dir")

    # Remove the Coverity analysis directory if it exists
    if os.path.exists(coverity_output_dir):
        shutil.rmtree(coverity_output_dir)

    # Create the analysis directory
    os.mkdir(coverity_output_dir)

    # Perform the build
    if bin_dir == '':
        call_string = "cov-build " + coverity_covbuild_flags
    else:
        call_string = bin_dir + "/cov-build " + coverity_covbuild_flags
    scrub_utilities.execute_command(call_string, os.environ.copy())

    # Set the permissions of the output directory
    os.chmod(coverity_output_dir, 509)


def cov_analyze(bin_dir, coverity_covanalyze_flags):
    """This function performs the Coverity analysis.

    Inputs:
        - bin_dir: Full path to the 'bin' directory of the Coverity installation [string]
        - coverity_covanalyze_flags: command flags to be passed to Coverity command "cov-analyze" [string]
    """

    # Perform the analysis
    if bin_dir == '':
        call_string = "cov-analyze " + coverity_covanalyze_flags
    else:
        call_string = bin_dir + "/cov-analyze " + coverity_covanalyze_flags
    scrub_utilities.execute_command(call_string, os.environ.copy())


def cov_format_errors(bin_dir, coverity_covformaterrors_flags):
    """This function formats the Coverity analysis into a readable format.

    Inputs:
        - bin_dir: Absolute path to the 'bin' directory of the Coverity installation [string]
        - coverity_covformaterrors_flags: Command flags to be passed to Coverity command "cov-format-errors" [string]
    """

    # Initialize variables
    coverity_output_file = get_argument_value(coverity_covformaterrors_flags, ">")

    # Remove the output file if it exists
    if os.path.exists(coverity_output_file):
        os.remove(coverity_output_file)

    # Reformat the results
    if bin_dir == '':
        call_string = "cov-format-errors " + coverity_covformaterrors_flags
    else:
        call_string = bin_dir + "/cov-format-errors " + coverity_covformaterrors_flags
    my_env = os.environ.copy()
    logging.info('')
    logging.info('\t>> Executing command: %s', call_string)
    logging.info('\t>> From directory: %s', os.getcwd())
    proc = subprocess.Popen(call_string, shell=True, env=my_env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
    std_out, std_err = proc.communicate()

    # Write to the log file
    logging.debug('\tConsole output:\n\n' + std_out + std_err)


def get_argument_value(input_string, argument):
    """This function gets the value of the argument from the input_string.

    Inputs:
        - input_string: Input_string containing all arguments [string]
        - argument: The argument of interest to be gathered from the input_string [string]

    Outputs:
        - argument_value: the value of the argument of interest [string]
    """

    # Gather the argument value
    argument_value = list(filter(None, re.split(' ', list(filter(None, re.split(argument, input_string)))[-1])))[0]

    return argument_value


def get_version_number(coverity_path):
    """This function determines the Coverity version number.

        Inputs:
            - coverity_path: Absolute path to the 'bin' directory of the Coverity installation [string]

        Outputs:
            - version_number: The version number of the Coverity instance being tested [string]
        """

    # Initialize variables
    version_number = None

    try:
        # Set the path, if necessary
        if coverity_path == '':
            coverity_path = scrub_utilities.get_executable_path('cov-build')

        # Read in the version information file
        with open(os.path.dirname(os.path.normpath(coverity_path)) + '/VERSION', 'r') as input_fh:
            input_data = input_fh.readlines()

        # Iterate through every line of the file to get the version number
        for line in input_data:
            if line.startswith('doc'):
                version_number = re.split('-', line.strip())[-1]
                break

    except:     # lgtm [py/catch-base-exception]
        version_number = 'Unknown'

    return version_number


def run_analysis(baseline_conf_data, override=False):
    """This function calls Coverity to perform analysis.

    Inputs:
        - baseline_conf_data: Dictionary of raw scrub.cfg configuration parameters [dict]
        - override: Force tool execution? [optional] [bool]

    Outputs:
        - coverity_analysis: Directory containing Coverity intermediary analysis files
        - log_file/coverity.log: SCRUB log file for the Coverity analysis
        - raw_results/coverity_raw.scrub: SCRUB-formatted results file containing raw Coverity results
        - raw_results/coverity_raw.sarif: SARIF-formatted results file containing raw Coverity results
    """

    # Import the config file data
    tool_conf_data = baseline_conf_data.copy()
    initialize_analysis(tool_conf_data)

    # Initialize variables
    coverity_exit_code = 2
    initial_dir = os.getcwd()
    attempt_analysis = tool_conf_data.get('coverity_warnings') or override

    if attempt_analysis:
        try:
            # Create the logger
            scrub_utilities.create_logger(tool_conf_data.get('coverity_log_file'))

            # Print a status message
            logging.info('')
            logging.info('Perform Coverity analysis...')

            # Get the version number
            version_number = get_version_number(tool_conf_data.get('coverity_path'))
            logging.info('\tCoverity Version: %s', version_number)
            tool_conf_data.update({'coverity_version': version_number})

            # Perform the analysis
            perform_analysis(tool_conf_data)

            # Post-process the analysis
            post_process_analysis(tool_conf_data)

            # Set the exit code
            coverity_exit_code = 0

        except scrub_utilities.CommandExecutionError:
            # Print a warning message
            logging.warning('Coverity analysis could not be performed. Please see log file {} for '
                            'more information.'.format(tool_conf_data.get('coverity_log_file')))

            # Print the exception traceback
            logging.warning(traceback.format_exc())

            # Set the exit code
            coverity_exit_code = 1

        except:     # lgtm [py/catch-base-exception]
            # Print a warning message
            logging.error('A SCRUB error has occurred. Please see log file {} for more '
                          'information.'.format(tool_conf_data.get('coverity_log_file')))

            # Print the exception traceback
            logging.error(traceback.format_exc())

            # Set the exit code
            coverity_exit_code = 100

        finally:
            # Change back to the initial dir if necessary
            if os.getcwd() != initial_dir:
                logging.info('\tChanging directory: %s', initial_dir)
                os.chdir(initial_dir)

            # Close the loggers
            logging.getLogger().handlers = []

    # Return the exit code
    return coverity_exit_code
