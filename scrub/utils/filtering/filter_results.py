import re
import pathlib
import logging
from scrub.tools.parsers import translate_results


# Initialize variables
# 'compiler': ['compiler', 'cmp', 'gbuild', 'dblchck', 'doublecheck', 'javac', 'pylint'],
suppression_lines = []
filtering_aliases = {'gcc': ['cmp', 'compiler', 'gcc'],
                     'gbuild': ['cmp', 'compiler', 'gbuild', 'dblchck', 'doublecheck'],
                     'javac': ['cmp', 'compiler', 'javac'],
                     'pylint': ['cmp', 'compiler', 'pylint'],
                     'coverity': ['coverity', 'cov'],
                     'codesonar': ['codesonar', 'cdsnr']
                     }


def micro_filter_check(source_file, warning_line, valid_warning_types):
    """This function checks to see if a warning has been marked as a false positive by the user.

    Inputs:
        - source_file: Absolute path to the source code file of interest [string]
        - warning_line: Line of interest of source code file [int]
        - valid_warning_types: List of strings containing valid types for each tool [list of strings]

    Outputs:
        - ignore_line: Indicator if warning should be ignored [bool]
    """
    # Set the base string
    ignore_base = "scrub_ignore_warning"

    # Initialize the return value
    ignore_line = False

    try:
        # Get the line of interest
        with open(source_file, 'r', errors='ignore') as input_fh:
            # Read the lines
            if warning_line == 0:
                line = input_fh.readlines()[0]
            else:
                line = input_fh.readlines()[warning_line - 1]

        # Check for suppression syntax
        if (ignore_base in line.lower()) or ('@suppress' in line.lower()):
            for check_type in valid_warning_types:
                if line.lower().strip().endswith(check_type):
                    # Print a status message
                    logging.debug('\tWarning removed - Warning has been marked as a false positive')
                    logging.debug('\t\t%s', line)

                    # Update the output
                    ignore_line = True

                    break

    except IOError:
        logging.warning('\t\tMicro-filter warning')
        logging.warning('\t\tFile %s could not be found.', source_file)

    # Return value
    return ignore_line


def ignore_query_check(warning_tool, warning_query, ignore_queries_file):
    """This function checks if a result should be skipped based on the type of query.

    Inputs:
        - line: Line of interest from SCRUB results [string]
        - ignore_queries_file: Full path to the SCRUBExcludeQueries file [string]

    Outputs:
        - skip: Indicator if result should be filtered out [bool]
    """

    # Initialize the variables
    skip = False

    # Import the ignore data
    if ignore_queries_file.is_file():
        with open(ignore_queries_file, 'r') as ignore_fh:
            ignore_queries = ignore_fh.readlines()

        # Iterate through every line of the ignore data
        for ignore_line in ignore_queries:
            # Split the line and store the values
            ignore_line_split = list(filter(None, re.split(':', ignore_line.strip())))
            ignore_tool = ignore_line_split[0].strip().lower()
            ignore_query = ignore_line_split[1].strip()

            # Determine if the ine should be skipped
            if (ignore_tool == warning_tool) and (ignore_query == warning_query):
                skip = True

                # Print a status message
                logging.debug('\tWarning removed - Warning generated by a filtered query')
                logging.debug('\t\t%s: %s', warning_tool, warning_query)

    return skip


def external_warning_check(warning_file, source_root):
    """This function checks to see if a warning originates outside the source code directory.

    Inputs:
        - warning_file:
        - source_root: Full path to the top level directory of the source code [string]

    Outputs:
        - skip: Indicator if result should be filtered out [bool]
    """

    # Check to see if the file exists outside the source root
    if source_root not in warning_file.parents:
        skip = True

        # Print a status message
        logging.debug('\tWarning removed - Warning occurs in a file that is outside the source root')
        logging.debug('\t\t%s', warning_file)
    else:
        skip = False

    return skip


def baseline_filtering_check(warning_file, excluded_files):
    """This function checks to see if a warning occurs in a directory or file that should be ignored.

    Inputs:
        - warning_file: File of interest from warning data [string]
        - excluded_files: Set of files read from SCRUBAnalysisFilteringList file [set [string]]

    Outputs:
        - skip: Indicator if result should be filtered out [bool]
    """
    # Iterate through every line of the ignore data
    if warning_file in excluded_files:
        logging.debug('\tWarning removed - Warning occurs in a file that has been excluded from analysis')
        logging.debug('\t\t%s', warning_file)
        return True
    return False


