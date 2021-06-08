# Integration-Test-Docker-Environment 0.3.0, released 2021-06-08

In this release, we add support for new Exasol Docker-DB versions and Docker runtimes to the integration-test-docker-environment. For example, you can run the Docker-DB with the [NVIDIA Container Runtime](https://github.com/NVIDIA/nvidia-container-runtime) to add support for GPUs to the UDFs of the Exasol database. This allows you to test your GPU-accelerated UDFs in your CI environment, before deploying them on your production cluster. Furthermore, we converted the project from a pipenv project to a poetry project to improve packaging and reusability in the future.

### New supported Exasol Versions

* **6.2**: 6.2.14, 6.2.15,
* **7.0**: 7.0.4, 7.0.5, 7.0.6, 7.0.7, 7.0.8, 7.0.9, 7.0.10

If you need further versions, please open an issue.

### Tested Docker Runtimes

- Docker Default Runtime
- [NVIDIA Container Runtime](https://github.com/NVIDIA/nvidia-container-runtime) for GPU accelerated UDFs

## Bug Fixes:

 - #71: Fix exception if goals are not available for docker builds
 - #26: Exception can get printed multiple times in the final exception summary if a task is the child task of multiple other tasks

## Features / Enhancements:
    
   - #83: Add docker-db versions 7.0.10 and 6.2.15-d1
   - #79: Remove support for Exasol 6.0 and 6.1
   - #72: Add support for new docker-db versions 6.2.14 and 7.0.9
   - #64: Add new docker-db versions
   - #62: Prepare release for version 0.2.0
   - #30: Add option for name server and set 8.8.8.8 as default name server

## Refactoring:
  
  - #81: Extract test/utils.py to testing/utils.py
  - #67: Remove DepHell dependency, because it is not maintained anymore

