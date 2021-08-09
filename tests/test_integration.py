import os
import re
import shutil
import pytest
import traceback
from tests import helpers
from tests import asserts


# Make the log directory if necessary
if not os.path.exists(helpers.log_dir):
    os.mkdir(helpers.log_dir)


@pytest.mark.parametrize("tool_module", helpers.module_list_c)
@pytest.mark.parametrize("state", ['clean', 'dirty', 'empty'])
@pytest.mark.parametrize("working_dir", ['source', 'external'])
def test_mod_helper(tool_module, state, working_dir, capsys):
    # Imports
    import scrub.module_helper as module_helper

    # Initialize variables
    tool = re.split('_', tool_module)[-1]
    output_dir = helpers.c_test_dir + '/.scrub'
    test_log_file = helpers.log_dir + '/' + tool + '-c-' + state + '-' + working_dir + '-mod_helper.log'

    start_dir = os.getcwd()
    os.chdir(helpers.c_test_dir)

    # Import the configuration data
    with open(helpers.c_conf_file, 'r') as input_fh:
        c_conf_data = input_fh.readlines()

    # Turn off all tools
    conf_data = helpers.disable_all_tools(c_conf_data)

    # Update the working dir if necessary
    if working_dir == 'external':
        conf_data = helpers.update_tag(conf_data, 'SCRUB_WORKING_DIR', '/root/scrub_working_dir')

    # Initialize the test
    helpers.init_testcase(conf_data, helpers.c_test_dir, state, helpers.log_dir)

    # Run module_helper
    module_helper.main(tool_module, 'scrub.cfg')

    # Write results to the output log file
    with open(test_log_file, 'w') as output_fh:
        system_output = capsys.readouterr()
        output_fh.write(system_output.err)
        output_fh.write(system_output.out)

    # Navigate to the start directory
    os.chdir(start_dir)

    # Check the SCRUB output
    asserts.assert_mod_helper_success(output_dir, tool, test_log_file)

    # Make sure the working directory no longer exists
    if working_dir == 'external':
        assert not os.path.exists('/root/scrub_working_dir')

    # Clean the codebase
    helpers.clean_codebase(helpers.c_test_dir, helpers.c_test_dir + '/src', 'make clean')


@pytest.mark.parametrize("language", ['c', 'j', 'p'])
@pytest.mark.parametrize("working_dir", ['source_root', 'external'])
def test_scrubme(language, working_dir):
    import scrub.scrubme as scrubme

    # Initialize variables
    if language == 'c':
        test_dir = helpers.c_test_dir
        conf_file = helpers.c_conf_file
        exclude_queries_file = helpers.c_exclude_queries_file
        regex_filtering_file = helpers.c_regex_filtering_file
    elif language == 'j':
        test_dir = helpers.java_test_dir
        conf_file = helpers.java_conf_file
        exclude_queries_file = helpers.java_exclude_queries_file
        regex_filtering_file = helpers.java_regex_filtering_file
    elif language == 'p':
        test_dir = helpers.python_test_dir
        conf_file = helpers.python_conf_file
        exclude_queries_file = helpers.python_exclude_queries_file
        regex_filtering_file = helpers.python_regex_filtering_file
    else:
        print('Unknown language selection.')

    # Make a copy of the test code
    tmp_test_dir = helpers.test_tmp_dir
    shutil.copytree(test_dir, tmp_test_dir)

    output_dir = tmp_test_dir + '/.scrub'

    # Navigate to the test directory
    start_dir = os.getcwd()
    os.chdir(tmp_test_dir)

    # Import the configuration data
    with open(conf_file, 'r') as input_fh:
        conf_data = input_fh.readlines()

    # Update the working dir if necessary
    if working_dir == 'external':
        conf_data = helpers.update_tag(conf_data, 'SCRUB_WORKING_DIR', '/root/scrub_working_dir')

    # Initialize the test
    if language == 'c':
        helpers.init_codebase(tmp_test_dir, conf_data, 'gcc')
    elif language == 'j':
        helpers.init_codebase(tmp_test_dir, conf_data, 'javac')
    else:
        None

    # Create the conf file
    helpers.create_conf_file(conf_data, tmp_test_dir + '/scrub.cfg')

    # Initialize the testcase
    if language != 'p':
        helpers.init_testcase(conf_data, tmp_test_dir, 'clean', helpers.log_dir)

    # Add the filtering files
    shutil.copyfile(exclude_queries_file, tmp_test_dir + '/SCRUBExcludeQueries')
    shutil.copyfile(regex_filtering_file, tmp_test_dir + '/SCRUBFilters')

    # Run scrubme
    try:
        scrubme.main('./scrub.cfg')

    except SystemExit:
        # Get the exit code
        sys_exit_text = traceback.format_exc()
        exit_code = int(list(filter(None, re.split('\n|:', sys_exit_text)))[-1])

        # There should be no system exit
        assert exit_code == 0

    finally:
        # Navigate to the start directory
        os.chdir(start_dir)

        # Check the SCRUB output
        asserts.assert_scrubme_success(output_dir, language)

        # Make sure the working directory no longer exists
        if working_dir == 'external':
            assert not os.path.exists('/root/scrub_working_dir')

        # Clean the test artifacts
        if os.path.exists(tmp_test_dir):
            shutil.rmtree(tmp_test_dir)
