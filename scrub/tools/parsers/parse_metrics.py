import logging
import sys
import json
import pathlib
import traceback
import csv
import xml.etree.ElementTree


def parse_csv(input_file, source_root):
    """This function parses a csv metrics file into a dictionary object.

    Inputs:
        - input_file: Absolute path to metrics csv file location [string]
        - source_root: Absolute path to source code root directory [string]

    Outputs:
        - metrics_data: Dictionary of metrics values [dict]
    """

    # Initialize variables
    metrics_data = {'project': {}}

    # Read in the metrics data
    with open(input_file) as input_fh:
        raw_metrics_data = list(csv.reader(input_fh, delimiter=','))

        # Get the project level metrics
        for i in range(2, len(raw_metrics_data[0])):
            metric_name = raw_metrics_data[0][i]
            metric_value = raw_metrics_data[1][i]

            # Add the metric as long as it has a value
            if metric_value != 'N/A' and metric_value != '':
                metrics_data['project'][metric_name] = float(metric_value)

        # Get file level metrics
        for i in range(2, len(raw_metrics_data)):
            file_name = str(source_root.joinpath(raw_metrics_data[i][0]))
            metrics_data[file_name] = {}
            for j in range(3, len(raw_metrics_data[0])):
                metric_name = raw_metrics_data[0][j]
                metric_value = raw_metrics_data[i][j]

                # Add the metric as long as it has a value
                if metric_value != 'N/A' and metric_value != '':
                    metrics_data[file_name][metric_name] = float(metric_value)

    return metrics_data


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