def check_filtering_file(filtering_file, create):
    """This function checks the filtering file to see if it exists.

    Inputs:
        - filtering_file: Full path to the filtering file to be checked [string]
        - create: Flag to indicate if the file should be created if it doesn't exist [bool]
    """

    # Check to see if all the files exist
    if not filtering_file.is_file():
        logging.info('No %s file exists.', str(filtering_file))

        # Create the file if necessary
        if create:
            logging.info('\tCreating blank filtering file %s.', str(filtering_file))
            logging.info('\tPlease add filtering patterns to this file.')
            open(filtering_file, 'w+').close()


def duplicate_check(warning, warning_log):
    """This function checks to make sure that the warning has not been reported before.

    Inputs:
        - warning: current warning to be checked [string]
        - warning_log: log containing all warnings written previously [list of strings]

    Outputs:
        - skip: Indicator if result should be filtered out [bool]
    """

    # Initialize the variables
    skip = False

    # Check if the waring has been written out before
    if warning in warning_log:
        skip = True

    return skip


def filter_results(warning_list, output_file, filtering_file, ignore_query_file, source_root, enable_micro_filtering,
                   enable_external_warnings):
    """This function performs the filtering, including all other filtering functions.

    Inputs:
        - input_files: List of absolute paths to the input file(s) of interest [list of string]
        - output_file: Absolute path to file where filtered results will be stored [string]
        - filtering_file: Absolute path to the SCRUBAnalayisFilteringList file [string]
        - ignore_query_file: Absolute path to the SCRUBExcludeQueries file [string]
        - source_root: Absolute path to the top level directory of the source code [string]
        - enable_micro_filtering: Flag to enable/disable micro filtering [logical]
        - enable_external_warnings: Flag to enable/disable external warnings [logical]

    Outputs:
        - output_file: All filtered results are written to the output_file
    """

    # Initialize the variables
    filtered_warnings = []
    valid_warning_types = []
    if output_file.stem == 'p10':
        valid_warning_types.append('p10')

    # Import the ignore data
    with open(filtering_file, 'r') as input_fh:
        excluded_files = set([x.strip() for x in input_fh.readlines()])

    # Print a log message
    logging.info('')
    logging.info('\tFiltering results...')
    logging.info('\t>> Executing command: filter_results.filter_results(<warning_list>, %s, %s, %s, %s, %r, %r)',
                 output_file, filtering_file, ignore_query_file, source_root, enable_micro_filtering,
                 enable_external_warnings)
    logging.info('\t>> From directory: %s', str(pathlib.Path().absolute()))

    # Update the source root to make it absolute
    source_root = source_root.resolve()

    # Add the filtering aliases
    if len(warning_list) > 0:
        if warning_list[0]['tool'] in filtering_aliases.keys():
            valid_warning_types.extend(filtering_aliases[warning_list[0]['tool']])

    # Iterate through every warning in the list
    for warning in warning_list:

        # Check to see if it should be ignored
        if baseline_filtering_check(warning['file'], excluded_files):
            continue

        # Check to see if the warning is external to the source directory
        if not enable_external_warnings and external_warning_check(warning['file'], source_root):
            continue

        # Perform micro filtering checking
        if enable_micro_filtering and micro_filter_check(warning['file'], warning['line'], valid_warning_types):
            continue

        # Check to see if the query should be ignore
        if ignore_query_check(warning['tool'], warning['query'], ignore_query_file):
            continue

        # If we made it here we want the warning.
        # Make the warning file path relative, make any description references relative, and append to filtered list
        warning['file'] = warning['file'].relative_to(source_root)
        for i, line in enumerate(warning['description']):
            warning['description'][i] = line.replace(str(source_root) + '/', '')
        filtered_warnings.append(warning)

    # Write out the results
    logging.info('\t>> Results filtered. Writing {}.'.format(output_file))

    translate_results.create_scrub_output_file(filtered_warnings, output_file)
