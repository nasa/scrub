import os
import re
import sys
import glob
import shutil
import pytest
import traceback
from scrub import scrubme
from tests import helpers


# Initialize variables
test_dir = helpers.c_test_dir
conf_file = helpers.c_custom_conf_file
exclude_queries_file = helpers.c_exclude_queries_file
regex_filtering_file = helpers.c_regex_filtering_file

# Make a copy of the test code
tmp_test_dir = helpers.test_tmp_dir
if os.path.exists(tmp_test_dir):
    shutil.rmtree(tmp_test_dir)
shutil.copytree(test_dir, tmp_test_dir)

# Make the log directory if necessary
if not os.path.exists(helpers.log_dir):
    os.mkdir(helpers.log_dir)

cli_flags = [['--config', './scrub.cfg', '--clean'],
             ['--tools', 'filtering', '--targets', 'scrub_gui'],
             ['--tools', 'coverity', '--targets', 'scrub_gui']]
# cli_flags = [['--tools', 'coverity', '--targets', 'scrub_gui']]

@pytest.mark.parametrize("flags", cli_flags)
@pytest.mark.parametrize("working_dir", ['source', 'external'])
def test_scrubme(working_dir, flags, capsys):
    # Create the log file
    test_log_file = helpers.log_dir + '/scrub-run-' + working_dir + '_' + str(cli_flags.index(flags)) + '.log'

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
    if '--clean' in cli_flags:
        helpers.init_codebase(tmp_test_dir, 'c', 'clean')

    # Create the conf file
    helpers.create_conf_file(conf_data, tmp_test_dir + '/scrub.cfg')

    # # Initialize the testcase
    # helpers.init_testcase(conf_data, tmp_test_dir, 'clean', helpers.log_dir)

    # Add the filtering files
    shutil.copyfile(exclude_queries_file, tmp_test_dir + '/SCRUBExcludeQueries')
    shutil.copyfile(regex_filtering_file, tmp_test_dir + '/SCRUBFilters')

    try:
        # Run scrubme
        sys.argv = ['/opt/project/scrub/scrub_cli.py', 'run'] + flags
        scrubme.parse_arguments()

    except SystemExit:
        # Write results to the output log file
        with open(test_log_file, 'w') as output_fh:
            system_output = capsys.readouterr()
            output_fh.write(system_output.err)
            output_fh.write(system_output.out)

        # Get the exit code
        sys_exit_text = traceback.format_exc()
        exit_code = int(list(filter(None, re.split('\n|:', sys_exit_text)))[-1])

        # There should be no system exit
        assert exit_code == 0

        # Make sure the working directory no longer exists
        if working_dir == 'external':
            assert not os.path.exists('/root/scrub_working_dir')

        # Make sure the filtering log file exists and isn't empty
        assert open(os.path.normpath(helpers.test_tmp_dir + '/.scrub/log_files/filtering.log')).read().count('') > 0

        # Verify analysis
        if '--tools' in flags:
            tool = flags[flags.index('--tools') + 1].lower()
            log_file = helpers.test_tmp_dir + '/.scrub/log_files/' + tool + '.log'

            # Make sure the log file exists and is error free
            assert open(log_file).read().count('') > 0
            assert open(log_file).read().count(' ERROR   ') == 0
            assert open(log_file).read().count('CommandExecutionError') == 0

            # Make sure the results files exist
            if tool != 'filtering':
                assert open(helpers.test_tmp_dir + '/.scrub/raw_results/' + tool + '_raw.scrub').read().count('') > 0
                assert open(helpers.test_tmp_dir + '/.scrub/' + tool + '.scrub').read().count('') > 0
        else:
            for line in conf_data:
                if ('_WARNINGS: ' in line) and ('True' in line):
                    tool = line.split('_')[0].lower()
                    log_file = helpers.test_tmp_dir + '/.scrub/log_files/' + tool + '.log'

                    # Make sure the log file exists and is error free
                    assert open(log_file).read().count('') > 0
                    assert open(log_file).read().count(' ERROR   ') == 0
                    assert open(log_file).read().count('CommandExecutionError') == 0

                    # Make sure the results files exist
                    raw_results_file = glob.glob(helpers.test_tmp_dir + '/.scrub/raw_results/' + tool + '*.scrub')[0]
                    assert open(raw_results_file).read().count('') > 0
                    if 'compiler' in raw_results_file:
                        assert open(helpers.test_tmp_dir + '/.scrub/compiler.scrub').read().count('') > 0
                    else:
                        assert open(helpers.test_tmp_dir + '/.scrub/' + tool + '.scrub').read().count('') > 0

        # Verify uploads
        if '--targets' in flags and 'scrub_gui' in flags:
            # Make sure SCRUB GUI distribution occurred
            assert os.path.exists(helpers.test_tmp_dir + '/src/.scrub')
            assert os.path.exists(helpers.test_tmp_dir + '/testcasesupport/.scrub')

        else:
            # Make sure the Collaborator log file exists and is error free
            collaborator_log_file = glob.glob(helpers.test_tmp_dir + '/.scrub/log_files/collaborator*.log')[0]
            assert open(collaborator_log_file).read().count('') > 0
            assert open(collaborator_log_file).read().count(' ERROR   ') == 0
            assert open(collaborator_log_file).read().count('CommandExecutionError') == 0

            # Make sure SCRUB GUI distribution occurred
            assert os.path.exists(helpers.test_tmp_dir + '/src/.scrub')
            assert os.path.exists(helpers.test_tmp_dir + '/testcasesupport/.scrub')


    finally:
        # Navigate to the start directory
        os.chdir(start_dir)

        # # Clean the test artifacts
        # if os.path.exists(tmp_test_dir):
        #     shutil.rmtree(tmp_test_dir)
