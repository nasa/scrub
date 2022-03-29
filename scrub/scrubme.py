import glob
import importlib
import os
import re
import shutil
import sys
import argparse
import logging
import traceback
from scrub.utils.filtering import do_filtering
from scrub.utils import do_clean
from scrub.utils import scrub_utilities


def parse_arguments():
    """This function parse command line arguments in preparation for analysis."""

    # Create the parser
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=main.__doc__)

    # Add parser arguments
    parser.add_argument('--config', default='./scrub.cfg')
    parser.add_argument('--clean', action='store_true')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--quiet', action='store_true')
    parser.add_argument('--tools', nargs='+', default=None)
    parser.add_argument('--targets', nargs='+', default=None)

    # Parse the arguments
    args = vars(parser.parse_args(sys.argv[2:]))

    # Set the logging level
    if args['debug']:
        logging_level = logging.DEBUG
    elif args['quiet']:
        logging_level = logging.CRITICAL
    else:
        logging_level = logging.INFO

    # Run analysis
    main(args['config'], args['clean'], logging_level, args['tools'], args['targets'])


def main(conf_file='./scrub.cfg', clean=False, console_logging=logging.INFO, tools=None, targets=None):
    """
    This function runs all applicable tools present within the configuration file.

    Inputs:
        - config: Path to SCRUB configuration file [string] [optional]
            Default value: ./scrub.cfg
        - clean: Should SCRUB clean existing results? [bool]
            Default value: False
        - console_logging: Logging level for console [int] [optional]
            Default value: logging.INFO (20)
        - tools: List of tools to run during analysis [list of strings] [optional]
            Default value: None
        - targets: List of output targets for exporting the analysis results [list of strings] [optional]
            Default value: None
    """

    # Read in the configuration data
    if os.path.exists(conf_file):
        scrub_conf_data = scrub_utilities.parse_common_configs(conf_file)
    else:
        sys.exit('ERROR: Configuration file ' + conf_file + ' does not exist.')

    # Initialize variables
    execution_status = []
    scrub_path = os.path.dirname(os.path.realpath(__file__))

    # Clean the previous SCRUB data from the current directory
    if clean:
        do_clean.clean_directory(scrub_conf_data.get('source_dir'))

    # Initialize the SCRUB storage directory
    scrub_utilities.initialize_storage_dir(scrub_conf_data)

    # Make a copy of the scrub.cfg file and add it to the log
    shutil.copyfile(conf_file, os.path.normpath(scrub_conf_data.get('scrub_analysis_dir') + '/scrub.cfg'))

    try:
        # Handle legacy language selections
        if scrub_conf_data.get('source_lang') == 'j':
            scrub_conf_data.update({'source_lang': 'java'})
        if scrub_conf_data.get('source_lang') == 'p':
            scrub_conf_data.update({'source_lang': 'python'})

        # Get the templates for the language
        available_analysis_templates = glob.glob(scrub_path + '/tools/templates/' + scrub_conf_data.get('source_lang') +
                                                 '/*.template')

        # Append the custom templates if provided
        if scrub_conf_data.get('custom_templates'):
            available_analysis_templates = (available_analysis_templates +
                                            scrub_conf_data.get('custom_templates').replace('\"', '').split(','))

        # Check to make sure at least one possible template has been identified
        if len(available_analysis_templates) == 0:
            print('WARNING: No analysis templates have been found.')

        # Update the analysis templates to be run
        if tools == 'filter' or tools == 'filtering':
            analysis_templates = []
        elif tools:
            analysis_templates = []
            for template in available_analysis_templates:
                for tool in tools:
                    if template.endswith(tool + '.template'):
                        analysis_templates.append(template)
                        scrub_conf_data.update({tool.lower() + '_warnings': True})
        else:
            analysis_templates = available_analysis_templates

        # Perform analysis using the template
        for analysis_template in analysis_templates:
            # Get the tool name
            tool_name = os.path.splitext(os.path.basename(analysis_template))[0]

            # Initialize execution status
            tool_execution_status = 2

            if scrub_conf_data.get(tool_name.lower() + '_warnings'):
                # Initialize variables
                analysis_scripts_dir = os.path.normpath(scrub_conf_data.get('scrub_analysis_dir') + '/analysis_scripts')
                analysis_script = os.path.normpath(analysis_scripts_dir + '/' + tool_name + '.sh')
                tool_analysis_dir = os.path.normpath(scrub_conf_data.get('scrub_analysis_dir') + '/' + tool_name +
                                                     '_analysis')

                # Add derived values to configuration values
                scrub_conf_data.update({'tool_analysis_dir': tool_analysis_dir})

                # Create the analysis scripts directory
                if not os.path.exists(analysis_scripts_dir):
                    os.mkdir(analysis_scripts_dir)

                # Create the tool analysis directory
                if os.path.exists(tool_analysis_dir):
                    shutil.rmtree(tool_analysis_dir)
                os.mkdir(tool_analysis_dir)

                # Create the log file
                analysis_log_file = scrub_conf_data.get('scrub_log_dir') + '/' + tool_name + '.log'
                scrub_utilities.create_logger(analysis_log_file, console_logging)

                # Print a status message
                logging.info('')
                logging.info('  Configuration values...')

                # Print general configuration values
                logging.info('    SOURCE_DIR: ' + scrub_conf_data.get('source_dir'))
                logging.info('    TOOL_ANALYSIS_DIR: ' + scrub_conf_data.get('scrub_working_dir') + '/' + tool_name +
                             '_analysis')

                # Print tool specific configuration values
                for config_value in scrub_conf_data.keys():
                    if config_value.startswith(tool_name):
                        logging.info('    ' + config_value.upper() + ': ' + str(scrub_conf_data.get(config_value)))

                # Print a status message
                logging.info('')
                logging.info('  Parsing ' + tool_name + ' template file...')

                # Create the analysis template
                scrub_utilities.parse_template(analysis_template, analysis_script, scrub_conf_data)

                # Update the permissions of the analysis script
                # os.chmod(analysis_script, 0o777)

                try:
                    # Set the environment for execution
                    user_env = os.environ.copy()

                    # Update the environment
                    if 'PYTHONPATH' in user_env.keys():
                        user_env.update({'PYTHONPATH': user_env.get('PYTHONPATH') + ':' +
                                        os.path.normpath(scrub_path + '/../')})
                    else:
                        user_env.update({'PYTHONPATH': os.path.normpath(scrub_path + '/../')})

                    # Execute the analysis
                    scrub_utilities.execute_command(analysis_script, user_env)

                    # Check the tool analysis directory
                    scrub_utilities.check_artifact(tool_analysis_dir, True)

                    # Check the raw results files
                    for raw_results_file in glob.glob(os.path.join(scrub_conf_data['raw_results_dir'],
                                                                   tool_name + '_*.scrub')):
                        scrub_utilities.check_artifact(raw_results_file, False)

                    # Check the log file
                    scrub_utilities.check_artifact(analysis_log_file, True)

                    # Update the execution status
                    tool_execution_status = 0

                except scrub_utilities.CommandExecutionError:
                    logging.warning(tool_name + ' analysis could not be performed.')

                    # Print the exception traceback
                    logging.warning(traceback.format_exc())

                    #  Update the execution status
                    tool_execution_status = 1

                finally:
                    # Close the logger
                    logging.getLogger().handlers = []

            # Update the execution status
            execution_status.append([tool_name, tool_execution_status])

        # Perform filtering
        filtering_status = do_filtering.run_analysis(scrub_conf_data)

        # Update the execution status
        execution_status.append(['filtering', filtering_status])

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
    available_target_modules = glob.glob(scrub_path + '/targets/*/do_*.py')

    # Handle legacy Collaborator tag
    if 'collaborator_upload' in scrub_conf_data.keys():
        scrub_conf_data.update({'collaborator_export': scrub_conf_data.get('collaborator_upload')})
    else:
        scrub_conf_data.update({'collaborator_export': False})

    # Update the targets to be run
    if targets:
        target_modules = []
        for module_path in available_target_modules:
            for target in targets:
                if target in os.path.basename(module_path):
                    target_modules.append(module_path)
                    scrub_conf_data.update({target.lower() + '_export': True})
    else:
        target_modules = available_target_modules

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
