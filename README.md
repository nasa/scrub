![CodeQL](https://github.com/nasa/scrub/actions/workflows/codeql.yml/badge.svg)
![Packaging](https://github.com/nasa/scrub/actions/workflows/python-publish.yml/badge.svg)
[![PyPI version shields.io](https://img.shields.io/pypi/v/nasa-scrub.svg)](https://pypi.python.org/pypi/nasa-scrub/)

# SCRUB

SCRUB is an orchestration and aggregation platform for static code analysis tools.

SCRUB allows users to run multiple static code analysis tools, collect the results, and export them to external tools. The results from each analyzer are post-processed to a standard warning format that provides information about the location of the warning as well as a brief description of the warning. These warnings can then reviewed and assessed by experienced developers to determine their merit.

A full description of the origins of SCRUB, written by the original author (Gerard Holzmann), can be [found here](http://spinroot.com/gerard/pdf/ScrubPaper_rev.pdf).

## [SCRUB Documentation](https://nasa.github.io/scrub)

