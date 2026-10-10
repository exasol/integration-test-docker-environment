"""Explicit ConfD-client execution through Docker exec integration scenario."""

from shlex import quote


def test_confd_client_docker_exec(confd_client_docker_exec_executor):
    """The Docker-exec command executor runs the read-only ConfD operation."""
    command = (
        'export COS_DIRECTORY="$(dirname "$(dirname "$(command -v confd_client)")")"; '
        "exec confd_client -c db_list -j"
    )
    with confd_client_docker_exec_executor() as executor:
        result = executor.exec(f"/bin/sh -c {quote(command)}")

    assert result.exit_code == 0
    assert result.output
