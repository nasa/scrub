import sys
import json
import pathlib
from scrub.tools.parsers import translate_results

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

    # Find all of the hotspot files
    hotspot_files = results_dir.glob('sonarqube_hotspot_[0-9]*.json')

    # Iterate through every hotspot file
    for hotspot_file in hotspot_files:
        # Read in the input data
        with open(hotspot_file, 'r', encoding='utf-8') as input_fh:
            hotspot_data = json.loads(input_fh.read())

        # Parse the finding
        warning_file = source_root.joinpath(hotspot_data['component']['path'])
        warning_message = hotspot_data['rule']['name'].splitlines()
        warning_query = hotspot_data['rule']['key']
        warning_id = ID_PREFIX + str(warning_count).zfill(3)
        warning_link = sonarqube_url + '/security_hotspots?id=' + hotspot_data['project']['key'] + '&hotspots=' + hotspot_data['key']

        # Get the ranking
        if hotspot_data['rule']['vulnerabilityProbability'].lower() == 'blocker':
            ranking = 'High'
        elif hotspot_data['rule']['vulnerabilityProbability'].lower() == 'critical':
            ranking = 'High'
        elif hotspot_data['rule']['vulnerabilityProbability'].lower() == 'major':
            ranking = 'Med'
        elif hotspot_data['rule']['vulnerabilityProbability'].lower() == 'minor':
            ranking = 'Low'
        elif hotspot_data['rule']['vulnerabilityProbability'].lower() == 'info':
            ranking = 'Low'
        else:
            ranking = 'Low'

        # Get the line
        if 'line' in hotspot_data.keys():
            warning_line = int(hotspot_data['line'])
        else:
            warning_line = 0

        # Check to see if the warning should be suppressed
        if 'resolution' in hotspot_data.keys():
            suppression = True
        else:
            suppression = False

        # Add the link to the message
        warning_message.append(warning_link)

        # Add to the warning dictionary
        raw_warnings.append(translate_results.create_warning(warning_id, warning_file, warning_line,
                                                             warning_message, ID_PREFIX, ranking,
                                                             warning_query, suppression))

        # Increment the warning count
        warning_count = warning_count + 1

    # Find all of the issues files
    issues_files = results_dir.glob('sonarqube_issues_[0-9]*.json')

    # Iterate through every issues results file
    for issues_file in issues_files:
        # Read in the input data
        with open(issues_file, 'r', encoding='utf-8') as input_fh:
            issues_data = json.loads(input_fh.read())

        # Iterate through every finding in the input file
        for issue in issues_data['issues']:
            # Check to see if the warning should be suppressed
            if 'resolution' in issue.keys():
                suppression = True
            else:
                suppression = False

            # Parse the finding
            warning_file = source_root.joinpath(issue['component'].split(':')[-1]).resolve()
            warning_message = issue['message'].splitlines()
            warning_id = ID_PREFIX + str(warning_count).zfill(3)

            # Get the ranking
            if issue['severity'].lower() == 'blocker':
                ranking = 'High'
            elif issue['severity'].lower() == 'critical':
                ranking = 'High'
            elif issue['severity'].lower() == 'major':
                ranking = 'Med'
            elif issue['severity'].lower() == 'minor':
                ranking = 'Low'
            elif issue['severity'].lower() == 'info':
                ranking = 'Low'
            else:
                ranking = 'Low'

            # Get a link to the finding
            warning_link = sonarqube_url + '/project/issues?id=' + issue['project'] + '&open=' + issue['key']

            # Add the link to the warning message
            warning_message.append(warning_link)

            # Parse the query if it exists
            if 'rule' in issue.keys():
                warning_query = issue['rule']
            else:
                warning_query = ''

            # Get the line number
            if 'textRange' in issue.keys():
                warning_line = int(issue['textRange']['startLine'])
            else:
                warning_line = 0

            # Add to the warning dictionary
            raw_warnings.append(translate_results.create_warning(warning_id, warning_file, warning_line,
                                                                 warning_message, ID_PREFIX, ranking,
                                                                 warning_query, suppression))

            # Increment the warning count
            warning_count = warning_count + 1

    # Create the SCRUB output file
    translate_results.create_scrub_output_file(raw_warnings, parsed_output_file)


if __name__ == '__main__':
    parse_warnings(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), sys.argv[4])
