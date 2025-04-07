***************
Developer Guide
***************

In this developer guide we explain how you can build this project.

Install Poetry:

``sudo apt install python3-poetry``

Install dependencies:
``poetry install``

Install the Git commit hooks:

``poetry run -- pre-commit install``

.. toctree::
   :maxdepth: 1

Creating a Release
*******************

Prerequisites
-------------

* Change log needs to be up to date
* ``unreleased`` change log version needs to be up-to-date
* Release tag needs to match package

  For Example:
        * Tag: 0.4.0
        * \`poetry version -s\`: 0.4.0

Preparing the Release
----------------------
Run the following nox task in order to prepare the changelog.

    .. code-block:: shell

        nox -s release:prepare

Triggering the Release
----------------------
In order to trigger a release a new tag must be pushed to Github.


#. Create a local tag with the appropriate version number

    .. code-block:: shell

        git tag x.y.z

#. Push the tag to Github

    .. code-block:: shell

        git push origin x.y.z

What to do if the release failed?
---------------------------------

The release failed during pre-release checks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Delete the local tag

    .. code-block:: shell

        git tag -d x.y.z

#. Delete the remote tag

    .. code-block:: shell

        git push --delete origin x.y.z

#. Fix the issue(s) which lead to the failing checks
#. Start the release process from the beginning


One of the release steps failed (Partial Release)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#. Check the Github action/workflow to see which steps failed
#. Finish or redo the failed release steps manually

.. note:: Example

    **Scenario**: Publishing of the release on Github was successfully but during the PyPi release, the upload step got interrupted.

    **Solution**: Manually push the package to PyPi

Running Tests
*************

You can execute all tests in a single file with the following command:

.. code-block:: shell

  poetry run -- python exasol_integration_test_docker_environment/test/test_cli_test_environment_db_mem_size.py

Some tests will use prebuilt Docker Containers.
After changing the implementation you might need to rebuild the container in order to make
your changes effective when executing the tests.

Please use the following command to rebuild the Docker Container:

.. code-block:: shell

  starter_scripts/build_docker_runner_image.sh

Configuring Tests
-----------------

ITDE supports tests with pytest although there currently are also tests using
``python.unittest`` mainly in directory
``exasol_integration_test_docker_environment/test``.  The plan is to migrate
all tests to pytest in directory ``test``

For pytest ITDE uses a pytest plugin in directory ``pytest_itde``. This plugin
enables to configure test execution, e.g. setting the hostname, user and
password of the database. For some configuration parameters there are also
default values.
