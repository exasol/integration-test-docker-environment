# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['exasol_integration_test_docker_environment',
 'exasol_integration_test_docker_environment.cli',
 'exasol_integration_test_docker_environment.cli.commands',
 'exasol_integration_test_docker_environment.cli.options',
 'exasol_integration_test_docker_environment.lib',
 'exasol_integration_test_docker_environment.lib.base',
 'exasol_integration_test_docker_environment.lib.config',
 'exasol_integration_test_docker_environment.lib.data',
 'exasol_integration_test_docker_environment.lib.docker',
 'exasol_integration_test_docker_environment.lib.docker.images',
 'exasol_integration_test_docker_environment.lib.docker.images.create',
 'exasol_integration_test_docker_environment.lib.docker.images.create.utils',
 'exasol_integration_test_docker_environment.lib.docker.images.push',
 'exasol_integration_test_docker_environment.lib.docker.images.save',
 'exasol_integration_test_docker_environment.lib.logging',
 'exasol_integration_test_docker_environment.lib.test_environment',
 'exasol_integration_test_docker_environment.lib.test_environment.database_setup',
 'exasol_integration_test_docker_environment.lib.test_environment.database_waiters',
 'exasol_integration_test_docker_environment.lib.test_environment.parameter',
 'exasol_integration_test_docker_environment.test']

package_data = \
{'': ['*'],
 'exasol_integration_test_docker_environment': ['docker_db_config/6.0.12/*',
                                                'docker_db_config/6.0.13/*',
                                                'docker_db_config/6.0.16/*',
                                                'docker_db_config/6.1.1/*',
                                                'docker_db_config/6.1.10/*',
                                                'docker_db_config/6.1.11/*',
                                                'docker_db_config/6.1.6/*',
                                                'docker_db_config/6.1.7/*',
                                                'docker_db_config/6.1.8/*',
                                                'docker_db_config/6.1.9/*',
                                                'docker_db_config/6.1/*',
                                                'docker_db_config/6.2.0/*',
                                                'docker_db_config/6.2.1/*',
                                                'docker_db_config/6.2.3/*',
                                                'docker_db_config/6.2.4/*',
                                                'docker_db_config/6.2.5/*',
                                                'docker_db_config/6.2.6/*',
                                                'docker_db_config/6.2.7/*',
                                                'docker_db_config/6.2.8/*',
                                                'docker_db_config/6.2.9/*',
                                                'docker_db_config/6.2/*',
                                                'docker_db_config/7.0.0/*',
                                                'docker_db_config/7.0.1/*']}

install_requires = \
['click>=7.0',
 'docker>=4.0.0',
 'gitpython>=2.1.0',
 'humanfriendly>=4.18',
 'jinja2>=2.10.1',
 'jsonpickle>=1.1',
 'luigi>=2.8.4',
 'netaddr>=0.7.19',
 'networkx>=2.3',
 'pydot>=1.4.0',
 'requests>=2.21.0',
 'simplejson>=3.16.0',
 'stopwatch.py>=1.0.0']

