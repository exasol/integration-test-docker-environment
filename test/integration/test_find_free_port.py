
import pytest

from exasol_integration_test_docker_environment.lib.test_environment.ports import (
    find_free_ports,
)


@pytest.mark.parametrize("num_ports", [1, 2, 100, 1000])
def test_find_ports(num_ports):
    ports = find_free_ports(num_ports)
    assert not 0 in ports
    assert len(ports) == num_ports
    # Check that there are no duplicates!
    ports_set = set(ports)
    assert len(ports) == len(ports_set)
