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
   `JUnit4 <https://java.testcontainers.org/test_framework_integration/junit_4/>`__,
   `JUnit5 <https://java.testcontainers.org/test_framework_integration/junit_5/>`__
   and
   `Spock <https://java.testcontainers.org/test_framework_integration/spock/>`__.
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
      Mac <https://docs.docker.com/desktop/setup/install/mac-install/>`__ and Intel
      processor
   -  Windows is currently **not supported**

-  Docker with privileged mode
-  At least 2 GiB RAM
-  We recommend at least 15 GB free disk space on the partition where
   Docker stores its images and containers. On Linux Docker typically
   stores the images under ``/var/lib/docker``.


Getting started
---------------

Download the standalone executable ``itde_linux_x86-64``, for linux, from `release-page <https://github.com/exasol/integration-test-docker-environment/releases>`_ or install the package in your virtual environment using virtual environment via Pip or Pipx.

Pip via PyPi

::

   python3 -m pip install exasol-integration-test-docker-environment


or Pipx via PyPi

::

   pipx install exasol-integration-test-docker-environment

This way you can run it using standalone executable, ``./itde_linux_x86-64 spawn-test-environment --environment-name <NAME>`` or through the package, ``itde spawn-test-environment --environment-name <NAME>``

Starting the test environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Using the standalone executable, ``itde_linux_x86-64`` as follows

::

   ./itde_linux_x86-64 spawn-test-environment --environment-name <NAME>

or if you installed it via Pip or Pipx

::

   itde spawn-test-environment --environment-name <NAME>

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
      --ssh-port-forward INTEGER      Host port to which the SSH port gets
                                      forwarded. If not specified then ITDE
                                      selects a random free port.
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
                                      tests should run.  [default: 2025.1.3]
      --docker-db-image-name TEXT     Docker DB Image Name against which the tests
                                      should run.  [default: exasol/docker-db]
      --db-os-access METHOD           How to access file system and command line
                                      of the database operating system.
                                      Experimental option, will show no effect
                                      until implementation of feature SSH access
                                      is completed.  [default: DOCKER_EXEC]
      --create-certificates / --no-create-certificates
                                      Creates and injects SSL certificates to the
                                      Docker DB container.
      -p, --additional-db-parameter TEXT
                                      Additional database parameter which will be
                                      injected to EXAConf. Value should have
                                      format '-param=value'.
      --docker-environment-variable TEXT
                                      An environment variable which will be added
                                      to the docker-db. The variable needs to have
                                      format "key=value". For example
                                      "HTTPS_PROXY=192.168.1.5". You can repeat
                                      this option to add further environment
                                      variables.
      --accelerator TEXT              Configures the nvidia container toolkit to
                                      use the given GPU.  Currently only value
                                      'nvidia=all' is supported.  For 2025.1.x and
                                      later only
      --source-docker-repository-name TEXT
                                      Name of the docker repository for pulling
                                      cached stages. The repository name may
                                      contain the URL of the docker registry, the
                                      username and the actual repository name. A
                                      common structure is <docker-registry-
                                      url>/<username>/<repository-name>  [default:
                                      exasol/script-language-container]
      --source-docker-tag-prefix TEXT
                                      Prefix for the tags which are used for
                                      pulling of cached stages  [default: ""]
      --source-docker-username TEXT   Username for the docker registry from where
                                      the system pulls cached stages.
      --source-docker-password TEXT   Password for the docker registry from where
                                      the system pulls cached stages. Without
                                      password option the system prompts for the
                                      password.
      --target-docker-repository-name TEXT
                                      Name of the docker repository for naming and
                                      pushing images of stages. The repository
                                      name may contain the URL of the docker
                                      registry, the username and the actual
                                      repository name. A common structure is
                                      <docker-registry-
                                      url>/<username>/<repository-name>  [default:
                                      exasol/script-language-container]
      --target-docker-tag-prefix TEXT
                                      Prefix for the tags which are used for
                                      naming and pushing of stages  [default: ""]
      --target-docker-username TEXT   Username for the docker registry where the
                                      system pushes images of stages.
      --target-docker-password TEXT   Password for the docker registry where the
                                      system pushes images of stages. Without
                                      password option the system prompts for the
                                      password.
      --output-directory DIRECTORY    Output directory where the system stores all
                                      output and log files.  [default:
                                      .build_output]
      --temporary-base-directory DIRECTORY
                                      Directory where the system creates temporary
                                      directories.  [default: /tmp]
      --workers INTEGER               Number of parallel workers  [default: 5]
      --task-dependencies-dot-file PATH
                                      Path where to store the Task Dependency
                                      Graph as dot file
      --log-level [DEBUG|INFO|WARNING|ERROR|FATAL]
                                      Log level used for console logging
      --use-job-specific-log-file BOOLEAN
                                      Use a job specific log file which write the
                                      debug log to the job directory in the build
                                      directory


