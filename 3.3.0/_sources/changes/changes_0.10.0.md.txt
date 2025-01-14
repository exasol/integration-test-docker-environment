# Integration-Test-Docker-Environment 0.10.0, released  2022-04-27

Code name: File logging

## Summary

This release adds support for file logging on execution of luigi tasks. Also, it contains one bugfix which solves the upload of the test container to dockerhub, and added support for new docker-db's.

### Supported Exasol Versions

* **7.0**: up to 7.0.18, **except 7.0.5**
* **7.1**: up to 7.1.9

If you need further versions, please open an issue.

### Tested Docker Runtimes

- Docker Default Runtime
- [NVIDIA Container Runtime](https://github.com/NVIDIA/nvidia-container-runtime) for GPU accelerated UDFs

## Bug Fixes:

 - #193: Test container doesn't get pushed to Docker-Hub in CI during push to main

## Features / Enhancements:

 - #198: Added support for Docker db 7.1.7, 7.1.8 and 7.0.17 
 - #201: Added support for Docker db 7.1.9 and 7.0.18
 - #207: Added support of file logging for Luigi tasks

## Refactoring:

n/a

## Documentation:

 - #209: Prepared release 0.10.0

## Security:

n/a