import re
import os
import sys
import logging
from distutils.version import StrictVersion

WARNING_LEVEL = 'Low'
ID_PREFIX = 'coverity'


def get_error_indices(raw_input_file):
    """This function gets the indices of the first line of all Coverity warnings.

    Inputs:
        - raw_input_file: Full path to the file containing raw Coverity warnings [string]

    Outputs:
        - error_indices: List of warning indices [list of int]
    """

    # Initialize variables
    error_indices = []

    # Import the input data file
    with open(raw_input_file, 'r') as input_fh:
        input_data = input_fh.readlines()

    # Iterate through every line of the input file
    for i in range(0, len(input_data)):
        # Get the line
        line = input_data[i].strip()

        if ('Error:' in line) or ('Checker:' in line) or ('Type:' in line):
            error_indices.append(i)

    return error_indices


def parse_warnings_2019_12(raw_input_file, parsed_output_file):
    """This function parses the raw Coverity warnings (version 2019.12) into the SCRUB format.

    Inputs:
        - input_file: Absolute path to the file containing raw Coverity warnings [string]
        - parsed_output_file: Absolute path to the file where the parsed warnings will be stored [string]
    """

    # Print status message
    logging.info('')
    logging.info('\t>> Executing command: get_coverity_warnings.parse_warnings_2019_12(%s, %s)',
                 raw_input_file, parsed_output_file)
    logging.info('\t>> From directory: %s', os.getcwd())

    # Import the input data file
    with open(raw_input_file, 'r') as input_fh:
        input_data = input_fh.readlines()

    # Create the output file
    with open(parsed_output_file, 'w+') as output_fh:
        # Iterate through every line of the input file
        error_indices = get_error_indices(raw_input_file)

        # Iterate through every line of the input file and parse warnings
        for i in range(0, len(error_indices)):
            # Initialize variables
            warning_text = []

            # Get the index line
            error_index = error_indices[i]

            # Get the name of the warnings
            warning_name = list(filter(None, re.split('[()]', input_data[error_index].strip())))[-1].strip()

            # Get the location information
            line = input_data[error_index - 1].strip()
            line_split = list(filter(None, re.split(':', line)))
            warning_file = line_split[-2]
            warning_line = int(line_split[-1])

            # Increment the warning count
            warning_count = i + 1

            # Get the warning text
            if i < len(error_indices) - 1:
                warning_index_end = error_indices[i + 1] - 2
            else:
                warning_index_end = len(input_data)

            for j in range(error_index + 1, warning_index_end):
                # Add the line ot the list, if it's not blank
                if not input_data[j].strip() == '':
                    warning_text.append(input_data[j].strip())

            # Write the data to the output file
            output_fh.write('%s%03d <%s> :%s:%d: %s\n' % (ID_PREFIX, warning_count, WARNING_LEVEL, warning_file,
                                                          warning_line, warning_name))
            for line in warning_text:
                output_fh.write('    %s\n' % line)
            output_fh.write('\n')

    # Change the permissions of the output file
    os.chmod(parsed_output_file, 438)


def parse_warnings_2019_06(raw_input_file, parsed_output_file):
    """This function parses the raw Coverity warnings (version 2019.06) into the SCRUB format.

    Inputs:
        - raw_input_file: Full path to the file containing raw Coverity warnings [string]
        - parsed_output_file: Full path to the file where the parsed warnings will be stored [string]
    """

    # Print status message
    logging.info('')
    logging.info('\tParsing results...')
    logging.info('\t>> Executing command: get_coverity_warnings.parse_warnings_2019_06(%s, %s)',
                 raw_input_file, parsed_output_file)
    logging.info('\t>> From directory: %s', os.getcwd())

    # Import the input data file
    with open(raw_input_file, 'r') as input_fh:
        input_data = input_fh.readlines()

    # Create the output file
    with open(parsed_output_file, 'w+') as output_fh:
        # Iterate through every line of the input file
        error_indices = get_error_indices(raw_input_file)

        # Iterate through every line of the input file and parse warnings
        for i in range(0, len(error_indices)):
            # Initialize variables
            warning_text = []

            # Get the index line
            error_index = error_indices[i]

            # Get the name of the warnings
            warning_name = list(filter(None, re.split(':', input_data[error_index].strip())))[-1].strip()

            # Get the location information
            line = input_data[error_index - 1].strip()
            line_split = list(filter(None, re.split(':', line)))
            warning_file = line_split[-2]
            warning_line = int(line_split[-1])

            # Increment the warning count
            warning_count = i + 1

            # Get the warning text
            if i < len(error_indices) - 1:
                warning_index_end = error_indices[i + 1] - 2
            else:
                warning_index_end = len(input_data)

            for j in range(error_index + 1, warning_index_end):
                # Add the line ot the list, if it's not blank
                if not input_data[j].strip() == '':
                    warning_text.append(input_data[j].strip())

            # Write the data to the output file
            output_fh.write('%s%03d <%s> :%s:%d: %s\n' % (ID_PREFIX, warning_count, WARNING_LEVEL, warning_file,
                                                          warning_line, warning_name))
            for line in warning_text:
                output_fh.write('    %s\n' % line)
            output_fh.write('\n')

    # Change the permissions of the output file
    os.chmod(parsed_output_file, 438)


