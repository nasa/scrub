import sys
import datetime
import shutil
import pathlib
from scrub.tools.parsers import translate_results


def parse_warnings(input_dir, output_format='legacy'):
    # Initialize variables
    source_dir = pathlib.Path(input_dir)
    output_dir = source_dir.joinpath('csv_output')
    timestamp = datetime.datetime.utcnow()

    # Make the output directory if it doesn't already exist
    if output_dir.exists():
        shutil.rmtree(str(output_dir))
    output_dir.mkdir()

    # Get a list of all the scrub files in the directory
    input_files = input_dir.glob('*.scrub')

    # Create the output file path
    output_file = output_dir.joinpath(timestamp.strftime("%m-%d-%Y") + '.csv')

    # Write the results out to the csv file
    with open(output_file, 'w') as output_fh:
        if output_format == 'generic':
            # Write out the header data
            output_fh.write('ID,Query,Description,Priority,File,Line\n')

            # Iterate through every file
            for input_file in input_files:

                # Parse the SCRUB files
                scrub_results = translate_results.parse_scrub(input_file, source_dir)

                # Iterate through every result
                for result in scrub_results:
                    output_fh.write('{},{},{},{},{},{}\n'.format(result.get('id'), result.get('query'),
                                                                 ' '.join(result.get('description')).replace(',', ''),
                                                                 result.get('priority'),
                                                                 result.get('file').relative_to(source_dir),
                                                                 result.get('line')))

        else:
            # Iterate through every file
            for input_file in input_files:

                # Parse the SCRUB files
                scrub_results = translate_results.parse_scrub(input_file, source_dir)

                # Iterate through every result
                for result in scrub_results:
                    description_text = ' '.join(result.get('description')).replace(',', '').replace('\t', '').strip()
                    output_fh.write('{},{},{},{},{},{}/{},{},{},{},{}\n'.format(result.get('query'), description_text,
                                                                             result.get('priority'), description_text,
                                                                             result.get('file').relative_to(source_dir),
                                                                             timestamp.strftime("%Y-%B-%d--%H-%M-%S"),
                                                                             result.get('file').relative_to(source_dir),
                                                                             result.get('line'), result.get('line'), 0,
                                                                             0))


if __name__ == '__main__':
    if len(sys.argv) == 2:
        parse_warnings(pathlib.Path(sys.argv[1]).resolve())
    else:
        parse_warnings(pathlib.Path(sys.argv[1]).resolve(), sys.argv[2])
