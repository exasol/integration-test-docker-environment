# Integration-Test-Docker-Environment 0.4.0, released 2021-07-22

Code name: New docker-db versions.

## Summary

This release contains support for new docker-db version 7.0.11. 

### New supported Exasol Versions

* **6.2**: 6.2.14, 6.2.15,
* **7.0**: 7.0.4, 7.0.5, 7.0.6, 7.0.7, 7.0.8, 7.0.9, 7.0.10, 7.0.11

If you need further versions, please open an issue.

### Tested Docker Runtimes

- Docker Default Runtime
- [NVIDIA Container Runtime](https://github.com/NVIDIA/nvidia-container-runtime) for GPU accelerated UDFs

## Bug Fixes:
   - #99: Fixed click parameters for external-exasol-db-port and external-exasol-bucketfs-port
   - #97: Fixed computation of hash in exaslct if path contains symlink loops

## Features / Enhancements:
    
   - #93: Add docker-db versions 7.0.11 and prepare release
   - #95: Changed changelog file names (#96)
   - #101: Added config for publishing release on community portal


## Refactoring:
n/a  

