import os
import sys

from scrub import scrubme
from scrub import module_helper
from scrub.utils import diff_results
from scrub.utils import scrub_utilities


help_message = ('run-all\n' +
                scrubme.main.__doc__ + '\n\n'
                'run-tool\n' +
                module_helper.main.__doc__ + '\n\n'
                'diff\n' +
                diff_results.diff.__doc__ + '\n\n'
                'get-conf\n' +
                scrub_utilities.create_conf_file.__doc__ + '\n')


def main():
    """Console script for SCRUB."""

    if len(sys.argv) <= 1:
        print(help_message)
    else:
        if 'run-all' in sys.argv:
            # Run analysis
            scrubme.parse_arguments()

        elif 'run-tool' in sys.argv:
            # Run analysis
            module_helper.parse_arguments()

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
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    sys.exit(main())
