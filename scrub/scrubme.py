import glob
import importlib
import os
import re
import shutil
import sys
import argparse
from scrub.utils import do_clean
from scrub.utils import scrub_utilities


def parse_arguments():
    """This function parse command line arguments in preparation for analysis."""

    # Create the parser
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=main.__doc__)

    # Add parser arguments
    parser.add_argument('--config', default='./scrub.cfg')

    # Parse the arguments
    args = vars(parser.parse_args(sys.argv[2:]))

    # Run analysis
    main(args['config'])


def main(conf_file=None):
    """
    This function runs all applicable tools present within the configuration file.

    Inputs:
        - config: Path to SCRUB configuration file [string] [optional]
            Default value: ./scrub.cfg
    """

    # Set the conf file to be used
    if conf_file:
        scrub_conf_file = os.path.abspath(conf_file)

    else:
        scrub_conf_file = os.path.abspath('scrub.cfg')

    # Read in the configuration data
    scrub_conf_data = scrub_utilities.parse_common_configs(scrub_conf_file)

    # Initialize variables
    execution_status = []
    scrub_path = os.path.dirname(os.path.realpath(__file__))

    # Clean the previous SCRUB data from the current directory
    do_clean.clean_directory(scrub_conf_data.get('source_dir'))

    # Initialize the SCRUB storage directory
    scrub_utilities.initialize_storage_dir(scrub_conf_data)

    # Make a copy of the scrub.cfg file and add it to the log
    shutil.copyfile(scrub_conf_file, os.path.normpath(scrub_conf_data.get('scrub_analysis_dir') + '/scrub.cfg'))

    try:
        # Search for analysis modules
        tool_modules = glob.glob(scrub_path + '/tools/*/do*.py')

        # If the custom module exists, place it last
        for module in tool_modules:
            if module.endswith('do_custom.py'):
                tool_modules.remove(module)
                tool_modules.append(module)
                break

        # Add the filtering module
        tool_modules = tool_modules + glob.glob(scrub_path + '/utils/*/do_*.py')

        # Loop through every tool and perform analysis
        for tool_module in tool_modules:
            # Form the call string
            module_name = 'scrub.' + re.split('\\.py', os.path.relpath(tool_module, scrub_path))[0].replace('/', '.')

            # Import the module
            module_object = importlib.import_module(module_name)

            # Call the analysis
            tool_status = getattr(module_object, "run_analysis")(scrub_conf_data)

            # Add the status to the execution status log
            execution_status.append([module_name, tool_status])

            # Check to see if a python error has occurred
            if tool_status == 100:
                sys.exit(tool_status)

    finally:
        # Move the results back with the source code if necessary
        if scrub_conf_data.get('scrub_working_dir') != scrub_conf_data.get('scrub_analysis_dir'):
            # Move every item in the directory
            for item in os.listdir(scrub_conf_data.get('scrub_working_dir')):
                shutil.move(scrub_conf_data.get('scrub_working_dir') + '/' + item,
                            scrub_conf_data.get('scrub_analysis_dir') + '/' + item)

            # Remove the working directory
            shutil.rmtree(scrub_conf_data.get('scrub_working_dir'))

        # Print a status message
        tool_failure_count = 0
        print('')
        print('Tool Execution Status:')
        for status in execution_status:
            # Decode the exit code
            if status[1] == 0:
                exit_code = 'Completed successfully'
            elif status[1] == 1:
                exit_code = 'Attempted analysis, did not complete'
                tool_failure_count = tool_failure_count + 1
            elif status[1] == 2:
                exit_code = 'Not attempted'
            elif status[1] == 100:
                exit_code = 'Fatal error'
            else:
                exit_code = 'Unknown error'

            # Print the status message
            print('\t%s: %s' % (status[0], exit_code))

    # Search for target modules
    target_modules = glob.glob(scrub_path + '/targets/*/do_*.py')

    # Loop through every tool and perform
    for target_module in target_modules:
        # Form the call string
        module_name = 'scrub.' + re.split('\\.py', os.path.relpath(target_module, scrub_path))[0].replace('/', '.')

        # Import the module
        module_object = importlib.import_module(module_name)

        # Call the analysis
        getattr(module_object, "run_analysis")(scrub_conf_data)

    # Set the exit code
    sys.exit(tool_failure_count)
