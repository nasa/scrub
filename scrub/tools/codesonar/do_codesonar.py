import os
import shutil
import glob
import subprocess
import logging
import traceback
import re
from scrub.utils import translate_results
from scrub.utils import scrub_utilities

VALID_TAGS = ['codesonar', 'cdsnr']


def initialize_analysis(tool_conf_data):
    """The purpose of this function is to prepare the tool to perform analysis.

    Inputs:
        - scrub_conf: Absolute path to the SCRUB configuration file to be used to perform analysis [string]

    Outputs:
        - scrub_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Initialize the derived variables
    codesonar_log_file = os.path.normpath(tool_conf_data.get('scrub_log_dir') + '/codesonar.log')
    codesonar_raw_warning_file = os.path.normpath(tool_conf_data.get('raw_results_dir') + '/codesonar_raw.scrub')
    codesonar_filtered_warning_file = os.path.normpath(tool_conf_data.get('scrub_working_dir') + '/codesonar.scrub')
    codesonar_raw_p10_warning_file = os.path.normpath(tool_conf_data.get('raw_results_dir') +
                                                      '/codesonar_p10_raw.scrub')
    codesonar_filtered_p10_warning_file = os.path.normpath(tool_conf_data.get('scrub_working_dir') + '/p10.scrub')
    codesonar_analysis_dir = os.path.normpath(tool_conf_data.get('scrub_working_dir') + '/codesonar_analysis')
    codesonar_project_dir = os.path.normpath(codesonar_analysis_dir + '/codesonar_project')

    # Add derived values to the dictionary
    tool_conf_data.update({'codesonar_analysis_dir': codesonar_analysis_dir})
    tool_conf_data.update({'codesonar_log_file': codesonar_log_file})
    tool_conf_data.update({'codesonar_raw_warning_file': codesonar_raw_warning_file})
    tool_conf_data.update({'codesonar_filtered_warning_file': codesonar_filtered_warning_file})
    tool_conf_data.update({'codesonar_raw_p10_warning_file': codesonar_raw_p10_warning_file})
    tool_conf_data.update({'codesonar_filtered_p10_warning_file': codesonar_filtered_p10_warning_file})
    tool_conf_data.update({'codesonar_project_dir': codesonar_project_dir})

    # Remove the existing artifacts
    if os.path.exists(codesonar_log_file):
        os.remove(codesonar_log_file)
    if os.path.exists(codesonar_analysis_dir):
        shutil.rmtree(codesonar_analysis_dir)

    # Update the P10 value if necessary
    if tool_conf_data.get('source_lang') == 'j':
        tool_conf_data.update({'codesonar_p10_analysis': False})

    # Make sure at least the baseline or P10 analysis will be run
    if not (tool_conf_data.get('codesonar_baseline_analysis') or tool_conf_data.get('codesonar_p10_analysis')):
        tool_conf_data.update({'codesonar_warnings': False})

    # Check to see if all the required value are present to perform analysis
    if not (tool_conf_data.get('codesonar_hub') and tool_conf_data.get('codesonar_cert') and
            tool_conf_data.get('codesonar_key') and tool_conf_data.get('codesonar_proj_name') and
            tool_conf_data.get('codesonar_build_cmd') and tool_conf_data.get('codesonar_clean_cmd')):
        # Print a status message if necessary
        if tool_conf_data.get('codesonar_warnings'):
            # Print a status message
            print('\nWARNING: Unable to perform CodeSonar analysis. Required configuration inputs are missing.\n')

        # Update the value of codesonar_warnings
        tool_conf_data.update({'codesonar_warnings': False})


def perform_analysis(tool_conf_data):
    """This function runs the analysis tool.

    Inputs:
        - scrub_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Change directory if necessary
    if tool_conf_data.get('codesonar_build_dir') != os.getcwd():
        # Navigate to the compilation directory
        logging.info('\tChanging directory: %s', tool_conf_data.get('codesonar_build_dir'))
        os.chdir(tool_conf_data.get('codesonar_build_dir'))

    # Set the CodeSonar path if necessary
    if not tool_conf_data.get('codesonar_path'):
        tool_conf_data.update({'codesonar_path': scrub_utilities.get_executable_path('codesonar')})

    # Perform a clean
    call_string = tool_conf_data.get('codesonar_clean_cmd')
    scrub_utilities.execute_command(call_string, os.environ.copy())

    # Determine the analysis presets
    codesonar_presets_list = []
    if tool_conf_data.get('codesonar_p10_analysis'):
        codesonar_presets_list.append("-preset pow10")
    if tool_conf_data.get('codesonar_baseline_analysis') and tool_conf_data.get('codesonar_analyze_flags'):
        codesonar_presets_list.append(tool_conf_data.get('codesonar_analyze_flags'))
    codesonar_presets = " ".join(codesonar_presets_list)
    tool_conf_data.update({'codesonar_presets': codesonar_presets})

    # Examine the analyze flag values
    required_analyze_flags = (tool_conf_data.get('codesonar_project_dir') + ' -project ' +
                              tool_conf_data.get('codesonar_proj_name') + ' -foreground ' + codesonar_presets +
                              ' -auth certificate -hubcert ' + tool_conf_data.get('codesonar_cert') + ' -hubkey ' +
                              tool_conf_data.get('codesonar_key') + ' ' + tool_conf_data.get('codesonar_hub'))
    tool_conf_data.update({'codesonar_analyze_flags': tool_conf_data.get('codesonar_analyze_flags') + ' ' +
                           required_analyze_flags})

    # Perform language specific configurations
    if tool_conf_data.get('source_lang') == 'c':
        # Update the analyze flags
        tool_conf_data.update({'codesonar_analyze_flags': tool_conf_data.get('codesonar_analyze_flags') + ' ' +
                               tool_conf_data.get('codesonar_build_cmd')})

    elif tool_conf_data.get('source_lang') == 'j':
        # Build the project
        call_string = tool_conf_data.get('codesonar_build_cmd')
        scrub_utilities.execute_command(call_string, os.environ.copy())

        # Update the analyze flags
        tool_conf_data.update({'codesonar_analyze_flags': tool_conf_data.get('codesonar_analyze_flags') + ' ' +
                               tool_conf_data.get('codesonar_path') + '/cs-java-scan ' +
                               tool_conf_data.get('source_dir')})

    # Perform the CodeSonar analysis
    analyze(tool_conf_data.get('codesonar_path'), tool_conf_data.get('codesonar_analyze_flags'))