setup_kwargs = {
    'name': 'exasol-integration-test-docker-environment',
    'version': '0.1.0',
    'description': 'Integration Test Docker Environment for Exasol',
    'long_description': '# Integration Test Docker Environment\n\n## About\n\nThis project provides a command line interface to start a test environment with an [Exasol Docker-DB](https://hub.docker.com/r/exasol/docker-db). It starts an Exasol Docker-DB container and an associated test container where [EXAPlus CLI](https://docs.exasol.com/connect_exasol/sql_clients/exaplus_cli/exaplus_cli.htm) and  the [Exasol ODBC driver](https://docs.exasol.com/connect_exasol/drivers/odbc.htm) are already installed.\n\nBoth containers exist in the same Docker network. This allows you to connect from the test container to the Docker-DB container. Furthermore, the database gets populated with some test data. You can find the test data under `tests/test/enginedb_small/import.sql`. Besides the test container, you can also access the Exasol database and the Bucket-FS from the host via forwarded ports.\n\n### Comparison to Docker-DB and the Exasol Testcontainers\n\n* This project uses the [Docker-DB](https://hub.docker.com/r/exasol/docker-db), but it does the configuration, setup and startup for you. For example, it waits until the Database and the Bucket-FS accept connections. It also populates the database with test data and provides with the test container as an environment to access the database.\n* The [Exasol Testcontainers](https://github.com/exasol/exasol-testcontainers/) provide similar features for Java integration tests, so if you have an Java project use the Exasol Testcontainer, because they are more integrated in the Java ecosystem then this project. Testcontainers are designed to integrate with popular unit testing frameworks like [JUnit4](https://www.testcontainers.org/test_framework_integration/junit_4/), [JUnit5](https://www.testcontainers.org/test_framework_integration/junit_5/) and [Spock](https://www.testcontainers.org/test_framework_integration/spock/). Most notably, lifecycle management of containers controlled by the tests lifecycle.\n\nHowever, if you have a project in any other language you can use this project to start a test Exasol database via a command line interface.\n\n## Prerequisites\n\nIn order to start a Docker-DB Test Environment, you need:\n\n* Tested Operating System:\n  * Linux\n  * Mac OS X with [Docker Desktop on Mac](https://docs.docker.com/docker-for-mac/install/) and Intel processor\n  * Windows is currently **not supported**\n* Docker with privileged mode\n* At least 2 GiB RAM\n* We recommend at least 15 GB free disk space on the partition \n  where Docker stores its images and containers. On Linux Docker typically stores \n  the images under `/var/lib/docker`.\n\n## Getting started\n\nClone the repository\n\n```\ngit clone https://github.com/exasol/integration-test-docker-environment\n```\n\nStarting the test environment:\n\n```\n./start-test-env spawn-test-environment --environment-name <NAME>\n```\nor if you work on the code of the Test Environment (requires Python >=3.6 with pip):\n\n```\n./start-test-env-without-docker-runner spawn-test-environment --environment-name <NAME>\n```\n\nShutdown of the test environment is currently done manual.\n\n### Options\n\nThe following options are available to customize the test environment. \n\n```\nUsage: main.py spawn-test-environment [OPTIONS]\n\n  This command spawn a test environment with a docker-db container and a\n  connected test-container. The test-container is reachable by the database\n  for output redirects of UDFs.\n\nOptions:\n  --environment-name TEXT         Name of the docker environment. This name\n                                  gets used as suffix for the container\n                                  db_container_<name> and\n                                  test_container_<name>  [required]\n\n  --database-port-forward INTEGER\n                                  Host port to which the database port gets\n                                  forwarded\n\n  --bucketfs-port-forward INTEGER\n                                  Host port to which the bucketfs port gets\n                                  forwarded\n\n  --db-mem-size TEXT              The main memory used by the database. Format\n                                  <number> <unit>, e.g. 1 GiB. The minimum\n                                  size is 1 GB, below that the database will\n                                  not start.  [default: 2 GiB]\n\n  --db-disk-size TEXT             The disk size available for the database.\n                                  Format <number> <unit>, e.g. 1 GiB. The\n                                  minimum size is 100 MiB. However, the setup\n                                  creates volume files with at least 2 GB\n                                  larger size, because the database needs at\n                                  least so much more disk.  [default: 2 GiB]\n\n  --deactivate-database-setup / --no-deactivate-database-setup\n                                  Deactivates the setup of the spawned\n                                  database, this means no data get populated\n                                  and no jdbc drivers get uploaded. This can\n                                  be used either to save time or as a\n                                  workaround for MacOSX where the\n                                  test_container seems not to be able to\n                                  access the tests directory  [default: False]\n\n  --docker-runtime TEXT           The docker runtime used to start all\n                                  containers\n\n  --docker-db-image-version TEXT  Docker DB Image Version against which the\n                                  tests should run.  [default: 6.2.6-d1]\n\n  --docker-db-image-name TEXT     Docker DB Image Name against which the tests\n                                  should run.  [default: exasol/docker-db]\n```\n\nYou can look at them on the commandline with:\n\n```\n./start-test-env spawn-test-environment --help \n```\n\n### Default Credentials\n\nThe default credentials for the database are\n\n  * User: `sys`\n  * Password: `exasol`\n  \nand for the Bucket-FS:\n\n  * User: `w`\n  * Password: `write`\n  \nor\n\n  * User: `r`\n  * Password: `read`\n\n### Accessing the Environment Information\n\nThe python setup script creates configuration files on the host and in the test container.\n\nOn the host the container information get stored in the build output directory usually under `.build_output/cache/<ENVIRONMENT_NAME>/*`. In the test container the config file is stored at the root directory `/`.\n\nThe following config files are available:\n\n- environment_info.sh: This file is meant to be source by the bash and then provides the information as environment variables. Here an example for the content:\n\n  ```\n  export ENVIRONMENT_NAME=test\n  export ENVIRONMENT_TYPE=EnvironmentType.docker_db\n\n  # Database IP in environment docker network\n  export ENVIRONMENT_DATABASE_HOST=172.21.0.2\n  export ENVIRONMENT_DATABASE_DB_PORT=8888\n  export ENVIRONMENT_DATABASE_BUCKETFS_PORT=6583\n  export ENVIRONMENT_DATABASE_CONTAINER_NAME=db_container_test\n  export ENVIRONMENT_DATABASE_CONTAINER_NETWORK_ALIASES="exasol_test_database db_container_test"\n  # Database IP in the environment docker network\n  export ENVIRONMENT_DATABASE_CONTAINER_IP_ADDRESS=172.21.0.2\n  export ENVIRONMENT_DATABASE_CONTAINER_VOLUMNE_NAME=db_container_test_volume\n  # Database IP on the docker default bridge which under Linux available from the host\n  export ENVIRONMENT_DATABASE_CONTAINER_DEFAULT_BRIDGE_IP_ADDRESS=172.17.0.3\n\n  export ENVIRONMENT_TEST_CONTAINER_NAME=test_container_test\n  export ENVIRONMENT_TEST_CONTAINER_NETWORK_ALIASES="test_container test_container_test"\n  # Test Container IP in the environment docker network\n  export ENVIRONMENT_TEST_CONTAINER_IP_ADDRESS=172.21.0.3\n  ```\n- environment_info.json: Contains the EnvironmentInfo objects pickled with JsonPickle\n  \n### Currently supported Exasol Versions\n\n* **6.0**: 6.0.12, 6.0.13, 6.0.16\n* **6.1**: 6.1.1, 6.1.6, 6.1.7, 6.1.8, 6.1.9, 6.1.10, 6.1.11\n* **6.2**: 6.2.4, 6.2.0, 6.2.1, 6.2.3, 6.2.5, 6.2.6, 6.2.7, 6.2.8, 6.2.9\n* **7.0**: 7.0.0, 7.0.1\n\nIf you need further versions, please open an issue.\n\n### Tested Docker Runtimes\n\n- Docker Default Runtime\n- [NVIDIA Container Runtime](https://github.com/NVIDIA/nvidia-container-runtime) for GPU accelerated UDFs\n\n## Mac OS X Support\n\n### What do I need to do to start the Test Environment with Mac OS X\n\nThe Exasol Docker-DB needs per default a bit more than 2 GB of RAM, however the Docker VM on Mac OS X provides often not enough RAM to accommodate this. You should increase the RAM of the Docker VM to at least 4.25 GB or reduce the DB Mem Size for the Exasol Docker-DB to less than 2 GB with `--db-mem-size 1 GiB`.\n\n### What happens under the hood\n\nMac OS X with Docker Desktop for Mac uses a lightweight virtual machine with linux in which the docker daemon runs and the containers get started. This makes [networking](https://docs.docker.com/docker-for-mac/networking/) and [shared directories](https://docs.docker.com/docker-for-mac/osxfs/) more complicated then on Linux.\n\nWe start the python setup script for the test environment in its own Docker container, lets call it `docker runner`, because the library [Luigi](https://luigi.readthedocs.io/en/stable/) can have problems with Mac OS X and to avoid the installation of further dependencies. To support Mac OS X, the `start-test-env` script starts the `docker runner` container and mounts the docker socket at `/var/run/docker.sock` and the directory of the test environment from the Mac OS X host to the container. Then, it starts `start-test-env-without-docker` which then starts the python script. It is important, that the repository gets cloned to the Mac OS X host and not to a docker container, because the python scripts tries to start further docker container which use host mounts to share the tests directory of the test environment with the docker container.\n',
    'author': 'Torsten Kilias',
    'author_email': 'torsten.kilias@exasol.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/exasol/integration-test-docker-environment',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.6',
}


setup(**setup_kwargs)