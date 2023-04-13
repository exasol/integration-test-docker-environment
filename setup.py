# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['exasol_integration_test_docker_environment',
 'exasol_integration_test_docker_environment.cli',
 'exasol_integration_test_docker_environment.cli.commands',
 'exasol_integration_test_docker_environment.cli.options',
 'exasol_integration_test_docker_environment.lib',
 'exasol_integration_test_docker_environment.lib.api',
 'exasol_integration_test_docker_environment.lib.base',
 'exasol_integration_test_docker_environment.lib.config',
 'exasol_integration_test_docker_environment.lib.data',
 'exasol_integration_test_docker_environment.lib.docker',
 'exasol_integration_test_docker_environment.lib.docker.container',
 'exasol_integration_test_docker_environment.lib.docker.images',
 'exasol_integration_test_docker_environment.lib.docker.images.clean',
 'exasol_integration_test_docker_environment.lib.docker.images.create',
 'exasol_integration_test_docker_environment.lib.docker.images.create.utils',
 'exasol_integration_test_docker_environment.lib.docker.images.push',
 'exasol_integration_test_docker_environment.lib.docker.images.save',
 'exasol_integration_test_docker_environment.lib.docker.networks',
 'exasol_integration_test_docker_environment.lib.docker.volumes',
 'exasol_integration_test_docker_environment.lib.logging',
 'exasol_integration_test_docker_environment.lib.test_environment',
 'exasol_integration_test_docker_environment.lib.test_environment.create_certificates',
 'exasol_integration_test_docker_environment.lib.test_environment.database_setup',
 'exasol_integration_test_docker_environment.lib.test_environment.database_waiters',
 'exasol_integration_test_docker_environment.lib.test_environment.parameter',
 'exasol_integration_test_docker_environment.lib.utils',
 'exasol_integration_test_docker_environment.testing',
 'pytest_itde']

package_data = \
{'': ['*'],
 'exasol_integration_test_docker_environment': ['certificate_resources/*',
                                                'certificate_resources/container/*',
                                                'docker_db_config/7.0.0/*',
                                                'docker_db_config/7.0.1/*',
                                                'docker_db_config/7.0.10/*',
                                                'docker_db_config/7.0.11/*',
                                                'docker_db_config/7.0.12/*',
                                                'docker_db_config/7.0.13/*',
                                                'docker_db_config/7.0.14/*',
                                                'docker_db_config/7.0.15/*',
                                                'docker_db_config/7.0.16/*',
                                                'docker_db_config/7.0.17/*',
                                                'docker_db_config/7.0.18/*',
                                                'docker_db_config/7.0.19/*',
                                                'docker_db_config/7.0.2/*',
                                                'docker_db_config/7.0.20/*',
                                                'docker_db_config/7.0.3/*',
                                                'docker_db_config/7.0.4/*',
                                                'docker_db_config/7.0.6/*',
                                                'docker_db_config/7.0.7/*',
                                                'docker_db_config/7.0.8/*',
                                                'docker_db_config/7.0.9/*',
                                                'docker_db_config/7.1.0/*',
                                                'docker_db_config/7.1.1/*',
                                                'docker_db_config/7.1.10/*',
                                                'docker_db_config/7.1.11/*',
                                                'docker_db_config/7.1.12/*',
                                                'docker_db_config/7.1.13/*',
                                                'docker_db_config/7.1.14/*',
                                                'docker_db_config/7.1.15/*',
                                                'docker_db_config/7.1.16/*',
                                                'docker_db_config/7.1.17/*',
                                                'docker_db_config/7.1.2/*',
                                                'docker_db_config/7.1.3/*',
                                                'docker_db_config/7.1.4/*',
                                                'docker_db_config/7.1.5/*',
                                                'docker_db_config/7.1.6/*',
                                                'docker_db_config/7.1.7/*',
                                                'docker_db_config/7.1.8/*',
                                                'docker_db_config/7.1.9/*',
                                                'templates/*']}

install_requires = \
['click>=7.0',
 'exasol-bucketfs>=0.6.0,<2.0.0',
 'gitpython>=2.1.0',
 'humanfriendly>=4.18',
 'importlib_resources>=5.4.0',
 'jinja2>=2.10.1',
 'jsonpickle>=1.1',
 'luigi>=2.8.4',
 'netaddr>=0.7.19',
 'networkx>=2.3',
 'pydot>=1.4.0',
 'pyexasol>=0.25.2,<0.26.0',
 'pytest>=7.2.2,<8.0.0',
 'requests>=2.21.0',
 'simplejson>=3.16.0',
 'stopwatch.py>=1.0.0']

extras_require = \
{':sys_platform != "win32"': ['docker>=4.0.0']}

entry_points = \
{'console_scripts': ['itde = '
                     'exasol_integration_test_docker_environment.main:main'],
 'pytest11': ['itde = pytest_itde']}

setup_kwargs = {
    'name': 'exasol-integration-test-docker-environment',
    'version': '1.6.0',
    'description': 'Integration Test Docker Environment for Exasol',
    'long_description': 'Integration Test Docker Environment\n===================================\n\nThis project provides a command line interface and a Python API layer to\nstart a test environment with an `Exasol\nDocker-DB <https://hub.docker.com/r/exasol/docker-db>`_. Both start an\nExasol Docker-DB container, but the API Layer has extended functionality\nand also can start an associated test container for whose content the\nclient is responsible.\n\nDocumentation\n-------------\n\n`Documentation for the current main branch <https://exasol.github.io/integration-test-docker-environment/main>`_ is hosted on the Github Pages of this project.\n`Here <https://exasol.github.io/integration-test-docker-environment>`_  is a list of documentations for previous releases.\n',
    'author': 'Torsten Kilias',
    'author_email': 'torsten.kilias@exasol.com',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'https://github.com/exasol/integration-test-docker-environment',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'extras_require': extras_require,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4',
}


setup(**setup_kwargs)
