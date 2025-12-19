import json
import pathlib
from scrub.tools.parsers import translate_results

ID_PREFIX = 'eslint'
SEVERITY_MAP = {0: 'Low',
                1: 'Med',
                2: 'High'}


def parse_warnings(analysis_dir, tool_config_data, raw_input_file=None, parsed_output_file=None):
    """This function parses the raw ESLint warnings into the SCRUB format.

    Inputs:
        - raw_input_file: Absolute path to the raw ESLint output file [string]
        - parsed_output_file: Absolute path to the file where the parsed warnings will be stored [string]
    """

    # Initialize the variables
    warning_count = 1

    # Set the input file
    if raw_input_file is None:
        raw_input_file = analysis_dir.joinpath('eslint.json')

    # Set the output file
    if parsed_output_file is None:
        parsed_output_file = tool_config_data.get('raw_results_dir').joinpath('eslint_compiler_raw.scrub')

    # Read in the input data
    with open(raw_input_file, 'r') as input_fh:
        input_data = json.loads(input_fh.read())

    # Iterate through every finding in the input file
    raw_warnings = []
    for source_file in input_data:
        warning_file = pathlib.Path(source_file['filePath']).resolve()
        for finding in input_data[0]['messages']:
            # Parse the individual findings
            warning_line = int(finding['line'])

            # Craft the description
            warning_message = [f"{finding['messageId']}: {finding['message']}"]

            # Get the severity
            if 'severity' in finding:
                severity = SEVERITY_MAP[finding['severity']]
            else:
                severity = 'Low'

            # Gather suggestions, if applicable
            if 'suggestions' in finding.keys():
                warning_message.append('Suggestions:')
                for suggestion in finding['suggestions']:
                    warning_message.append(f"  {suggestion['desc']}")

            warning_id = ID_PREFIX + str(warning_count).zfill(3)
            warning_type = finding['ruleId']

            # Add to the warning dictionary
            raw_warnings.append(translate_results.create_warning(warning_id, warning_file, warning_line,
                                                                 warning_message, ID_PREFIX, severity, warning_type))

            # Increment the warning count
            warning_count = warning_count + 1

    # Create the SCRUB output file
    translate_results.create_scrub_output_file(raw_warnings, parsed_output_file)
