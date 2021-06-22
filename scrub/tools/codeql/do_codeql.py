import os
import re
import logging
import traceback
import glob
import subprocess
from scrub.utils import translate_results
from scrub.utils import scrub_utilities

VALID_TAGS = ['codeql']


def initialize_analysis(tool_conf_data):
    """This function takes in configuration variables from scrub.cfg file and initializes derived variables like
       analysis directories and output file paths before executing CodeQL analysis.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Initialize the derived variables
    codeql_log_file = os.path.normpath(tool_conf_data.get('scrub_log_dir') + '/codeql.log')
    codeql_analysis_dir = os.path.normpath(tool_conf_data.get('scrub_working_dir') + '/codeql_analysis')
    codeql_database_dir = os.path.normpath(codeql_analysis_dir + '/db')
    codeql_p10_raw_warning_file = os.path.normpath(tool_conf_data.get('raw_results_dir') + '/codeql_p10_raw.scrub')
    codeql_raw_warning_file = os.path.normpath(tool_conf_data.get('raw_results_dir') + '/codeql_raw.scrub')
    codeql_baseline_output_file = os.path.normpath(codeql_analysis_dir + '/codeql_raw.sarif')
    codeql_p10_output_file = os.path.normpath(codeql_analysis_dir + '/codeql_p10_raw.sarif')

    # Valid language identifiers for `database create` flag
    codeql_lang_ids = {'c': 'cpp', 'j': 'java'}

    # Add derived values to the dictionary
    tool_conf_data.update({'codeql_lang_id': codeql_lang_ids[tool_conf_data.get('source_lang')]})
    tool_conf_data.update({'codeql_log_file': codeql_log_file})
    tool_conf_data.update({'codeql_raw_warning_file': codeql_raw_warning_file})
    tool_conf_data.update({'codeql_p10_raw_warning_file': codeql_p10_raw_warning_file})
    tool_conf_data.update({'codeql_analysis_dir': codeql_analysis_dir})
    tool_conf_data.update({'codeql_database_dir': codeql_database_dir})
    tool_conf_data.update({'codeql_baseline_output_file': codeql_baseline_output_file})
    tool_conf_data.update({'codeql_p10_output_file': codeql_p10_output_file})

    # Update the p10 flag if necessary
    if tool_conf_data.get('source_lang').lower() == 'j':
        tool_conf_data.update({'codeql_p10_analysis': False})

    # Make sure the required inputs are present
    if not (tool_conf_data.get('codeql_query_path') and tool_conf_data.get('codeql_build_cmd') and
            tool_conf_data.get('codeql_clean_cmd')):
        # Update the run flag if necessary
        if tool_conf_data.get('codeql_warnings'):
            tool_conf_data.update({'codeql_warnings': False})

            # Print a status message
            print('\nWARNING: Unable to perform CodeQL analysis. Required configuration inputs are missing.\n')

    # Make sure at least the baseline or P10 analysis will be run
    if not (tool_conf_data.get('codeql_baseline_analysis') or tool_conf_data.get('codeql_p10_analysis')):
        tool_conf_data.update({'codeql_warnings': False})


def perform_analysis(tool_conf_data):
    """This function prepares the analysis directory by executing clean commands specified in the configuration options.
       performs analysis by executing commands from CodeQL CLI.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Create the project directory
    initial_dir = os.getcwd()
    os.mkdir(tool_conf_data.get('codeql_analysis_dir'))

    # Change directory if necessary
    working_dir = os.path.abspath(tool_conf_data.get('codeql_build_dir'))
    if working_dir != initial_dir:
        # Navigate to compilation directory
        logging.info('\tChanging directory: %s', working_dir)
        os.chdir(working_dir)

    # Perform a clean
    call_string = tool_conf_data.get('codeql_clean_cmd')
    scrub_utilities.execute_command(call_string, os.environ.copy())

    # Change back to the initial dir if necessary
    if os.getcwd() != initial_dir:
        logging.info('\tChanging directory to: %s', initial_dir)
        os.chdir(initial_dir)

    # Examine the `database create` flag values
    required_databasecreate_flags = ('--language ' + tool_conf_data.get('codeql_lang_id') + ' --source-root ' +
                                     tool_conf_data.get('source_dir') + ' --working-dir ' +
                                     tool_conf_data.get('codeql_build_dir') + ' --command \"' +
                                     tool_conf_data.get('codeql_build_cmd') + '\"')
    codeql_databasecreate_flags = (tool_conf_data.get('codeql_databasecreate_flags') + ' ' +
                                   tool_conf_data.get('codeql_database_dir') + ' ' + required_databasecreate_flags)

    # Create the codeql database
    database_create(tool_conf_data.get('codeql_path'), codeql_databasecreate_flags)

    # Examine the 'database upgrade' flag values
    required_databaseupgrade_flags = ('--search-path ' + tool_conf_data.get('codeql_query_path') + ' ' +
                                      tool_conf_data.get('codeql_database_dir'))

    # Perform database upgrade
    database_upgrade(tool_conf_data.get('codeql_path'), required_databaseupgrade_flags)

    # Get the user provided database analyze flags
    user_databaseanalyze_flags = tool_conf_data.get('codeql_databaseanalyze_flags')

    # Perform lgtm full analysis on database
    if tool_conf_data.get('codeql_baseline_analysis'):
        # Determine what query suites to use
        if tool_conf_data.get('source_lang') == 'c':
            suite_file = os.path.normpath(tool_conf_data.get('codeql_query_path') +
                                          '/cpp/ql/src/codeql-suites/cpp-lgtm-full.qls')
            suppression_query = os.path.normpath(tool_conf_data.get('codeql_query_path') +
                                                 '/cpp/ql/src/AlertSuppression.ql')
        elif tool_conf_data.get('source_lang') == 'j':
            suite_file = os.path.normpath(tool_conf_data.get('codeql_query_path') +
                                          '/java/ql/src/codeql-suites/java-lgtm-full.qls')
            suppression_query = os.path.normpath(tool_conf_data.get('codeql_query_path') +
                                                 '/java/ql/src/AlertSuppression.ql')
        else:
            raise UserWarning()

        # Set the baseline queries
        baseline_queries = (suite_file + ' ' + suppression_query)

        # Examine the `database analyze` flag values
        required_databaseanalyze_flags = (tool_conf_data.get('codeql_database_dir') + ' ' + baseline_queries +
                                          ' --format sarif-latest --output ' +
                                          tool_conf_data.get('codeql_baseline_output_file'))
        codeql_databaseanalyze_flags = user_databaseanalyze_flags + ' ' + required_databaseanalyze_flags

        database_analyze(tool_conf_data.get('codeql_path'), codeql_databaseanalyze_flags)

        # Update the permissions of the output directory
        os.chmod(tool_conf_data.get('codeql_baseline_output_file'), 509)

    # Perform p10 analysis on database
    if tool_conf_data.get('source_lang').lower() == 'c' and tool_conf_data.get('codeql_p10_analysis'):
        # Set the suite file path
        p10_queries = (os.path.normpath(tool_conf_data.get('codeql_query_path') + '/cpp/ql/src/"Power of 10"/') + ' ' +
                       os.path.normpath(tool_conf_data.get('codeql_query_path') + '/cpp/ql/src/AlertSuppression.ql'))

        # Examine the `database analyze` flag values
        required_databaseanalyze_flags = (tool_conf_data.get('codeql_database_dir') + ' ' + p10_queries +
                                          ' --format sarif-latest --output ' +
                                          tool_conf_data.get('codeql_p10_output_file'))
        codeql_databaseanalyze_flags = user_databaseanalyze_flags + ' ' + required_databaseanalyze_flags

        database_analyze(tool_conf_data.get('codeql_path'), codeql_databaseanalyze_flags)

        # Update the permissions of the output directory
        os.chmod(tool_conf_data.get('codeql_p10_output_file'), 509)


