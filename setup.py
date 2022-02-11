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
 'exasol_integration_test_docker_environment.lib.docker.images.clean',
 'exasol_integration_test_docker_environment.lib.docker.images.create',
 'exasol_integration_test_docker_environment.lib.docker.images.create.utils',
 'exasol_integration_test_docker_environment.lib.docker.images.push',
 'exasol_integration_test_docker_environment.lib.docker.images.save',
 'exasol_integration_test_docker_environment.lib.logging',
 'exasol_integration_test_docker_environment.lib.test_environment',
 'exasol_integration_test_docker_environment.lib.test_environment.database_setup',
 'exasol_integration_test_docker_environment.lib.test_environment.database_waiters',
 'exasol_integration_test_docker_environment.lib.test_environment.parameter',
 'exasol_integration_test_docker_environment.testing']

package_data = \
{'': ['*'],
 'exasol_integration_test_docker_environment': ['docker_db_config/7.0.0/*',
                                                'docker_db_config/7.0.1/*',
                                                'docker_db_config/7.0.10/*',
                                                'docker_db_config/7.0.11/*',
                                                'docker_db_config/7.0.12/*',
                                                'docker_db_config/7.0.13/*',
                                                'docker_db_config/7.0.14/*',
                                                'docker_db_config/7.0.15/*',
                                                'docker_db_config/7.0.2/*',
                                                'docker_db_config/7.0.3/*',
                                                'docker_db_config/7.0.4/*',
                                                'docker_db_config/7.0.6/*',
                                                'docker_db_config/7.0.7/*',
                                                'docker_db_config/7.0.8/*',
                                                'docker_db_config/7.0.9/*',
                                                'docker_db_config/7.1.0/*',
                                                'docker_db_config/7.1.1/*',
                                                'docker_db_config/7.1.2/*',
                                                'docker_db_config/7.1.3/*',
                                                'docker_db_config/7.1.4/*',
                                                'docker_db_config/7.1.5/*',
                                                'test_container_config/*']}

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
    'version': '0.9.0',
    'description': 'Integration Test Docker Environment for Exasol',
    'long_description': '# Deprecation Warning\nYou currently using the `master` references of the git repository, this reference is no longer maintained,\nplease switch to the `main` reference for the default branch.\n',
    'author': 'Torsten Kilias',
    'author_email': 'torsten.kilias@exasol.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/exasol/integration-test-docker-environment',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.6,<4',
}


setup(**setup_kwargs)
