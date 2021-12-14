import re
import os
import sys
import logging
from scrub.tools.parsers import translate_results

WARNING_LEVEL = 'Low'
ID_PREFIX = 'gbuild'


def get_raw_warning(raw_input_file, initial_index):
    """This function returns the total text of a gbuild warning message.

    Inputs:
        - raw_input_file: Absolute path to the raw gbuild compiler log containing warnings [string]
        - initial_index: The numeric index of where the warnings was found in the log file [int]

    Outputs:
        - warning_text: Full text of the warning starting at initial_index [string]
    """

    # Read in the input file
    with open(raw_input_file, 'r') as input_fh:
        input_data = input_fh.readlines()

    # Initialize variables
    start_point = 0
    end_point = len(input_data)

    # Get the initial line
    current_index = initial_index
    line = input_data[current_index]

    # Get the start point
    while (not line.startswith('\n')) and ('output from compiling' not in line.lower()):
        # Update the start point
        start_point = current_index

        # Update the current line
        current_index = current_index - 1
        line = input_data[current_index]

    # Get the initial line
    current_index = initial_index
    line = input_data[current_index]

    # Get the end point
    while not line == '\n':
        # Update the end point
        end_point = current_index

        # Update the current line
        current_index = current_index + 1
        line = input_data[current_index]

    # Store the warning text
    warning_text = []
    for i in range(start_point, end_point):
        warning_text.append(input_data[i])

    return warning_text


def parse_doublecheck_warnings(raw_input_file, parsed_output_file):
    """This function parses a GHS log file for DoubleCheck warnings.

    Inputs:
        - raw_input_file: Absolute path to the raw gbuild compiler log containing warnings [string]
        - parsed_output_file: Absolute path to the desired output file location [string]
    """

    # Initialize the variables
    warning_count = 1

    # Read in the log file contents
    with open(raw_input_file, 'r') as input_fh:
        input_data = input_fh.readlines()

    # Iterate through every line of the input file
    raw_warnings = []
    for i in range(0, len(input_data)):
        # Initialize vriables
        warning_file = None
        warning_line = None
        warning_query = None
        line = input_data[i]

        # Find lines that contain DoubleCheck warnings
        if 'source analysis warning #' in line:
            # Get the raw warning text
            raw_warning = get_raw_warning(raw_input_file, i)

            # Find the file and line number
            for warning_line_itr in raw_warning:
                if "\", line" in warning_line_itr:
                    warning_file = os.path.abspath(list(filter(None, re.split('"', warning_line_itr.strip())))[0])
                    warning_line = int(list(filter(None, re.split(':', re.split('line ',
                                                                                warning_line_itr.strip())[-1])))[0])
                    break

            # Find the query name
            for warning_line_itr in raw_warning:
                if re.search(r'source analysis warning #[0-9]*:', warning_line_itr):
                    warning_query = ('source analysis warning #' +
                                     list(filter(None,
                                                 re.split(':', re.split('#', warning_line_itr.strip())[-1])))[0])
                    break

            # Create the warning description
            warning_message = ['Warning from DoubleCheck:']
            for text in raw_warning:
                warning_message.append(text.rstrip())

            # Set the warning ID
            warning_id = ID_PREFIX + str(warning_count).zfill(3)

            # Add to the warning dictionary
            raw_warnings.append(translate_results.create_warning(warning_id, warning_file, warning_line,
                                                                 warning_message, ID_PREFIX, WARNING_LEVEL,
                                                                 warning_query))

            # Increment the warning count
            warning_count = warning_count + 1

        elif 'source analysis error #' in line:
            # Get the raw warning text
            raw_warning = get_raw_warning(raw_input_file, i)

            # Find the file and line number
            for warning_line_itr in raw_warning:
                if "\", line" in warning_line_itr:
                    warning_file = os.path.abspath(list(filter(None, re.split('"', warning_line_itr.strip())))[0])
                    warning_line = int(list(filter(None, re.split(':', re.split('line ',
                                                                                warning_line_itr.strip())[-1])))[0])
                    break

            # Find the query name
            for warning_line_itr in raw_warning:
                if 'source analysis error #' in warning_line_itr:
                    warning_query = ('source analysis error #' +
                                     list(filter(None, re.split(':', re.split('#', warning_line_itr.strip())[-1])))[0])
                    break

            # Create the warning description
            warning_message = ['Warning from DoubleCheck:']
            for text in raw_warning:
                warning_message.append(text.rstrip())

            # Set the warning ID
            warning_id = ID_PREFIX + str(warning_count).zfill(3)

            # Add to the warning dictionary
            raw_warnings.append(translate_results.create_warning(warning_id, warning_file, warning_line,
                                                                 warning_message, ID_PREFIX, WARNING_LEVEL,
                                                                 warning_query))

            # Increment the warning count
            warning_count = warning_count + 1

        elif ': warning #' in line:
            # Get the raw warning text
            raw_warning = get_raw_warning(raw_input_file, i)

            # Get the warning location data
            warning_location = raw_warning[0].split(':')[0]
            warning_file = warning_location.split(',')[0].replace('"', '').strip()
            warning_line = int(warning_location.split('line ')[-1].strip())
            warning_query = raw_warning[0].split(':')[1].strip()

            # Create the warning description
            warning_message = ['Warning from gbuild:']
            for text in raw_warning:
                warning_message.append(text.rstrip())

            # Set the warning ID
            warning_id = ID_PREFIX + str(warning_count).zfill(3)

            # Add to the warning dictionary
            raw_warnings.append(translate_results.create_warning(warning_id, warning_file, warning_line,
                                                                 warning_message, ID_PREFIX, WARNING_LEVEL,
                                                                 warning_query))

            # Increment the warning count
            warning_count = warning_count + 1

    # Create the SCRUB output file
    translate_results.create_scrub_output_file(raw_warnings, parsed_output_file)


def parse_warnings(raw_input_file, parsed_output_file):
    """This function parses the raw gbuild compiler warnings into the SCRUB format.

    Inputs:
        - raw_input_file: Absolute path to the raw gbuild compiler log containing warnings [string]
        - parsed_output_file: Absolute path to the file where the parsed warnings will be stored [string]
    """

    # Print a status message
    logging.info('')
    logging.info('\tParsing results...')
    logging.info('\t>> Executing command: get_gbuild_warnings.parse_warnings(%s, %s)', raw_input_file,
                 parsed_output_file)
    logging.info('\t>> From directory: %s', os.getcwd())

    # Search for DoubleCheck warnings in the log file
    parse_doublecheck_warnings(raw_input_file, parsed_output_file)


if __name__ == '__main__':
    parse_warnings(sys.argv[1], sys.argv[2])
