"""Explicit ConfD-client execution through Docker exec integration scenario."""


def test_confd_client_docker_exec(confd_client_docker_exec_executor):
    """The Docker-exec command executor runs the read-only ConfD operation."""
    with confd_client_docker_exec_executor() as executor:
        result = executor.exec("confd_client -c db_list -j")

    assert result.exit_code == 0
    assert result.output