def parse_codesonar_metrics(raw_analysis_metrics_file, raw_file_metrics_file, parsed_output_file, source_root):
    """This function parses the CodeSonar metrics output file into a more human-readable format.

    Inputs:
        - raw_analysis_metrics_file: Absolute path to the raw analysis-level CodeSonar metrics file [string]
        - raw_file_metrics_file: Absolute path to the raw file-level CodeSonar metrics file [string]
        - parsed_output_file: Absolute path to the parsed output file [string]

    Outputs:
        - codesonar_metrics: Dictionary of all captured metrics [dict]
    """

    # Initialize variables
    cleaned_metrics_data = {'project_metrics': {}}
    metrics_list = {'Top-level file instances': 'Number of Files',
                    'User-defined functions': 'Number of Functions',
                    'Total Lines': 'Total Lines',
                    'Code Lines': 'Lines of Code',
                    'Comment Lines': 'Number of Comments',
                    'Comment Density': 'Comment Density',
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

    # Parse the metrics files if they exist
    if raw_analysis_metrics_file.exists() and raw_file_metrics_file.exists():
        # Read in the analysis-level metrics file
        with open(raw_analysis_metrics_file, 'r') as input_fh:
            analysis_metrics_data = json.load(input_fh)

        # Read in the file-level metrics file
        with open(raw_file_metrics_file, 'r') as input_fh:
            file_metrics_data = json.load(input_fh)

        # Update the data structure
        for metric in analysis_metrics_data.get('metrics'):
            if metric.get('granularity').lower() == 'analysis':
                cleaned_metrics_data['project_metrics'][metric.get('description')] = (metric.get('rows')[0]
                                                                                      .get('metricValue'))

        # Update the data structure
        file_list = []
        file_path = None
        for metric in file_metrics_data.get('metrics'):
            if metric.get('granularity').lower() == 'file':
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
                    cleaned_metrics_data[file_path][metric.get('description')] = file_metric.get('metricValue')
                    cleaned_metrics_data[file_path]['Top-level file instances'] = 1

        # Calculate comment density
        for item in cleaned_metrics_data.keys():
            if int(cleaned_metrics_data[item]['Code Lines']) != 0:
                comment_density = round(int(cleaned_metrics_data[item]['Comment Lines']) /
                                        int(cleaned_metrics_data[item]['Code Lines']) * 100, 2)
            else:
                comment_density = 'N/A'
            cleaned_metrics_data[item]['Comment Density'] = comment_density

        # Check to make sure we have data
        if cleaned_metrics_data:
            # Generate the output file
            create_output_file(cleaned_metrics_data, parsed_output_file, metrics_list, file_list)
        else:
            logging.warning('\tCould not parse metrics data. Check log for more information.')
    else:
        logging.warning('\tSome metrics data is missing. Check log for more information.')

    return cleaned_metrics_data


def parse_sonarqube_metrics(metrics_directory, parsed_output_file):
    """This function parses the SonarQube metrics output file into a more human-readable format.

    Inputs:
        - metrics_directory: Absolute path to the directory containing raw SonarQube metrics data [string]
        - parsed_output_file: Absolute path to the parsed output file [string]

    Outputs:
        - cleaned_metrics_data: Dictionary of all captured metrics [dict]
    """

    # Initialize variables
    cleaned_metrics_data = {}
    project_metrics_file = metrics_directory.joinpath('sonarqube_metrics_project.json')
    metrics_files = list(metrics_directory.glob('sonarqube_metrics_file_*.json'))
    metrics_list = {'files': 'Number of Files',
                    'functions': 'Number of Functions',
                    'lines': 'Total Lines',
                    'ncloc': 'Lines of Code',
                    'comment_lines': 'Number of Comments',
                    'comment_density': 'Comment Density',
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

    # Read in the metrics data, if it exists
    if project_metrics_file.exists() and metrics_files:
        with open(project_metrics_file, 'r') as input_fh:
            project_metrics_data = json.load(input_fh)

        # Parse the project level metrics
        cleaned_metrics_data = {'project_metrics': {}}
        for project_measures in project_metrics_data.get('baseComponent').get('measures'):
            cleaned_metrics_data['project_metrics'][project_measures.get('metric')] = float(project_measures
                                                                                            .get('value'))

        # Add in the comment density information
        comment_density = round(int(cleaned_metrics_data['project_metrics']['comment_lines']) /
                                int(cleaned_metrics_data['project_metrics']['ncloc']) * 100, 2)
        cleaned_metrics_data['project_metrics']['comment_density'] = comment_density

        # Parse the file level metrics
        file_list = []
        if len(metrics_files) > 0:
            for metrics_file in metrics_files:
                with open(metrics_file, 'r') as input_fh:
                    file_metrics_data = json.load(input_fh)

                # Parse every component
                for source_file in file_metrics_data.get('components'):
                    for file_metric in source_file.get('measures'):
                        if source_file.get('path') not in cleaned_metrics_data.keys():
                            cleaned_metrics_data[source_file.get('path')] = {}
                            file_list.append(source_file.get('path'))
                        cleaned_metrics_data[source_file.get('path')][file_metric.get('metric')] = float(file_metric
                                                                                                         .get('value'))

                    # Add in the comment density information
                    if cleaned_metrics_data[source_file['path']]['ncloc'] > 0:
                        comment_density = round(int(cleaned_metrics_data[source_file['path']]['comment_lines']) /
                                                int(cleaned_metrics_data[source_file['path']]['ncloc']) * 100, 2)
                    else:
                        comment_density = 'N/A'
                    cleaned_metrics_data[source_file.get('path')]['comment_density'] = comment_density

                    # Update complexity measurement if necessary
                    if 'complexity' not in cleaned_metrics_data[source_file.get('path')].keys():
                        cleaned_metrics_data[source_file.get('path')]['complexity'] = 0
                    # Update functions count measurement if necessary
                    if 'functions' not in cleaned_metrics_data[source_file.get('path')].keys():
                        cleaned_metrics_data[source_file.get('path')]['functions'] = 0

        # Generate the output file
        if cleaned_metrics_data:
            create_output_file(cleaned_metrics_data, parsed_output_file, metrics_list, file_list)
        else:
            logging.warning('\tCould parse metrics data. Check log for more details.')
    else:
        logging.warning('\tSome metrics data is missing. Check log for more information.')

    return cleaned_metrics_data


def parse_coverity_metrics(metrics_directory, parsed_output_file):
    """This function parses the SonarQube metrics output file into a more human-readable format.

    Inputs:
        - raw_metrics_file: Absolute path to the directory containing raw Coverity metrics data [string]
        - parsed_output_file: Absolute path to the parsed output file [string]

    Outputs:
        - coverity_metrics: Dictionary of all captured metrics [dict]
    """

    # Initialize variables
    project_metrics_file = metrics_directory.joinpath('output/ANALYSIS.metrics.xml')
    cleaned_metrics_data = {'project_metrics': {}}
    metrics_list = {'files-analyzed': 'Number of Files',
                    'function-metrics-count': 'Number of Functions',
                    'code-lines': 'Lines of Code',
                    'comment-lines': 'Number of Comments'}

    # Read in the project metrics file
    if project_metrics_file.exists():
        project_metrics_tree = xml.etree.ElementTree.parse(project_metrics_file)

        # Parse the project level metrics
        for raw_metric_data in project_metrics_tree.findall('metrics/metric'):
            metric_name = raw_metric_data.find('name').text
            metric_value = raw_metric_data.find('value').text

            # Gather only the metrics of interest
            if metric_name in metrics_list:
                cleaned_metrics_data['project_metrics'][metric_name] = metric_value

        # Generate the output file
        create_output_file(cleaned_metrics_data, parsed_output_file, metrics_list, [])
    else:
        logging.warning('\tSome metrics data is missing. Check log for more information.')

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
