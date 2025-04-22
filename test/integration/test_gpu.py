from inspect import cleandoc

import pyexasol
import pytest


@pytest.mark.gpu
def test_gpu(cli_context):

    query_accelerator_parameters = cleandoc(
        f"""
            SELECT PARAM_VALUE, PARAM_NAME FROM EXA_METADATA 
            WHERE PARAM_NAME LIKE '%accelerator%' 
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
        port = db.on_host_docker_environment.ports.database
        dsn = f"{host_name}:{port}"
        connection = pyexasol.connect(dsn=dsn, user="sys", password="exasol")
        result = connection.execute(query_accelerator_parameters).fetchall()
        assert result == [
            ("1", "acceleratorDeviceDetected"),
            ("1", "acceleratorDeviceGpuNvidiaDetected"),
        ]
