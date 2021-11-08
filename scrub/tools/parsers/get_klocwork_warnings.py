import os
import re
import sys
import json
import logging
from distutils.version import StrictVersion
from scrub.tools.parsers import translate_results

WARNING_LEVEL = 'Low'
ID_PREFIX = 'klocwork'


def parse_warnings_2020_2(input_file, output_file):
    """This function parse Klocwork results from v2020.2.

    Inputs:
        - input_file: Absolute path to the file containing raw Klocwork warnings [string]
        - output_file: Absolute path to the file where the parsed warnings will be stored [string]
    """

    # Print status message
    logging.info('')
    logging.info('\t>> Executing command: get_klocwork_warnings.parse_warnings_2020_2(%s, %s)', input_file,
                 output_file)
    logging.info('\t>> From directory: %s', os.getcwd())

    # Initialize the variables
    warning_count = 1

    # Import the input data file
    with open(input_file, 'r') as input_fh:
        input_data = input_fh.readlines()

    # Create the output file
    raw_warnings = []
    for line in input_data:
        # Convert the warning to a dictionary
        warning_data = json.loads(line)

        # Parse the warning data
        warning_file = warning_data['file']
        warning_line = 0
        warning_query = warning_data['code']
        warning_message = warning_data['message']
        warning_link = re.split(',searchquery', warning_data['url'])[0]
        warning_id = ID_PREFIX + str(warning_count).zfill(3)
        warning_description = [warning_message, warning_link]

        # Add to the warning dictionary
        raw_warnings.append(translate_results.create_warning(warning_id, warning_file, warning_line,
                                                             warning_description, ID_PREFIX, WARNING_LEVEL,
                                                             warning_query))

        # Increment the warning count
        warning_count = warning_count + 1

    # Create the SCRUB output file
    translate_results.create_scrub_output_file(raw_warnings, output_file)


def parse_warnings(input_file, output_file, version_number):
    """This function will examine the input_file to determine which parser will be used.

    Inputs:
        - input_file: Absolute path to the file containing raw Klocwork warnings [string]
        - output_file: Absolute path to the file where the parsed warnings will be stored [string]
        - version_number: Version number for Klocwork instance being used [string]

    Outputs:
        - output_file: All parsed warnings will be written to the output_file
    """

    if StrictVersion(version_number) >= StrictVersion('20.2.0'):
        parse_warnings_2020_2(input_file, output_file)
    else:
        parse_warnings_2020_2(input_file, output_file)


if __name__ == '__main__':
    parse_warnings(sys.argv[1], sys.argv[2], sys.argv[3])
