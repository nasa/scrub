import re
import pathlib
import logging
from scrub.tools.parsers import translate_results

WARNING_LEVEL = 'Low'
ID_PREFIX = 'javac'


def parse_warnings(analysis_dir, tool_config_data, raw_input_file=None, parsed_output_file=None):
    """This function parses the raw javac compiler warnings into the SCRUB format.

    Inputs:
        - analysis_dir: Absolute path to the raw javac output file directory [string]
        - tool_config_data: Dictionary of scrub configuration data [dict]
        - raw_input_file: Absolute path to the raw input file [string] [optional]
        - parsed_output_file: Absolute path to the raw output file [string] [optional]
    """

    # Initialize variables
    warning_count = 1

    # Set the input file
    if raw_input_file is None:
        raw_input_file = analysis_dir.joinpath('javac_build.log')

    # Set the output file
    if parsed_output_file is None:
        parsed_output_file = tool_config_data.get('raw_results_dir').joinpath('javac_compiler_raw.scrub')

    # Print a status message
    logging.info('')
    logging.info('\tParsing results...')
    logging.info('\t>> Executing command: get_javac_warnings.parse_warnings(%s, %s)', str(raw_input_file),
                 str(parsed_output_file))
    logging.info('\t>> From directory: %s', str(pathlib.Path().absolute()))

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
            warning_file = pathlib.Path(line_split[0]).resolve()
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
