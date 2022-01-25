# Integration-Test-Docker-Environment 0.8.0, released t.b.d.

Code name: t.b.d.

## Summary

t.b.d.

### Supported Exasol Versions

* **6.2**: up to 6.2.17
* **7.0**: up to 7.0.14, **except 7.0.5**
* **7.1**: up to 7.1.3

If you need further versions, please open an issue.

### Tested Docker Runtimes

- Docker Default Runtime
- [NVIDIA Container Runtime](https://github.com/NVIDIA/nvidia-container-runtime) for GPU accelerated UDFs

## Bug Fixes:

 - #148: Fix broken Github actions
 - #152: Fix bug where Bucket- and Database-forward might be the same 
 - #154: Fix comparison of db versions
 - #160: Remove support for docker db v 7.0.5

## Features / Enhancements:

 - #150: Updated exaplus and jdbc for test environment and cleaned up Dockerfile
 - #157: Add shellcheck verification
 - #146: Port starter scripts from script-languages-container-tool to this project
 - #140: Create or inject SSL Certificates into the Docker-DB 
 - #146: Port starter scripts

## Refactoring:

 - #141: Extract module name extraction into separate method

## Documentation:

n/a

## Security:

n/a
