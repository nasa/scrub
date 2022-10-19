import re
import os
import sys
import time
import shutil
import pathlib
import logging
import threading
import subprocess
import configparser
import argparse
from scrub.tools.parsers import translate_results


class Spinner:
    busy = False
    delay = 0.1

    @staticmethod
    def spinning_cursor():
        while 1:
            for cursor in '|/-\\':
                yield cursor

    def __init__(self, delay=None):
        self.spinner_generator = self.spinning_cursor()
        if delay and float(delay):
            self.delay = delay

    def spinner_task(self):
        while self.busy:
            sys.stdout.write(next(self.spinner_generator))
            sys.stdout.flush()
            time.sleep(self.delay)
            sys.stdout.write('\b')
            sys.stdout.flush()

    def __enter__(self):
        self.busy = True
        threading.Thread(target=self.spinner_task).start()

    def __exit__(self, exception, value, tb):
        self.busy = False
        time.sleep(self.delay)
        if exception is not None:
            return False


def parse_template(template_file, output_file, conf_data):
    """This function parsers analysis templates and populates them with configuration values.

    Inputs:
        - template_file: Absolute path to analysis template file [Path object]
        - output_file: Absolute path to output analysis script [Path object]
        - conf_data: Dictionary of values read from configuration file [dict]
    """

    # Read in the analysis template
    with open(template_file, 'r') as input_fh:
        template_data = input_fh.read()

    # Replace all of the variables with config data
    for key in conf_data.keys():
        if isinstance(conf_data.get(key), bool):
            template_data = template_data.replace('${{' + key.upper() + '}}', str(conf_data.get(key)).lower())
        else:
            template_data = template_data.replace('${{' + key.upper() + '}}', str(conf_data.get(key)))

    # Write out the completed template
    with open(output_file, 'w') as output_fh:
        output_file.chmod(0o777)
        output_fh.write('%s' % template_data)

    # Check the contents of the analysis script file
    check_artifact(output_file, True)


class CommandExecutionError(Exception):
    pass


def check_artifact(input_artifact, critical=False):
    """This function checks to ensure the given file is not empty.

    Inputs:
        - input_artifact: Absolute path to the artifact of interest [string]
        - critical: Indication of artifact criticality [bool]
            - True: Artifact is critical and should not be empty
    """

    # Get the size of the item
    if input_artifact.is_file():
        size = input_artifact.stat().st_size
    else:
        size = len(list(input_artifact.iterdir()))

    # Check to make sure the file isn't empty
    if size == 0:
        if critical:
            message = input_artifact.name + ' is empty. This should not be empty.'
            raise CommandExecutionError(message)
        else:
            logging.warning('')
            logging.warning('\t%s is empty.', str(input_artifact.name))
            logging.warning('\tThis may or may not be a problem.')


def split_results(baseline_file, subset_file, remainder_file, queries):
    """This function splits a baseline set of SCRUB results into two separate files based on a given query list.

    Inputs:
        - baseline_file: Absolute path to the baseline file containing SCRUB warnings [string]
        - subset_file: Absolute path to the output file to contain filtered warnings [string]
        - remainder_file: Absolute path to the output file to contain remaining warnings not filtered [string]
        - query_list: List of query strings to filter on [list of strings]
    """

    # Import the contents of the baseline input file
    with open(baseline_file, 'r') as input_fh:
        baseline_data = input_fh.readlines()

    try:
        # Open the output files
        subset_fh = open(subset_file, 'w')
        remainder_fh = open(remainder_file, 'w')

        # Iterate through every line of the baseline data
        for i in range(0, len(baseline_data)):
            line = baseline_data[i]

            # Check to see if the line contains a warning header
            if re.search(translate_results.WARNING_LINE_REGEX, line):
                # Get the current warning query
                warning_query = list(filter(None, re.split(":", line)))[-1].strip()

                # Get the full warning content
                current_warning = get_warning(baseline_data, i)

                # Check to see if the query is in the queries list of interest
                if warning_query in queries:
                    # Write the query to the output file
                    subset_fh.write('%s' % current_warning)

                else:
                    # If not, write the result to to remaining output file
                    remainder_fh.write('%s' % current_warning)

    finally:
        # Close the files
        subset_fh.close()
        remainder_fh.close()


