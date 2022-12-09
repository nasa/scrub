import glob
import importlib
import os
import re
import shutil
import sys
import time
import argparse
import logging
import traceback
import pathlib
from scrub import __version__
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
    parser.add_argument('--tools', nargs='+', default=[])
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
    main(pathlib.Path(args['config']).resolve(), args['clean'], logging_level, args['tools'], args['targets'])


def main(conf_file=pathlib.Path('./scrub.cfg').resolve(), clean=False, console_logging=logging.INFO, tools=None,
         targets=None):
    """
    This function runs all applicable tools present within the configuration file.

    Inputs:
        - config: Path to SCRUB configuration file [Path object] [optional]
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
    if conf_file.exists():
        scrub_conf_data = scrub_utilities.parse_common_configs(conf_file)
    else:
        print('ERROR: Configuration file ' + str(conf_file) + ' does not exist.')
        sys.exit(10)

    # Initialize variables
    execution_status = []
    scrub_path = pathlib.Path(__file__).resolve().parent

    # Clean the previous SCRUB data from the current directory
    if clean:
        do_clean.clean_directory(scrub_conf_data.get('source_dir'))

    # Initialize the SCRUB storage directory
    scrub_utilities.initialize_storage_dir(scrub_conf_data)

    # Make sure the working directory exists
    if not scrub_conf_data.get('scrub_working_dir').exists():
        print('ERROR: Working directory ' + str(scrub_conf_data.get('scrub_working_dir')) + ' does not exist.')
        sys.exit(10)

    # Make a copy of the scrub.cfg file and add it to the log
    shutil.copyfile(conf_file, str(scrub_conf_data.get('scrub_analysis_dir').joinpath('scrub.cfg')))

    # Create a VERSION file
    with open(str(scrub_conf_data.get('scrub_analysis_dir').joinpath('VERSION')), 'w') as output_fh:
        output_fh.write(__version__)

    try:
        # Get the templates
        available_analysis_templates = list(scrub_path.glob('tools/templates/*template'))

        # Append the custom templates if provided
        if scrub_conf_data.get('custom_templates'):
            available_analysis_templates = (available_analysis_templates +
                                            scrub_conf_data.get('custom_templates').replace('\"', '').split(','))

        # Check to make sure at least one possible template has been identified
        if len(available_analysis_templates) == 0:
            print('WARNING: No analysis templates have been found.')

        # Update the analysis templates to be run
        perform_filtering = True
        if ('filter' in tools) or ('filtering' in tools):
            analysis_templates = []
        elif 'none' in tools:
            analysis_templates = []
            perform_filtering = False
        elif tools:
            analysis_templates = []
            for template in available_analysis_templates:
                for tool in tools:
                    if template.name  == tool + '.template':
                        analysis_templates.append(template)
                        scrub_conf_data.update({tool.lower() + '_warnings': True})
        else:
            analysis_templates = available_analysis_templates

        # Perform analysis using the template
        for analysis_template in analysis_templates:
            # Initialize variables
            execution_time = 0

            # Get the tool name
            tool_name = analysis_template.stem

            # Initialize execution status
            tool_execution_status = 2

            if scrub_conf_data.get(tool_name.lower() + '_warnings'):
                # Initialize variables
                analysis_scripts_dir = scrub_conf_data.get('scrub_analysis_dir').joinpath('analysis_scripts')
                analysis_script = analysis_scripts_dir.joinpath(tool_name + '.sh')
                tool_analysis_dir = scrub_conf_data.get('scrub_working_dir').joinpath(tool_name + '_analysis')

                # Add derived values to configuration values
                scrub_conf_data.update({'tool_analysis_dir': tool_analysis_dir})

                # Create the analysis scripts directory
                if not analysis_scripts_dir.exists():
                    analysis_scripts_dir.mkdir()

                # Create the tool analysis directory
                if tool_analysis_dir.exists():
                    shutil.rmtree(tool_analysis_dir)
                tool_analysis_dir.mkdir()

                # Create the log file
                analysis_log_file = scrub_conf_data.get('scrub_log_dir').joinpath(tool_name + '.log')
                scrub_utilities.create_logger(analysis_log_file, console_logging)

                # Print a status message
                logging.info('')
                logging.info('  Configuration values...')

                # Print general configuration values
                logging.info('    SOURCE_DIR: ' + str(scrub_conf_data.get('source_dir')))
                logging.info('    TOOL_ANALYSIS_DIR: ' + str(tool_analysis_dir))

                # Print tool specific configuration values
                for config_value in scrub_conf_data.keys():
                    if config_value.startswith(tool_name):
                        logging.info('    ' + config_value.upper() + ': ' + str(scrub_conf_data.get(config_value)))

                # Print a status message
                logging.info('')
                logging.info('  Parsing ' + tool_name + ' template file...')

                # Create the analysis template
                scrub_utilities.parse_template(analysis_template, analysis_script, scrub_conf_data)

                try:
                    # Start the timer
                    start_time = time.time()

                    # Set the environment for execution
                    user_env = os.environ.copy()

                    # Update the environment
                    if 'PYTHONPATH' in user_env.keys():
                        user_env.update({'PYTHONPATH': user_env.get('PYTHONPATH') + ':' + str(scrub_path.parent)})
                    else:
                        user_env.update({'PYTHONPATH': str(scrub_path.parent)})

                    # Execute the analysis and track execution time
                    scrub_utilities.execute_command(str(analysis_script), user_env)

                    # Check the tool analysis directory
                    scrub_utilities.check_artifact(tool_analysis_dir, True)

                    # Check the raw results files
                    for raw_results_file in scrub_conf_data.get('raw_results_dir').glob(tool_name + '_*.scrub'):
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

                    # Calculate the execution time
                    execution_time = time.time() - start_time

            # Update the execution status
            execution_status.append([tool_name, tool_execution_status, execution_time])

        # Perform filtering and track execution time, if necessary
        if perform_filtering:
            start_time = time.time()
            filtering_status = do_filtering.run_analysis(scrub_conf_data, console_logging)
            execution_time = time.time() - start_time

            # Update the execution status
            execution_status.append(['filtering', filtering_status, execution_time])

    finally:
        # Move the results back with the source code if necessary
        if scrub_conf_data.get('scrub_working_dir') != scrub_conf_data.get('scrub_analysis_dir'):
            # Move every item in the directory
            for item in scrub_conf_data.get('scrub_working_dir').iterdir():
                # Remove the destination directory, if it exists
                if scrub_conf_data.get('scrub_analysis_dir').joinpath(item.stem).exists():
                    shutil.rmtree(scrub_conf_data.get('scrub_analysis_dir').joinpath(item.stem))

                # Move the contents
                shutil.move(item, scrub_conf_data.get('scrub_analysis_dir').joinpath(item.stem))

            # Remove the working directory
            shutil.rmtree(scrub_conf_data.get('scrub_working_dir'))

        # Create a visible directory of results
        viewable_results_dir = scrub_conf_data.get('source_dir').joinpath('scrub_results')
        if viewable_results_dir.exists():
            shutil.rmtree(viewable_results_dir)
        viewable_results_dir.mkdir()

        # Copy SCRUB format output files
        for scrub_file in scrub_conf_data.get('scrub_analysis_dir').glob('*.scrub'):
            shutil.copy(scrub_file, viewable_results_dir.joinpath(scrub_file.name))

        # Copy the SARIF format output files
        for sarif_file in scrub_conf_data.get('sarif_results_dir').glob('*.sarif'):
            shutil.copy(sarif_file, viewable_results_dir.joinpath(sarif_file.name))

        # Print a status message
        tool_failure_count = 0
        total_execution_time = 0
        print('\nTool Execution Status:\n')
        for status in execution_status:
            # Track the execution time
            total_execution_time = total_execution_time + status[2]

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
            print('\t%s | %s: %s' % (time.strftime("%H:%M:%S", time.gmtime(status[2])), status[0], exit_code))
            print('\t--------------------------------------------------')

        # Print the execution time
        print('\n\tTotal Execution Time: %s\n' % time.strftime("%H:%M:%S", time.gmtime(total_execution_time)))

    # Search for target modules
    available_target_modules = scrub_path.glob('targets/*/do_*.py')

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
                if target in str(module_path.parent):
                    target_modules.append(module_path)
                    scrub_conf_data.update({target.lower() + '_export': True})
                    scrub_conf_data.update({target.lower() + '_upload': True})
    else:
        target_modules = available_target_modules

    # Loop through every tool and perform
    for target_module in target_modules:
        # Form the call string
        module_name = 'scrub.' + str(target_module.relative_to(scrub_path))[0:-3].replace('/', '.')

        # Import the module
        module_object = importlib.import_module(module_name)

        # Call the analysis
        getattr(module_object, "run_analysis")(scrub_conf_data, console_logging)

    # Set the exit code
    sys.exit(tool_failure_count)
