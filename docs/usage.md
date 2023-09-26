---
layout: default
title: Usage
nav_order: 3
---

# Usage
## SCRUB Sub-Commands
After SCRUB has been installed, it can be run using the command line interface. There are a few defined entry points:

### scrub run
This function runs all applicable tools present within the configuration file.

    scrub run [--config <path>] [--tools <tools>] [--targets <targets>] [--clean] [--quiet/--debug] [--define <override values>]

| Flag                       | Description                                                  | Default Value  |
| -------------------------- | ------------------------------------------------------------ | -------------- |
| `--config [config path]`   | Path to SCRUB configuration file                             | `./scrub.cfg`  |
| `--tools [tools list]`     | Tools to run during analysis (any supported tools)           | N/A            | 
| `--targets [targets list]` | Targets to run during results export (any supported targets) | N/A            |
| `--clean`                  | Remove all previous analysis artifacts                       | N/A            |
| `--debug`                  | Print verbose execution information to the console           | N/A            |
| `--quiet`                  | Print minimal execution information to the console           | N/A            |
| `--define [define value]`  | Override values found in the configuration file              | N/A            |

Some sample usages are shown below:

    scrub run --clean --debug
    scrub run --tools coverity codesonar --targets collaborator
    scrub run --quiet
    scrub run --config /home/user/scrub.cfg --define "COVERITY_COVANALYZE_FLAGS=--aggressiveness-level=high"

### scrub run-tool
This function runs a single analysis module, while preserving existing analysis results. **Note**: `scrub run-tool` is a legacy command and only included for backwards compatability. Users are incouraged to use the `scrub run` command and `--tools` flag to run individual tools.

    scrub run-tool <module> [--config <path>]

| Flag/Positional Argument   | Description                                                       | Default Value  |
| -------------------------- | ----------------------------------------------------------------- | -------------- |
| `<module>`                 | Tool import location of the form scrub.tools.\<tool\>.do_\<tool\> | N/A            |
| `--config [config path]`   | Path to SCRUB configuration file                                  | `./scrub.cfg`  |     


### scrub diff
This function compares a set of static analysis results to a defined baseline set of results.

    scrub diff --baseline_source <path> --baseline_scrub <path> --comparison_source <path> --comparison_scrub <path>

| Flag/Positional Argument     | Description                                             | Default Value  |
| ---------------------------- | ------------------------------------------------------- | -------------- |
| `--baseline_source <path>`   | Absolute path to baseline source root directory         | N/A            |
| `--baseline_scrub <path>`    | Absolute path to the baseline SCRUB working directory   | N/A            |
| `--comparison_source <path>` | Absolute path to comparison source root directory       | N/A            |
| `--comparison_scrub <path>`  | Absolute path to the comparison SCRUB working directory | N/A            |

### scrub get-conf
This function generates a blank configuration file at the desired output location.

    scrub get-conf [--output <path>]

| Flag/Positional Argument | Description                     | Default Value          |
| ------------------------ | ------------------------------- | ---------------------- |
| `--output <path>`        | Path to desired output location | `./scrub_template.cfg` |

### scrub version
This function prints the current SCRUB version information and latest available version information to the console.

    scrub version


## Running SCRUB

Running SCRUB is a relatively straightforward process after it has been configured properly. Users only need to perform the following steps.

1. Retrieve the desired version of source code to be analyzed. This source code must reside locally for SCRUB to work.
2. Create a valid scrub.cfg configuration file and fill out the applicable portions
3. Execute the following command from this directory to begin SCRUB execution:

    `scrub run --config scrub.cfg --debug --clean`

During execution SCRUB will print various status messages to the console. Additionally, log information and results will be stored in a hidden directory named `.scrub` located at `SOURCE_DIR` as defined in the scrub.cfg file used during execution.

A subset of tools can also be run by using using the `run --tools` command. The tools flag expects a space-separated list of tools to be provided.

    scrub run --tools codeql --config scrub.cfg --quiet
    
    scrub run --tools coverity codesonar --debug


## Dependencies

This document assumes that working versions of the all static code analyzers to be used have been installed and tested on the host machine.

Python v3.6 or later is required.

## Supported COTS Tools and Languages


| Tool            | Languages                        | Supports P10? | License Required? |
| --------------- | -------------------------------- | ------------- | ----------------- |
| CodeSonar       | C/C++, Java, JavaScript, Python  | Yes           | Yes               |
| CodeQL          | C/C++, Java, JavaScript, Python  | Yes           | No*               |
| Coverity        | C/C++, Java, JavaScript, Python  | No            | Yes               |
| GBUILD Compiler | C/C++                            | No            | Yes               |
| GCC Compiler    | C/C++                            | No            | No                |
| JAVAC Compiler  | Java                             | No            | No                |
| Pylint          | Python                           | No            | No                |
| SonarQube       | C/C++, Java, JavaScript, Python  | No            | No**              |

**Note**: P10 checks are only applicable to C/C++ analysis.

\* CodeQL does not require a license to perform analysis, but there are restrictions on its usage. Please refer to the [full license](https://github.com/github/codeql-cli-binaries/blob/main/LICENSE.md) for more information.

\** SonarQube analysis of C/C++ code requires the Enterprise Edition, which requires a license.

## Known Limitations

SCRUB is currently not compatible with Windows system due to differences in how the tools are executed on Windows.

Some tools that analyze C/C++ must be pre-configured to support various compilers. Not every tool supports every compiler. Please refer to the tool documentation for more information on which compilers are supported.

## Installation and Setup

SCRUB can be easily installed using `pip`. More information can be found on the [Installation](installation.md) page.

SCRUB can easily be configured using the `scrub.cfg` configuration file. More detailed information on how to complete the scrub.conf file for your project can be found on the [Detailed Configuration](configuration.md) page.


## Expected Output and Exit Codes

After SCRUB execution has started, high-level progress information will be printed to the console. All of the data generated by SCRUB will be stored in the directory `SOURCE_DIR/.scrub`. The structure of this directory can be found on the [SCRUB Output](output.md) page.

SCRUB execution will end with a status message of the following format:

    Tool Execution Status:
        Tool 1: <Status Message>
        Tool 2: <Status Message>
        ...
        Tool N: <Status Message>

SCRUB will also return an exit code for the execution that indicates the number of tool failures that occurred during analysis. For example, an exit code of 0 indicates that no tool failures occurred. An exit code of 1 indicates that 1 tool failure occurred.

There are 4 possible exit codes from each `<tool>.template` template.

| Exit Code | Meaning                                                   |
| --------- | --------------------------------------------------------- |
| 0         | No issues encountered during tool execution               |
| 1         | An error occurred while executing a tool specific command |
| 2         | Tool execution was not attempted                          |
| 100*      | A Python error occurred while executing a SCRUB command   |

**Note**: An exit code of 100 will immediately halt SCRUB execution.
