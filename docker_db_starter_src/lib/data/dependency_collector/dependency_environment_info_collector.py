from typing import Dict

from docker_db_starter_src.lib.data.dependency_collector.dependency_collector import DependencyInfoCollector
from docker_db_starter_src.lib.data.environment_info import EnvironmentInfo


class DependencyEnvironmentInfoCollector(DependencyInfoCollector[EnvironmentInfo]):

    def is_info(self, input):
        return isinstance(input, Dict) and ENVIRONMENT_INFO in input

    def read_info(self, value) -> EnvironmentInfo:
        with value[ENVIRONMENT_INFO].open("r") as file:
            return EnvironmentInfo.from_json(file.read())


ENVIRONMENT_INFO = "environment_info"
