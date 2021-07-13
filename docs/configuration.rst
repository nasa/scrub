.. _Detailed Configuration:

======================
Detailed Configuration
======================

The information below provides a detailed description of each ``scrub.cfg`` value. A blank ``scrub.cfg`` file containing
all of these values can be found here: :download:`scrub.cfg <../scrub/scrub.cfg>`

Each table below represents a portion of the complete ``scrub.cfg`` file.

.. Note:: The use of environment variables is supported in ``scrub.cfg`` is supported. Environment variables will be
          resolved when the configuration file is read.

.. Note:: All variables ending with ``_PATH`` will automatically be converted in absolute paths.

Source Code Attributes
######################

+-------------------+--------+-----------+-----------------------------------------------------------------------------+
| Variable Name     | Format | Required? | Description                                                                 |
+===================+========+===========+=============================================================================+
| SOURCE_DIR        | String | Yes       | Define the location of the source code. This is where the compilation       |
|                   |        |           | command will execute                                                        |
+-------------------+--------+-----------+-----------------------------------------------------------------------------+
| SOURCE_LANG       | String | Yes       | Define the language of the source code. Valid options are 'c' and 'j' for   |
|                   |        |           | C/C++ and Java respectively                                                 |
+-------------------+--------+-----------+-----------------------------------------------------------------------------+
| SCRUB_WORKING_DIR | String | Optional  | Define the location of the SCRUB output files. SCRUB execution will create  |
|                   |        |           | the .scrub working directory here                                           |
+-------------------+--------+-----------+-----------------------------------------------------------------------------+

Tool Variables
##############
GCC Compiler Variables
**********************
+---------------+------------+-----------+-----------------------------------------------------------------------------+
| Variable Name | Format     | Required? | Description                                                                 |
+===============+============+===========+=============================================================================+
| GCC_WARNINGS  | True/False | Yes       | Should compiler analysis be performed using the gcc compiler?               |
+---------------+------------+-----------+-----------------------------------------------------------------------------+
| GCC_BUILD_DIR | String     | Optional  | Relative (to SOURCE_DIR) path to the build directory for the source code    |
+---------------+------------+-----------+-----------------------------------------------------------------------------+
| GCC_BUILD_CMD | String     | Yes       | Build command used by the GCC compiler                                      |
+---------------+------------+-----------+-----------------------------------------------------------------------------+
| GCC_CLEAN_CMD | String     | Yes       | Clean command used by the GCC compiler                                      |
+---------------+------------+-----------+-----------------------------------------------------------------------------+

JAVAC Compiler Variables
************************
+-----------------+------------+-----------+---------------------------------------------------------------------------+
| Variable Name   | Format     | Required? | Description                                                               |
+=================+============+===========+===========================================================================+
| JAVAC_WARNINGS  | True/False | Yes       | Should compiler analysis be performed using the javac compiler?           |
+-----------------+------------+-----------+---------------------------------------------------------------------------+
| JAVAC_BUILD_DIR | String     | Optional  | Relative (to SOURCE_DIR) path to the build directory for the source code  |
+-----------------+------------+-----------+---------------------------------------------------------------------------+
| JAVAC_BUILD_CMD | String     | Yes       | Build command used by the JAVAC compiler                                  |
+-----------------+------------+-----------+---------------------------------------------------------------------------+
| JAVAC_CLEAN_CMD | String     | Yes       | Clean command used by the JAVAC compiler                                  |
+-----------------+------------+-----------+---------------------------------------------------------------------------+

GBUILD Compiler Variables
*************************
+------------------+------------+-----------+--------------------------------------------------------------------------+
| Variable Name    | Format     | Required? | Description                                                              |
+==================+============+===========+==========================================================================+
| GBUILD_WARNINGS  | True/False | Yes       | Should compiler analysis be performed using the gbuild compiler?         |
+------------------+------------+-----------+--------------------------------------------------------------------------+
| GBUILD_BUILD_DIR | String     | Optional  | Relative (to SOURCE_DIR) path to the build directory for the source code |
+------------------+------------+-----------+--------------------------------------------------------------------------+
| GBUILD_BUILD_CMD | String     | Yes       | Build command used by the GBUILD compiler                                |
+------------------+------------+-----------+--------------------------------------------------------------------------+
| GBUILD_CLEAN_CMD | String     | Yes       | Clean command used by the GBUILD compiler                                |
+------------------+------------+-----------+--------------------------------------------------------------------------+

