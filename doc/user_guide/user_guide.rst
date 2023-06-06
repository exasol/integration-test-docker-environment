User Guide
===================================

About
-----

This project starts the database container,
and optionally (only available via API) also a test container.
Both containers exist in the same Docker network. This allows you to
connect from the test container to the Docker-DB container. Furthermore,
this package provides two utility tasks which allow the population of
some test data and upload of files to the BucketFS. Besides the test
container, you can also access the Exasol database and the Bucket-FS
from the host via forwarded ports.

Comparison to Docker-DB and the Exasol Testcontainers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  This project uses the
   `Docker-DB <https://hub.docker.com/r/exasol/docker-db>`__, but it
   does the configuration, setup and startup for you. For example, it
   waits until the Database and the Bucket-FS accept connections. It
   also provides tasks which simplify the population the database with
   test data and upload of files to the BucketFS.
-  The `Exasol
   Testcontainers <https://github.com/exasol/exasol-testcontainers/>`__
   provide similar features for Java integration tests, so if you have a
   Java project use the Exasol Testcontainer, because they are more
   integrated in the Java ecosystem than this project. Testcontainers
   are designed to integrate with popular unit testing frameworks like
   `JUnit4 <https://www.testcontainers.org/test_framework_integration/junit_4/>`__,
   `JUnit5 <https://www.testcontainers.org/test_framework_integration/junit_5/>`__
   and
   `Spock <https://www.testcontainers.org/test_framework_integration/spock/>`__.
   Most notably, lifecycle management of containers controlled by the
   tests lifecycle.

However, if you have a project in any other language you can use this
project to start a test Exasol database via a command line interface.
And if you have a Python project, you also have the possibility to start
the additional test-container, which is started in the same docker
network as the database.

Prerequisites
-------------

In order to start a Docker-DB Test Environment, you need:

-  Tested Operating System:

   -  Linux
   -  Mac OS X with `Docker Desktop on
      Mac <https://docs.docker.com/docker-for-mac/install/>`__ and Intel
      processor
   -  Windows is currently **not supported**

-  Docker with privileged mode
-  At least 2 GiB RAM
-  We recommend at least 15 GB free disk space on the partition where
   Docker stores its images and containers. On Linux Docker typically
   stores the images under ``/var/lib/docker``.

Getting started
---------------

Clone the repository

::

   git clone https://github.com/exasol/integration-test-docker-environment

Starting the test environment:

::

   ./start-test-env spawn-test-environment --environment-name <NAME>

or if you work on the code of the Test Environment (requires Python
>=3.8 with `poetry <https://python-poetry.org/>`__):

::

   ./start-test-env-with-poetry spawn-test-environment --environment-name <NAME>

Shutdown of the test environment is currently done manual.

Options
~~~~~~~

The following options are available to customize the test environment.

::

   Usage: main.py spawn-test-environment [OPTIONS]

     This command spawn a test environment with a docker-db container.

   Options:
     --environment-name TEXT         Name of the docker environment. This name
                                     gets used as suffix for the container
                                     db_container_<name> and
                                     test_container_<name>  [required]

     --database-port-forward INTEGER
                                     Host port to which the database port gets
                                     forwarded

     --bucketfs-port-forward INTEGER
                                     Host port to which the BucketFS port gets
                                     forwarded

     --ssh-port-forward INTEGER
                                     Host port to which the SSH port gets
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

     --nameserver TEXT               Add a nameserver to the list of DNS
                                     nameservers which the docker-db should use
                                     for resolving domain names. You can repeat
                                     this option to add further nameservers.

     --docker-runtime TEXT           The docker runtime used to start all
                                     containers

     --docker-db-image-version TEXT  Docker DB Image Version against which the
                                     tests should run.  [default: 7.1.17]

     --docker-db-image-name TEXT     Docker DB Image Name against which the tests
                                     should run.  [default: exasol/docker-db]

     --db-os-access METHOD           How to access file system and command
                                     line of the database operating
                                     system. Experimental option, will show no
                                     effect until implementation of feature
                                     SSH access is completed. [default:
                                     DOCKER_EXEC]

     --output-directory DIRECTORY    Output directory where the system stores all
                                     output and log files.  [default:
                                     .build_output]

     --temporary-base-directory DIRECTORY
                                     Directory where the system creates temporary
                                     directories.  [default: /tmp]

You can look at them on the commandline with:

::

   ./start-test-env spawn-test-environment --help

