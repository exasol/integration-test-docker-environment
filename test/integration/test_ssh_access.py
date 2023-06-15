from exasol_integration_test_docker_environment.lib.base.ssh_access import SshKeyCache
from test.integration.helpers import container_named


def test_generate_ssh_key_file(api_database):
    params = { "db_os_access": "SSH" }
    with api_database(additional_parameters=params) as db:
        cache = SshKeyCache()
        container_name = db.environment_info.database_info.container_info.container_name
        with container_named(container_name) as container:
            command = container.exec_run("cat /root/.ssh/authorized_keys")
    assert cache.private_key.exists()
    " itde-ssh-access" in command[1].decode("utf-8")