.. Note:: DoubleCheck analysis is included under gbuild compiler analysis. DoubleCheck must be enabled external to
          SCRUB.

Semmle Variables
****************
+------------------------------+------------+-----------+--------------------------------------------------------------+
| Variable Name                | Format     | Required? | Description                                                  |
+==============================+============+===========+==============================================================+
| SEMMLE_WARNINGS              | True/False | Yes       | Should Semmle analysis be performed?                         |
+------------------------------+------------+-----------+--------------------------------------------------------------+
| SEMMLE_PATH                  | String     | Optional  | Absolute path to the directory of the Semmle installation    |
|                              |            |           | containing setup.sh                                          |
|                              |            |           |                                                              |
|                              |            |           |   Default value: None                                        |
+------------------------------+------------+-----------+--------------------------------------------------------------+
| SEMMLE_BUILD_DIR             | String     | Optional  | Relative (to SOURCE_DIR) path to the build directory for the |
|                              |            |           | source code                                                  |
|                              |            |           |                                                              |
|                              |            |           |   Default value: SOURCE_DIR                                  |
+------------------------------+------------+-----------+--------------------------------------------------------------+
| SEMMLE_BUILD_CMD             | String     | Yes       | Command to build the source code for Semmle analysis         |
+------------------------------+------------+-----------+--------------------------------------------------------------+
| SEMMLE_CLEAN_CMD             | String     | Yes       | Command to clean the source code for Semmle analysis         |
+------------------------------+------------+-----------+--------------------------------------------------------------+
| SEMMLE_BASELINE_ANALYSIS     | True/False | Yes       | Should baseline Semmle analysis be performed?                |
+------------------------------+------------+-----------+--------------------------------------------------------------+
| SEMMLE_P10_ANALYSIS          | True/False | Yes       | Should Semmle P10 analysis be performed?                     |
+------------------------------+------------+-----------+--------------------------------------------------------------+
| SEMMLE_SUITE_FILE            | String     | Optional  | Suite file that can override the default suite file for      |
|                              |            |           | baseline Semmle analysis                                     |
|                              |            |           |                                                              |
|                              |            |           |   Default value: None                                        |
+------------------------------+------------+-----------+--------------------------------------------------------------+
| SEMMLE_TEMPLATE_PATH         | String     | Optional  | Template file that can be used to initialize Semmle projects |
|                              |            |           |                                                              |
|                              |            |           |   Default value: None                                        |
+------------------------------+------------+-----------+--------------------------------------------------------------+
| SEMMLE_ADDSNAPSHOT_FLAGS     | String     | Optional  | Customized command flags to be passed into the               |
|                              |            |           | 'odasa addSnapshot' command                                  |
|                              |            |           |                                                              |
|                              |            |           |   Default value: None                                        |
+------------------------------+------------+-----------+--------------------------------------------------------------+
| SEMMLE_BUILDSNAPSHOT_FLAGS   | String     | Optional  | Customized command flags to be passed into the               |
|                              |            |           | 'odasa buildSnapshot' command                                |
|                              |            |           |                                                              |
|                              |            |           |   Default value: None                                        |
+------------------------------+------------+-----------+--------------------------------------------------------------+
| SEMMLE_ANALYZESNAPSHOT_FLAGS | String     | Optional  | Customized command flags to be passed into the               |
|                              |            |           | 'odasa analyzeSnapshot' command                              |
|                              |            |           |                                                              |
|                              |            |           |   Default value: None                                        |
+------------------------------+------------+-----------+--------------------------------------------------------------+