def get_warning(warning_data, index):
    """This function gets a complete warning when passed the index of a warning header.

    Inputs:
        - warning_data: List of lines of warning file contents [list of strings]
        - index: Index of warning header of interest [int]

    Outputs:
        - warning_content: Full warnings contents including header data [string]
    """

    # Initialize variables
    warning_content = warning_data[index]

    # Get the warning content
    for i in range(index + 1, len(warning_data)):
        # Get the line content
        line = warning_data[i]

        # Make sure you haven't hit the next warning header
        if re.search(translate_results.WARNING_LINE_REGEX, line):
            break
        else:
            warning_content = warning_content + line

    return warning_content


def execute_command(call_string, my_env, output_file=None, interactive=False):
    """This function executes a command string and captures the results.

    Inputs:
        - call_string: Command to execute in the shell [string]
        - my_env: Environment to use during execution [dict]
        - output_file: Absolute path to output file for storing results [string] [optional]
        - interactive: Open command for user input? [bool] [optional]
    """

    # Initialize variables
    output_data = ''

    # Write out a logging message
    logging.info('')
    logging.info('    >> Executing command: %s', call_string)
    logging.info('    >> From directory: %s', str(pathlib.Path().absolute()))
    logging.debug('    Console output:')

    # Execute the call string and capture the output
    with Spinner():
        if interactive:
            proc = subprocess.Popen(call_string, shell=True, env=my_env, encoding='utf-8')
        else:
            proc = subprocess.Popen(call_string, shell=True, env=my_env, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, encoding='utf-8')

            # Write the output to the logging file
            for stdout_line in iter(proc.stdout.readline, ''):
                logging.debug('        %s', stdout_line.replace('\n', ''))
                output_data = output_data + stdout_line

            # Write results to the output file
            if output_file is not None:
                with open(output_file, 'w') as output_fh:
                    output_fh.write(output_data)

    # Wait for the process to finish
    proc.wait(timeout=None)

    # Throw an exception if necessary
    if proc.poll() > 0:
        raise CommandExecutionError


def create_logger(log_file, console_logging=logging.INFO):
    """This function creates the logger to be used for logging SCRUB data.

    Inputs:
        - log_file: Absolute path to the location of the log file to be created [string]
        - console_logging: Should debugging info be printed to the console?
            - Default value: logging.INFO
    """

    # Clear any existing loggers
    logging.getLogger().handlers = []

    # Create the logger, if it doesn't already exist
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        filename=str(log_file),
                        filemode='w')

    # Start the console logger
    console = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    console.setLevel(console_logging)


def create_conf_file(output_path=None):
    """
    This function generates a blank configuration file at the desired output location.

    Inputs:
        --output: Path to desired output location [string] [optional]
            Default value: ./scrub_template.cfg
    """

    # Parse arguments if necessary
    if output_path is None:
        # Create the parser
        parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description=create_conf_file.__doc__)

        # Add parser arguments
        parser.add_argument('--output', default='./scrub_template.cfg')

        # Parse the arguments
        args = vars(parser.parse_args(sys.argv[2:]))
        output_path = args['output']

    # Initialize variables
    default_config_file = pathlib.Path(__file__).parent.joinpath('scrub_defaults.cfg').resolve()

    # Copy the default configuration file
    shutil.copyfile(default_config_file, output_path)


