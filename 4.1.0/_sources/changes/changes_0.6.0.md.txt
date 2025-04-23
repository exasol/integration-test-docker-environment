# Integration-Test-Docker-Environment 0.6.0, released 2021-11-16

Code name: Docker db 7.1.2 

## Summary

This release updates to docker db 7.1.2, and also contains a major refactoring, where the job id needs to be assigned to every root task.
Besides this, it also contains a bugfix where the test data was not initially populated if the reuse_database_setup was set to true.
Also some release consistency checks were introduced.

### Supported Exasol Versions

* **6.2**: up to 6.2.17
* **7.0**: up to 7.0.13
* **7.1**: up to 7.1.2

If you need further versions, please open an issue.

### Tested Docker Runtimes

- Docker Default Runtime
- [NVIDIA Container Runtime](https://github.com/NVIDIA/nvidia-container-runtime) for GPU accelerated UDFs

## Bug Fixes:

 - #120: Test data not populated if reuse_database_setup is set to true, but database not setup

## Features / Enhancements:

 - #118: Check release consistency
 - #129: Added docker-db version 7.1.2

## Refactoring:

 - #122: make jobid a parameter of the task

## Documentation:
 - #132: Prepare documentation for release 0.6.0

## Security:
 -#126: Update urllib3 package