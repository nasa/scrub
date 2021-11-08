import os
import sys
import glob
import argparse
from scrub.tools.parsers import translate_results


def parse_arguments():
    """This function handles argument parsing in preparation for diff utility."""

    # Create the parser
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=diff.__doc__)

    # Add parser arguments
    parser.add_argument('--baseline-source', required=True)
    parser.add_argument('--baseline-scrub', required=True)
    parser.add_argument('--comparison-source', required=True)
    parser.add_argument('--comparison-scrub', required=True)

    # Parse the arguments
    args = vars(parser.parse_args(sys.argv[2:]))

    # Run analysis
    diff(args['baseline_source'], args['baseline_scrub'], args['comparison_source'], args['comparison_scrub'])


def get_lines(source_file, line):
    """This function gets the line number from the source code file of interest

    Inputs:
        - file: Absolute path to the source code file of interest [string]
        - line: Line number of the file to retrieve [int]

    Outputs:
        - source_line: The line of interest from the source code file [string]
    """

    # Initialize variables
    source_lines = []

    # Import the source code data
    with open(source_file, 'r') as input_fh:
        input_data = input_fh.readlines()

    # Get a 3 lines of source code
    if (line >= 2) and (line <= len(input_data) - 1):
        comparison_source_target = [line - 1, line, line + 1]

    elif line == 1:
        comparison_source_target = [line, line + 1, line + 2]

    elif line >= len(input_data) - 1:
        comparison_source_target = [line - 2, line - 1, line]

    else:
        comparison_source_target = [0]

    # Get the source file line
    for i in comparison_source_target:
        if ((i - 1) <= len(input_data)) and (i != 0):
            source_lines.append(input_data[i - 1].strip())

    return source_lines


def make_warning_relative(warning, source_root):
    """This function makes a warning relative to a root location.

    Inputs:
        - warning: Dictionary containing the warning data [dict]
        - source_root: Absolute path to the source root directory [string]

    Outputs:
        - relative_warning: Dictionary containing the warning data relative to the source root directory [dict]
    """

    # Initialize variables
    relative_warning = warning.copy()

    # Update the file path
    relative_warning['file'] = os.path.relpath(relative_warning['file'], source_root)

    # Update the description
    for line in relative_warning['description']:
        relative_warning['description'][relative_warning['description'].index(line)] = line.replace(source_root + '/',
                                                                                                    '')

    return relative_warning


def find_exact_match(comparison_warning, baseline_warnings):
    """This functions checks to see if an exact match exists.

    Inputs:
        - comparison_warning: Dictionary containing warning data of interest [dict]
        - baseline_warnings: List of warning dictionaries to search [list of dicts]

    Outputs:
        exact_match: Is this an exact match with a baseline warning? [bool]
    """

    # Initialize variables
    exact_match = False

    # See if an exact match can be found
    for baseline_warning in baseline_warnings:
        if ((comparison_warning['file'] == baseline_warning['file']) and
                (comparison_warning['line'] == baseline_warning['line']) and
                (comparison_warning['description'] == baseline_warning['description'])):
            # Print a status message
            print('        >> Exact match found in baseline results: {}'.format(baseline_warning['id']))

            # Update the flag
            exact_match = True

    return exact_match


def find_probable_match(comparison_warning, baseline_warnings, comparison_source_root, baseline_source_root):
    """This function checks to see if a corresponding baseline warning can be found.

    Inputs:
        - comparison_warning: Dictionary containing warning data of interest [dict]
        - baseline_warnings: List of warning dictionaries to search [list of dicts]
        - comparison_source_root: Absolute path to comparison source root directory [string]
        - baseline_source_root: Absolute path to baseline source root directory [string]

    Outputs:
        - probable_match: Is this a probable match with a baseline warning? [bool]
    """

    # Initialize variables
    probable_match = False

    comparison_source_lines = get_lines(comparison_source_root + '/' + comparison_warning['file'],
                                        comparison_warning['line'])

    # Search through all of the baseline warnings and get the corresponding data
    for baseline_warning in baseline_warnings:
        # Check to see if the warning query and warning file match
        if ((baseline_warning['file'] == comparison_warning['file']) and
                (baseline_warning['query'] == comparison_warning['query'])):
            # Get the baseline source file line
            baseline_source_lines = get_lines(baseline_source_root + '/' + baseline_warning['file'],
                                              baseline_warning['line'])

            # Check to see if the source file lines match
            if baseline_source_lines == comparison_source_lines:
                # Update the flag
                probable_match = True

                # Print a status message
                print('        >> Probable match found in baseline results: {}'.format(baseline_warning['id']))

    return probable_match


def diff(baseline_source_root, baseline_scrub_root, comparison_source_root, comparison_scrub_root):
    """
    This function compares a set of static analysis results to a defined baseline set of results.

    Inputs:
        --baseline_source: Absolute path to baseline source root directory [string]
        --baseline_scrub: Absolute path to the baseline SCRUB working directory [string]
        --comparison_source: Absolute path to comparison source root directory [string]
        --comparison_scrub: Absolute path to the comparison SCRUB working directory [string]
    """

    # Find all of the SCRUB files in comparison results
    comparison_scrub_files = glob.glob(comparison_scrub_root + '/*[!_diff].scrub')

    # Iterate through every SCRUB file and remove baseline results
    for comparison_scrub_file in comparison_scrub_files:
        # Print a status message
        print('Examining comparison results file: {}'.format(comparison_scrub_file))

        # Import the comparison SCRUB file data
        comparison_warnings = translate_results.parse_scrub(comparison_scrub_file, comparison_source_root)

        # Make a copy of the results
        comparison_warnings_diff = comparison_warnings.copy()

        # Find the corresponding baseline results file
        baseline_scrub_file = os.path.normpath(baseline_scrub_root + '/' + os.path.basename(comparison_scrub_file))

        # Check to make sure the baseline file exists
        if os.path.exists(baseline_scrub_file):
            # Import the baseline results
            baseline_warnings = translate_results.parse_scrub(baseline_scrub_file, baseline_source_root)

            # Make the baseline warning_relative
            relative_baseline_warnings = []
            for baseline_warning in baseline_warnings:
                relative_baseline_warnings.append(make_warning_relative(baseline_warning, baseline_source_root))

            # Iterate through every warning
            for comparison_warning in comparison_warnings:
                # Make the warning relative
                relative_comparison_warning = make_warning_relative(comparison_warning, comparison_source_root)

                # Print a status message
                print('    >> Searching for warning: {}'.format(comparison_warning['id']))

                # See if an exact match can be found
                exact_match = find_exact_match(relative_comparison_warning, relative_baseline_warnings)

                # See if a probable match can be found
                if exact_match:
                    comparison_warnings_diff.remove(comparison_warning)

                if not exact_match:
                    # Print a status message
                    print('        >> No exact match found. Attempting to find probable match.')

                    probable_match = find_probable_match(relative_comparison_warning, relative_baseline_warnings,
                                                         comparison_source_root, baseline_source_root)

                    # Print a status message
                    if probable_match:
                        comparison_warnings_diff.remove(comparison_warning)

                    if not probable_match:
                        print('        >> No probable match found.')

        else:
            # Print a warning message
            print('    >> Baseline results file {} does not exist.'.format(baseline_scrub_file))
            print('    >> All results are new.')

        # Create the output file path
        diff_output_file = (comparison_scrub_root + '/' +
                            os.path.basename(comparison_scrub_file).replace('.scrub', '') + '_diff.scrub')

        # Write out the results
        translate_results.create_scrub_output_file(comparison_warnings_diff, diff_output_file)
