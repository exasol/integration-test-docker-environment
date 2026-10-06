from test.integration.helpers import container_named


def test_docker_exec_fixture_does_not_publish_ssh_port(api_context):
    with api_context() as db:
        container_name = db.environment_info.database_info.container_info.container_name
        with container_named(container_name) as container:
            assert container is not None
            container.reload()
            assert container.attrs["NetworkSettings"]["Ports"].get("22/tcp") is None
