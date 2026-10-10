"""Explicit ConfD-client execution through SSH integration scenario."""


def test_confd_client_ssh(confd_client_ssh_executor):
    """The SSH command executor runs the read-only ConfD operation."""
    with confd_client_ssh_executor() as executor:
        _assert_confd_client_db_list(executor)


def _assert_confd_client_db_list(executor) -> None:
    result = executor.exec("confd_client -c db_list -j")
    assert result.exit_code == 0
    assert result.output
