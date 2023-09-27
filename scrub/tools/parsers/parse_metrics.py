import sys
import json
import pathlib
import traceback
import xml.etree.ElementTree as ET


def create_output_file(metrics_data, output_file, tool_metrics_list, file_list):
    """This function generates the output CSV file.

    Inputs:
        - metrics_data: Dictionary containing metrics information [dict]
        - output_file: Absolute path to output file location [string]
        - tool_metrics_list: Dictionary of tool metrics mapped to their common name [dict]
        - file_list: List of all files present in the metrics data [list of strings]

    Outputs:
        None
    """

    # Generate the output file
    with open(output_file, 'w+') as output_fh:
        # Print the header data
        output_fh.write('Scope,Directory,')
        for metric in tool_metrics_list.keys():
            output_fh.write('{},'.format(tool_metrics_list.get(metric)))
        output_fh.write('\n')

        # Print the project level metrics
        output_fh.write('Project,N/A,')
        for metric in tool_metrics_list:
            output_fh.write('{},'.format(metrics_data.get('project_metrics').get(metric, 'N/A')))
        output_fh.write('\n')

        # Print out the file level metrics
        file_list.sort()
        for file_path in file_list:
            output_fh.write('{},{},'.format(file_path, str(pathlib.Path(file_path).parent)))
            for metric in tool_metrics_list.keys():
                output_fh.write('{},'.format(metrics_data.get(file_path).get(metric, 'N/A')))
            output_fh.write('\n')


def parse_codesonar_metrics(raw_metrics_file, parsed_output_file, source_root):
    """This function parses the CodeSonar metrics output file into a more human readable format.

    Inputs:
        - raw_metrics_file: Absolute path to the raw CodeSonar metrics file [string]
        - parsed_output_file: Absolute path to the parsed output file [string]

    Outputs:
        - codesonar_metrics: Dictionary of all captured metrics [dict]
    """

    # Initialize variables
    metrics_list = {'Top-level file instances': 'Number of Files',
                    'User-defined functions': 'Number of Functions',
                    'Total Lines': 'Total Lines',
                    'Code Lines': 'Lines of Code',
                    'Comment Lines': 'Number of Comments',
                    'Cyclomatic Complexity': 'Cyclomatic Complexity',
                    'Modified Cyclomatic Complexity': 'Modified Cyclomatic Complexity',
                    'Taint Propagator Total': 'Taint Propagator Total',
                    'Taint Sink Total': 'Taint Sink Total',
                    'Taint Source Total': 'Taint Source Total',
                    'Lines with Code': 'Lines with Code',
                    'Lines with Comments': 'Lines with Comments',
                    'Blank Lines': 'Blank Lines',
                    'Mixed Lines': 'In-Line Comments',
                    'Include file instances': 'Number of Includes'}

    # Read in the metrics file
    with open(raw_metrics_file, 'r') as input_fh:
        metrics_data = json.load(input_fh)

    # Update the data structure
    file_list = []
    cleaned_metrics_data = {'project_metrics': {}}
    for metric in metrics_data.get('metrics'):
        if metric.get('granularity').lower() == 'analysis':
            cleaned_metrics_data['project_metrics'][metric.get('description')] = metric.get('rows')[0].get('value')
        elif metric.get('granularity').lower() == 'file':
            for file_metric in metric.get('rows'):
                # Find the file name in the source tree
                file_name = file_metric.get('file')
                file_search = source_root.rglob(file_name)
                if len(list(file_search)) == 1:
                    file_path = str(next(source_root.rglob(file_name)).relative_to(source_root))
                else:
                    print('ERROR: Could not resolve file path {}'.format(file_name))

                # Add the file to the list
                if file_path not in cleaned_metrics_data.keys():
                    cleaned_metrics_data[file_path] = {}
                    file_list.append(file_path)

                # Add the metric to the dictionary
                cleaned_metrics_data[file_path][metric.get('description')] = file_metric.get('value')

    # Generate the output file
    create_output_file(cleaned_metrics_data, parsed_output_file, metrics_list, file_list)

    return cleaned_metrics_data


