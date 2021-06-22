import os
import re
import shutil
import logging
import traceback
import subprocess
from scrub.tools.klocwork import get_klocwork_warnings
from scrub.utils import scrub_utilities

VALID_TAGS = ['klocwork', 'klcwrk']


def initialize_analysis(tool_conf_data):
    """This function prepares the tool to perform analysis.

    Inputs:
        - tool_conf_data: Absolute path to the SCRUB configuration file to be used to perform analysis [string]

    Outputs:
        - tool_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Initialize the derived variables
    klocwork_log_file = os.path.normpath(tool_conf_data.get('scrub_log_dir') + '/klocwork.log')
    klocwork_analysis_dir = os.path.normpath(tool_conf_data.get('scrub_working_dir') + '/klocwork_analysis')
    klocwork_kwinject_output_file = os.path.normpath(klocwork_analysis_dir + '/kwinject.out')
    klocwork_kwtables_dir = os.path.normpath(klocwork_analysis_dir + '/kw_tables')
    klocwork_output_file = os.path.normpath(klocwork_analysis_dir + '/klocwork_results.json')
    klocwork_raw_warning_file = os.path.normpath(tool_conf_data.get('raw_results_dir') + '/klocwork_raw.scrub')
    klocwork_filtered_warning_file = os.path.normpath(tool_conf_data.get('scrub_working_dir') + '/klocwork.scrub')
    klocwork_ltoken_file = os.path.expanduser('~/.klocwork/ltoken')

    # Add derived values to the dictionary
    tool_conf_data.update({'klocwork_log_file': klocwork_log_file})
    tool_conf_data.update({'klocwork_analysis_dir': klocwork_analysis_dir})
    tool_conf_data.update({'klocwork_output_file': klocwork_output_file})
    tool_conf_data.update({'klocwork_kwinject_output_file': klocwork_kwinject_output_file})
    tool_conf_data.update({'klocwork_kwtables_dir': klocwork_kwtables_dir})
    tool_conf_data.update({'klocwork_raw_warning_file': klocwork_raw_warning_file})
    tool_conf_data.update({'klocwork_filtered_warning_file': klocwork_filtered_warning_file})
    tool_conf_data.update({'klocwork_ltoken': klocwork_ltoken_file})

    # Remove any existing Klocwork results
    if os.path.exists(klocwork_analysis_dir):
        shutil.rmtree(klocwork_analysis_dir)

    # Remove any existing log files
    if os.path.exists(klocwork_log_file):
        os.remove(klocwork_log_file)

    # Make sure the codebase is not java
    if (tool_conf_data.get('source_lang') == 'j') and tool_conf_data.get('klocwork_warnings'):
        # Print a status message
        print('\nWARNING: Java analysis with Klocwork is not currently supported by SCRUB.\n')

        # Update the value
        tool_conf_data.update({'klocwork_warnings': False})

    # Determine if Klocwork can be run
    if not (tool_conf_data.get('klocwork_hub') and tool_conf_data.get('klocwork_proj_name') and
            tool_conf_data.get('klocwork_build_cmd') and tool_conf_data.get('klocwork_clean_cmd') and
            tool_conf_data.get('klocwork_ltoken')):
        # Update the analysis flag if necessary
        if tool_conf_data.get('klocwork_warnings'):
            tool_conf_data.update({'klocwork_warnings': False})

            # Print a status message
            print('\nWARNING: Unable to perform Klocwork analysis. Required configuration inputs are missing.\n')


def perform_analysis(tool_conf_data):
    """This function runs the analysis tool.

    Inputs:
        - scrub_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Change directory if necessary
    if tool_conf_data.get('klocwork_build_dir') != os.getcwd():
        # Navigate to the compilation directory
        logging.info('\tChanging directory: %s', tool_conf_data.get('klocwork_build_dir'))
        os.chdir(tool_conf_data.get('klocwork_build_dir'))

    # Perform a clean
    call_string = tool_conf_data.get('klocwork_clean_cmd')
    scrub_utilities.execute_command(call_string, os.environ.copy())

    # Set the kwinject command flags
    required_kwinject_flags = '--output ' + tool_conf_data.get('klocwork_kwinject_output_file') + ' ' + \
                              tool_conf_data.get('klocwork_build_cmd')
    tool_conf_data.update({'klocwork_kwinject_flags': tool_conf_data.get('klocwork_kwinject_flags') + ' ' +
                           required_kwinject_flags})

    # Capture the build
    kwinject(tool_conf_data.get('klocwork_path'), tool_conf_data.get('klocwork_kwinject_flags'))

    # Set the kwbuildproject command flags
    required_kwbuildproject_flags = '--url ' + tool_conf_data.get('klocwork_hub') + ':443/' + \
                                    tool_conf_data.get('klocwork_proj_name') + ' --tables-directory ' + \
                                    tool_conf_data.get('klocwork_kwtables_dir') + ' ' + \
                                    tool_conf_data.get('klocwork_kwinject_output_file')
    tool_conf_data.update({'klocwork_kwbuildproject_flags': tool_conf_data.get('klocwork_kwbuildproject_flags') + ' ' +
                           required_kwbuildproject_flags})

    # Build the project
    kwbuildproject(tool_conf_data.get('klocwork_path'), tool_conf_data.get('klocwork_kwbuildproject_flags'))

    # Set the kwadmin load command flags
    required_adminload_flags = '--url ' + tool_conf_data.get('klocwork_hub') + ':443 load ' + \
                               tool_conf_data.get('klocwork_proj_name') + ' ' + \
                               tool_conf_data.get('klocwork_kwtables_dir')
    tool_conf_data.update({'klocwork_kwadminload_flags': tool_conf_data.get('klocwork_kwadminload_flags') + ' ' +
                           required_adminload_flags})

    # Push the results to the server
    kwadmin(tool_conf_data.get('klocwork_path'), tool_conf_data.get('klocwork_kwadminload_flags'))

    # Set the curl command flags
    klocwork_username, ltoken = get_ltoken_data(tool_conf_data.get('klocwork_ltoken'))

    # Define the path to the build ID log file
    build_id_log = tool_conf_data.get('klocwork_kwtables_dir') + '/kwloaddb.log'

    # Get the build ID
    if os.path.exists(build_id_log):
        build_id = get_build_id(build_id_log)
    else:
        raise UserWarning('Could not retrieve analysis from Klocwork server.')

    # Set the curl search flags
    required_search_flags = '--silent --data \"action=search&user=' + klocwork_username + \
                            '&project=' + tool_conf_data.get('klocwork_proj_name') + \
                            '&ltoken=' + ltoken + '&query=build:' + build_id + ' state:New,+Existing\" ' + \
                            tool_conf_data.get('klocwork_hub') + '/review/api'
    tool_conf_data.update({'klocwork_search_flags': required_search_flags})

    # Get the result from the server
    curl_search(tool_conf_data.get('klocwork_search_flags'), tool_conf_data.get('klocwork_output_file'))

    # Change the permissions of the Klocwork output file
    os.chmod(tool_conf_data.get('klocwork_output_file'), 438)