def post_process_analysis(tool_conf_data):
    """This function post-processes results from the analysis tool.

    Inputs:
        - scrub_conf_data: Dictionary of scrub.cfg input variables [dict]
    """

    # Parse the output log to get the analysis ID
    analysis_id_log = os.path.normpath(tool_conf_data.get('codesonar_project_dir') + '.prj_files/aid.txt')
    analysis_id = get_analysis_id(analysis_id_log)

    # Make the call to retrieve the results from the Hub and store them in the specified location
    codesonar_results = str(analysis_id) + '-allwarnings.sarif'
    codesonar_results_url = (tool_conf_data.get('codesonar_hub') + "/analysis/" + codesonar_results + '?filter=' +
                             str(tool_conf_data.get('codesonar_results_template')))

    # Examine the codesonar get command flags
    required_get_flags = ('-auth certificate -hubcert ' + tool_conf_data.get('codesonar_cert') + ' -hubkey ' +
                          tool_conf_data.get('codesonar_key') + ' ' + codesonar_results_url)
    tool_conf_data.update({'codesonar_get_flags': tool_conf_data.get('codesonar_get_flags') + ' ' + required_get_flags})

    # Get the results from the server
    get(tool_conf_data.get('codesonar_path'), tool_conf_data.get('codesonar_get_flags'))

    # Check to make sure the output file was retrieved successfully
    if not os.path.isfile(codesonar_results):
        message = 'Could not retrieve analysis from CodeSonar Hub.'

        # Print the message to the screen
        raise UserWarning(message)

    # Get the absolute path of the output file
    codesonar_results_path = os.path.normpath(tool_conf_data.get('codesonar_analysis_dir') + '/' + codesonar_results)

    # Move the output file to the raw_results folder
    shutil.move(os.path.abspath(codesonar_results), codesonar_results_path)

    # Post process the SARIF file
    baseline_codesonar_scrub_output_path = os.path.normpath(tool_conf_data.get('codesonar_analysis_dir') +
                                                            '/codesonar_raw.scrub')
    parse_exit_code = translate_results.perform_translation(codesonar_results_path,
                                                            baseline_codesonar_scrub_output_path,
                                                            tool_conf_data.get('source_dir'), 'scrub')

    if parse_exit_code == 0:
        # Separate the P10 results if necessary
        if tool_conf_data.get('codesonar_p10_analysis'):
            # Get the P10 preset queries
            p10_queries = get_preset_queries(os.path.abspath(tool_conf_data.get('codesonar_path') +
                                                             '/../presets/pow10.conf'))
            # Separate the results
            scrub_utilities.split_results(baseline_codesonar_scrub_output_path,
                                          tool_conf_data.get('codesonar_raw_p10_warning_file'),
                                          tool_conf_data.get('codesonar_raw_warning_file'), p10_queries)

            # Remove the baseline results file if necessary
            if not tool_conf_data.get('codesonar_baseline_analysis'):
                os.remove(tool_conf_data.get('codesonar_raw_warning_file'))

        else:
            # Copy the results file as is
            shutil.copyfile(baseline_codesonar_scrub_output_path, tool_conf_data.get('codesonar_raw_warning_file'))

        # Update the permissions of the file, if it exists
        if os.path.exists(tool_conf_data.get('codesonar_raw_warning_file')):
            os.chmod(tool_conf_data.get('codesonar_raw_warning_file'), 438)

        # Update the permissions of the file, if it exists
        if os.path.exists(tool_conf_data.get('codesonar_raw_p10_warning_file')):
            os.chmod(tool_conf_data.get('codesonar_raw_p10_warning_file'), 438)

    return parse_exit_code


