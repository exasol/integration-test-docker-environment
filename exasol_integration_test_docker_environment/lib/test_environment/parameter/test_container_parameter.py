from luigi.parameter import ParameterVisibility

from exasol_integration_test_docker_environment.lib.base.json_pickle_parameter import JsonPickleParameter
from exasol_integration_test_docker_environment.lib.data.test_container_content_description import \
    TestContainerContentDescription


class TestContainerParameter:
    test_container_content = JsonPickleParameter(TestContainerContentDescription,
                                                 visibility=ParameterVisibility.HIDDEN)


class OptionalTestContainerParameter:
    test_container_content = JsonPickleParameter(TestContainerContentDescription,
                                                 visibility=ParameterVisibility.HIDDEN,
                                                 is_optional=True)
