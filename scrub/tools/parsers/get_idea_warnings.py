import pathlib
import logging
from scrub.tools.parsers import translate_results


def parse_warnings(analysis_dir, tool_config_data, raw_input_file=None, parsed_output_file=None):
    """This function handles parsing of raw IntelliJ IDEA data.

    Inputs:
        - analysis_dir: Absolute path to the raw IntelliJ IDEA output file directory [string]
        - tool_config_data: Dictionary of scrub configuration data [dict]
        - raw_input_file: Absolute path to the raw input file [string] [optional]
        - parsed_output_file: Absolute path to the raw output file [string] [optional]
    """

    # Initialize variables
    source_dir = tool_config_data.get('source_dir')

    # Set the input file
    if raw_input_file is None:
        raw_input_file = analysis_dir.joinpath('idea.sarif')

    # Set the output file
    if parsed_output_file is None:
        parsed_output_file = tool_config_data.get('raw_results_dir').joinpath('idea_raw.scrub')

    # Print a status message
    logging.info('\t>> Executing command: get_idea_warnings.parse_warnings(%s, %s)', analysis_dir,
                 parsed_output_file)
    logging.info('\t>> From directory: %s', str(pathlib.Path().absolute()))

    # Parse the SARIF file
    raw_warnings = translate_results.parse_sarif(raw_input_file, source_dir)

    # Create the SCRUB output file
    translate_results.create_scrub_output_file(raw_warnings, parsed_output_file)

