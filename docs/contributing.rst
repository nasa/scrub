.. _Contributing:

============
Contributing
============

Contributions to SCRUB are always welcome and credit will always be given.

You can contribute in many ways:


Types of Contributions
----------------------

The JPL development team will periodically review GitHub issues for potential inclusion in future releases.

All proposed changes can be found by browsing the open issues: https://github.com/nasa/scrub/issues

Any user can address any GitHub issue. Simply search for issues that are marked as "open". Ideally, after a GitHub
issue has been completed, the regression test suite should be assessed to determine if a new testcase is required or
if an existing testcase can be modified to confirm the fix or feature that has been implemented.

Bugs
~~~~

If you are reporting a bug, please include:

* Your operating system name and version
* Any details about your local setup that might be helpful in troubleshooting
* Detailed steps to reproduce the bug

Feature Requests
~~~~~~~~~~~~~~~~

Feature requests should include the following information:

* Detailed information about the proposed new feature
* keep the focus of the feature request as narrow as possible
* Potential benefit to larger SCRUB community (if applicable)

Documentation
~~~~~~~~~~~~~

If something is unclear or missing from the SCRUB documentation, users may also modify or supplement the current
documentation. Documentation should focus on the end user perspective.

Get Started
-----------

Ready to contribute? Here's how to set up SCRUB for local development.

1. Fork the SCRUB repo on GitHub
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/scrub.git

3. Install your local copy into a virtualenv. Assuming you have virtualenvwrapper installed, this is how you set up
your fork for local development::

    $ mkvirtualenv scrub
    $ cd scrub
    $ python setup.py develop

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass pylint and the tests::

    $ pylint scrub tests
    $ python setup.py test or pytest

   To get pylint, just conda/pip install them into your conda env/virtualenv.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.


.. Note:: SCRUB development should following the PEP8 style guide as much as possible

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

* The pull request notes should include information on what issues were addressed
* The pull request should include updated tests specifically for the new functionality or the bug that was fixed that
  was added as well as a successful test report
* If the pull request adds functionality, the docs should be updated. Put your new functionality into a function with
  a docstring, and modify the documentation where applicable
* The pull request should work for Python 3.5, 3.6, 3.7 and 3.8, and for PyPy. Check and make sure that the tests
  pass for all supported Python versions.
* Users should perform a static code analysis scan of SCRUB and fix any critical items before committing

.. Note:: `SonarQube`_ and `lgtm`_ provide two free open source scanning capabilities for Python.

Pull Request Review Process
---------------------------

The internal development team will review the pull request in an effort to identify:

* Incomplete or insufficient test cases
* Static analysis findings that should be addressed
* Gaps in documentation
* Compliance with PEP8 style guide
* Applicability of updates to general SCRUB audience

The contributor(s) will have an opportunity to respond to any issues/concerns that are identified during pull request
review.

Regression Test Suite
---------------------

SCRUB contains a regression test suite that exercises all of the key functionality and integration of SCRUB. The test
cases and associated test data can be found underneath the ``tests`` directory. In order to fully execute the test
suite, a suitable test environment is required. This environment must contain valid installations for each of the static
analysis tools, including valid license files. The following table indicates the environmental requirements for each
test case in the regression test suite. If a test case is not explicitly mentioned, it does not have any external
dependencies. For more information on the supported tools see the :ref:`Usage` page.

+----------------------------------+--------------------------+
| Test Case                        | Requires Analysis Tools? |
+==================================+==========================+
| test_tool:test_tool              | Yes, all tools required  |
+----------------------------------+--------------------------+
| test_target:test_collaborator    | Only Collaborator        |
+----------------------------------+--------------------------+
| test_integration:test_mod_helper | Yes, all tools required  |
+----------------------------------+--------------------------+
| test_integration:test_scrubme    | Yes, all tools required  |
+----------------------------------+--------------------------+

Running Tests
~~~~~~~~~~~~~

The tests can be run by executing the command::

    make test

Alternatively, to examine the test case coverage of SCRUB execute the following command::

    make coverage

To run a subset of tests::

    python3 -m pytest -k <subset string> tests/test_<function>.py

Running the entire test suite requires SCRUB to be installed in a

Deploying
---------

A reminder for the maintainers on how to deploy.
Make sure all your changes are committed (including appropriate updates to documentation).
Then run::

$ bump2version patch # possible: major / minor / patch
$ git push
$ git push --tags