def parse_sonarqube_metrics(metrics_directory, parsed_output_file):
    """This function parses the SonarQube metrics output file into a more human readable format.

    Inputs:
        - metrics_directory: Absolute path to the directory containing raw SonarQube metrics data [string]
        - parsed_output_file: Absolute path to the parsed output file [string]

    Outputs:
        - cleaned_metrics_data: Dictionary of all captured metrics [dict]
    """

    # Initialize variables
    metrics_list = {'files': 'Number of Files',
                    'functions': 'Number of Functions',
                    'ncloc': 'Lines of Code',
                    'comment_lines_density': 'Comment Density',
                    'classes': 'Number of Classes',
                    'complexity': 'Cyclomatic Complexity',
                    'cognitive_complexity': 'Cognitive Complexity',
                    'violations': 'Number of Violations',
                    'vulnerabilities': 'Number of Vulnerabilities',
                    'security_hotspots': 'Security Hotspots',
                    'coverage': 'Code Coverage',
                    'line_coverage': 'Code Coverage: Lines',
                    'branch_coverage': 'Code Coverage: Branches',
                    'sqale_index': 'SQALE Index',
                    'duplicated_lines_density': 'Duplication Density'}

    # Read in the project metrics file
    project_metrics_file = metrics_directory.joinpath('sonarqube_metrics_project.json')
    with open(project_metrics_file, 'r') as input_fh:
        project_metrics_data = json.load(input_fh)

    # Parse the project level metrics
    cleaned_metrics_data = {'project_metrics': {}}
    for project_measures in project_metrics_data.get('baseComponent').get('measures'):
        cleaned_metrics_data['project_metrics'][project_measures.get('metric')] = project_measures.get('value')

    # Find all of the file level metrics
    metrics_files = metrics_directory.glob('sonarqube_metrics_file_*.json')

    # Parse the file level metrics
    file_list = []
    for metrics_file in metrics_files:
        with open(metrics_file, 'r') as input_fh:
            file_metrics_data = json.load(input_fh)

        # Parse every component
        for source_file in file_metrics_data.get('components'):
            for file_metric in source_file.get('measures'):
                if source_file.get('path') not in cleaned_metrics_data.keys():
                    cleaned_metrics_data[source_file.get('path')] = {}
                    file_list.append(source_file.get('path'))
                cleaned_metrics_data[source_file.get('path')][file_metric.get('metric')] = file_metric.get('value')

    # Generate the output file
    create_output_file(cleaned_metrics_data, parsed_output_file, metrics_list, file_list)

    return cleaned_metrics_data


def parse_coverity_metrics(metrics_directory, parsed_output_file):
    """This function parses the SonarQube metrics output file into a more human readable format.

    Inputs:
        - raw_metrics_file: Absolute path to the directory containing raw Coverity metrics data [string]
        - parsed_output_file: Absolute path to the parsed output file [string]

    Outputs:
        - coverity_metrics: Dictionary of all captured metrics [dict]
    """

    # Initialize variables
    metrics_list = {'files-analyzed': 'Number of Files',
                    'function-metrics-count': 'Number of Functions',
                    'code-lines': 'Lines of Code',
                    'comment-lines': 'Number of Comments'}

    # Read in the project metrics file
    project_metrics_file = metrics_directory.joinpath('output/ANALYSIS.metrics.xml')
    project_metrics_tree = ET.parse(project_metrics_file)

    # Parse the project level metrics
    cleaned_metrics_data = {'project_metrics': {}}
    for raw_metric_data in project_metrics_tree.findall('metrics/metric'):
        metric_name = raw_metric_data.find('name').text
        metric_value = raw_metric_data.find('value').text

        # Gather only the metrics of interest
        if metric_name in metrics_list:
            cleaned_metrics_data['project_metrics'][metric_name] = metric_value

    # Generate the output file
    create_output_file(cleaned_metrics_data, parsed_output_file, metrics_list, [])

    return cleaned_metrics_data

def parse(metrics_input, output_file, source_dir, tool):
    """This function finds the correct parser for each metrics report.

    Inputs:
        - metrics_input: Absolute path to the raw metrics file or directory containing metrics files [string]
        - output_file: Absolute path to the parsed output file [string]

    Outputs:
        - metrics: Dictionary of all parsed metrics [dict]
    """

    # Initialize variables
    metrics = {}

    # Choose the correct parser
    if tool == 'sonarqube':
        metrics = parse_sonarqube_metrics(metrics_input, output_file)
    elif tool == 'codesonar':
        metrics = parse_codesonar_metrics(metrics_input, output_file, source_dir)
    elif tool == 'coverity':
        metrics = parse_coverity_metrics(metrics_input, output_file)
    else:
        print('ERROR: Unknown metrics file type')
        print(traceback.format_exc())

    return metrics


if __name__ == '__main__':
    parse(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), sys.argv[4])
