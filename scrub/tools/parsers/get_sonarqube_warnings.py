import os
import sys
import json
import glob
from scrub.tools.parsers import translate_results

WARNING_LEVEL = 'Low'
ID_PREFIX = 'sonarqube'


def parse_findings(findings_file, parsed_output_file, source_root):
    """This function parses the raw SonarQube findings from api/projects/export_findings into the SCRUB format.

    Inputs:
        - findings_file: Absolute path to the raw SonarQube output file [string]
        - parsed_output_file: Absolute path to the file where the parsed warnings will be stored [string]
        - source_root: Absolute pth to the source root directory [string]
    """
    # Initialize the variables
    warning_count = 1
    raw_warnings = []

    # Read in the input data
    with open(findings_file, 'r') as input_fh:
        input_data = json.loads(input_fh.read())

    # Iterate through every finding in the input file
    for finding in input_data['export_findings']:
        # Parse the finding
        warning_file = os.path.normpath(source_root + '/' + finding['path'])
        warning_message = finding['message'].splitlines()
        warning_id = ID_PREFIX + str(warning_count).zfill(3)
        warning_query = finding['ruleReference']

        # Get the line number
        if finding['lineNumber'].isdigit():
            warning_line = int(finding['lineNumber'])
        else:
            warning_line = 0

        # Add to the warning dictionary
        raw_warnings.append(translate_results.create_warning(warning_id, warning_file, warning_line,
                                                             warning_message, ID_PREFIX, WARNING_LEVEL,
                                                             warning_query))

        # Increment the warning count
        warning_count = warning_count + 1

        # Create the SCRUB output file
    translate_results.create_scrub_output_file(raw_warnings, parsed_output_file)


def parse_issues(results_dir, parsed_output_file, source_root):
    """This function parses the raw SonarQube issues from api/issues/search into the SCRUB format.

        Inputs:
            - results_dir: Absolute path to the raw SonarQube output file directory [string]
            - parsed_output_file: Absolute path to the file where the parsed warnings will be stored [string]
            - source_root: Absolute pth to the source root directory [string]
        """

    # Initialize the variables
    warning_count = 1
    raw_warnings = []

    # Find all the raw results files in the directory
    results_files = glob.glob(results_dir + '/sonarqube_warnings_*.json')

    # Iterate through every results file
    for raw_input_file in results_files:
        # Read in the input data
        with open(raw_input_file, 'r') as input_fh:
            input_data = json.loads(input_fh.read())

        # Iterate through every finding in the input file
        for issue in input_data['issues']:
            # Parse the finding
            warning_file = os.path.normpath(source_root + '/' + issue['component'].split(':')[-1])
            warning_message = issue['message'].splitlines()
            warning_id = ID_PREFIX + str(warning_count).zfill(3)
            warning_query = issue['rule'].replace(':', '-')

            # Get the line number
            if 'line' in issue.keys():
                warning_line = int(issue['line'])
            elif 'textRange' in issue.keys():
                warning_line = int(issue['textRange']['startLine'])
            else:
                warning_line = 0

            # Add to the warning dictionary
            raw_warnings.append(translate_results.create_warning(warning_id, warning_file, warning_line,
                                                                 warning_message, ID_PREFIX, WARNING_LEVEL,
                                                                 warning_query))

            # Increment the warning count
            warning_count = warning_count + 1

    # Create the SCRUB output file
    translate_results.create_scrub_output_file(raw_warnings, parsed_output_file)


if __name__ == '__main__':
    parse_findings(sys.argv[1], sys.argv[2], sys.argv[3])
