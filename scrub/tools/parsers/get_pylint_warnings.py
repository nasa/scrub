import json
import pathlib
from scrub.tools.parsers import translate_results

WARNING_LEVEL = 'Low'
ID_PREFIX = 'pylint'


def parse_warnings(analysis_dir, tool_config_data, raw_input_file=None, parsed_output_file=None):
    """This function parses the raw PyLint warnings into the SCRUB format.

    Inputs:
        - raw_input_file: Absolute path to the raw PyLint output file [string]
        - parsed_output_file: Absolute path to the file where the parsed warnings will be stored [string]
    """

    # Initialize the variables
    warning_count = 1

    # Set the input file
    if raw_input_file is None:
        raw_input_file = analysis_dir.joinpath('pylint_output.json')

    # Set the output file
    if parsed_output_file is None:
        parsed_output_file = tool_config_data.get('raw_results_dir').joinpath('pylint_compiler_raw.scrub')

    # Read in the input data
    with open(raw_input_file, 'r') as input_fh:
        input_data = json.loads(input_fh.read())

    # Iterate through every finding in the input file
    raw_warnings = []
    for finding in input_data:
        # Parse the finding
        warning_file = pathlib.Path(finding['path']).resolve()
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
