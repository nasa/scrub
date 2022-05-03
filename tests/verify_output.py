import os
import sys
import glob
import scrub.tools.parsers.translate_results as translate_results

def validate_unfiltered_scrub_results(input_file, source_root):
    """This function validates the unfiltered SCRUB output file.
    """

    # Initialize variables
    valid_results = True

    # Print a status message
    print('Checking results file: ' + input_file)

    # Parse the file
    results_list = translate_results.parse_scrub(input_file, source_root)

    # Iterate through every results
    for result in results_list:
        # Check the ID to make sure it starts with the tool name
        if not result.get('id').startswith(result.get('tool')):
            valid_results = False

        # Make sure the file exists
        if not os.path.exists(result['file']):
            valid_results = False

        # Make sure the file is a valid file path and doesn't start with a duplicate //
        if not (result.get('file')[0] == '/' and result.get('file')[1] != '/'):
            valid_results = False

        # Check the line number
        if not isinstance(result.get('line'), int):
            valid_results = False

        # Check the priority
        if not (result.get('priority') == 'Low' or result.get('priority') == 'Med' or result.get('priority') == 'High'):
            valid_results = False

        # Check the description
        if not result.get('description'):
            valid_results = False

    return valid_results, len(results_list)


def validate_filtered_scrub_results(input_file, source_root):
    """This function validates the unfiltered SCRUB output file.
    """
    # NOTE: Assumes that all other values have been checked for unfiltered results

    # Initialize variables
    valid_results = True

    # Parse the file
    results_list = translate_results.parse_scrub(input_file, source_root)

    # Print a status message
    print('Checking results file: ' + input_file)

    # Iterate through every results file
    for result in results_list:
        # Check the ID to make sure it starts with the tool name
        if not result.get('id').startswith(result.get('tool')):
            valid_results = False

        # Make sure the file is a valid file path
        if not os.path.exists(result['file']):
            valid_results = False

    return valid_results


def validate_results_set(source_root):
    """This function validates key aspects of SCRUB analysis.
    """

    # Initialize variables
    valid_output = True

    # Check the analysis scripts
    analysis_scripts = glob.glob(os.path.join(source_root, '.scrub/analysis_scripts/*.sh'))
    for analysis_script in analysis_scripts:
        tool_name = os.path.basename(analysis_script).split('.')[0]

        # Check to make sure an analysis directory exists and is not empty
        if not os.listdir(os.path.join(source_root, '.scrub/' + tool_name + '_analysis')):
            print('ERROR: Missing analysis directory')
            valid_output = False

        # Check to make sure there is a log file and it isn't empty
        if not os.path.getsize(os.path.join(source_root, '.scrub/log_files/' + tool_name + '.log')) > 0:
            print('ERROR: Missing log file(s)')
            valid_output = False

        # Find all the raw output files from the tool
        unfiltered_files = glob.glob(os.path.join(source_root, '.scrub/raw_results/*' + tool_name + '*.scrub'))
        if unfiltered_files:
            for unfiltered_file in unfiltered_files:
                # Check the results file
                if not validate_unfiltered_scrub_results(unfiltered_file, source_root):
                    print('ERROR: Invalid unfiltered results file(s)')
                    valid_output = False

        else:
            print('ERROR: Missing unfiltered results file(s)')
            valid_output = False

        # Find all the filtered output files from the tool
        if 'gcc' in os.path.basename(analysis_script) or 'javac' in os.path.basename(analysis_script) or 'gbuild' in os.path.basename(analysis_script) or 'pylint' in os.path.basename(analysis_script):
            filtered_files = [os.path.join(source_root, '.scrub/compiler.scrub')]
        else:
            filtered_files = glob.glob(os.path.join(source_root, '.scrub/' + tool_name + '*.scrub'))
        if filtered_files:
            # # Check to make sure the unfiltered and filtered counts match
            # if len(filtered_files)  len(unfiltered_files):
            #     print('ERROR: Mismatch between filtered and unfiltered results')
            #     valid_output = False

            for filtered_file in filtered_files:
                # Check the results file
                if not validate_filtered_scrub_results(filtered_file, source_root):
                    print('ERROR: Invalid filtered results file(s)')
                    valid_output = False

        else:
            print('ERROR: Missing filtered results file(s)')
            valid_output = False

    # Check to make sure the filtering log file exists


    # Check to make sure the configuration file exists

    return valid_output

if __name__ == '__main__':
    validate_results_set(sys.argv[1])