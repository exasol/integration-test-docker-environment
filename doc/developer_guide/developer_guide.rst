***************
Developer Guide
***************

In this developer guide we explain how you can build this project.

Install Poetry:

``sudo apt install python3-poetry``

Install the Git commit hooks:

``githooks/install.sh``

.. toctree::
   :maxdepth: 1

Creating a Release
*******************

Prerequisites
-------------

* Change log needs to be up to date
* Latest change log version needs to match project and package version
* Release tag needs to match package, changelog and project version

  For Example:
        * Tag: 0.4.0
        * Changelog: changes_0.4.0.md
        * \`poetry version -s\`: 0.4.0

Triggering the Release
----------------------
In order to trigger a release a new tag must be pushed to Github.
For further details see: `.github/workflows/release.yml`.


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