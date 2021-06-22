import os
import re
import glob
import shutil
import importlib
import pytest
from tests import helpers
from tests import asserts
from scrub.utils import scrub_utilities
from scrub.utils import do_clean

# Get a list of the raw output files
raw_output_files = []
for path, folders, files in os.walk(helpers.test_root + '/test_data/sample_data/sample_output_files'):
    for file in files:
        raw_output_files.append(os.path.join(path, file))

# Make the log directory if necessary
if not os.path.exists(helpers.log_dir):
    os.mkdir(helpers.log_dir)

# Create the operation scenarios
operations = ['normal', 'tool_error', 'invalid_config', 'custom_config']
test_tool_scenarios = []
for module in helpers.module_list:
    tool_name = list(filter(None, re.split('_', module)))[-1]
    for operation in operations:
        if operation == 'custom_config' and tool_name in helpers.custom_flag_tools:
            test_tool_scenarios.append([module, operation])
        elif operation != 'custom_config':
            test_tool_scenarios.append([module, operation])


@pytest.mark.parametrize('scenario', test_tool_scenarios)
def test_tool(scenario):
    # Import the module
    tool_module = scenario[0]
    operation = scenario[1]
    module_object = importlib.import_module(tool_module)

    # Print a status message
    print('Performing analysis: ' + scenario[0] + ' ' + scenario[1])

    # Initialize variables
    tool = re.split('_', tool_module)[-1]
    start_dir = os.getcwd()

    # Perform C analysis if applicable
    if tool_module in helpers.module_list_c:
        # Initialize variables
        log_file = os.path.normpath(helpers.c_test_dir + '/.scrub/log_files/' + tool.lower() + '.log')
        test_log_file = os.path.normpath(helpers.log_dir + '/' + tool.lower() + '-c-' + operation + '.log')

        # Move to the c_testcase
        os.chdir(helpers.c_test_dir)

        # Import the configuration data
        if operation == 'custom_config':
            c_conf_data = scrub_utilities.parse_common_configs(helpers.c_custom_conf_file)
        else:
            c_conf_data = scrub_utilities.parse_common_configs(helpers.c_conf_file)

        # Modify the config data as necessary
        if operation == 'tool_error':
            if tool == 'custom':
                c_conf_data.update({tool.lower() + '_cmd': 'make dummy'})
            else:
                c_conf_data.update({tool.lower() + '_build_cmd': 'make dummy'})
        if operation == 'invalid_config':
            if tool == 'custom':
                c_conf_data.update({tool.lower() + '_cmd': ''})
            else:
                c_conf_data.update({tool.lower() + '_build_cmd': ''})
        if operation == 'custom_config':
            # Add the tool path to PATH
            if tool.lower() == 'semmle':
                tool_path = c_conf_data.get(tool.lower() + '_path') + '/tools'
            else:
                tool_path = c_conf_data.get(tool.lower() + '_path')

            os.environ['PATH'] = tool_path + os.pathsep + os.environ['PATH']

            c_conf_data.update({tool.lower() + '_path': ''})

        # Clean the previous SCRUB data from the current directory
        do_clean.clean_directory(c_conf_data.get('source_dir'))

        # Initialize the SCRUB storage directory
        scrub_utilities.initialize_storage_dir(c_conf_data)

        # Perform analysis
        tool_status = getattr(module_object, "run_analysis")(c_conf_data)

        # Copy the log file
        if os.path.exists(log_file):
            shutil.copyfile(log_file, test_log_file)

        # Check the exit code
        if operation == 'normal' or operation == 'custom_config':
            assert tool_status == 0
            assert os.path.exists(log_file)

        elif operation == 'tool_error':
            assert tool_status == 1

        elif operation == 'invalid_config':
            assert tool_status == 2
            assert not os.path.exists(log_file)

        # Change back to the starting directory
        os.chdir(start_dir)

    if tool_module in helpers.module_list_java and operation == 'normal':
        # Initialize variables
        log_file = os.path.normpath(helpers.java_test_dir + '/.scrub/log_files/' + tool.lower() + '.log')
        test_log_file = os.path.normpath(helpers.log_dir + '/' + tool.lower() + '-java-' + operation + '.log')

        # Move to the c_testcase
        os.chdir(helpers.java_test_dir)

        # Import the configuration data
        java_conf_data = scrub_utilities.parse_common_configs(helpers.java_conf_file)

        # Clean the previous SCRUB data from the current directory
        do_clean.clean_directory(java_conf_data.get('source_dir'))

        # Initialize the SCRUB storage directory
        scrub_utilities.initialize_storage_dir(java_conf_data)

        # Perform analysis
        tool_status = getattr(module_object, "run_analysis")(java_conf_data)

        # Copy the log file
        if os.path.exists(log_file):
            shutil.copyfile(log_file, test_log_file)

        # Check the exit code
        assert tool_status == 0
        assert os.path.exists(test_log_file)

        # Change back to the starting directory
        os.chdir(start_dir)


@pytest.mark.parametrize("raw_output_file", raw_output_files)
def test_parser(raw_output_file):
    # Initialize variables
    parsed_output_file = helpers.test_root + '/test_parse.scrub'

    # Get the tool module
    tool_name = list(filter(None, re.split('/', os.path.relpath(raw_output_file, helpers.test_root +
                                                                '/test_data/sample_data/sample_output_files'))))[0]

    if 'java' in raw_output_file:
        source_root = '/root/scrub/test/integration_tests/java_testcase'
    else:
        source_root = '/root/scrub/test/integration_tests/c_testcase'

    # Parse SARIF files
    if raw_output_file.endswith('.sarif'):
        # Import the translator
        import scrub.utils.translate_results as translate_results

        # Parse the results
        translate_results.perform_translation(raw_output_file, parsed_output_file, source_root, 'scrub')

    # Parse other files
    else:
        # Import the parser module
        module_path = glob.glob(helpers.scrub_root + '/**/get_' + tool_name + '_warnings.py', recursive=True)[0]
        module_name = re.split('\\.py', os.path.relpath(module_path, helpers.scrub_root))[0].replace('/', '.')

        # Import the module
        module_object = importlib.import_module(module_name)

        # Parse the results
        if tool_name in helpers.versioned_tools:
            # Get the tool version
            tool_version = list(filter(None, re.split('/', raw_output_file)))[-3]

            getattr(module_object, "parse_warnings")(raw_output_file, parsed_output_file, tool_version)
        else:
            getattr(module_object, "parse_warnings")(raw_output_file, parsed_output_file)

    # Check the state of the SCRUB file
    asserts.assert_valid_scrub(parsed_output_file)

    # Cleanup
    if os.path.exists(parsed_output_file):
        os.remove(parsed_output_file)
