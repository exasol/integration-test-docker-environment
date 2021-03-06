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

* Tested Operating System:
  * Linux
  * Mac OS X with [Docker Desktop on Mac](https://docs.docker.com/docker-for-mac/install/) and Intel processor
  * Windows is currently **not supported**
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
or if you work on the code of the Test Environment (requires Python >=3.6 with pip):

```
./start-test-env-without-docker-runner spawn-test-environment --environment-name <NAME>
```

Shutdown of the test environment is currently done manual.

### Options

The following options are available to customize the test environment. 

```
Usage: main.py spawn-test-environment [OPTIONS]

  This command spawn a test environment with a docker-db container and a
  connected test-container. The test-container is reachable by the database
  for output redirects of UDFs.

Options:
  --environment-name TEXT         Name of the docker environment. This name
                                  gets used as suffix for the container
                                  db_container_<name> and
                                  test_container_<name>  [required]

  --database-port-forward INTEGER
                                  Host port to which the database port gets
                                  forwarded

  --bucketfs-port-forward INTEGER
                                  Host port to which the bucketfs port gets
                                  forwarded

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

  --deactivate-database-setup / --no-deactivate-database-setup
                                  Deactivates the setup of the spawned
                                  database, this means no data get populated
                                  and no jdbc drivers get uploaded. This can
                                  be used either to save time or as a
                                  workaround for MacOSX where the
                                  test_container seems not to be able to
                                  access the tests directory  [default: False]

  --docker-runtime TEXT           The docker runtime used to start all
                                  containers

  --docker-db-image-version TEXT  Docker DB Image Version against which the
                                  tests should run.  [default: 6.2.6-d1]

  --docker-db-image-name TEXT     Docker DB Image Name against which the tests
                                  should run.  [default: exasol/docker-db]
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

### Accessing the Environment Information

The python setup script creates configuration files on the host and in the test container.

On the host the container information get stored in the build output directory usually under `.build_output/cache/<ENVIRONMENT_NAME>/*`. In the test container the config file is stored at the root directory `/`.

The following config files are available:

- environment_info.sh: This file is meant to be source by the bash and then provides the information as environment variables. Here an example for the content:

  ```
  export ENVIRONMENT_NAME=test
  export ENVIRONMENT_TYPE=EnvironmentType.docker_db

  # Database IP in environment docker network
  export ENVIRONMENT_DATABASE_HOST=172.21.0.2
  export ENVIRONMENT_DATABASE_DB_PORT=8888
  export ENVIRONMENT_DATABASE_BUCKETFS_PORT=6583
  export ENVIRONMENT_DATABASE_CONTAINER_NAME=db_container_test
  export ENVIRONMENT_DATABASE_CONTAINER_NETWORK_ALIASES="exasol_test_database db_container_test"
  # Database IP in the environment docker network
  export ENVIRONMENT_DATABASE_CONTAINER_IP_ADDRESS=172.21.0.2
  export ENVIRONMENT_DATABASE_CONTAINER_VOLUMNE_NAME=db_container_test_volume
  # Database IP on the docker default bridge which under Linux available from the host
  export ENVIRONMENT_DATABASE_CONTAINER_DEFAULT_BRIDGE_IP_ADDRESS=172.17.0.3

  export ENVIRONMENT_TEST_CONTAINER_NAME=test_container_test
  export ENVIRONMENT_TEST_CONTAINER_NETWORK_ALIASES="test_container test_container_test"
  # Test Container IP in the environment docker network
  export ENVIRONMENT_TEST_CONTAINER_IP_ADDRESS=172.21.0.3
  ```
- environment_info.json: Contains the EnvironmentInfo objects pickled with JsonPickle
  
### Currently supported Exasol Versions

* **6.0**: 6.0.12, 6.0.13, 6.0.16
* **6.1**: 6.1.1, 6.1.6, 6.1.7, 6.1.8, 6.1.9, 6.1.10, 6.1.11, 6.1.12, 6.1.13
* **6.2**: 6.2.4, 6.2.0, 6.2.1, 6.2.3, 6.2.5, 6.2.6, 6.2.7, 6.2.8, 6.2.9, 6.2.10, 6.2.11
* **7.0**: 7.0.0, 7.0.1, 7.0.2, 7.0.3

If you need further versions, please open an issue.

### Tested Docker Runtimes

- Docker Default Runtime
- [NVIDIA Container Runtime](https://github.com/NVIDIA/nvidia-container-runtime) for GPU accelerated UDFs

## Mac OS X Support

### What do I need to do to start the Test Environment with Mac OS X

The Exasol Docker-DB needs per default a bit more than 2 GB of RAM, however the Docker VM on Mac OS X provides often not enough RAM to accommodate this. You should increase the RAM of the Docker VM to at least 4.25 GB or reduce the DB Mem Size for the Exasol Docker-DB to less than 2 GB with `--db-mem-size 1 GiB`.

### What happens under the hood

Mac OS X with Docker Desktop for Mac uses a lightweight virtual machine with linux in which the docker daemon runs and the containers get started. This makes [networking](https://docs.docker.com/docker-for-mac/networking/) and [shared directories](https://docs.docker.com/docker-for-mac/osxfs/) more complicated then on Linux.

We start the python setup script for the test environment in its own Docker container, lets call it `docker runner`, because the library [Luigi](https://luigi.readthedocs.io/en/stable/) can have problems with Mac OS X and to avoid the installation of further dependencies. To support Mac OS X, the `start-test-env` script starts the `docker runner` container and mounts the docker socket at `/var/run/docker.sock` and the directory of the test environment from the Mac OS X host to the container. Then, it starts `start-test-env-without-docker` which then starts the python script. It is important, that the repository gets cloned to the Mac OS X host and not to a docker container, because the python scripts tries to start further docker container which use host mounts to share the tests directory of the test environment with the docker container.
