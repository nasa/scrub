import sys
import json
from scrub.tools.parsers import translate_results

WARNING_LEVEL = 'Low'
ID_PREFIX = 'pylint'


def parse_warnings(raw_input_file, parsed_output_file):
    """This function parses the raw PyLint warnings into the SCRUB format.

    Inputs:
        - raw_input_file: Absolute path to the raw PyLint output file [string]
        - parsed_output_file: Absolute path to the file where the parsed warnings will be stored [string]
    """

    # Initialize the variables
    warning_count = 1

    # Read in the input data
    with open(raw_input_file, 'r') as input_fh:
        input_data = json.loads(input_fh.read())

    # Iterate through every finding in the input file
    raw_warnings = []
    for finding in input_data:
        # Parse the finding
        warning_file = finding['path']
        warning_line = int(finding['line'])
        warning_description = finding['message'].splitlines()
        warning_message = ['[Type: ' + finding['message-id'] + ']' + ' [' + finding['type'] + ']'] + warning_description
        warning_id = ID_PREFIX + str(warning_count).zfill(3)
        warning_type = finding['symbol']

        # Add to the warning dictionary
        raw_warnings.append(translate_results.create_warning(warning_id, warning_file, warning_line, warning_message,
                                                             ID_PREFIX, WARNING_LEVEL, warning_type))

        # Increment the warning count
        warning_count = warning_count + 1

    # Create the SCRUB output file
    translate_results.create_scrub_output_file(raw_warnings, parsed_output_file)


if __name__ == '__main__':
    parse_warnings(sys.argv[1], sys.argv[2])
