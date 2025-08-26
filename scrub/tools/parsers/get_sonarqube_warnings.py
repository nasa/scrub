import json
from scrub.tools.parsers import translate_results
from scrub.tools.parsers import parse_metrics

ID_PREFIX = 'sonarqube'


def parse_warnings(analysis_dir, tool_config_data, parsed_output_file=None):
    """This function parses the raw SonarQube warnings into the SCRUB format.

    Inputs:
        - analysis_dir: Absolute path to the raw SonarQube output file directory [string]
        - tool_config_data: Dictionary of scrub configuration data [dict]
    """

    # Initialize the variables
    warning_count = 1
    raw_warnings = []
    sonarqube_url = tool_config_data.get('sonarqube_server')
    source_root = tool_config_data.get('source_dir')
    metrics_output_file = tool_config_data.get('scrub_analysis_dir').joinpath('sonarqube_metrics.csv')

    # Set the output file
    if parsed_output_file is None:
        parsed_output_file = tool_config_data.get('raw_results_dir').joinpath('sonarqube_raw.scrub')

    # Find all the raw findings results files in the directory
    findings_results_files = (list(analysis_dir.glob('sonarqube_issues*.json')) +
                              list(analysis_dir.glob('sonarqube_hotspots*.json')))

    # Iterate through every issue results file
    for raw_findings_file in findings_results_files:
        # Read in the input data
        with open(raw_findings_file, 'r') as input_fh:
            input_data = json.loads(input_fh.read())

        # Iterate through every finding in the input file
        if 'issues' in input_data.keys():
            findings = input_data['issues']
        elif 'hotspots' in input_data.keys():
            findings = input_data['hotspots']
        else:
            break

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
                warning_link = sonarqube_url + '/security_hotspots?id=' + finding['project'] + '&hotspots=' + finding[
                    'key']
            else:
                warning_link = sonarqube_url + '/project/issues?id=' + finding['project'] + '&open=' + finding['key']

            # Add the link to the warning message
            warning_message.append(warning_link)

            # Parse the query if it exists
            if 'rule' in finding.keys():
                warning_query = finding['rule']
            elif 'ruleKey' in finding.keys():
                warning_query = finding['ruleKey']
            else:
                warning_query = ''

            # Get the priority value from SonarQube
            if 'vulnerabilityProbability' in finding.keys():
                sonarqube_priority = finding['vulnerabilityProbability'].lower()
            elif 'severity' in finding.keys():
                sonarqube_priority = finding['severity'].lower()
            else:
                sonarqube_priority = 'low'

            # Translate the priority to High/Med/Low
            if ((sonarqube_priority == 'blocker') or
                    (sonarqube_priority == 'critical') or
                    (sonarqube_priority == 'high')):
                priority = 'High'
            elif (sonarqube_priority == 'major') or (sonarqube_priority == 'medium'):
                priority = 'Med'
            elif (sonarqube_priority == 'minor') or (sonarqube_priority == 'info') or (sonarqube_priority == 'low'):
                priority = 'Low'
            else:
                priority = 'Low'

            # Get the line number
            if 'line' in finding.keys():
                warning_line = int(finding['line'])
            elif 'textRange' in finding.keys():
                warning_line = int(finding['textRange']['startLine'])
            else:
                warning_line = 0

            # Add to the warning dictionary
            raw_warnings.append(translate_results.create_warning(warning_id, warning_file, warning_line,
                                                                 warning_message, ID_PREFIX, priority,
                                                                 warning_query, suppression))

            # Increment the warning count
            warning_count = warning_count + 1

    # Create the SCRUB output file
    translate_results.create_scrub_output_file(raw_warnings, parsed_output_file)

    # Parse the metrics data
    parse_metrics.parse(analysis_dir, metrics_output_file, source_root, 'sonarqube')
