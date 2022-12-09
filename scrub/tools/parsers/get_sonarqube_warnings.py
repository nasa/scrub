import sys
import json
import pathlib
from scrub.tools.parsers import translate_results

WARNING_LEVEL = 'Low'
ID_PREFIX = 'sonarqube'


def parse_warnings(results_dir, parsed_output_file, source_root, sonarqube_url):
    """This function parses the raw SonarQube warnings into the SCRUB format.
        Inputs:
            - results_dir: Absolute path to the raw SonarQube output file directory [string]
            - parsed_output_file: Absolute path to the file where the parsed warnings will be stored [string]
            - source_root: Absolute path to the source root directory [string]
            - sonarqube_url: URL of the SonarQube server [string]
        """

    # Initialize the variables
    warning_count = 1
    raw_warnings = []

    # Find all the raw findings results files in the directory
    findings_results_files = results_dir.glob('*.json')

    # Iterate through every issues results file
    for raw_findings_file in findings_results_files:
        # Read in the input data
        with open(raw_findings_file, 'r') as input_fh:
            input_data = json.loads(input_fh.read())

        # Iterate through every finding in the input file
        if 'issues' in input_data.keys():
            findings = input_data['issues']
        else:
            findings = input_data['hotspots']
        for finding in findings:
            # Check to see if the warning should be suppressed
            if 'resolution' in finding.keys():
                suppression = True
            else:
                suppression = False

            # Parse the finding
            warning_file = source_root.joinpath(finding['component'].split(':')[-1]).resolve()
            warning_message = finding['message'].splitlines()
            warning_id = ID_PREFIX + str(warning_count).zfill(3)

            # Get a link to the finding
            if 'sonarqube_hotspots' in raw_findings_file.stem:
                warning_link = sonarqube_url + '/security_hotspots?id=' + finding['project'] + '&hotspots=' + finding['key']
            else:
                warning_link = sonarqube_url + '/project/issues?id=' + finding['project'] + '&open=' + finding['key']

            # Add the link to the warning message
            warning_message.append(warning_link)

            # Parse the query if it exists
            if 'rule' in finding.keys():
                warning_query = finding['rule'].replace(':', '-')
            elif 'securityCategory' in finding.keys():
                warning_query = finding['securityCategory']
            else:
                warning_query = ''

            # Get the line number
            if 'line' in finding.keys():
                warning_line = int(finding['line'])
            elif 'textRange' in finding.keys():
                warning_line = int(finding['textRange']['startLine'])
            else:
                warning_line = 0

            # Add to the warning dictionary
            raw_warnings.append(translate_results.create_warning(warning_id, warning_file, warning_line,
                                                                 warning_message, ID_PREFIX, WARNING_LEVEL,
                                                                 warning_query, suppression))

            # Increment the warning count
            warning_count = warning_count + 1

    # Create the SCRUB output file
    translate_results.create_scrub_output_file(raw_warnings, parsed_output_file)


if __name__ == '__main__':
    parse_warnings(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), sys.argv[4])
