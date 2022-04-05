import os
import sys
import glob
import datetime
import shutil
from scrub.tools.parsers import translate_results


def parse_warnings(input_dir):
    # Initialize variables
    source_dir = os.path.dirname(input_dir)
    output_dir = os.path.normpath(input_dir + '/csv_output')

    # Make the output directory if it doesn't already exist
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.mkdir(output_dir)

    # Get a list of all the scrub files in the directory
    input_files = glob.glob(input_dir + '/*.scrub')

    # Create the output file path
    output_file = (output_dir + '/' + datetime.datetime.utcnow().strftime("%m-%d-%Y") + '.csv')

    # Write the results out to the csv file
    with open(output_file, 'w') as output_fh:
        # Write out the header data
        output_fh.write('ID,Query,Description,Priority,File,Line\n')

        # Iterate through every file
        for input_file in input_files:

            # Parse the SCRUB files
            scrub_results = translate_results.parse_scrub(input_file, source_dir)

            # Iterate through every result
            for result in scrub_results:
                output_fh.write('{},{},{},{},{},{}\n' .format(result.get('id'), result.get('query'),
                                                              ' '.join(result.get('description')).replace(',', ''),
                                                              result.get('priority'),
                                                              os.path.relpath(result.get('file'), source_dir),
                                                              result.get('line')))


if __name__ == '__main__':
    parse_warnings(sys.argv[1])
