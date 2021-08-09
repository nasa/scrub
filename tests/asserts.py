import os
import re
import glob
from tests import helpers
from scrub.utils import translate_results


def assert_valid_scrub(scrub_file):
    # Import the file contents
    with open(scrub_file, 'r') as input_fh:
        scrub_data = input_fh.readlines()

    for line in scrub_data:
        if (not line.startswith(' ')) and (line.strip() != ''):
            # Make sure the line fits the format
            assert(re.search(translate_results.WARNING_LINE_REGEX, line) is not None)
        elif line.startswith(' '):
            assert(re.search('    ', line) is not None)
        else:
            assert(line == '\n')


def assert_scrubme_success(output_dir, language):
    # Initialize variables
    test_dir = helpers.test_tmp_dir
    if language == 'c':
        module_list = helpers.module_list_c

    elif language == 'j':
        module_list = helpers.module_list_java
    elif language == 'p':
        module_list = helpers.module_list_python
    else:
        print('Unkown language selection.')

    # Get the list of log files
    log_files = []
    for module in module_list:
        tool_name = list(filter(None, re.split('_', module)))[-1]
        log_files.append(test_dir + '/.scrub/log_files/' + tool_name + '.log')
    filtering_log_file = os.path.normpath(output_dir + '/log_files/filtering.log')

    # Iterate through all of the log files
    for log_file in log_files:
        # Initialize variables
        tool = list(filter(None, re.split('/|\\.log', log_file)))[-1]

        # Make sure the log file exists and is error free
        assert open(log_file).read().count('') > 0
        assert open(log_file).read().count(' ERROR   ') == 0
        assert open(log_file).read().count('CommandExecutionError') == 0

        # Check for version info in the test log
        if tool in helpers.versioned_tools:
            assert open(log_file).read().count(' Version: ') > 0
        else:
            assert open(log_file).read().count(' Version: ') == 0

    # Make sure the filtering log file exists and isn't empty
    assert open(filtering_log_file).read().count('') > 0

    # Make sure the results files exist and aren't empty
    raw_results_files = glob.glob(output_dir + '/raw_results/*.scrub')
    parsed_results_files = glob.glob(output_dir + '/*.scrub')
    for results_file in raw_results_files:
        assert open(results_file).read().count('') > 0
    for results_file in parsed_results_files:
        assert open(results_file).read().count('') > 0


def assert_mod_helper_success(output_dir, tool, test_log):
    # Initialize variables
    tool_log_file = os.path.abspath(output_dir + '/log_files/' + tool + '.log')
    filtering_log_file = os.path.normpath(output_dir + '/log_files/filtering.log')

    # Make sure the log file exists and isn't empty
    assert open(tool_log_file).read().count('') > 0
    assert open(filtering_log_file).read().count('') > 0

    # Make sure the results files exist and aren't empty
    raw_results_files = glob.glob(output_dir + '/raw_results/*.scrub')
    parsed_results_files = glob.glob(output_dir + '/*.scrub')
    for results_file in raw_results_files:
        assert open(results_file).read().count('') > 0
    for results_file in parsed_results_files:
        assert open(results_file).read().count('') > 0

    # Make sure there aren't any errors during execution
    assert open(tool_log_file).read().count(' ERROR   ') == 0

    # Check for version info in the test log
    if tool in helpers.versioned_tools:
        assert open(test_log).read().count(' Version: ') > 0
    else:
        assert open(test_log).read().count(' Version: ') == 0

    # Make sure no errors are present in the test log
    assert open(test_log).read().count(' ERROR   ') == 0
    assert open(test_log).read().count('CommandExecutionError') == 0


def assert_tool_failure(output_dir, tool, test_log, mod_helper):
    # Initialize variables
    tool_log_file = os.path.abspath(output_dir + '/log_files/' + tool + '.log')
    filtering_log_file = os.path.normpath(output_dir + '/log_files/filtering.log')

    # Make sure the log files exist and aren't empty
    assert open(tool_log_file).read().count('') > 0
    assert open(test_log).read().count('') > 0

    # Make sure that the tool failure is logged correctly
    assert open(tool_log_file).read().count('CommandExecutionError') > 0
    assert open(test_log).read().count('CommandExecutionError') > 0

    if not mod_helper:
        # Check to make sure the filtering file exists and isn't empty
        assert open(filtering_log_file).read().count('') > 0


def assert_python_failure(source_dir, tool, test_log, mod_helper):
    # Initialize variables
    tool_log_file = os.path.abspath(source_dir + '/.scrub/log_files/' + tool + '.log')
    filtering_log_file = os.path.normpath(source_dir + '/log_files/filtering.log')

    # Make sure the log file exists and isn't empty
    assert open(tool_log_file).read().count('') > 0

    if not mod_helper:
        # Make sure execution was halted
        assert not os.path.exists(filtering_log_file)

    # Make sure the errors are logged
    assert open(tool_log_file).read().count(' A SCRUB error has occurred.') > 0
    assert open(test_log).read().count(' A SCRUB error has occurred.') > 0
