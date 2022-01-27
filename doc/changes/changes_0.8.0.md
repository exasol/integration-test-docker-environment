# Integration-Test-Docker-Environment 0.8.0, released 2022-01-27

Code name: Certificate injection and automatic docker hub login.

## Summary

This version supports now the automatic creation and injection of SSL certificates to the database and test-container, automatic login to Docker hub for any docker interaction, and uses similar starter scripts as script-language-container-tools.
Support for Exasol DB 6.2.x and 7.0.5 was dropped, and support for 7.0.15, 7.1.4 and 7.1.5 added. 
Also, there were several bug-fixes and the CI build now runs shellcheck on all bash scripts.  

### Supported Exasol Versions

* **7.0**: up to 7.0.15, **except 7.0.5**
* **7.1**: up to 7.1.5

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
 - #164: Remove test and support for Exasol DB 6.2.x
 - #162: Make sure that all docker function calls use docker credentials if possible
 - #165: Integrate docker db 7.1.4, 7.1.5 and 7.0.15 and prepare release

## Refactoring:

 - #141: Extract module name extraction into separate method

## Documentation:

n/a

## Security:

n/a
