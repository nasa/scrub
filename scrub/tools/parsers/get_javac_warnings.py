import re
import os
import sys
import logging
from scrub.tools.parsers import translate_results

WARNING_LEVEL = 'Low'
ID_PREFIX = 'javac'


def parse_warnings(raw_input_file, parsed_output_file):
    """This function parses the raw javac compiler warnings into the SCRUB format.

    Inputs:
        - raw_input_file: Absolute path to the raw javac compiler log containing warnings [string]
        - parsed_output_file: Absolute path to the file where the parsed warnings will be stored [string]
    """

    # Initialize variables
    warning_count = 1

    # Print a status message
    logging.info('')
    logging.info('\tParsing results...')
    logging.info('\t>> Executing command: get_javac_warnings.parse_warnings(%s, %s)', raw_input_file,
                 parsed_output_file)
    logging.info('\t>> From directory: %s', os.getcwd())

    # Import the data from the input file
    with open(raw_input_file, 'r') as input_fh:
        input_data = input_fh.readlines()

    # Iterate through every line of the input file
    raw_warnings = []
    for line in input_data:
        # Check to see if there is a warning or error
        if (' warning: ' in line) or (' error: ' in line):
            # Split the line and store the file name and line
            line_split = list(filter(None, re.split('[ :]', line.strip())))
            warning_file = os.path.abspath(line_split[0])
            warning_line = line_split[1]

            # Split the line and store the message and type of warning
            line_split = list(filter(None, re.split(':', line.strip())))
            warning_message = ['Javac Compiler Warning: ' + line_split[-1].strip()]
            warning_type = line_split[-2].strip()
            warning_id = ID_PREFIX + str(warning_count).zfill(3)

            # Add to the warning dictionary
            raw_warnings.append(translate_results.create_warning(warning_id, warning_file, warning_line,
                                                                 warning_message, ID_PREFIX, WARNING_LEVEL,
                                                                 warning_type))

            # Increment the counter
            warning_count = warning_count + 1

    # Create the output file
    translate_results.create_scrub_output_file(raw_warnings, parsed_output_file)


if __name__ == '__main__':
    parse_warnings(sys.argv[1], sys.argv[2])
