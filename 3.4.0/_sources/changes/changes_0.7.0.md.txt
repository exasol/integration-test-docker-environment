# Integration-Test-Docker-Environment 0.7.0, released 2021-12-02

Code name: Docker db 7.1.3 and 7.0.14

## Summary

This release updates to docker db 7.1.3 and 7.0.14, and also contains a some bugfixes.

### Supported Exasol Versions

* **6.2**: up to 6.2.17
* **7.0**: up to 7.0.14
* **7.1**: up to 7.1.3

If you need further versions, please open an issue.

### Tested Docker Runtimes

- Docker Default Runtime
- [NVIDIA Container Runtime](https://github.com/NVIDIA/nvidia-container-runtime) for GPU accelerated UDFs

## Bug Fixes:

 - #134: Release: Upload of artifacts must not run within matrix build
 - #25: Avoid that cleanup methods can be called multiple times when the task is a child task of multiple other task

## Features / Enhancements:

 - #138: Integrate new Docker dbs 7.1.3 and 7.0.14

## Refactoring:

n/a

## Documentation:

 - #143: Prepare release 0.7.0

## Security:

n/a