def analyze(bin_dir, codesonar_analyze_flags):
    """This function performs the CodeSonar analysis.

    Inputs:
        - bin_dir: absolute path to the 'bin' directory of CodeSonar [string]
        - codesonar_analyze_flags: command flags to be passed to CodeSonar command "analyze" [string]
    """

    # Initialize variables
    local_proj_name = codesonar_analyze_flags.split()[0]

    # Remove any existing analysis data
    if os.path.exists(local_proj_name + '.conf'):
        os.remove(local_proj_name + '.conf')

    if os.path.exists(local_proj_name + '.prj'):
        os.remove(local_proj_name + '.prj')

    if os.path.exists(local_proj_name + '.prj_files'):
        shutil.rmtree(local_proj_name + '.prj_files')

    aid_files = glob.glob('aid*.xml')
    for aid_file in aid_files:
        os.remove(aid_file)

    # Perform CodeSonar analysis
    if bin_dir == '':
        call_string = "codesonar analyze " + codesonar_analyze_flags
    else:
        call_string = bin_dir + "/codesonar analyze " + codesonar_analyze_flags

    # Execute the command
    scrub_utilities.execute_command(call_string, os.environ.copy())


def get(bin_dir, codesonar_get_flags):
    """This function retrieves the analysis from the CodeSonar Hub.

    Inputs:
        - bin_dir: absolute path to the 'bin' directory of CodeSonar [string]
        - codesonar_get_flags: command flags to be passed to CodeSonar command "get" [string]
    """

    # Retrieve the results
    if bin_dir == '':
        call_string = "codesonar get " + codesonar_get_flags
    else:
        call_string = bin_dir + "/codesonar get " + codesonar_get_flags

    # Execute the command
    scrub_utilities.execute_command(call_string, os.environ.copy())


def get_analysis_id(input_file):
    """This function parses a CodeSonar log file to determine the analysis ID

    Inputs:
        - input_file: Absolute path to the CodeSonar analysis log file of interest [string]

    Outputs:
        - analysis_id: the analysis ID found in the input file will be returned [string]
    """

    # Import the log file
    with open(input_file, 'r') as input_fh:
        log_data = input_fh.readlines()

    # Pull the number from the log file
    analysis_id = log_data[0].strip()

    return analysis_id