The integration-test-docker-environment command line tool
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Besides, the already mentioned command ``spawn-test-environment``, the
integration-test-docker-environemnt command line tool provides a couple
of other helpful tools.

Run ``main.py --help``, to get a list of the available commands:

.. code:: console

   Usage: main.py [OPTIONS] COMMAND [ARGS]...

   Options:
     --help  Show this message and exit.

   Commands:
     health                  Check the health of the execution environment.
     spawn-test-environment  This command spawn a test environment with a...

To get more details on a specific command run
``main.py <command> --help``, e.g. \ ``main.py health --help``:

.. code:: console

   Usage: main.py health [OPTIONS]

     Check the health of the execution environment.

     If no issues have been found, using the library or executing the test should
     work just fine. For all found issues there will be a proposed fix/solution.

     If the environment was found to be healthy the exit code will be 0.

   Options:
     --help  Show this message and exit.

The integration-test-docker-environment API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

t.b.d. *Link to sphinx documentation*

Default Credentials
~~~~~~~~~~~~~~~~~~~

The default credentials for the database are

-  User: ``sys``
-  Password: ``exasol``

and for the Bucket-FS:

-  User: ``w``
-  Password: ``write``

or

-  User: ``r``
-  Password: ``read``

Accessing the Environment Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The python setup script creates configuration files on the host and in
the test container.

On the host the container information get stored in the build output
directory usually under ``.build_output/cache/<ENVIRONMENT_NAME>/*``. In
the test container the config file is stored at the root directory
``/``.

The following config files are available:

-  environment_info.sh: This file is meant to be source by the bash and
   then provides the information as environment variables. Here an
   example for the content:

   ::

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

-  environment_info.json: Contains the EnvironmentInfo objects pickled
   with JsonPickle

Currently supported Exasol Versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **7.0**: up to 7.0.20 **except 7.0.5**
-  **7.1**: up to 7.1.15

If you need further versions, please open an issue.


SSH Access
""""""""""

Up to version 1.6.0 ITDE used ``docker_exec`` to access the operating system
of the Exasol database inside the Docker Container, e.g. to analyze the
content of logfiles or execute some shell commands. With version 8 of Exasol
database the format of the Docker Containers might change so that
``docker_exec`` is no longer possible. Instead ITDE will then need to use SSH
access.

You can select the access method with command line option
``--db-os-access``. The default value is ``DOCKER_EXEC``.

ITDE will create a random SSH key pair and store it to the file
``~/.cache/exasol/itde/id_rsa`` with access permissions limited to the current
user only. By this ITDE enables to reuse the same SSH keys for future sessions
which leaves the container unchanged and hence reusable.

The public key will be added as file ``/root/.ssh/authorized_keys`` inside the
Docker Container to enable SSH access with public key authentication.


Tested Docker Runtimes
~~~~~~~~~~~~~~~~~~~~~~

-  Docker Default Runtime
-  `NVIDIA Container
   Runtime <https://github.com/NVIDIA/nvidia-container-runtime>`__ for
   GPU accelerated UDFs

Mac OS X Support
----------------

What do I need to do to start the Test Environment with Mac OS X
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Exasol Docker-DB needs per default a bit more than 2 GB of RAM,
however the Docker VM on Mac OS X provides often not enough RAM to
accommodate this. You should increase the RAM of the Docker VM to at
least 4.25 GB or reduce the DB Mem Size for the Exasol Docker-DB to less
than 2 GB with ``--db-mem-size 1 GiB``.

What happens under the hood
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Mac OS X with Docker Desktop for Mac uses a lightweight virtual machine
with linux in which the docker daemon runs and the containers get
started. This makes
`networking <https://docs.docker.com/docker-for-mac/networking/>`__ and
`shared directories <https://docs.docker.com/docker-for-mac/osxfs/>`__
more complicated then on Linux.

We start the python setup script for the test environment in its own
Docker container, lets call it ``docker runner``, because the library
`Luigi <https://luigi.readthedocs.io/en/stable/>`__ can have problems
with Mac OS X and to avoid the installation of further dependencies. To
support Mac OS X, the ``start-test-env`` script starts the
``docker runner`` container and mounts the docker socket at
``/var/run/docker.sock`` and the directory of the test environment from
the Mac OS X host to the container. Then, it starts
``start-test-env-without-docker`` which then starts the python script.
It is important, that the repository gets cloned to the Mac OS X host
and not to a docker container, because the python scripts tries to start
further docker container which use host mounts to share the tests
directory of the test environment with the docker container.

.. toctree::
   :maxdepth: 1