def post_process_analysis(tool_conf_data):
    """This function performs clean up steps after CodeQL analysis is executes and generates SCRUB format warnings from
       the SARIF results output.

    Inputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Initialize variables
    parse_exit_code = 0

    # Find all the result files to be parsed
    raw_results = glob.glob(tool_conf_data.get('codeql_analysis_dir') + '/*raw.sarif')

    # Iterate through the results files
    for results_file in raw_results:
        # Initialize variable for output file
        if '_p10_' in results_file:
            filtered_output = tool_conf_data.get('codeql_p10_raw_warning_file')
        else:
            filtered_output = tool_conf_data.get('codeql_raw_warning_file')

        # Post-process the data, returns error code 1 for failed conversions
        exit_code = translate_results.perform_translation(results_file, filtered_output,
                                                          tool_conf_data.get('source_dir'), 'scrub')

        # Update the parse exit code
        parse_exit_code = parse_exit_code + exit_code

    return parse_exit_code


def database_create(codeql_path, codeql_databasecreate_flags):
    """This function executes CodeQL CLI 'create' command using python subprocess library and any flags specified in
       scrub.cfg file.

    Inputs:
        - codeql_path: Absolute path to the root directory of the CodeQL installation [string]
        - codeql_databasecreate_flags: Flags to use during execution of `codeql database create` command. [string]
    """

    # Build the database
    if codeql_path == '':
        call_string = 'codeql database create ' + codeql_databasecreate_flags
    else:
        call_string = codeql_path + '/codeql database create ' + codeql_databasecreate_flags
    scrub_utilities.execute_command(call_string, os.environ.copy())


def database_upgrade(codeql_path, codeql_databaseupgrade_flags):
    """This function performs a database upgrade to ensure analysis can be performed.

    Inputs:
        - codeql_path: Absolute path to the root directory of the CodeQL installation [string]
        - codeql_databaseupgrade_flags: Flags to use during execution of `codeql database upgrade` command. [string]
    """

    # Upgrade the database
    if codeql_path == '':
        call_string = 'codeql database upgrade ' + codeql_databaseupgrade_flags
    else:
        call_string = codeql_path + '/codeql database upgrade ' + codeql_databaseupgrade_flags
    scrub_utilities.execute_command(call_string, os.environ.copy())


def database_analyze(codeql_path, codeql_databaseanalyze_flags):
    """This function executes CodeQL CLI `analyze` command using python subprocess library and any flags specified in
       scrub.cfg file.

    Inputs:
        - codeql_path: Absolute path to the root directory of the CodeQL installation [string]
        - codeql_databaseanalyze_flags: Flags to use during execution of `codeql database analyze` command. [string]
    """

    # Analyze the database
    if codeql_path == '':
        call_string = 'codeql database analyze ' + codeql_databaseanalyze_flags
    else:
        call_string = codeql_path + '/codeql database analyze ' + codeql_databaseanalyze_flags
    scrub_utilities.execute_command(call_string, os.environ.copy())


def get_version_number(codeql_path):
    """This function determines the CodeQL CLI version number.

    Inputs:
        - codeql_path: Absolute path to the CodeQL installation of interest [string]

    Outputs:
        - version_number: The version number of the CodeQL instance being tested [string]
    """

    # Initialize variables
    version_number = None

    try:
        # Set the path, if necessary
        if codeql_path == '':
            call_string = 'which codeql'
            proc = subprocess.Popen(call_string, shell=True, env=os.environ.copy(),
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            codeql_path = os.path.dirname(proc.communicate()[0].strip())

        # Run the CodeQL version command
        proc = subprocess.Popen(codeql_path + '/codeql --version', shell=True, env=os.environ.copy(),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        std_out, std_err = proc.communicate()

        # Get the line with the version number
        version_line = re.split('\n', std_out)[0]

        # Iterate through every item and find the one with numbers
        for item in re.split(' ', version_line):
            if any(char.isdigit() for char in item):
                version_number = item.strip()
                break

    except:  # lgtm [py/catch-base-exception]
        version_number = 'Unknown'

    return version_number


def run_analysis(baseline_conf_data, override=False):
    """This function starts the execution of CodeQL, which initializes the directory and configuration options then
       runs the analysis and post-analysis process.

    Inputs:
        - baseline_conf_data: Parsed configuration options from the scrub.cfg file being used [string]
        - override: For overriding a `False` result on ATTEMPT_ANALYSIS, continues CodeQL execution [string]

    Returns:
        codeql_exit_code:           exit code for this tool execution, returns `1` if there is an error when
                                    executing commands using python subprocess, and `100` for all other errors.
    Outputs:
        - codeql.log: Log file for the CodeQL analysis, where uid is the user ID (stdout and stderr)
        - codeql_analysis: Directory containing CodeQL analysis database and results
        - codeql.scrub: SCRUB-formatted results file containing converted CodeQL SARIF results (baseline/LGTM)
        - codeql_p10.scrub: SCRUB-formatted results file containing converted CodeQL SARIF results (Power of 10)
        - codeql_raw.sarif: SARIF-formatted results file containing raw CodeQL LGTM analysis results
        - codeql_raw_p10.sarif: SARIF-formatted results file containing raw CodeQL P10 analysis results
        - stdout and stderr data will be directed to log_file
    """

    # Import the config data
    tool_conf_data = baseline_conf_data.copy()
    initialize_analysis(tool_conf_data)

    # Initialize variables
    attempt_analysis = tool_conf_data.get('codeql_warnings') or override
    initial_dir = os.getcwd()
    codeql_exit_code = 2

    # Run analysis if scrub conf. wants CodeQL warnings
    if attempt_analysis:
        try:
            # Create the logger
            scrub_utilities.create_logger(tool_conf_data.get('codeql_log_file'))

            # Print a status message
            logging.info('')
            logging.info('Perform CodeQL analysis...')
            logging.info('\tPerform CodeQL baseline analysis: ' + str(tool_conf_data.get('codeql_baseline_analysis')))
            logging.info('\tPerform CodeQL P10 analysis: ' + str(tool_conf_data.get('codeql_p10_analysis')))

            # Get the CodeQL version number
            version_number = get_version_number(tool_conf_data.get('codeql_path'))
            logging.info('\tCodeQL Version: %s', version_number)

            # Perform the analysis
            perform_analysis(tool_conf_data)

            # Post-process the analysis
            parse_exit_code = post_process_analysis(tool_conf_data)

            # Set the exit code
            codeql_exit_code = parse_exit_code

        except scrub_utilities.CommandExecutionError:
            # Print a warning message
            logging.warning('CodeQL analysis could not be performed. Please see log file {} for '
                            'more information.'.format(tool_conf_data.get('codeql_log_file')))

            # Print the exception traceback
            logging.warning(traceback.format_exc())

            codeql_exit_code = 1

        except:  # lgtm [py/catch-base-exception]
            # Print a warning message
            logging.error('A SCRUB error has occurred. Please see log file {} for more '
                          'information.'.format(tool_conf_data.get('codeql_log_file')))

            # Print the exception traceback
            logging.error(traceback.format_exc())

            # Set the exit code
            codeql_exit_code = 100

        finally:
            # Change back to the initial directory if necessary
            if os.getcwd() != initial_dir:
                logging.info('\tChanging directory: %s', initial_dir)
                os.chdir(initial_dir)

            # Close the loggers
            logging.getLogger().handlers = []

    # Return the exit code
    return codeql_exit_code
