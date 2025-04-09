# Unreleased

### Summary 

### Supported Exasol Versions

* **7.1**: up to 7.1.29
* **8**: from 8.17.0 up to 8.32.0

## Features

 - #463: Added option to inject environment variables to docker-db 
 - #467: Add Docker-DB 8.32.0

## Security:

- #469 Resolved CVE-2024-12797 in transitive dependency `cryptography` via fabric & pyexasol by updating `cryptography` to version 44.0.2
  - Due to changes in cryptography's Python support (!=3.9.0 and 3.9.1), we updated our support to Python ^3.9.2. 

## Refactorings

 - #427: Use GH approval required for slow tests
 - #469: Updated to poetry 2.1.2
   - Updated `exasol-toolbox` to 1.0.0
 - #452: Use luigi mypy plugin for luigi parameters
  -#472: Convert integration API test to pytest - part I
