# Integration-Test-Docker-Environment 0.9.0, released  2022-02-25

Code name: Bumblebee - Update Docker DB to 7.0.16 and 7.1.6 

## Summary
This version improves overall stability and adds support for automated health check(s) of the system.
Added support for new Docker DB's 7.0.16 and 7.1.6 and also fixed various bugs and a security vulnerability.

### Supported Exasol Versions

* **7.0**: up to 7.0.15, **except 7.0.5**
* **7.1**: up to 7.1.5

If you need further versions, please open an issue.

### Tested Docker Runtimes

- Docker Default Runtime
- [NVIDIA Container Runtime](https://github.com/NVIDIA/nvidia-container-runtime) for GPU accelerated UDFs

## Bug Fixes:

 - #170: Fix docker image publication
 - #172: Fix Python3.6 installation script
 - #175: Fix docker push and allow docker push workflow for ci_test branch

## Features / Enhancements:

 - #17: Improve error message when docker socket can't be found 
 - #186: Add support for DB 7.1.6 and 7.0.16

## Refactoring:

n/a

## Documentation:

n/a

## Security:

 - #186 Fix CVE-2021-32559