CodeQL Variables
****************
+------------------------------+------------+-----------+--------------------------------------------------------------+
| Variable Name                | Format     | Required? | Description                                                  |
+==============================+============+===========+==============================================================+
| CODEQL_WARNINGS              | True/False | Yes       | Should CodeQL analysis be performed?                         |
+------------------------------+------------+-----------+--------------------------------------------------------------+
| CODEQL_PATH                  | String     | Optional  | Absolute path to the directory of the CodeQL installation    |
|                              |            |           | containing codeql                                            |
|                              |            |           |                                                              |
|                              |            |           |   Default value: None                                        |
+------------------------------+------------+-----------+--------------------------------------------------------------+
| CODEQL_QUERY_PATH            | String     | Yes       | Absolute path to the CodeQL query files, pulled from CodeQL  |
|                              |            |           | repository                                                   |
+------------------------------+------------+-----------+--------------------------------------------------------------+
| CODEQL_BUILD_DIR             | String     | Optional  | Relative (to SOURCE_DIR) path to the build directory for the |
|                              |            |           | source code                                                  |
|                              |            |           |                                                              |
|                              |            |           |   Default value: SOURCE_DIR                                  |
+------------------------------+------------+-----------+--------------------------------------------------------------+
| CODEQL_BUILD_CMD             | String     | Yes       | Command to build the source code for CodeQL analysis         |
+------------------------------+------------+-----------+--------------------------------------------------------------+
| CODEQL_CLEAN_CMD             | String     | Yes       | Command to clean the source code for CodeQL analysis         |
+------------------------------+------------+-----------+--------------------------------------------------------------+
| CODEQL_BASELINE_ANALYSIS     | True/False | Yes       | Should baseline CodeQL analysis be performed?                |
+------------------------------+------------+-----------+--------------------------------------------------------------+
| CODEQL_P10_ANALYSIS          | True/False | Yes       | Should CodeQL P10 analysis be performed?                     |
+------------------------------+------------+-----------+--------------------------------------------------------------+
| CODEQL_DATABASECREATE_FLAGS  | String     | Optional  | Customized command flags to be passed into the               |
|                              |            |           | 'codeql database create' command                             |
|                              |            |           |                                                              |
|                              |            |           |   Default value: None                                        |
+------------------------------+------------+-----------+--------------------------------------------------------------+
| CODEQL_DATEBASEANALYZE_FLAGS | String     | Optional  | Customized command flags to be passed into the               |
|                              |            |           | 'codeql database analyze' command                            |
|                              |            |           |                                                              |
|                              |            |           |   Default value: None                                        |
+------------------------------+------------+-----------+--------------------------------------------------------------+


Coverity Variables
******************
+--------------------------------+------------+-----------+------------------------------------------------------------+
| Variable Name                  | Format     | Required? | Description                                                |
+================================+============+===========+============================================================+
| COVERITY_WARNINGS              | True/False | Yes       | Should Coverity analysis be performed?                     |
+--------------------------------+------------+-----------+------------------------------------------------------------+
| COVERITY_PATH                  | String     | Optional  | Absolute path to the bin directory of the Coverity         |
|                                |            |           | installation                                               |
|                                |            |           |                                                            |
|                                |            |           |   Default value: None                                      |
+--------------------------------+------------+-----------+------------------------------------------------------------+
| COVERITY_BUILD_DIR             | String     | Optional  | Relative (to SOURCE_DIR) path to the build directory for   |
|                                |            |           | the source code                                            |
|                                |            |           |                                                            |
|                                |            |           |   Default value: SOURCE_DIR                                |
+--------------------------------+------------+-----------+------------------------------------------------------------+
| COVERITY_BUILD_CMD             | String     | Yes       | Command to build the source code for Coverity analysis     |
+--------------------------------+------------+-----------+------------------------------------------------------------+
| COVERITY_CLEAN_CMD             | String     | Yes       | Command to clean the source code for Coverity analysis     |
+--------------------------------+------------+-----------+------------------------------------------------------------+
| COVERITY_COVBUILD_FLAGS        | String     | Optional  | Customized command flags to be passed into the 'cov-build' |
|                                |            |           | command                                                    |
|                                |            |           |                                                            |
|                                |            |           |   Default value: None                                      |
+--------------------------------+------------+-----------+------------------------------------------------------------+
| COVERITY_COVANALYZE_FLAGS      | String     | Optional  | Customized command flags to be passed into the             |
|                                |            |           | 'cov-analyze' command                                      |
|                                |            |           |                                                            |
|                                |            |           |   Default value: None                                      |
+--------------------------------+------------+-----------+------------------------------------------------------------+
| COVERITY_COVFORMATERRORS_FLAGS | String     | Optional  | Customized command flags to be passed into the             |
|                                |            |           | 'cov-format-errors' command                                |
|                                |            |           |                                                            |
|                                |            |           |   Default value: None                                      |
+--------------------------------+------------+-----------+------------------------------------------------------------+