def parse_common_configs(user_conf_file, scrub_keys=[]):
    """This function parses a SCRUB configuration file and adds default values.

    Inputs:
        - conf_file: Absolute path to the SCRUB configuration file [string]
        - scrub_keys: List of configuration file sections to be retrieved [list of strings]

    Outputs:
        - scrub_conf_data: Dictionary of values read from configuration file [dict]
    """

    # Initialize the variables
    scrub_conf_data = {}
    scrub_init_path = pathlib.Path(__file__).parent.joinpath('scrub_defaults.cfg')

    # Read in the default config data
    scrub_init_data = configparser.ConfigParser()
    scrub_init_data.read(scrub_init_path)

    # Set the keys, if necessary
    if not scrub_keys:
        scrub_keys = scrub_init_data.sections()

    # Convert to a dictionary
    for key in scrub_keys:
        scrub_conf_data.update(dict(scrub_init_data.items(key)))

    # Read in the values from the conf file
    user_conf_data = configparser.ConfigParser()
    user_conf_data.read(user_conf_file)

    # Update the dictionary
    for user_section in user_conf_data.sections():
        for section_key in user_conf_data.options(user_section):
            # Update the value if the user conf has something
            if user_conf_data.get(user_section, section_key):
                scrub_conf_data.update({section_key: user_conf_data.get(user_section, section_key)})
            elif section_key not in scrub_conf_data.keys():
                # Add the key if it doesn't exist
                scrub_conf_data.update({section_key: user_conf_data.get(user_section, section_key)})

    # Update the configuration data
    for key in scrub_conf_data.keys():
        scrub_conf_data.update({key: os.path.expandvars(scrub_conf_data.get(key))})

        # # Update boolean values
        if scrub_conf_data.get(key).lower() == 'true':
            scrub_conf_data.update({key: True})
        elif scrub_conf_data.get(key).lower() == 'false':
            scrub_conf_data.update({key: False})

    # Process the language data to a standard format
    source_langs = list(filter(None, scrub_conf_data.get('source_lang').replace(' ', '').split(',')))
    for i, source_lang in enumerate(source_langs):
        if source_lang == 'c':
            source_langs[i] = 'cpp'
        elif source_lang == 'j':
            source_langs[i] = 'java'
        elif source_lang == 'p':
            source_langs[i] = 'python'
        elif source_lang == 'js':
            source_langs[i] = 'javascript'
    scrub_conf_data.update({'source_lang': ', '.join(source_langs)})

    # Make the source root absolute
    scrub_conf_data.update({'source_dir': pathlib.Path(scrub_conf_data.get('source_dir')).expanduser().resolve()})

    # Make access tokens absolute
    scrub_conf_data.update({'codesonar_cert': pathlib.Path(scrub_conf_data.get('codesonar_cert')).resolve()})
    scrub_conf_data.update({'codesonar_key': pathlib.Path(scrub_conf_data.get('codesonar_key')).resolve()})

    # Set the SCRUB analysis directory
    scrub_conf_data.update({'scrub_analysis_dir': scrub_conf_data.get('source_dir').joinpath('.scrub')})

    # Set the default filtering file locations
    if scrub_conf_data.get('analysis_filters') == '':
        analysis_filters_file = user_conf_file.parent.joinpath('SCRUBFilters')
        scrub_conf_data.update({'analysis_filters': analysis_filters_file})
    if scrub_conf_data.get('query_filters') == '':
        analysis_filters_file = user_conf_file.parent.joinpath('SCRUBExcludeQueries')
        scrub_conf_data.update({'query_filters': analysis_filters_file})
    if scrub_conf_data.get('collaborator_filters') == '':
        collaborator_filters = user_conf_file.parent.joinpath('SCRUBCollaboratorFilters')
        scrub_conf_data.update({'collaborator_filters': collaborator_filters})

    # Set the SCRUB working directory
    if (scrub_conf_data.get('scrub_working_dir') is None) or (scrub_conf_data.get('scrub_working_dir') == ''):
        scrub_working_dir = scrub_conf_data.get('scrub_analysis_dir')
    else:
        scrub_working_dir = pathlib.Path(scrub_conf_data.get('scrub_working_dir')).expanduser().resolve()
    scrub_conf_data.update({'scrub_working_dir': scrub_working_dir})

    # Make every *path variable absolute and make every *build_dir variable absolute
    for key in scrub_conf_data.keys():
        if re.search(r'.+path', key) and (scrub_conf_data.get(key) != ''):
            path_value = scrub_conf_data.get(key)
            #path_value = os.path.abspath(os.path.expanduser(path_value))
            path_value = pathlib.Path(path_value).expanduser().resolve()
            scrub_conf_data.update({key: path_value})

        elif re.search(r'.+build_dir', key):
            if scrub_conf_data.get(key) == '':
                scrub_conf_data.update({key: scrub_conf_data.get('source_dir')})
            elif not scrub_conf_data.get(key).startswith(str(scrub_conf_data.get('source_dir'))):
                path_value = scrub_conf_data.get(key)
                #path_value = os.path.abspath(os.path.expanduser(path_value))
                path_value = pathlib.Path(path_value).expanduser().resolve()
                scrub_conf_data.update({key: path_value})

    # Add SCRUB root path
    scrub_path = pathlib.Path(__file__).parents[1]
    scrub_conf_data.update({'scrub_path': scrub_path})

    # Add the log directory
    scrub_log_dir = scrub_conf_data.get('scrub_analysis_dir').joinpath('log_files')
    scrub_conf_data.update({'scrub_log_dir': scrub_log_dir})

    # Add the raw results directory
    raw_results_dir = scrub_conf_data.get('scrub_analysis_dir').joinpath('raw_results')
    scrub_conf_data.update({'raw_results_dir': raw_results_dir})

    # Add the SARIF results directory
    sarif_results_dir = scrub_conf_data.get('scrub_analysis_dir').joinpath('sarif_results')
    scrub_conf_data.update({'sarif_results_dir': sarif_results_dir})

    # Add the filtering output file
    filtering_output_file = scrub_conf_data.get('scrub_analysis_dir').joinpath('SCRUBAnalysisFilteringList')
    scrub_conf_data.update({'filtering_output_file': filtering_output_file})

    return scrub_conf_data


