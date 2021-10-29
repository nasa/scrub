import os
import re
import sys
import glob
import traceback
from scrub import scrub_cli
from tests import helpers


# Make the log directory if necessary
if not os.path.exists(helpers.log_dir):
    os.mkdir(helpers.log_dir)


def test_scrubme_cli(capsys):
    # Initialize variables
    test_log_file = helpers.log_dir + '/run_all-cli.log'

    # Navigate to the test directory
    start_dir = os.getcwd()
    os.chdir(helpers.c_test_dir)

    # Import the configuration data
    with open(helpers.c_conf_file, 'r') as input_fh:
        c_conf_data = input_fh.readlines()

    # Turn off all tools, except gcc
    conf_data = helpers.isolate_tool(c_conf_data, 'GCC_WARNINGS')

    # Initialize the test
    helpers.init_testcase(conf_data, helpers.c_test_dir, 'clean', helpers.log_dir)

    # Set the sys-argv values
    sys.argv = ['scrub', 'run', '--config', './scrub.cfg']

    # Run cli
    try:
        scrub_cli.main()

    except SystemExit:
        # Get the exit code
        sys_exit_text = traceback.format_exc()
        exit_code = int(list(filter(None, re.split('\n|:', sys_exit_text)))[-1])

        # There should be no system exit
        assert exit_code == 0

    finally:
        # Navigate to the start directory
        os.chdir(start_dir)

        # Write results to the output log file
        with open(test_log_file, 'w') as output_fh:
            system_output = capsys.readouterr()
            output_fh.write(system_output.err)
            output_fh.write(system_output.out)

        # Clean the codebase
        helpers.clean_codebase(helpers.c_test_dir, helpers.c_test_dir + '/src', 'make clean')


def test_diff_cli(capsys):
    # Initialize variables
    log_file = helpers.log_dir + '/diff_cli.log'

    # Perform the analysis
    baseline_source_dir = helpers.test_root + '/test_data/sample_data/diff_results/baseline_testcase'
    comparison_source_dir = helpers.test_root + '/test_data/sample_data/diff_results/comparison_testcase'
    baseline_scrub_root = baseline_source_dir + '/.scrub'
    comparison_scrub_root = comparison_source_dir + '/.scrub'

    # SEt sys.argv values
    sys.argv = ['scrub', 'diff', '--baseline-source', baseline_source_dir, '--baseline-scrub', baseline_scrub_root,
                '--comparison-source', comparison_source_dir, '--comparison-scrub', comparison_scrub_root]

    # Run cli
    scrub_cli.main()

    # Write out the stdout
    with open(log_file, 'w') as output_fh:
        output_fh.write('{}'.format(capsys.readouterr().out))
        output_fh.write('{}'.format(capsys.readouterr().err))

    # Check the output data
    comparison_files = glob.glob(comparison_scrub_root + '/*[!_diff].scrub')
    diff_output_files = glob.glob(comparison_scrub_root + '/*_diff.scrub')
    with open(log_file, 'r') as input_fh:
        log_file_data = input_fh.read()
    assert len(comparison_files) == len(diff_output_files)
    assert log_file_data.find('Error') == -1

    # Cleanup
    for diff_file in diff_output_files:
        os.remove(diff_file)


def test_conf_cli():
    # Remove the configuration file if it exists
    conf_file_out = './scrub.cfg'
    if os.path.exists(conf_file_out):
        os.remove(conf_file_out)

    # Set sys.argv values
    sys.argv = ['scrub', 'get-conf', '--output', conf_file_out]

    # Generate a configuration file
    scrub_cli.main()

    # Make the output file exists
    assert os.path.exists(conf_file_out)

    # Remove the conf file if it exists
    if os.path.exists(conf_file_out):
        os.remove(conf_file_out)
