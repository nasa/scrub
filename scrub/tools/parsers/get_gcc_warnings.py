import re
import os
import sys
import logging
from scrub.tools.parsers import translate_results

WARNING_LEVEL = 'Low'
ID_PREFIX = 'gcc'


def parse_warnings(raw_input_file, parsed_output_file):
    """This function parses the raw GCC compiler warnings into the SCRUB format.

    Inputs:
        - raw_input_file: Absolute path to the raw GCC compiler log containing warnings [string]
        - parsed_output_file: Absolute path to the file where the parsed warnings will be stored [string]
    """

    # Initialize the variables
    warning_count = 1

    # Print a status message
    logging.info('')
    logging.info('\tParsing results...')
    logging.info('\t>> Executing command: get_gcc_warnings.parse_warnings(%s, %s)', raw_input_file, parsed_output_file)
    logging.info('\t>> From directory: %s', os.getcwd())

    # Read in the input data
    with open(raw_input_file, 'r') as input_fh:
        input_data = input_fh.readlines()

    # Iterate through every line of the input file
    raw_warnings = []
    for line in input_data:
        # Find lines that contain warnings
        if 'warning:' in line.strip():
            # Split the line and store the data
            warning_file = os.path.abspath(line.split(':')[0].strip())
            warning_line = int(line.split(':')[1].strip())
            warning_message = ['GCC Compiler Warning: ' + line.split('warning:')[-1].strip()]
            warning_id = ID_PREFIX + str(warning_count).zfill(3)

            # Add to the warning dictionary
            raw_warnings.append(translate_results.create_warning(warning_id, warning_file, warning_line,
                                                                 warning_message, ID_PREFIX, WARNING_LEVEL))

            # Increment the warning count
            warning_count = warning_count + 1

    # Create the SCRUB output file
    translate_results.create_scrub_output_file(raw_warnings, parsed_output_file)


if __name__ == '__main__':
    parse_warnings(sys.argv[1], sys.argv[2])