def get_version_number(codesonar_path):
    """This function determines the CodeSonar version number.

        Inputs:
            - codesonar_path: Absolute path to the CodeSonar installation of interest [string]

        Outputs:
            - version_number: The version number of the CodeSonar instance being tested [string]
        """

    # Initialize variables
    version_number = None

    try:
        # Set the path, if necessary
        if codesonar_path == '':
            call_string = 'which codesonar'
            my_env = os.environ.copy()
            # subprocess.call(call_string, shell=True, env=my_env)
            proc = subprocess.Popen(call_string, shell=True, env=my_env, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, encoding='utf-8')
            codesonar_path = os.path.dirname(proc.communicate()[0].strip())

        # import the version data
        with open(os.path.normpath(codesonar_path) + '/../../SIGNATURE.txt', 'r') as input_fh:
            input_data = input_fh.readlines()

        # Iterate through every line of the input file to get the version number
        for line in input_data:
            if line.startswith('Version'):
                version_number = re.split(':', line.strip())[-1].strip()
    except:     # lgtm [py/catch-base-exception]
        version_number = 'Unknown'

    return version_number


def get_preset_queries(preset_file):
    """This function returns a list of CodeSonar preset queries contained in the provided preset file.

    Inputs:
        - preset_file: Absolute path to the preset file of interest.

    Outputs:
        - preset_queries: List of queries that are contained in the preset [list of strings]
    """

    # Initialize variables
    preset_queries = []

    # Import the configuration file data
    with open(preset_file, 'r') as input_fh:
        input_data = input_fh.readlines()

        # Iterate through every line in the file
        for line in input_data:
            if 'WARNING_FILTER' in line.strip():
                preset_queries.append(list(filter(None, re.split('\\"', line.strip())))[-1])

    return preset_queries


def run_analysis(baseline_conf_data, override=False):
    """This function calls CodeSonar to perform analysis.

    Inputs:
        - baseline_conf_data: Absolute path to the SCRUB configuration file to be used to perform analysis [string]
        - override: Override the automatic checks to see if analysis should be performed? [optional] [bool]

    Outputs:
        - codesonar_results_path: location of results file will be returned [string]
    """

    # Import the configuration data
    tool_conf_data = baseline_conf_data.copy()
    initialize_analysis(tool_conf_data)

    # Initialize variables
    codesonar_exit_code = 2
    initial_dir = os.getcwd()
    attempt_analysis = tool_conf_data.get('codesonar_warnings') or override

    if attempt_analysis:
        try:
            # Create the analysis directory if it doesn't exist
            if not os.path.exists(tool_conf_data.get('codesonar_analysis_dir')):
                os.mkdir(tool_conf_data.get('codesonar_analysis_dir'))

            # Create the logger
            scrub_utilities.create_logger(tool_conf_data.get('codesonar_log_file'))

            # Print a status message
            logging.info('')
            logging.info('Perform CodeSonar analysis...')
            logging.info('\tPerform CodeSonar baseline analysis: ' +
                         str(tool_conf_data.get('codesonar_baseline_analysis')))
            logging.info('\tPerform CodeSonar P10 analysis: ' + str(tool_conf_data.get('codesonar_p10_analysis')))

            # Get the version number
            version_number = get_version_number(tool_conf_data.get('codesonar_path'))
            logging.info('\tCodeSonar Version: %s', version_number)

            # Perform the analysis
            perform_analysis(tool_conf_data)

            # Post-process the analysis
            parse_exit_code = post_process_analysis(tool_conf_data)

            # Return the exit code
            codesonar_exit_code = parse_exit_code

        except scrub_utilities.CommandExecutionError:
            # Print a warning message
            logging.warning('CodeSonar analysis could not be performed. Please see log file {} for '
                            'more information.'.format(tool_conf_data.get('codesonar_log_file')))

            # Print the exception traceback
            logging.warning(traceback.format_exc())

            # Set the exit code
            codesonar_exit_code = 1

        except:     # lgtm [py/catch-base-exception]
            # Print a warning message
            logging.error('A SCRUB error has occurred. Please see log file {} for more '
                          'information.'.format(tool_conf_data.get('codesonar_log_file')))

            # Print the exception traceback
            logging.error(traceback.format_exc())

            # Set the exit code
            codesonar_exit_code = 100

        finally:
            # Change back to the initial dir if necessary
            if os.getcwd() != initial_dir:
                logging.info('\tChanging directory: %s', initial_dir)
                os.chdir(initial_dir)

            # Close the loggers
            logging.getLogger().handlers = []

    # Return the exit code
    return codesonar_exit_code
