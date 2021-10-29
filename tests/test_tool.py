import os
import re
import sys
import glob
import shutil
import importlib
import pytest
import traceback
from tests import helpers
from tests import asserts
from scrub import scrubme

# Get a list of the raw output files
raw_output_files = []
for path, folders, files in os.walk(helpers.test_root + '/test_data/sample_data/sample_output_files'):
    for file in files:
        raw_output_files.append(os.path.join(path, file))

# Make the log directory if necessary
if not os.path.exists(helpers.log_dir):
    os.mkdir(helpers.log_dir)

@pytest.mark.parametrize('template', glob.glob(helpers.scrub_root + '/scrub/tools/templates/**/*.template'))
@pytest.mark.parametrize('operation', ['normal', 'flags'])
def test_tool(template, operation, capsys):
    # Initialize variables
    tool = os.path.basename(template).replace('.template', '')
    start_dir = os.getcwd()
    language = template.split('/')[-2]
    test_log_file = helpers.log_dir + '/' + tool + '-' + language + '-' + operation + '.log'

    # Set the configuration file
    if language == 'c':
        conf_file = helpers.c_conf_file
        custom_conf_file = helpers.c_custom_conf_file
        codebase = helpers.c_test_dir
    elif language == 'java':
        conf_file = helpers.java_conf_file
        custom_conf_file = helpers.java_custom_conf_file
        codebase = helpers.java_test_dir
    elif language == 'python':
        conf_file = helpers.python_conf_file
        custom_conf_file = helpers.python_custom_conf_file
        codebase = helpers.python_test_dir

    # Make a copy of the test code
    if os.path.exists(helpers.test_tmp_dir):
        shutil.rmtree(helpers.test_tmp_dir)
    shutil.copytree(codebase, helpers.test_tmp_dir)

    # Create the configuration file
    if operation == 'normal':
        # Import the configuration data
        with open(conf_file, 'r') as input_fh:
            conf_data = input_fh.readlines()

        # Create the conf file
        conf_data = helpers.update_tag(conf_data, 'COLLABORATOR_UPLOAD', 'False')
        helpers.create_conf_file(conf_data, helpers.test_tmp_dir + '/scrub.cfg')
    elif operation == 'flags':
        # Import the configuration data
        with open(custom_conf_file, 'r') as input_fh:
            conf_data = input_fh.readlines()

        # Create the conf file
        conf_data = helpers.update_tag(conf_data, 'COLLABORATOR_UPLOAD', 'False')
        helpers.create_conf_file(conf_data, helpers.test_tmp_dir + '/scrub.cfg')

    # Run the test
    try:
        os.chdir(helpers.test_tmp_dir)
        sys.argv = ['/opt/project/scrub/scrub_cli.py', 'run', '--tools', tool]
        scrubme.parse_arguments()

    except SystemExit:
        # Get the exit code
        sys_exit_text = traceback.format_exc()
        exit_code = int(list(filter(None, re.split('\n|:', sys_exit_text)))[-1])

        # There should be no system exit
        assert exit_code == 0

    finally:
        # Write results to the output log file
        with open(test_log_file, 'w') as output_fh:
            system_output = capsys.readouterr()
            output_fh.write(system_output.err)
            output_fh.write(system_output.out)

        # Navigate to the start directory
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
    elif 'pylint' in raw_output_file:
        source_root = '/root/scrub/scrub'
    else:
        source_root = '/root/scrub/test/integration_tests/c_testcase'

    # Parse SARIF files
    if raw_output_file.endswith('.sarif'):
        # Import the translator
        from scrub.tools.parsers import translate_results

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
