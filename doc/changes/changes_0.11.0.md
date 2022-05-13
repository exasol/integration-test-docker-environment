# Integration-Test-Docker-Environment 0.11.0, released 13.05.2022

Code name: Update python 3.8

## Summary

Updated minimal supported python version to 3.8. Furthermore, changed start-test-env script so that it 
switches to Integration-Test-Docker-Environment directory during execution.


### Supported Exasol Versions

* **7.0**: up to 7.0.18, **except 7.0.5**
* **7.1**: up to 7.1.9

If you need further versions, please open an issue.

### Tested Docker Runtimes

- Docker Default Runtime
- [NVIDIA Container Runtime](https://github.com/NVIDIA/nvidia-container-runtime) for GPU accelerated UDFs

## Bug Fixes:

 - #169: Changed start-test-env script so that it switches to itde directory during execution 

## Features / Enhancements:

 - #213: Removed virtualschema-jdbc-adaptar.jar 

## Refactoring:
 - #192: Updated minimal supported python version to 3.8

## Documentation:


 - #218: Prepare release

## Security:

n/a