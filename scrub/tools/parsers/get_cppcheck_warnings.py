import pathlib
import logging
from scrub.tools.parsers import translate_results

ID_PREFIX = 'cppcheck'


def parse_warnings(analysis_dir, tool_config_data, raw_input_file=None, parsed_output_file=None):
    """This function parses the raw CppCheck warnings into the SCRUB format.

    Inputs:
        - analysis_dir:
        - tool_config_data:
        - raw_input_file: Absolute path to the raw PyLint output file [string]
        - parsed_output_file: Absolute path to the file where the parsed warnings will be stored [string]

    """

    # Initialize the variables
    warning_count = 1

    # Set the input file
    if raw_input_file is None:
        raw_input_file = analysis_dir.joinpath('cppcheck_output.txt')

    # Set the output file
    if parsed_output_file is None:
        parsed_output_file = tool_config_data.get('raw_results_dir').joinpath('cppcheck_compiler_raw.scrub')

    # Read in the input data
    with open(raw_input_file, 'r') as input_fh:
        raw_input_data = input_fh.readlines()

    # Print a status message
    logging.info('\t>> Executing command: get_cppcheck_warnings.parse_warnings(%s, %s)', analysis_dir,
                 parsed_output_file)
    logging.info('\t>> From directory: %s', str(pathlib.Path().absolute()))

    # Iterate through every finding in the input file
    raw_warnings = []
    for line in raw_input_data:
        # Parse the finding
        finding = line.strip().split('::')

        # Add everything that has a file location
        if finding[0] != 'nofile':
            warning_file = pathlib.Path(finding[0]).resolve()
            warning_line = int(finding[1])
            warning_message = [finding[-1]]
            warning_id = ID_PREFIX + str(warning_count).zfill(3)
            warning_severity = finding[2]
            warning_type = finding[3]
            cwe = int(finding[4])

            # Set the warning level based on the severity
            if warning_severity == 'error':
                warning_level = 'High'
            elif warning_severity == 'warning':
                warning_level = 'Med'
            else:
                warning_level = 'Low'

            # Add CWE data if applicable
            if cwe != 0:
                warning_message.append('Related CWE: {}'.format(cwe))

            # Add to the warning dictionary
            raw_warnings.append(translate_results.create_warning(warning_id, warning_file, warning_line,
                                                                 warning_message, ID_PREFIX, warning_level,
                                                                 warning_type))

            # Increment the warning count
            warning_count = warning_count + 1

    # Create the SCRUB output file
    translate_results.create_scrub_output_file(raw_warnings, parsed_output_file)