# Integration Test Docker Environment

## About

This project provides a command line interface to start a test environment with an [Exasol Docker-DB](https://hub.docker.com/r/exasol/docker-db). It starts an Exasol Docker-DB container and an associated test container where [EXAPlus CLI](https://docs.exasol.com/connect_exasol/sql_clients/exaplus_cli/exaplus_cli.htm) and  the [Exasol ODBC driver](https://docs.exasol.com/connect_exasol/drivers/odbc.htm) are already installed.

Both containers exist in the same Docker network. This allows you to connect from the test container to the Docker-DB container. Furthermore, the database gets populated with some test data. You can find the test data under `tests/test/enginedb_small/import.sql`. Besides the test container, you can also access the Exasol database and the Bucket-FS from the host via forwarded ports.

### Comparison to Docker-DB and the Exasol Testcontainers

* This project uses the [Docker-DB](https://hub.docker.com/r/exasol/docker-db), but it does the configuration, setup and startup for you. For example, it waits until the Database and the Bucket-FS accept connections. It also populates the database with test data and provides with the test container as an environment to access the database.
* The [Exasol Testcontainers](https://github.com/exasol/exasol-testcontainers/) provide similar features for Java integration tests, so if you have an Java project use the Exasol Testcontainer, because they are more integrated in the Java ecosystem then this project. Testcontainers are designed to integrate with popular unit testing frameworks like [JUnit4](https://www.testcontainers.org/test_framework_integration/junit_4/), [JUnit5](https://www.testcontainers.org/test_framework_integration/junit_5/) and [Spock](https://www.testcontainers.org/test_framework_integration/spock/). Most notably, lifecycle management of containers controlled by the tests lifecycle.

However, if you have a project in any other language you can use this project to start a test Exasol database via a command line interface.

## Prerequisites

In order to start a Docker-DB Test Environment, you need:

* Tests Operating System:
  * Linux 
  * MaxOS X with [Docker Desktop on Mac](https://docs.docker.com/docker-for-mac/install/) works with some limitations, for more details, see [here](#macos-x-support).
  * Windows is currently **not supported**, because the Exasol Docker-DB requires [privileged mode](https://docs.docker.com/engine/reference/run/#runtime-privilege-and-linux-capabilities). Please use a Linux virtual machine.
* Docker with privileged mode
* At least 2 GiB RAM
* We recommend at least 15 GB free disk space on the partition 
  where Docker stores its images and containers. On Linux Docker typically stores 
  the images under `/var/lib/docker`.

## Getting started

Clone the repository

```
git clone https://github.com/exasol/integration-test-docker-environment
```

Starting the test environment:

```
./start-test-env spawn-test-environment --environment-name <NAME>
```
or if you work on the code of the the Test Environment (requires Python >=3.6 with pip):

```
./start-test-env-without-docker-runner spawn-test-environment --environment-name <NAME>
```

Shutdown of the test environment is currently done manual.

### Options

The following options are available to customize the test environment. 

```
  --environment-name TEXT         Name of the docker environment. This name
                                  gets used as suffix for the container
                                  db_container_<name> and
                                  test_container_<name>  [required]

  --database-port-forward INTEGER
                                  Host port to which the database port gets
                                  forwarded  [default: 8888]

  --bucketfs-port-forward INTEGER
                                  Host port to which the bucketfs port gets
                                  forwarded  [default: 6666]

  --db-mem-size TEXT              The main memory used by the database. Format
                                  <number> <unit>, e.g. 1 GiB. The minimum
                                  size is 1 GB, below that the database will
                                  not start.  [default: 2 GiB]

  --db-disk-size TEXT             The disk size available for the database.
                                  Format <number> <unit>, e.g. 1 GiB. The
                                  minimum size is 100 MiB. However, the setup
                                  creates volume files with at least 2 GB
                                  larger size, because the database needs at
                                  least so much more disk.  [default: 2 GiB]

  --deactivate-database-setup BOOLEAN
                                  Deactivates the setup of the spawned
                                  database, this means no data get populated
                                  and no jdbc drivers get uploaded. This can
                                  be used either to save time or as a
                                  workaround for MacOSX where the
                                  test_container seems not to be able to
                                  access the tests directory  [default: False]
```

You can look at them on the commandline with:

```
./start-test-env spawn-test-environment --help 
```

### Default Credentials

The default credentials for the database are

  * User: `sys`
  * Password: `exasol`
  
and for the Bucket-FS:

  * User: `w`
  * Password: `write`
  
or

  * User: `r`
  * Password: `read`
  
## MacOS X Support

MacOS X with Docker Desktop for Mac uses a lightwight Virtual machine in which the container run. This makes [networking](https://docs.docker.com/docker-for-mac/networking/) and [shared directories](https://docs.docker.com/docker-for-mac/osxfs/) more complicated then on Linux.

We start the python setup script for the test environment in its own Docker container, because the the library [Luigi](https://luigi.readthedocs.io/en/stable/) can have problems with MacOS X and to avoid the installation of further dependencies. This Docker container has the Docker socket mounted and uses this to start the [Docker-DB](https://hub.docker.com/r/exasol/docker-db) container and the associate test container. This currently breaks mounting directories to the test container for populating the database.

Kudos to [@nndo1991](https://github.com/nndo1991) for helping to figure out, how we can use the test environment on Mac OS X.

### What do I need to do to start the Test Environment with MacOS X
1. Increase the RAM of the Docker VM to at least 4,25 GB or reduce the the DB Mem Size to less than 2 GB with `--db-mem-size 1 GiB`
2. Start the test environment with `--deactivate-database-setup`