You can look at them on the commandline with:

::

   ./itde_linux_x86-64 spawn-test-environment --help
   # or
   itde spawn-test-environment --help

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
     environment             Displays the default configurations of the DB.
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

To get the details of default configurations run ``main.py environment --help``

.. code:: console

   Usage: itde environment [OPTIONS]

      Displays the default configurations of the DB.

      --show-default-db-version  Displays the defualt Docker DB Image version
      --show-default-mem-size    Displays the defualt DB mem size
      --show-default-disk-size   Displays the defualt DB disk size
      --help                     Show this message and exit.

   Eg: itde environment --show-default-db-version

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
directory usually under ``.build_output/cache/<ITDE_NAME>/*``. In
the test container the config file is stored at the root directory
``/``.

The following config files are available:

-  environment_info.sh: This file is meant to be source by the bash and
   then provides the information as environment variables. Here an
   example for the content:

   ::

      export ITDE_NAME=test
      export ITDE_TYPE=EnvironmentType.docker_db

      # Database IP in environment docker network
      export ITDE_DATABASE_HOST=172.21.0.2
      export ITDE_DATABASE_DB_PORT=8563
      export ITDE_DATABASE_BUCKETFS_PORT=2580
      export ITDE_DATABASE_SSH_PORT=22
      export ITDE_DATABASE_CONTAINER_NAME=db_container_test
      export ITDE_DATABASE_CONTAINER_NETWORK_ALIASES="exasol_test_database db_container_test"
      # Database IP in the environment docker network
      export ITDE_DATABASE_CONTAINER_IP_ADDRESS=172.21.0.2
      export ITDE_DATABASE_CONTAINER_VOLUMNE_NAME=db_container_test_volume
      # Database IP on the docker default bridge which under Linux available from the host
      export ITDE_DATABASE_CONTAINER_DEFAULT_BRIDGE_IP_ADDRESS=172.17.0.3

      export ITDE_TEST_CONTAINER_NAME=test_container_test
      export ITDE_TEST_CONTAINER_NETWORK_ALIASES="test_container test_container_test"
      # Test Container IP in the environment docker network
      export ITDE_TEST_CONTAINER_IP_ADDRESS=172.21.0.3

-  environment_info.json: Contains the EnvironmentInfo objects pickled
   with JsonPickle

Currently supported Exasol Versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  **7.1**: up to 7.1.29
-  **8**: from 8.17.0 up to 8.34
-  **2025**: 2025.1.3

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

You can use command line option ``--ssh-port-forward`` to specify a port on
your host machine to which ITDE forwards the SSH port of the Docker Container
running the Exasol database. If you do not specify a port then ITDE will
select a random free port.


Docker Runtimes
~~~~~~~~~~~~~~~

ITDE supports launching of the test environment with an alternate
docker runtime, via option ``--docker-runtime``.
The docker runtime is the software enabling containers to function within a
host environment.  It handles tasks ranging from retrieving container images
from a registry and managing their lifecycle to executing the containers on
your system.  See https://docs.docker.com/engine/daemon/alternative-runtimes/
for details.

GPU Usage
~~~~~~~~~

Use the flag `--accelerator="nvidia=all"` to activate all available NVidia GPUs in the docker db.
Additionaly, you need to set the respective db parameter using the `--additional-db-parameter` option, e.g.
.. code:: console

itde spawn-test-environment --environment-name my_env --accelerator="nvidia=all" --additional-db-parameter=-enableAcceleratorDeviceDetection=1