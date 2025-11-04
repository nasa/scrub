import pathlib
import logging
import xml.etree.ElementTree
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
        raw_input_file = analysis_dir.joinpath('cppcheck_output.xml')

    # Set the output file
    if parsed_output_file is None:
        parsed_output_file = tool_config_data.get('raw_results_dir').joinpath('cppcheck_compiler_raw.scrub')

    # Read in the input data
    raw_input_data = xml.etree.ElementTree.parse(raw_input_file).getroot()

    # Print a status message
    logging.info('\t>> Executing command: get_cppcheck_warnings.parse_warnings(%s, %s)', analysis_dir,
                 parsed_output_file)
    logging.info('\t>> From directory: %s', str(pathlib.Path().absolute()))

    # Iterate through every finding in the input file
    raw_warnings = []
    for finding in raw_input_data.find('errors').findall('error'):
        # Make sure we haven't hit the metadata
        if finding.get('id') != 'checkersReport':
            # Parse the finding
            warning_file = pathlib.Path(finding.find('location').get('file')).resolve()
            warning_line = int(finding.find('location').get('line'))
            warning_message = finding.get('verbose')
            warning_id = ID_PREFIX + str(warning_count).zfill(3)
            warning_type = finding.get('id')
            warning_severity = finding.get('severity')

            # Set the warning level based on the severity
            if warning_severity == 'error':
                warning_level = 'High'
            elif warning_severity == 'warning':
                warning_level = 'Med'
            else:
                warning_level = 'Low'

            # Add to the warning dictionary
            raw_warnings.append(translate_results.create_warning(warning_id, warning_file, warning_line, warning_message,
                                                                 ID_PREFIX, warning_level, warning_type))

            # Increment the warning count
            warning_count = warning_count + 1

    # Create the SCRUB output file
    translate_results.create_scrub_output_file(raw_warnings, parsed_output_file)