CodeSonar Variables
*******************
+-----------------------------+------------+-----------+---------------------------------------------------------------+
| Variable Name               | Format     | Required? | Description                                                   |
+=============================+============+===========+===============================================================+
| CODESONAR_WARNINGS          | True/False | Yes       | Should CodeSonar analysis be performed?                       |
+-----------------------------+------------+-----------+---------------------------------------------------------------+
| CODESONAR_PATH              | String     | Optional  | Absolute path to the bin directory of the CodeSonar           |
|                             |            |           | installation                                                  |
|                             |            |           |                                                               |
|                             |            |           |   Default value: None                                         |
+-----------------------------+------------+-----------+---------------------------------------------------------------+
| CODESONAR_HUB               | String     | Yes       | CodeSonar Hub domain and port in the form of                  |
|                             |            |           | '<hub location>:<port>'                                       |
+-----------------------------+------------+-----------+---------------------------------------------------------------+
| CODESONAR_CERT              | String     | Yes       | Absolute path of the Hub certificate                          |
+-----------------------------+------------+-----------+---------------------------------------------------------------+
| CODESONAR_KEY               | String     | Yes       | Absolute path of the user's private key                       |
+-----------------------------+------------+-----------+---------------------------------------------------------------+
| CODESONAR_PROJ_NAME         | String     | Yes       | Project name provided by the Hub administrator upon project   |
|                             |            |           | creation                                                      |
+-----------------------------+------------+-----------+---------------------------------------------------------------+
| CODESONAR_RESULTS_TEMPLATE  | Integer    | Optional  | CodeSonar report template to use when retrieving findings     |
|                             |            |           | from the Hub                                                  |
|                             |            |           |                                                               |
|                             |            |           |   Default value: 2                                            |
+-----------------------------+------------+-----------+---------------------------------------------------------------+
| CODESONAR_BUILD_DIR         | String     | Optional  | Relative (to SOURCE_DIR) path to the build directory for the  |
|                             |            |           | source code                                                   |
|                             |            |           |                                                               |
|                             |            |           |   Default value: SOURCE_DIR                                   |
+-----------------------------+------------+-----------+---------------------------------------------------------------+
| CODESONAR_BUILD_CMD         | String     | Yes       | Command to build the source code for CodeSonar analysis       |
+-----------------------------+------------+-----------+---------------------------------------------------------------+
| CODESONAR_CLEAN_CMD         | String     | Yes       | Command to clean the source code for CodeSonar analysis       |
+-----------------------------+------------+-----------+---------------------------------------------------------------+
| CODESONAR_BASELINE_ANALYSIS | True/False | Yes       | Should baseline CodeSonar analysis be performed?              |
+-----------------------------+------------+-----------+---------------------------------------------------------------+
| CODESONAR_P10_ANALYSIS      | True/False | Yes       | Should CodeSonar P10 analysis be performed?                   |
+-----------------------------+------------+-----------+---------------------------------------------------------------+
| CODESONAR_ANALYZE_FLAGS     | String     | Optional  | Customized command flags to be passed into the                |
|                             |            |           | 'codesonar analyze' command                                   |
|                             |            |           |                                                               |
|                             |            |           |   Default value: None                                         |
+-----------------------------+------------+-----------+---------------------------------------------------------------+
| CODESONAR_GET_FLAGS         | String     | Optional  | Customized command flags to be passed into the                |
|                             |            |           | 'codesonar get' command                                       |
|                             |            |           |                                                               |
|                             |            |           |   Default value: None                                         |
+-----------------------------+------------+-----------+---------------------------------------------------------------+


