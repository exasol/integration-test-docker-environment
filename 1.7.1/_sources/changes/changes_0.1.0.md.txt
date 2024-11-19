# Integration-Test-Docker-Environment 0.1.0, released 25.06.2020
 
## Summary

In this first release we created an docker test environment for Exasol. The test environment consists of two docker containers with their own docker network which isolates them from the host. The first container is an Exasol Docker-DB container and the second container is the test container which can be used for the test execution. The setup script creates a new environment accordingly the given options, creates the Exasol configuration and waits for Exasol database and BucketFS to be available. Afterwards, it runs an initial setup for the database where it uploads the Exasol JDBC Driver and imports some test data.

### Currently supported Operating Systems

* Linux
* Mac OS X with Intel processors (please consult the README for more details)

### Currently supported Exasol Versions

* **6.0**: 6.0.12, 6.0.13, 6.0.16
* **6.1**: 6.1.1, 6.1.6, 6.1.7, 6.1.8, 6.1.9
* **6.2**: 6.2.4, 6.2.0, 6.2.1, 6.2.3, 6.2.5, 6.2.6

If you need further versions, please open an issue.

## Features
 
* #20: Provide container information on the host and in the test container
* #19: Cleanup up docker resources after failure during setup
* #15: Add command line flag to deactivate the database setup
* #14: Make disk size adjustable
* #13: Make the DB MemSize adjustable
* #11: Start the Test-Environment in docker runner to avoid dependency installation 