def post_process_analysis(tool_conf_data):
    """This function post-processes results from the analysis tool.

    Inputs:
        - scrub_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Post process the results
    get_klocwork_warnings.parse_warnings(tool_conf_data.get('klocwork_output_file'),
                                         tool_conf_data.get('klocwork_raw_warning_file'),
                                         tool_conf_data.get('klocwork_version'))


def get_version_number(klocwork_path):
    """This function determines the Klocwork version number.

    Inputs:
        - klocwork_path: Absolute path to the bin directory of the Klocwork installation [string]

    Ouputs:
        - version_number: The version number of the Klocwork instance being tested [string]
    """

    try:
        # Set the path, if necessary
        if klocwork_path == '':
            call_string = 'which kwinject'
            my_env = os.environ.copy()
            subprocess.call(call_string, shell=True, env=my_env)
            proc = subprocess.Popen(call_string, shell=True, env=my_env, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, encoding='utf-8')
            klocwork_path = os.path.dirname(proc.communicate()[0].strip())

        # Get the version number
        call_string = klocwork_path + '/kwinject -v'
        my_env = os.environ.copy()
        proc = subprocess.Popen(call_string, shell=True, env=my_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                encoding='utf-8')
        std_out, std_err = proc.communicate()

        # Get the version number
        version_number = re.split(' ', re.split('\n', std_out)[1])[-1]

        # Truncate the version number if necessary
        version_split = re.split('\\.', version_number)
        if len(version_split) > 3:
            version_number = '.'.join(version_split[0:3])

    except:      # lgtm [py/catch-base-exception]
        version_number = 'Unknown'

    return version_number


def kwinject(bin_dir, kwinject_flags):
    """This function performs the Klocwork build capture process.

    Inputs:
        - bin_dir: Absolute path to the 'bin' directory of the Klocwork installation [string]
        - kwinject_flags: command flags to be passed to Klocwork command "kwinject" [string]
    """

    # Perform the build
    if bin_dir == '':
        call_string = "kwinject " + kwinject_flags
    else:
        call_string = bin_dir + "/kwinject " + kwinject_flags
    scrub_utilities.execute_command(call_string, os.environ.copy())


def kwbuildproject(bin_dir, kwbuildproject_flags):
    """This function performs the Klocwork build capture process.

    Inputs:
        - bin_dir: Absolute path to the 'bin' directory of the Klocwork installation [string]
        - kwinject_flags: command flags to be passed to Klocwork command "kwinject" [string]
    """

    # Perform the build
    if bin_dir == '':
        call_string = "kwbuildproject " + kwbuildproject_flags
    else:
        call_string = bin_dir + "/kwbuildproject " + kwbuildproject_flags
    scrub_utilities.execute_command(call_string, os.environ.copy())


def kwadmin(bin_dir, kwadmin_flags):
    """This function performs the Klocwork build capture process.

    Inputs:
        - bin_dir: Absolute path to the 'bin' directory of the Klocwork installation [string]
        - kwadmin_flags: command flags to be passed to Klocwork command "kwadmin" [string]
    """

    # Perform the build
    if bin_dir == '':
        call_string = "kwadmin " + kwadmin_flags
    else:
        call_string = bin_dir + "/kwadmin " + kwadmin_flags
    scrub_utilities.execute_command(call_string, os.environ.copy())


def curl_search(curl_search_flags, output_file):
    """This function retrieves the Klocwork results from the server.

    Inputs:
        - curl_search_flags: Command flags to be passed to the system curl command [string]
        - output_file: Absolute path to the file that will store raw Klocwork results [string]
    """

    # Construct the call string
    call_string = "curl " + curl_search_flags
    scrub_utilities.execute_command(call_string, os.environ.copy(), output_file)


def get_ltoken_data(ltoken_file):
    """This function returns the ltoken value found in the file ltoken_file.

    Inputs:
        - ltoken_file: Absolute path to the file containing a Klocwork ltoken file. [string]

    Outputs:
        - ltoken: User ltoken file to be used by Klocwork. [string]
    """

    # Read in the contents of the ltoken file
    with open(ltoken_file, 'r') as input_fh:
        input_data = input_fh.read()

    # Get the ltoken data
    ltoken_split = list(filter(None, re.split(';', input_data.strip())))
    username = ltoken_split[-2]
    ltoken = ltoken_split[-1]

    return username, ltoken


def get_build_id(log_file):
    """This function finds the build ID within the appropriate log file.

    Inputs:
        - log_file: Absolute path to the Klocwork log file kwloaddb.log [string]

    Outputs:
        - build_id: The build ID that is used by Klocwork to identify the analysis [string]
    """

    # Initialize variables
    build_id = None

    # Read in the first line of the log file
    with open(log_file, 'r') as input_fh:
        log_line = input_fh.readline()

    # Split the line
    line_split = filter(None, re.split('[" ]', log_line))

    # Find the build ID parameter
    for item in line_split:
        if item.startswith('build'):
            build_id = item
            break

    return build_id


def run_analysis(baseline_conf_data, override=False):
    """This function performs Klocwork analysis.

    Inputs:
        - baseline_conf_data: Dictionary of raw scrub.cfg configuration parameters [dict]
        - override: Force tool execution? [optional] [bool]

    Outputs:
        - klocwork_analysis: Directory containing Klocwork intermediary analysis files
        - log_file/klocwork.log: SCRUB log file for the KLocwork analysis
        - raw_results/klocwork_raw.scrub: SCRUB-formatted results file containing raw Coverity results
        - raw_results/klocwork_raw.sarif: SARIF-formatted results file containing raw Coverity results
    """

    # Import the config file data
    tool_conf_data = baseline_conf_data.copy()
    initialize_analysis(tool_conf_data)

    # Initialize variables
    tool_exit_code = 2
    initial_dir = os.getcwd()
    attempt_analysis = tool_conf_data.get('klocwork_warnings') or override

    if attempt_analysis:
        try:
            # Create the analysis directory if it doesn't exist
            if not os.path.exists(tool_conf_data.get('klocwork_analysis_dir')):
                os.mkdir(tool_conf_data.get('klocwork_analysis_dir'))

            # Create the logger
            scrub_utilities.create_logger(tool_conf_data.get('klocwork_log_file'))

            # Print a status message
            logging.info('')
            logging.info('Perform Klocwork analysis...')

            # Get the version number
            version_number = get_version_number(tool_conf_data.get('klocwork_path'))
            logging.info('\tKlocwork Version: %s', version_number)
            tool_conf_data.update({'klocwork_version': version_number})

            # Perform the analysis
            perform_analysis(tool_conf_data)

            # Post-process the analysis
            post_process_analysis(tool_conf_data)

            # Set the exit code
            tool_exit_code = 0

        except scrub_utilities.CommandExecutionError:
            # Print a warning message
            logging.warning('Klocwork analysis could not be performed. Please see log file {} for '
                            'more information.'.format(tool_conf_data.get('klocwork_log_file')))

            # Print the exception traceback
            logging.warning(traceback.format_exc())

            # Set the exit code
            tool_exit_code = 1

        except:     # lgtm [py/catch-base-exception]
            # Print a warning message
            logging.error('A SCRUB error has occurred. Please see log file {} for more '
                          'information.'.format(tool_conf_data.get('klocwork_log_file')))

            # Print the exception traceback
            logging.error(traceback.format_exc())

            # Set the exit code
            tool_exit_code = 100

        finally:
            # Change back to the initial dir if necessary
            if os.getcwd() != initial_dir:
                logging.info('\tChanging directory: %s', initial_dir)
                os.chdir(initial_dir)

            # Close the loggers
            logging.getLogger().handlers = []

    # Return the exit code
    return tool_exit_code
