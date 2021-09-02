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
        # Get the templates for the language
        if scrub_conf_data.get('source_lang') == 'c':
            template_search_string = 'templates/c/*.template'
        elif scrub_conf_data.get('source_lang') == 'j':
            template_search_string = 'templates/java/*.template'
        elif scrub_conf_data.get('source_lang') == 'p':
            template_search_string = 'templates/python/*.template'
        else:
            sys.exit()

        # Search for analysis templates
        analysis_templates = glob.glob(scrub_path + '/tools/' + template_search_string)

        # Perform analysis using the template
        for analysis_template in analysis_templates:
            # Get the tool name
            tool_name = os.path.splitext(os.path.basename(analysis_template))[0]

            # Create the log file
            analysis_log_file = scrub_conf_data.get('scrub_log_dir') + '/' + tool_name + '.log'
            scrub_utilities.create_logger(analysis_log_file)

            # Print a status message
            logging.info('')
            logging.info('Attempt ' + tool_name + ' analysis: ' +
                         str(scrub_conf_data.get(tool_name.lower() + '_warnings')))

            # Initialize execution status
            tool_execution_status = 2

            if scrub_conf_data.get(tool_name.lower() + '_warnings'):
                # Print a status message
                logging.info('  Parsing ' + tool_name + ' template file...')

                # Create the analysis directory
                tool_analysis_dir = os.path.normpath(scrub_conf_data.get('scrub_analysis_dir') + '/' + tool_name +
                                                     '_analysis')
                scrub_conf_data.update({'tool_analysis_dir': tool_analysis_dir})
                os.mkdir(tool_analysis_dir)

                # Create the analysis template
                analysis_script = scrub_utilities.parse_template(analysis_template, tool_name, scrub_conf_data)

                # # Read in the analysis template
                # with open(analysis_template, 'r') as input_fh:
                #     analysis_template_data = input_fh.read()
                #
                # # Replace all of the variables with config data
                # for key in scrub_conf_data.keys():
                #     analysis_template_data = analysis_template_data.replace('${{' + key.upper() + '}}',
                #                                                             str(scrub_conf_data.get(key)))
                #
                # # Write out the completed template
                # completed_analysis_script = os.path.normpath(scrub_conf_data.get('scrub_analysis_dir') + '/' +
                #                                              tool_name + '.sh')
                # with open(completed_analysis_script, 'w') as output_fh:
                #     output_fh.write('%s' % analysis_template_data)
                #
                # # Update the permissions to allow for execution
                # os.chmod(completed_analysis_script, 775)

                try:
                    # Execute the analysis
                    scrub_utilities.execute_command(analysis_script, os.environ.copy())

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
