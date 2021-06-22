import os
import glob
from tests import helpers


def test_conf_generation():
    # Import the module
    from scrub.utils import scrub_utilities

    # Remove the configuration file if it exists
    conf_file_out = './scrub.cfg'
    if os.path.exists(conf_file_out):
        os.remove(conf_file_out)

    # Generate a configuration file
    scrub_utilities.create_conf_file(conf_file_out)

    # Make the output file exists
    assert os.path.exists(conf_file_out)

    # Remove the conf file if it exists
    if os.path.exists(conf_file_out):
        os.remove(conf_file_out)


def test_diff_results(capsys):
    # Import the module
    from scrub.utils import diff_results

    # Initialize variables
    log_file = helpers.log_dir + '/util-diff_results.log'

    # Perform the analysis
    baseline_source_dir = helpers.test_root + '/test_data/sample_data/diff_results/baseline_testcase'
    comparison_source_dir = helpers.test_root + '/test_data/sample_data/diff_results/comparison_testcase'
    baseline_scrub_root = baseline_source_dir + '/.scrub'
    comparison_scrub_root = comparison_source_dir + '/.scrub'
    diff_results.diff(baseline_source_dir, baseline_scrub_root, comparison_source_dir, comparison_scrub_root)

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
