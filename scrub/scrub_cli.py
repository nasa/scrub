import sys

from scrub import scrubme
from scrub.utils import diff_results
from scrub.utils import scrub_utilities


help_message = ('run\n' +
                scrubme.main.__doc__ + '\n\n'
                'diff\n' +
                diff_results.diff.__doc__ + '\n\n'
                'get-conf\n' +
                scrub_utilities.create_conf_file.__doc__ + '\n')


def main():
    """Console script for SCRUB."""

    if len(sys.argv) <= 1:
        print(help_message)
    else:
        if 'run' in sys.argv or 'run-all' in sys.argv:
            # Run analysis
            scrubme.parse_arguments()

        elif 'run-tool' in sys.argv:
            # Get the tool name
            tool = sys.argv[sys.argv.index('--module') + 1].split('_')[-1]
            insert_index = sys.argv.index('--module')

            # Update the arguments
            sys.argv[1] = 'run'
            sys.argv[insert_index] = '--tool'
            sys.argv[insert_index + 1] = tool

            # Run analysis
            scrubme.parse_arguments()

        elif 'diff' in sys.argv:
            # Run analysis
            diff_results.parse_arguments()

        elif 'get-conf' in sys.argv:
            # Run analysis
            scrub_utilities.create_conf_file()

        else:
            print(help_message)

    return 0


if __name__ == "__main__":
    sys.exit(main())
