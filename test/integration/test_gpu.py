import ssl
from inspect import cleandoc

import pyexasol
import pytest

from exasol_integration_test_docker_environment.lib.docker import ContextDockerClient


@pytest.mark.gpu
def test_gpu(cli_context):

    query_accelerator_parameters = cleandoc(
        f"""
            SELECT PARAM_VALUE, PARAM_NAME FROM EXA_METADATA 
            WHERE PARAM_NAME IN ('acceleratorDeviceDetected', 'acceleratorDeviceGpuNvidiaDetected') 
            ORDER BY PARAM_NAME;
            """
    )
    additional_param = [
        "--docker-runtime",
        "nvidia",
        "--docker-environment-variable",
        "NVIDIA_VISIBLE_DEVICES=all",
        "--additional-db-parameter",
        "-enableAcceleratorDeviceDetection=1",
    ]
    with cli_context(name="test_gpu", additional_parameters=additional_param) as db:
        host_name = db.on_host_docker_environment.database_host
        with ContextDockerClient() as docker_client:
            db_container = docker_client.containers.get(
                db.on_host_docker_environment.environment_info.database_info.container_info.container_name
            )
            print("--------------------Printing docker logs----------------------------")
            for line in db_container.logs(stream=True, stdout=True, stderr=True):
                print(line.decode())
            print("--------------------Finished printing docker logs----------------------------")

        port = db.on_host_docker_environment.ports.database
        dsn = f"{host_name}:{port}"
        connection = pyexasol.connect(
            dsn=dsn,
            user="sys",
            password="exasol",
            websocket_sslopt={"cert_reqs": ssl.CERT_NONE},
        )
        result = connection.execute(query_accelerator_parameters).fetchall()
        assert result == [
            ("1", "acceleratorDeviceDetected"),
            ("1", "acceleratorDeviceGpuNvidiaDetected"),
        ]
