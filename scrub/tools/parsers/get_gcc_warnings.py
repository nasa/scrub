import pathlib
import logging
from scrub.tools.parsers import translate_results

WARNING_LEVEL = 'Low'
ID_PREFIX = 'gcc'


def parse_warnings(analysis_dir, tool_config_data, raw_input_file=None, parsed_output_file=None):
    """This function parses raw GCC/Clang compiler warnings into the SCRUB format.

    Inputs:
        - analysis_dir: Absolute path to the raw GCC/Clang output file directory [string]
        - tool_config_data: Dictionary of SCRUB configuration data [dict]
    """

    # Initialize the variables
    warning_count = 1
    warning_list = []
    raw_warnings = []

    # Set the input file
    if raw_input_file is None:
        raw_input_file = analysis_dir.joinpath('gcc_build.log')

    # Set the output file
    if parsed_output_file is None:
        parsed_output_file = tool_config_data.get('raw_results_dir').joinpath('gcc_compiler_raw.scrub')

    # Print a status message
    logging.info('')
    logging.info('\tParsing results...')
    logging.info('\t>> Executing command: get_gcc_warnings.parse_warnings(%s, %s)', str(raw_input_file),
                 str(parsed_output_file))
    logging.info('\t>> From directory: %s', str(pathlib.Path().absolute()))

    # Read in the input data
    with open(raw_input_file, 'r') as input_fh:
        input_data = input_fh.readlines()

    # Iterate through every line of the input file
    for i, line in enumerate(input_data):
        # Find lines that contain warnings
        if 'warning: ' in line.lower():
            # Split the line and store the data
            warning_file = pathlib.Path(line.split(':')[0].strip()).resolve()
            warning_line = int(line.split(':')[1].strip())
            warning_overview = line.split('warning: ')[-1].rstrip()
            warning_message = ['Compiler Warning:', '\t' + warning_overview]
            warning_id = ID_PREFIX + str(warning_count).zfill(3)

            # Get the rest of the warning description
            for j, desc_line in enumerate(input_data[i + 1:]):
                if desc_line.startswith(' '):
                    warning_message.append('\t' + desc_line.rstrip())
                else:
                    break

            # Check to see if the warning is in the list
            warning = [warning_file, warning_line, warning_message]
            if warning not in warning_list:
                # Add the warning to the list
                warning_list.append(warning)
                raw_warnings.append(translate_results.create_warning(warning_id, warning_file, warning_line,
                                                                     warning_message, ID_PREFIX, WARNING_LEVEL))

                # Increment the warning count
                warning_count = warning_count + 1

            else:
                logging.info('\t>> Duplicate warning omitted.')

    # Create the SCRUB output file
    translate_results.create_scrub_output_file(raw_warnings, parsed_output_file)
