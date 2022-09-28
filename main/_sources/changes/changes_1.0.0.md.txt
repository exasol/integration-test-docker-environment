# Integration-Test-Docker-Environment 1.0.0, released 2022-09-28

Code name: API, Test-Container injection and Sphinx Documentation

## Summary
This release supports the injection of an externally defined test-container. Also, it provides a public API which enables clients to spawn the environment using pure Python functions. The generation of Sphinx documentation was added. 
Support of new docker db version was added. Finally, there were several minor bugfixes.

### Supported Exasol Versions

* **7.0**: up to 7.0.20, **except 7.0.5**
* **7.1**: up to 7.1.14

If you need further versions, please open an issue.

### Tested Docker Runtimes
TBD


## Bug Fixes:
- #228: Fixed graph plot generator
- #230: Fixed default value of click option external-exasol-xmlrpc-port should be int
- #211: Fixed output of test DockerTestEnvironmentDockerRuntimeInvalidRuntimeGivenTest
- #244: Fixed bug in generate graph plot if task uses luigi.ListParameter
- #249: Fixed bug of calculation of hash value of docker images when using volatile absolute paths

## Features / Enhancements:

- #221: Add support for exasol 7.1.10
- #223: Updated docker-db versions
- #168: Implemented injection of external test container via CLI
- #257: Added Docker-db's 7.1.13,7.1.14 and 7.0.20

## Refactoring:

- #235: Moved implementations of all click commands in separate methods
- #240: Created more integation tests for api calls and implemented return values
- #251: Updated Poetry

## Documentation:
- #255: Added support for sphinx based documentation
- #185: Restructured README.md and converted to RST

## Security:

n/a
