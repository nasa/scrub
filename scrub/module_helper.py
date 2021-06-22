import sys
import os
import importlib
import shutil
import argparse
from scrub.utils.filtering import do_filtering
from scrub.utils import scrub_utilities


def parse_arguments():
    """This function handles argument parsing in preparation for analysis."""

    # Create the parser
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=main.__doc__)

    # Add parser arguments
    parser.add_argument('--config', default='./scrub.cfg')
    parser.add_argument('--module', required=True)

    # Parse the arguments
    args = vars(parser.parse_args(sys.argv[2:]))

    # Run analysis
    main(args['module'], args['config'])


def main(scrub_module, conf_file='/.scrub.cfg'):
    """
    This function runs a single analysis module, while preserving existing analysis results.

    Inputs:
        --module: Tool import location of the form scrub.tools.<tool>.do_<tool> [string]
        --config: Absolute path to the SCRUB configuration file to be used [string]
    """

    # Read in the configuration data
    scrub_conf_data = scrub_utilities.parse_common_configs(conf_file)

    # Initialize the SCRUB storage directory
    scrub_utilities.initialize_storage_dir(scrub_conf_data)

    try:

        # Import the module
        module_object = importlib.import_module(scrub_module)

        # Call the analysis
        tool_status = getattr(module_object, "run_analysis")(scrub_conf_data, True)

        # Run filtering, if necessary
        if (scrub_module.startswith('scrub.tool')) and (tool_status == 0):
            # Filter and distribute the results
            do_filtering.run_analysis(scrub_conf_data)

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
