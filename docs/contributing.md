# Contributing

Contributions to SCRUB are always welcome and credit will always be given. Guidelines for contributing are provided below.


## Types of Contributions

The JPL development team will periodically review GitHub issues for potential inclusion in future releases.

All proposed changes can be found by browsing the [open issues](https://github.com/nasa/scrub/issues).

Any user can address any GitHub issue. Simply search for issues that are marked as "open". Ideally, after a GitHub issue has been completed, the regression test suite should be assessed to determine if a new testcase is required or if an existing testcase can be modified to confirm the fix or feature that has been implemented.

### Bugs

If you are reporting a bug, please include:

* Your operating system name and version
* Any details about your local setup that might be helpful in troubleshooting
* Detailed steps to reproduce the bug


### Feature Requests

Feature requests should include the following information:

* Detailed information about the proposed new feature
* keep the focus of the feature request as narrow as possible
* Potential benefit to larger SCRUB community (if applicable)


### Documentation

If something is unclear or missing from the SCRUB documentation, users may also modify or supplement the current documentation. Documentation should focus on the end user perspective.


## Get Started

Ready to contribute? Here's how to set up SCRUB for local development.

1. Fork the SCRUB repo on GitHub
2. Clone your fork locally:  

    `git clone git@github.com:nasa/scrub.git`

3. Install your local copy for development:

    `cd scrub`  
    `python3 setup.py develop`

4. Create a branch for local development:

    `git checkout -b <branch name>`

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass pylint and the tests::

    `pylint scrub tests`  
    `python3 setup.py test or pytest`

6. Commit your changes and push your branch to GitHub::

    `git add .`  
    `git commit -m "Your detailed description of your changes."`  
    `git push origin <branch name>`

7. Submit a pull request through the GitHub website.


**Note**: SCRUB development should following the PEP8 style guide as much as possible


## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

* The pull request notes should include information on what issues were addressed
* The pull request should include updated tests specifically for the new functionality or the bug that was fixed that
  was added as well as a successful test report
* If the pull request adds functionality, the docs should be updated. Put your new functionality into a function with
  a docstring, and modify the documentation where applicable
* The pull request should work for Python 3.5, 3.6, 3.7 and 3.8, and for PyPy. Check and make sure that the tests
  pass for all supported Python versions.
* Users should perform a static code analysis scan of SCRUB and fix any critical items before committing

**Note**: [SonarQube](https://www.sonarqube.org/) and [lgtm](https://lgtm.com) provide two free open source scanning capabilities for Python.


## Pull Request Review Process

The internal development team will review the pull request in an effort to identify:

* Incomplete or insufficient test cases
* Static analysis findings that should be addressed
* Gaps in documentation
* Compliance with PEP8 style guide
* Applicability of updates to general SCRUB audience

The contributor(s) will have an opportunity to respond to any issues/concerns that are identified during pull request review.


## Regression Test Suite

SCRUB contains a regression test suite that exercises all of the key functionality and integration of SCRUB. The test
cases and associated test data can be found underneath the `tests` directory. In order to fully execute the test
suite, a suitable test environment is required. This environment must contain valid installations for each of the static
analysis tools, including valid license files. The following table indicates the environmental requirements for each
test case in the regression test suite. If a test case is not explicitly mentioned, it does not have any external
dependencies. For more information on the supported tools see the :ref:`Usage` page.

| Test Case                        | Requires Analysis Tools? |
| -------------------------------- | ------------------------ |
| test_tool:test_tool              | Yes, all tools required  |
| test_target:test_collaborator    | Only Collaborator        |
| test_integration:test_mod_helper | Yes, all tools required  |
| test_integration:test_scrubme    | Yes, all tools required  |


### Running Tests

The tests can be run by executing the command:

    make test

Alternatively, to examine the test case coverage of SCRUB execute the following command:

    make coverage

To run a subset of tests:

    python3 -m pytest -k <subset string> tests/test_<function>.py

Running the entire test suite requires SCRUB to be installed in a


## Deploying

A reminder for the maintainers on how to deploy.
Make sure all your changes are committed (including appropriate updates to documentation).
Then run:

    bump2version patch # possible: major / minor / patch
    git push
    git push --tags


## Adding New Analysis Tools

SCRUB is set up to automatically discover and incorporate new analysis tools during execution. There are three updates that must be made in order for a new module to be included in SCRUB analysis. Filtering is automatically performed by SCRUB and does not need to be addressed in the analysis template.

1. A new section in the scrub.cfg to all SCRUB to read in the input values for the new analysis module
2. A new analysis template in the tools directory, for each applicable language
3. A new module for parsing raw tool results into the defined SCRUB output format*

**Note**: Item 3 may be omitted if the new tool supports the SARIF output format. In this case the new tool may utilize the built in SARIF parsing utility `scrub.utils.translate_results.parse_sarif`

The items mentioned above should be stored in the following locations::

    <SCRUB Root>
      scrub.cfg (item 1)
      -> tools
        -> templates
          -> <language>
            -> <tool>.template (item 2)
        -> parsers
          -> get_<tool>_warnings.py (item 3)


### Updates to scrub.cfg

SCRUB uses the standard Python configuration file parsing module ConfigParser. New sections can be added to the SCRUB configuration file by following the instructions provided in the [Python documentation](https://docs.python.org/3.6/library/configparser.html).

Every variable that is required to complete execution should be stored in the `scrub.cfg` file. SCRUB will read the configuration file and replace relevant values in the analysis template file. If a required variable is missing, SCRUB will generate an error message when attempting analysis.


### Creation of New Analysis Template

Analysis templates attempt to minimize the work required to integrate new analysis tools into SCRUB. Once developers have determined how to run a tool from the command line, they can take these instructions and create an analysis template file using the same shell commands and dynamic substitutions from variables within the `scrub.cfg` configuration file.

Configuration file variables within the analysis template should match the name found within the configuration file. For example, the configuration file variable `GCC_BUILD_CMD` can be referenced using `${{GCC_BUILD_CMD}}` within the analysis template. If the value cannot be found in the configuration file, an error will occur during execution.

In addition to perform the core tool analysis, the template should also handle parsing the native tool output into a SCRUB formatted output file that resides within the `.scrub/raw_results` directory.

An example template, with comments, is provided below:

    #!/bin/bash -x

    # Change to the build directory
    cd ${{GCC_BUILD_DIR}}

    # Clean the build
    ${{GCC_CLEAN_CMD}}

    # Build and capture the output in the GCC analysis directory
    ${{GCC_BUILD_CMD}} > ${{TOOL_ANALYSIS_DIR}}/gcc_build.log 2>&1

    # Parse the log file and send the output to .scrub/raw_results/gcc_raw.scrub
    python3 -m scrub.tools.parsers.get_gcc_warnings ${{TOOL_ANALYSIS_DIR}}/gcc_build.log ${{RAW_RESULTS_DIR}}/gcc_raw.scrub


### Creation of New Parsing Module

The parsing module is responsible converting warnings from the raw format outputted by the tool into the SCRUB format and storing it in the appropriate location (``.scrub/raw_results/<tool>_raw.scrub``).

The contents of this file must match the expected SCRUB format or else filtering, moving warnings, and exporting warnings to various output targets will not work properly. More information about the SCRUB format can be found on the
[SCRUB Output](output.md) page.


### Error Handling

After parsing, each analysis script is run by `scrub.utils.scrub_utilities.execute_command`. If any non-zero exit code is generated, the `execute_command` function with raise a CommandExecutionError. Users can debug issues by examining the log file found at `.scrub/log_files/<tool>.log`. Unless a non-zero execution code is encountered, SCRUB will assume that the analysis was successfully completed.

