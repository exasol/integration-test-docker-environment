# Integration-Test-Docker-Environment 3.1.0, released 2024-06-26

## Summary

Updated dependency constraints and supported Exasol versions.

### Supported Exasol Versions

* **7.1**: up to 7.1.26
* **8**: from 8.17.0 up to 8.27.0

## Dependencies

* Update docker dependency constrains to `>= 4.0.0, != 7.0.0`, for further details see:
    - [docker/docker-py#3240](https://github.com/docker/docker-py/issues/3240)
    - [docker/docker-py#3223](https://github.com/docker/docker-py/issues/3223)

## Changes

* Moved `pytest` dependency to development dependencies
* Add explicit dependency and version constraint (`<= 0.20.1`) for `docutils`
* #396: Added new docker-db versions