def parse_warnings_legacy(raw_input_file, parsed_output_file):
    """This function parses the raw Coverity warnings (version 2018.09 and older) into the SCRUB format.

    Inputs:
        - raw_input_file: Full path to the file containing raw Coverity warnings [string]
        - parsed_output_file: Full path to the file where the parsed warnings will be stored [string]
    """

    # Print status message
    logging.info('')
    logging.info('\tParsing results...')
    logging.info('\t>> Executing command: get_coverity_warnings.parse_warnings_legacy(%s, %s)',
                 raw_input_file, parsed_output_file)
    logging.info('\t>> From directory: %s', os.getcwd())

    # Import the input data file
    with open(raw_input_file, 'r') as input_fh:
        input_data = input_fh.readlines()

    # Create the output file
    with open(parsed_output_file, 'w+') as output_fh:
        # Iterate through every line of the input file
        error_indices = get_error_indices(raw_input_file)

        # Iterate through every line of the input file and parse warnings
        for i in range(0, len(error_indices)):
            # Initialize variables
            warning_text = []

            # Get the index line
            error_index = error_indices[i]

            # Get the name of the warnings
            warning_name = list(filter(None, re.split(':', input_data[error_index].strip())))[-1].strip()

            # Get the location information
            line = input_data[error_index + 1].strip()
            line_split = list(filter(None, re.split(':', line)))
            warning_file = line_split[-2]
            warning_line = int(line_split[-1])

            # Increment the warning count
            warning_count = i + 1

            # Get the warning text
            if i < len(error_indices)-1:
                warning_index_end = error_indices[i+1]-1
            else:
                warning_index_end = len(input_data)

            for j in range(error_index+1, warning_index_end):
                # Add the line ot the list
                warning_text.append(input_data[j].strip())

            # Write the data to the output file
            output_fh.write('%s%03d <%s> :%s:%d: %s\n' % (ID_PREFIX, warning_count, WARNING_LEVEL, warning_file,
                                                          warning_line, warning_name))
            for line in warning_text:
                output_fh.write('    %s\n' % line)
            output_fh.write('\n')

    # Change the permissions of the output file
    os.chmod(parsed_output_file, 438)


def parse_warnings(raw_input_file, parsed_output_file, coverity_version_number):
    """This function will examine the raw_input_file to determine which parser will be used.

    Inputs:
        - raw_input_file: Full path to the file containing raw Coverity warnings [string]
        - parsed_output_file: Full path to the file where the parsed warnings will be stored [string]
        - version_number: Version number for Coverity instance being used [string]
    """

    # Select which parser should be used
    if StrictVersion(coverity_version_number) >= StrictVersion('2019.12'):
        parse_warnings_2019_12(raw_input_file, parsed_output_file)
    elif (StrictVersion(coverity_version_number) >= StrictVersion('2019.06')) and \
            (StrictVersion(coverity_version_number) < StrictVersion('2019.12')):
        parse_warnings_2019_06(raw_input_file, parsed_output_file)
    else:
        parse_warnings_legacy(raw_input_file, parsed_output_file)


if __name__ == '__main__':
    parse_warnings(sys.argv[1], sys.argv[2], sys.argv[3])
