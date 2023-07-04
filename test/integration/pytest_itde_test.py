import os
from inspect import cleandoc
from itertools import chain

import pytest

pytest_plugins = "pytester"


@pytest.fixture
def make_test_files():
    def make(pytester, files):
        pytester.makepyfile(**files)

    return make


def _ids(params):
    keys = (k for k in params.keys())
    return next(keys)


default_version = "8.18.1"
default_version_only=pytest.mark.skipif(
    "EXASOL_VERSION" in os.environ and os.environ["EXASOL_VERSION"] != default_version,
    reason="""This test always uses default version of Exasol database.  If
    the current run of a matrix build uses a different version then executing
    all tests requires to download two docker images in total.  For Exasol
    versions 8 and higher the size of the Docker Containers did drastically
    increase which in turn causes error "no space left on device" in the GitHub Action Runners.""",
)


@default_version_only
@pytest.mark.slow
@pytest.mark.parametrize(
    "files",
    [
        {
            "test_smoke_test": cleandoc(
                """
                def test_itde_smoke_test(itde):
                    # This smoke test just makes sure db spin up etc does not fail
                    assert True
                """
            )
        }], ids=_ids
)
def test_itde_smoke_test(make_test_files, pytester, files):
    make_test_files(pytester, files)
    result = pytester.runpytest()
    assert result.ret == pytest.ExitCode.OK


@default_version_only
@pytest.mark.parametrize(
    "files",
    [
        {
            "test_exasol_settings": cleandoc(
                """
    def test_default_settings_of_exasol(exasol_config):
        assert exasol_config.host == 'localhost'
        assert exasol_config.port == 8563
        assert exasol_config.username == 'SYS'
        assert exasol_config.password == 'exasol'
    """
            )
        },
        {
            "test_bucketfs_settings": cleandoc(
                """
    def test_default_settings_of_bucketfs(bucketfs_config):
        assert bucketfs_config.url == 'http://127.0.0.1:2580'
        assert bucketfs_config.username == 'w'
        assert bucketfs_config.password == 'write'
    """
            )
        },
        {
            "test_itde_settings": cleandoc(
                f"""
def test_default_settings_of_itde(itde_config):
    assert itde_config.db_version == '{default_version}'
    assert set(itde_config.schemas) == set(('TEST', 'TEST_SCHEMA'))
"""
            )
        },
    ],
    ids=_ids,
)
def test_default_settings_for_options(pytester, make_test_files, files):
    make_test_files(pytester, files)
    result = pytester.runpytest()
    assert result.ret == pytest.ExitCode.OK


@pytest.mark.parametrize(
    "files,cli_args",
    [
        (
                {
                    "test_exasol_settings": cleandoc(
                        """
        def test_default_settings_of_exasol(exasol_config):
            assert exasol_config.host == '127.0.0.1'
            assert exasol_config.port == 7777
            assert exasol_config.username == 'foo'
            assert exasol_config.password == 'bar'
        """
                    )
                },
                {
                    "--exasol-port": 7777,
                    "--exasol-host": "127.0.0.1",
                    "--exasol-username": "foo",
                    "--exasol-password": "bar",
                },
        ),
        (
                {
                    "test_bucketfs_settings": cleandoc(
                        """
        def test_default_settings_of_bucketfs(bucketfs_config):
            assert bucketfs_config.url == 'https://127.0.0.1:7777'
            assert bucketfs_config.username == 'user'
            assert bucketfs_config.password == 'pw'
        """
                    )
                },
                {
                    "--bucketfs-url": "https://127.0.0.1:7777",
                    "--bucketfs-username": "user",
                    "--bucketfs-password": "pw",
                },
        ),
        (
                {
                    "test_itde_settings": cleandoc(
                        """
    def test_default_settings_of_itde(itde_config):
        assert itde_config.db_version == '7.1.0'
        assert set(itde_config.schemas) == set(('TEST_FOO', 'TEST_BAR'))
    """
                    )
                },
                {"--itde-db-version": "7.1.0", "--itde-schemas": "TEST_FOO, TEST_BAR"},
        ),
    ],
    ids=_ids,
)
def test_pass_options_via_cli(pytester, make_test_files, files, cli_args):
    make_test_files(pytester, files)
    args = chain.from_iterable(cli_args.items())
    result = pytester.runpytest(*args)
    assert result.ret == pytest.ExitCode.OK
