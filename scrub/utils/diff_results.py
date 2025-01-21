import os
import sys
import argparse
import pathlib
from scrub.utils import scrub_utilities


def parse_arguments():
    """This function handles argument parsing in preparation for diff utility."""

    # Create the parser
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=diff.__doc__)

    # Add parser arguments
    parser.add_argument('--baseline-scrub', required=True)
    parser.add_argument('--comparison-scrub', required=True)

    # Parse the arguments
    args = vars(parser.parse_args(sys.argv[2:]))

    # Run analysis
    diff(pathlib.Path(args['baseline_scrub']).resolve(), pathlib.Path(args['comparison_scrub']).resolve())


def diff(baseline_scrub_root, comparison_scrub_root):
    """This function diffs two sets of SARIF results directories.

    NOTE: This function depends on the open-source SARIF parsing library "sarif-tools"
          https://github.com/microsoft/sarif-tools/tree/main

    Inputs:
        - baseline_scrub_root: Absolute path to baseline SARIF results directory [string]
        - comparison_scrub_root: Absolute path to comparison SARIF results directory [string]

    Outputs:
        - None
    """

    # Find all the SARIF files in each directory
    baseline_sarif_files = baseline_scrub_root.joinpath('sarif_results').glob('*.sarif')
    comparison_sarif_files = comparison_scrub_root.joinpath('sarif_results').glob('*.sarif')

    for comparison_file in comparison_sarif_files:
        for baseline_file in baseline_sarif_files:
            if comparison_file.stem == baseline_file.stem:
                # Set the output file
                output_file = 'diff_' + comparison_file.name + '.json'

                # Set the command call
                command_call = 'sarif diff -o {} {} {}'.format(output_file, baseline_file, comparison_file)

                # Set the environment for execution
                user_env = os.environ.copy()

                # Execute the analysis
                scrub_utilities.execute_command(command_call, user_env)