Adding New Analysis Tools
-------------------------
SCRUB is set up to automatically discover and incorporate new analysis tools during execution. There are three updates
that must be made in order for a new module to be included in SCRUB analysis.

1. A new section in the scrub.cfg to all SCRUB to read in the input values for the new analysis module
2. A new module in the tools directory that can read the scrub.cfg configuration file and make the applicable calls to
   the analysis tool
3. A new module for parsing raw tool results into the defined SCRUB output format*

.. Note:: Item 3 may be omitted if the new tool supports the SARIF output format. In this case the new tool may utilize
          the built in SARIF parsing utility ``scrub.utils.translate_results.parse_sarif``

Items 2 and 3 should be stored in the following location::

    <SCRUB Root>
      -> tools
        -> <tool>
          -> do_<tool>.py (item 2)
          -> get_<tool>_warnings.py (item 3)

Updates to scrub.cfg
~~~~~~~~~~~~~~~~~~~~

SCRUB uses the standard Python configuration file parsing module ConfigParser. New sections can be added to the SCRUB
configuration file by following the instructions provided in the `Python documentation`_.

Every variable that is required to complete execution should be stored in the scrub.cfg file. The logic for
determining if all required variables are present should be stored in the Analysis Module. SCRUB will pass your module
one variable: the scrub.cfg file. Your module should be able to read the values stored in this variable and then
determine if it is able to attempt execution.

Creation of New Analysis Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module should be the bulk of the development work to incorporate a new module. The main function of the module
should be titled "run_analysis" and should take exactly one argument: the path to scrub.cfg. This requirement,
combined with the requirements above means that SCRUB will attempt to run the following command when dynamically
adding a module::

        scrub.tools.<tool>.do_<tool>.run_analysis(<path to scrub.cfg>)

If this pattern is not followed, SCRUB will not be able to automatically incorporate your new analysis module.

In general the logic for the following major tasks should be included in this module in the following order.

* Read in and store all the values from the scrub.cfg configuration file and determine if execution can be attempted
* Make necessary calls to the analysis tool
* Parse the raw tool output and convert to the SCRUB file format
* Filter the raw SCRUB file based on filtering configuration options (discussed more in the following section)
* Check the log files and output files to ensure that execution completed successfully

Reading Values From the scrub.cfg File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In addition to the values needed for the new tool execution, your tool will likely need to read in and use the Source
Code Variables and Filtering Variables sections from the ``scrub.cfg`` configuration file.

Expected Outputs:

- All necessary values for execution have been stored locally
- A determination of whether or not the tool can be run

Logic for Running Analysis Tool
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

How this section is implemented is almost entirely up to your discretion. Make whatever calls are necessary to perform
your analysis.

Expected Outputs:

- A file (or set of files) containing raw analysis results from the new analysis tool

Parsing the Raw Output Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This should actually be a separate module, but it should be called from within this module. More on the definition of
this module can be found below in Creation of New Parsing Module section.

Expected Outputs:

- A SCRUB formatted file stored at ``<SOURCE_DIR>.scrub/raw_results/<tool>_raw.scrub``

Filtering the Raw SCRUB-formatted Output File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
There is a module that can be used specifically for filtering raw SCRUB-formatted output files: ``utils/filter_results``
This module should be called directly from the new main analysis module.

Expected Outputs:

- A filtered SCRUB formatted file stored at ``<SOURCE_DIR>/.scrub/<tool>.scrub``

Checking the Log Files and Execution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The final step is to examine the log files and output files to ensure that analysis completed successfully. Generally,
it is enough to check that the SCRUB formatted files are not empty and there are no warnings/errors in the analysis
tool's log file.

Expected Outputs:

The tool should return an exit code of the following format

* 0: Tool execution completed successfully
* 1: Tool execution was attempted, but did not complete successfully
* 2: Tool execution was not attempted
* 100: An unknown Python error occurred during tool execution

Creation of New Parsing Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The parsing module ``scrub.tools.<tool>.get<tool>_warnings`` is responsible converting warnings from the raw format outputted
by the tool into the SCRUB format and storing it in the appropriate location
(``SOURCE_DIR/.scrub/raw_results/<tool>.scrub``).

The contents of this file must match the expected SCRUB format or else filtering, moving warnings, and exporting
warnings to various output targets will not work properly. More information about the SCRUB format can be found on the
:ref:`Scrub Output` page.


.. _`Python documentation`: https://docs.python.org/3.6/library/configparser.html
.. _`lgtm`: https://lgtm.com
.. _`SonarQube`: https://www.sonarqube.org/
