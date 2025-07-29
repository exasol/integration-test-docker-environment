from exasol_integration_test_docker_environment.lib.base.info import Info


class RequiredTaskInfo(Info):
    def __init__(self, module_name: str, class_name: str, params: dict) -> None:
        self.params = params
        self.class_name = class_name
        self.module_name = module_name


class RequiredTaskInfoDict:
    def __init__(self, infos: dict[str, RequiredTaskInfo]) -> None:
        self.infos = infos