def initialize_storage_dir(scrub_conf_data):
    """This function handles setting up the SCRUB analysis storage directory

    Inputs:
        - scrub_conf_data: Dictionary of values read from configuration file [dict]
    """

    # Create the .scrub analysis directory
    if not scrub_conf_data.get('scrub_analysis_dir').exists():
        scrub_conf_data.get('scrub_analysis_dir').mkdir()
        scrub_conf_data.get('scrub_analysis_dir').chmod(0o666)

    # Create the logging directory
    if not scrub_conf_data.get('scrub_log_dir').exists():
        scrub_conf_data.get('scrub_log_dir').mkdir()
        scrub_conf_data.get('scrub_log_dir').chmod(0o666)

    # Create the output directory
    if not scrub_conf_data.get('raw_results_dir').exists():
        scrub_conf_data.get('raw_results_dir').mkdir()
        scrub_conf_data.get('raw_results_dir').chmod(0o666)

    # Create the SARIF results directory
    if not scrub_conf_data.get('sarif_results_dir').exists():
        scrub_conf_data.get('sarif_results_dir').mkdir()
        scrub_conf_data.get('sarif_results_dir').chmod(0o666)

    # Create the analysis directory if it doesn't exist
    if scrub_conf_data.get('scrub_working_dir') != scrub_conf_data.get('scrub_analysis_dir'):
        if scrub_conf_data.get('scrub_working_dir').exists():
            print('ERROR: SCRUB storage directory ' + str(scrub_conf_data.get('scrub_working_dir')) +
                  ' already exists. Aborting analysis.')
            sys.exit(10)
        else:
            # Create the scrub working dir
            scrub_conf_data.get('scrub_working_dir').mkdir()
            scrub_conf_data.get('scrub_working_dir').chmod(0o666)