Klocwork Analysis Variables
***************************
+-------------------------------+------------+-----------+-------------------------------------------------------------+
| Variable Name                 | Format     | Required? | Description                                                 |
+===============================+============+===========+=============================================================+
| KLOCWORK_WARNINGS             | True/False | Yes       | Should Klocwork analysis be performed?                      |
+-------------------------------+------------+-----------+-------------------------------------------------------------+
| KLOCWORK_PATH                 | String     | Optional  | Absolute path to the Klocwork installation                  |
|                               |            |           |                                                             |
|                               |            |           |   Default value: None                                       |
+-------------------------------+------------+-----------+-------------------------------------------------------------+
| KLOCWORK_HUB                  | String     | Yes       | Klocwork Hub domain and port in the form of                 |
|                               |            |           | '<hub location>:<port>'                                     |
+-------------------------------+------------+-----------+-------------------------------------------------------------+
| KLOCWORK_PROJ_NAME            | String     | Yes       | Project name provided by the Hub administrator upon project |
|                               |            |           | creation                                                    |
+-------------------------------+------------+-----------+-------------------------------------------------------------+
| KLOCWORK_KWINJECT_FLAGS       | String     | Optional  | Customized command flags to be passed into the 'kwinject'   |
|                               |            |           | command                                                     |
|                               |            |           |                                                             |
|                               |            |           |   Default value: None                                       |
+-------------------------------+------------+-----------+-------------------------------------------------------------+
| KLOCWORK_KWBUILDPROJECT_FLAGS | String     | Optional  | Customized command flags to be passed into the              |
|                               |            |           | 'kwbuildproject' command                                    |
|                               |            |           |                                                             |
|                               |            |           |   Default value: None                                       |
+-------------------------------+------------+-----------+-------------------------------------------------------------+
| KLOCWORK_BUILD_DIR            | String     | Optional  | Relative (to SOURCE_DIR) path to the build directory for    |
|                               |            |           | the source code                                             |
|                               |            |           |                                                             |
|                               |            |           |   Default value: SOURCE_DIR                                 |
+-------------------------------+------------+-----------+-------------------------------------------------------------+
| KLOCWORK_BUILD_CMD            | String     | Yes       | Command to build the source code for Klocwork analysis      |
+-------------------------------+------------+-----------+-------------------------------------------------------------+
| KLOCWORK_CLEAN_CMD            | String     | Yes       | Command to clean the source code for Klocwork analysis      |
+-------------------------------+------------+-----------+-------------------------------------------------------------+

Custom Analysis Variables
*************************
+--------------------+------------+-----------+------------------------------------------------------------------------+
| Variable Name      | Format     | Required? | Description                                                            |
+====================+============+===========+========================================================================+
| CUSTOM_WARNINGS    | True/False | Yes       | Should custom analysis be performed?                                   |
+--------------------+------------+-----------+------------------------------------------------------------------------+
| CUSTOM_BUILD_DIR   | String     | Optional  | Relative (to SOURCE_DIR) path to the run directory for the custom      |
|                    |            |           | checks                                                                 |
|                    |            |           |                                                                        |
|                    |            |           |   Default value: SOURCE_DIR                                            |
+--------------------+------------+-----------+------------------------------------------------------------------------+
| CUSTOM_CMD         | String     | Yes       | Command to invoke the custom checks                                    |
+--------------------+------------+-----------+------------------------------------------------------------------------+
| CUSTOM_OUTPUT_FILE | String     | Yes       | Absolute path to the SCRUB formatted results output file               |
+--------------------+------------+-----------+------------------------------------------------------------------------+

