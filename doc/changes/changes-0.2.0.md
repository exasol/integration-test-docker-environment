# Integration-Test-Docker-Environment 0.2.0, released 2020-09-25

## Summary

In this release, we add support for new Exasol Docker-DB versions and Docker runtimes to the integration-test-docker-environment. For example, you can run the Docker-DB with the nvidia-container-runtime to add support for GPUs to the UDFs of the Exasol Version. This allows you to test your GPU-accelerated UDFs in your CI environment, before deploying them on your production cluster.

### New supported Exasol Versions

* **6.1**: 6.1.10, 6.1.11
* **6.2**: 6.2.7, 6.2.8, 6.2.9
* **7.0**: 7.0.0, 7.0.1

If you need further versions, please open an issue.

### Tested Docker Runtimes

- Docker Default Runtime
- [NVIDIA Container Runtime](https://github.com/NVIDIA/nvidia-container-runtime) for GPU accelerated UDFs

## Bug Fixes

* #38: Fix logging of database startup log and fetching all logs after DB startup (#38) 
 
## Features / Enhancements

* #46: Add support for Exasol Docker-DB 7.0.1 
* #42: Set Exasol 7.0.0 as default version
* #36: Add new docker-db versions 7.0.0, 6.2.9, 6.2.8, 6.2.7, 6.1.11 and 6.1.10
* #27: Add support for different docker-runtimes
 
## Documentation
 
* #44: Update Readme to reflect recent changes 
 
## Refactoring
 
* #28: Refactoring test environment lib code (#28) 
