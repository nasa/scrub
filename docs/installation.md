---
layout: default
title: Installation
nav_order: 2
---

# Installation
## Stable release

To install SCRUB, run this command in your terminal:

    pip install nasa-scrub
    
To install SCRUB only for the current user, user the `--user` flag during installation:

    pip install --user nasa-scrub

To upgrade your existing version to the latest version of SCRUB, run this command in your terminal:

    pip install --upgrade nasa-scrub

This is the preferred method to install scrub, as it will always install the most recent stable release.

If you don't have [pip](https://pip.pypa.io) installed, this [Python installation guide](http://docs.python-guide.org/en/latest/starting/installation/) can guide you through the process.

## From sources

The sources for scrub can be downloaded from the [Github repo](https://github.com/nasa/scrub).

You can either clone the public repository:

    git clone https://github.com/nasa/scrub.git

Or download the [tarball](https://github.com/nasa/scrub/archive/master.tar.gz):

    curl -OJL https://github.com/nasa/scrub/archive/tarball/master

Once you have a copy of the source, you can install it with:

    python3 setup.py install

## GitHub Actions
SCRUB can also be integrated into the CodeQL GitHub Action to produce SCRUB formatted output files. Ading the following code snippet to the end of the baseline CodeQL Github Action allows users to generate SCRUB formatted output files.

    - name: Post-Process Output
      run: |
        python3 -m pip install nasa-scrub

        results_dir=`realpath ${{ github.workspace }}/../results`
        sarif_files=`find $results_dir -name '*.sarif'`

        for sarif_file in $sarif_files
        do
          output_file="$results_dir/$(basename $sarif_file .sarif).scrub"

          python3 -m scrub.tools.parsers.translate_results $sarif_file $output_file ${{ github.workspace }} scrub
        done

        python3 -m scrub.tools.parsers.csv_parser $results_dir

        echo "RESULTS_DIR=$results_dir" >> $GITHUB_ENV
        
      
    - name: Upload CodeQL Artifacts
      uses: actions/upload-artifact@v3
      with:
        name: codeql-artifacts
        path: ${{ env.RESULTS_DIR }}

The first section of this code (`Post-Process Output`) converts all of the SARIF output files using the `scrub.tools.parsers.translate_results` module. After the SCRUB output has been generated, a secondary `.csv` output file type is generated using the `scrub.tools.parsers.csv_parser` module.

The second section of this code (`Upload CodeQL Artifacts`) makes the output of this conversion available as a downloadable package. This zip file contains the raw SARIF output file, the parsed SCRUB output file, and the CSV formatted output file.
