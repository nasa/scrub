import sys
import os
import traceback
import importlib
import shutil
import logging
import argparse
from scrub.utils.filtering import do_filtering
from scrub.utils import scrub_utilities


def parse_arguments():
    """This function handles argument parsing in preparation for analysis."""

    # Create the parser
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=main.__doc__)

    # Add parser arguments
    parser.add_argument('--config', default='./scrub.cfg')
    parser.add_argument('--tool', default=None)
    parser.add_argument('--template', default=None)

    # Parse the arguments
    args = vars(parser.parse_args(sys.argv[2:]))

    # Make sure all the required inputs are present
    if not args['tool'] and args['template']:
        args['tool'] = os.path.basename(args['template']).split('.')[0]


    # Run analysis
    main(args['tool'], args['config'])



def main(template_path, conf_file='/.scrub.cfg'):
    """
    This function runs a single analysis module, while preserving existing analysis results.

    Inputs:
        --analysis: Name of tool that needs to be run or path to custom template file to be executed [string]
        --config: Absolute path to the SCRUB configuration file to be used [string]
    """

    # Read in the configuration data
    scrub_conf_data = scrub_utilities.parse_common_configs(conf_file)

    # Get the tool name
    tool_name = ''

    # Initialize the SCRUB storage directory
    scrub_utilities.initialize_storage_dir(scrub_conf_data)
    scrub_path = os.path.dirname(os.path.realpath(__file__))

    # Find the template of interest
    # template_path = (scrub_path + '/tools/templates/' + scrub_conf_data.get('source_lang') + '/' +
    #                  tool_name.lower() + '.template')

    # Attempt analysis if the template exists
    if os.path.exists(template_path):
        try:
            # Create the log file
            analysis_log_file = scrub_conf_data.get('scrub_log_dir') + '/' + tool_name + '.log'
            scrub_utilities.create_logger(analysis_log_file)

            # Print a status message
            logging.info('  Parsing ' + tool_name + ' template file...')

            # Remove the analysis directory if it exists
            tool_analysis_dir = os.path.normpath(scrub_conf_data.get('scrub_analysis_dir') + '/' + tool_name +
                                                 '_analysis')
            if os.path.exists(tool_analysis_dir):
                shutil.rmtree(tool_analysis_dir)

            # Create the analysis directory
            scrub_conf_data.update({'tool_analysis_dir': tool_analysis_dir})
            os.mkdir(tool_analysis_dir)

            # Create the analysis template
            analysis_script = scrub_utilities.parse_template(template_path, tool_name, scrub_conf_data)

            try:
                # Execute the analysis
                scrub_utilities.execute_command(analysis_script, os.environ.copy())

                # Filter and distribute the results
                do_filtering.run_analysis(scrub_conf_data)

            except scrub_utilities.CommandExecutionError:
                logging.warning(tool_name + ' analysis could not be performed.')

                # Print the exception traceback
                logging.warning(traceback.format_exc())

            finally:
                # Close the logger
                logging.getLogger().handlers = []

        finally:
            # Move the results back with the source code if necessary
            if scrub_conf_data.get('scrub_working_dir') != scrub_conf_data.get('scrub_analysis_dir'):
                # Move every item in the directory
                for item in os.listdir(scrub_conf_data.get('scrub_working_dir')):
                    # Remove the item if it exists
                    if os.path.exists(scrub_conf_data.get('scrub_analysis_dir') + '/' + item):
                        if os.path.isfile(scrub_conf_data.get('scrub_analysis_dir') + '/' + item):
                            os.remove(scrub_conf_data.get('scrub_analysis_dir') + '/' + item)
                        else:
                            shutil.rmtree(scrub_conf_data.get('scrub_analysis_dir') + '/' + item)

                    # Move the item
                    shutil.move(scrub_conf_data.get('scrub_working_dir') + '/' + item,
                                scrub_conf_data.get('scrub_analysis_dir') + '/' + item)

                # Remove the working directory
                shutil.rmtree(scrub_conf_data.get('scrub_working_dir'))

    elif tool_name == 'filter':
        # Filter and distribute the results
        do_filtering.run_analysis(scrub_conf_data)

    elif tool_name == 'collaborator':
        # Import the module
        module_object = importlib.import_module('scrub.targets.collaborator.do_collaborator')

        # Call the analysis
        getattr(module_object, "run_analysis")(scrub_conf_data, True)

    else:
        sys.exit('ERROR: Template does not exist.')
