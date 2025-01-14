# 3.3.0 - 2025-01-14

Code name: Python3.12 support and toolbox support

## Summary

This release removed the usage of `pkg_resources` which enables clients to run the integration-test-docker-environment with Python3.12. Also, now the Exasol toolbox is used to run several CI checks. Besides this, the formatting was updated and missing type hints reported by MyPy were fixed. 

## Bugfixes

* #432: Fixed localhost ip address

## Refactorings

* #119: Refactored `pkg_resources` usage to `importlib.resources`
* #420: Added file `py.typed` to enable mypy to find project specific types
* #418: Use exasol/python-toolbox
* #411: Removed usage of exasol-bucketfs
* #425: Fixed type checks found by MyPy
* #423: Updated formatting

## Bugs

* #432: Fixed localhost ip address
