from inspect import cleandoc

import pytest


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
        "--gpu",
        "all",
        "--additional-db-parameter",
        "-enableAcceleratorDeviceDetection=1",
    ]
    with cli_context(name="test_gpu", additional_parameters=additional_param) as db:
        with db.on_host_docker_environment.create_connection() as connection:
            result = connection.execute(query_accelerator_parameters).fetchall()
            assert result == [
                ("1", "acceleratorDeviceDetected"),
                ("1", "acceleratorDeviceGpuNvidiaDetected"),
            ]