Output Target Variables
#######################
Collaborator Variables
**********************
+-------------------------------+----------------+-----------+---------------------------------------------------------+
| Variable Name                 | Format         | Required? | Description                                             |
+===============================+================+===========+=========================================================+
| COLLABORATOR_UPLOAD           | True/False     | Yes       | Should Collaborator upload be performed?                |
+-------------------------------+----------------+-----------+---------------------------------------------------------+
| COLLABORATOR_SERVER           | String         | Yes       | URL of the Collaborator server                          |
+-------------------------------+----------------+-----------+---------------------------------------------------------+
| COLLABORATOR_CCOLLAB_LOCATION | String         | Optional  | Absolute path to the directory containing the ccollab   |
|                               |                |           | Collaborator command line utility                       |
|                               |                |           |                                                         |
|                               |                |           |   Default value: None                                   |
+-------------------------------+----------------+-----------+---------------------------------------------------------+
| COLLABORATOR_USERNAME         | String         | Yes       | Collaborator username to be used to create the review   |
+-------------------------------+----------------+-----------+---------------------------------------------------------+
| COLLABORATOR_REVIEW_TITLE     | String         | Optional  | Optional title for the review                           |
|                               |                |           |                                                         |
|                               |                |           |   Default value: SCRUB Review                           |
+-------------------------------+----------------+-----------+---------------------------------------------------------+
| COLLABORATOR_REVIEW_GROUP     | String         | Optional  | Optional review group for the review                    |
|                               |                |           |                                                         |
|                               |                |           |   Default value:                                        |
+-------------------------------+----------------+-----------+---------------------------------------------------------+
| COLLABORATOR_REVIEW_TEMPLATE  | String         | Optional  | Template to be used when creating review                |
|                               |                |           |                                                         |
|                               |                |           |   Default value:                                        |
+-------------------------------+----------------+-----------+---------------------------------------------------------+
| COLLABORATOR_REVIEW_ACCESS    | String         | Optional  | Access level to be used or the review                   |
|                               |                |           |                                                         |
|                               |                |           |   Default value:                                        |
+-------------------------------+----------------+-----------+---------------------------------------------------------+
| COLLABORATOR_FINDING_LEVEL    | comment/defect | Optional  | Level at which findings will be added to review         |
|                               |                |           |                                                         |
|                               |                |           |  Default value: comment                                 |
+-------------------------------+----------------+-----------+---------------------------------------------------------+
| COLLABORATOR_FILTERS          | String         | Optional  | Absolute path to file containing list of regex patterns |
|                               |                |           | defining which source files to exclude/include in       |
|                               |                |           | upload                                                  |
|                               |                |           |                                                         |
|                               |                |           |   Default value:                                        |
+-------------------------------+----------------+-----------+---------------------------------------------------------+
| COLLABORATOR_SRC_FILES        | String         | Optional  | Comma separated list of static analysis results files   |
|                               |                |           | to push to Collaborator                                 |
|                               |                |           |                                                         |
|                               |                |           |   Default value:                                        |
+-------------------------------+----------------+-----------+---------------------------------------------------------+

Filtering Variables
###################
+-----------------------+------------+-----------+---------------------------------------------------------------------+
| Variable Name         | Format     | Required? | Description                                                         |
+=======================+============+===========+=====================================================================+
| ENABLE_EXT_WARNINGS   | True/False | Yes       | Should SCRUB display external warnings? These are warnings found in |
|                       |            |           | directories outside of the source code directory                    |
+-----------------------+------------+-----------+---------------------------------------------------------------------+
| ENABLE_MICRO_FILTER   | True/False | Yes       | Enable micro filtering?                                             |
+-----------------------+------------+-----------+---------------------------------------------------------------------+
| CUSTOM_FILTER_COMMAND | String     | Optional  | User-defined filtering command to perform specialty filtering       |
|                       |            |           |                                                                     |
|                       |            |           |   Default value: None                                               |
+-----------------------+------------+-----------+---------------------------------------------------------------------+
| ANALYSIS_FILTERS      | String     | Optional  | Absolute path to file containing list of regex patterns defining    |
|                       |            |           | which source files to exclude/include in analysis results           |
|                       |            |           |                                                                     |
|                       |            |           |   Default value: ./SCRUBFilters                                     |
+-----------------------+------------+-----------+---------------------------------------------------------------------+
| QUERY_FILTERS         | String     | Optional  | Absolute path to file containing list of tool queries to exclude    |
|                       |            |           | from analysis results                                               |
|                       |            |           |                                                                     |
|                       |            |           |   Default value: ./SCRUBExcludeQueries                              |
+-----------------------+------------+-----------+---------------------------------------------------------------------+