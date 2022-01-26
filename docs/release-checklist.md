# Release Checklist
The purpose of this document is to establish a process and checklist for new SCRUB releases. The process assumes that
all code changes have been completed and is ready for testing and subsequent release

## Preparation
- [ ] Planned code changes have been completed
- [ ] Unit testing for affected modules has been completed
- [ ] Make sure that any branched code and pending pull requests have been merged
- [ ] Check for commented out/debugging code


## Static Analysis
- [ ] Perform static analysis on SCRUB
- [ ] Make necessary code changes based on findings

## Integration Testing
- [ ] Make updates to the integration test suite, if necessary
- [ ] Run integration test suite
- [ ] Run performance test case
    - [ ] Analyze and compare metrics to previous releases

## Documentation
- [ ] Make any necessary updates to the [SCRUB documentation](https://nasa.github.io/scrub)

## Create Release
- [ ] Update [setup.cfg](https://github.com/nasa/scrub/blob/master/setup.cfg) for new release
- [ ] Upload new release to [pip](https://pypi.org/project/nasa-scrub)
- [ ] Create new release on [GitHub](https://github.com/nasa/scrub/releases)

## Process Improvement
- [ ] Update this release checklist as necessary