# Integration-Test-Docker-Environment 0.2.0, released 2020-11-17

In this release, we add support for new Exasol Docker-DB versions and Docker runtimes to the integration-test-docker-environment. For example, you can run the Docker-DB with the nvidia-container-runtime to add support for GPUs to the UDFs of the Exasol Version. This allows you to test your GPU-accelerated UDFs in your CI environment, before deploying them on your production cluster. Furthermore, we converted the project from a pipenv project to a poetry project to improve packaging and reusability in the future.

### New supported Exasol Versions

* **6.1**: 6.1.10, 6.1.11, 6.1.12, 6.1.13
* **6.2**: 6.2.7, 6.2.8, 6.2.9, 6.2.10, 6.2.11
* **7.0**: 7.0.0, 7.0.1, 7.0.2, 7.0.3

If you need further versions, please open an issue.

### Tested Docker Runtimes

- Docker Default Runtime
- [NVIDIA Container Runtime](https://github.com/NVIDIA/nvidia-container-runtime) for GPU accelerated UDFs

## Bug Fixes:

  - #38: Fix logging of database startup log and fetching all DB logs after startup

## Features / Enhancements:

  - #58: Add support for Docker-DB versions 6.1.12, 6.1.13, 6.2.10, 6.2.11, 7.0.2, 7.0.3 and set default to 7.0.3
  - #48: Package with poetry
  - #46: Add support for Exasol Docker-DB 7.0.1
  - #36: Add support for Exasol Docker-DB versions 7.0.0, 6.2.9, 6.2.8, 6.2.7, 6.1.11 and 6.1.10
  - #27: Add support for different docker-runtimes

## Refactoring:

  - #28: Refactoring test environment lib code
  - #56: Run all tests for each db version only for master, for pull requests and on request [run all tests] in the commit message
  - #39: Remove print statement or replace them with logging
