# Integration Test Docker Environment

## About

This project provides a command line interface to start a test environment with an [Exasol Docker DB](https://hub.docker.com/r/exasol/docker-db). It starts an Exasol Docker-DB container and an associated test container where Exaplus and ODBC is already installed. Both containers exist in the same Docker network. This allows you to connect from the test container to the Docker-DB container. Further more, the database gets populated with some test data. You can find the test data under `tests/test/enginedb_small/import.sql`. Besides the test container, you can also access the Exasol database and the Bucket-FS from the host via port forwards. 

### Comparison to Docker-DB and the Exasol Testcontainers

* This project uses the [Docker-DB](https://hub.docker.com/r/exasol/docker-db), but it does the configuration, setup and startup for you. For example, it waits until the Database and the Bucket-FS accept connections. It also populates it with test data and provides with the test container an environment to access the database.
* The [Exasol Testcontainers](https://github.com/exasol/exasol-testcontainers/) provides similar features for Java JUnit integration tests, so if you have an Java project use the Exasol Testcontainer, because they are more integrated in the Java ecosystem then this project. However, if you have a project in any other language you can use this project to start a test Exasol database via a commandline interface.

## Prerequisites

In order to start a Docker-DB Test Environment, you need:

* Linux (MaxOS X and Windows is currently not supported, because the Exasol Docker-DB requires privileged mode)
* Docker with privileged mode
* We recommend at least 15 GB free disk space on the partition 
  where Docker stores its images and containers, on Linux Docker typically stores 
  the images at /var/lib/docker.

## Getting started

Clone the repository

```
git clone https://github.com/exasol/integration-test-docker-environment
```

Starting the test environment:

```
./start-test-env spawn-test-environment --environment-name <NAME> --database-port-forward <PORT> --bucketfs-port-forward <PORT>
```
or if you work on the code of the the Test Environment (requires Python >=3.6 with pip):

```
./start-test-env-without-docker-runner spawn-test-environment --environment-name <NAME> --database-port-forward <PORT> --bucketfs-port-forward <PORT>
```

Shutdown of the test environment is currently done manual.

### Default Credentials

The default credentials for the database are
  * User: sys
  * Password: exasol
  
and for the Bucket-FS:

  * User: w
  * Password: write
  
or

  * User: r
  * Password: read
