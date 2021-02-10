import shutil
import time
import unittest
from datetime import datetime

import luigi
from luigi import Parameter, Config

from exasol_integration_test_docker_environment.lib.base.dependency_logger_base_task import DependencyLoggerBaseTask
from exasol_integration_test_docker_environment.lib.base.json_pickle_parameter import JsonPickleParameter

TestBaseTask = DependencyLoggerBaseTask


class TestTask1(TestBaseTask):
    def register_required(self):
        self.task2 = self.register_dependency(TestTask2())

    def run_task(self):
        self.logger.info("RUN")
        self.logger.info(f"task2 list_outputs {self.task2.list_outputs()}")
        self.logger.info(f"task2 {self.task2.get_output()}")
        tasks_3 = yield from self.run_dependencies({
            "1": TestTask3(input_param="e"),
            "2": TestTask3(input_param="d"),
        })
        self.logger.info(f"""task3_1 {tasks_3["1"].get_output("output")}""")
        self.logger.info(f"""task3_2 {tasks_3["2"].get_output("output")}""")


class TestTask2(TestBaseTask):

    def run_task(self):
        self.logger.info("RUN")
        self.return_object([1, 2, 3, 4])


class TestTask3(TestBaseTask):
    input_param = Parameter()

    def run_task(self):
        self.logger.info(f"RUN {self.input_param}")
        self.return_object(name="output", object=["a", "b", self.input_param])


class TestTask4(TestBaseTask):

    def run_task(self):
        yield from self.run_dependencies([
            TestTask5(),
            TestTask6()])


class TestTask5(TestBaseTask):

    def run_task(self):
        raise Exception()


class TestTask6(TestBaseTask):

    def run_task(self):
        pass


class TestParameter(Config):
    test_parameter = Parameter()


class TestTask7(TestBaseTask, TestParameter):

    def register_required(self):
        task8 = self.create_child_task_with_common_params(TestTask8, new_parameter="new")
        self.task8_future = self.register_dependency(task8)

    def run_task(self):
        pass


class TestTask8(TestBaseTask, TestParameter):
    new_parameter = Parameter()

    def run_task(self):
        pass


class Data:
    def __init__(self, a1: int, a2: str):
        self.a2 = a2
        self.a1 = a1

    def __repr__(self):
        return str(self.__dict__)


class Data1:
    pass


class TestTask9_Success(TestBaseTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def register_required(self):
        inputs = [Data(i, f"{i}") for i in range(2)]
        tasks = [TestTask10(parameter_1=input) for input in inputs]
        self.register_dependencies(tasks)

    def run_task(self):
        yield from self.run_dependencies(TestTask10(parameter_1=Data(3,"3")))


class TestTask10(TestBaseTask):
    parameter_1 = JsonPickleParameter(Data)

    def run_task(self):
        time.sleep(1)
        print(self.parameter_1)

class TestTask9_Fail(TestBaseTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def register_required(self):
        pass

    def run_task(self):
        yield from self.run_dependencies(TestTask10(parameter_1=Data1()))

class TestTask11(TestBaseTask):

    def run_task(self):
        tasks = [TestTask12(p=f"{i}") for i in range(10)]
        self.logger.info(tasks)
        yield from self.run_dependencies(tasks)


class TestTask12(TestBaseTask):
    p = Parameter()

    def run_task(self):
        self.logger.info("Start and wait")
        import time
        time.sleep(5)
        self.logger.info("Finished wait and fail")
        raise Exception("%s" % self.task_id)


class TestTask13(TestBaseTask):

    def register_required(self):
        tasks = [TestTask14(p=f"{i}") for i in range(10)]
        self.register_dependencies(tasks)

    def run_task(self):
        pass


class TestTask14(TestBaseTask):
    p = Parameter()

    def register_required(self):
        self.register_dependency(TestTask15())

    def run_task(self):
        pass

class TestTask15(TestBaseTask):
    def run_task(self):
        raise Exception("%s" % self.task_id)


class BaseTaskTest(unittest.TestCase):

    def set_job_id(self, task_cls):
        strftime = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        job_id = f"{strftime}_{task_cls.__name__}"
        config = luigi.configuration.get_config()
        config.set('job_config', 'job_id', job_id)
        # config.reload()

    def test_dependency_creation(self):
        self.set_job_id(TestTask1)
        task = TestTask1()
        luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
        if task._get_tmp_path_for_job().exists():
            shutil.rmtree(str(task._get_tmp_path_for_job()))

    def test_failing_task(self):
        self.set_job_id(TestTask4)
        task = TestTask4()
        luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
        if task._get_tmp_path_for_job().exists():
            shutil.rmtree(str(task._get_tmp_path_for_job()))

    def test_common_parameter(self):
        self.set_job_id(TestTask7)
        task = TestTask7(test_parameter="input")
        luigi.build([task], workers=1, local_scheduler=True, log_level="INFO")
        if task._get_tmp_path_for_job().exists():
            shutil.rmtree(str(task._get_tmp_path_for_job()))

    def test_json_pickle_parameter_success(self):
        self.set_job_id(TestTask9_Success)
        task = TestTask9_Success()
        try:
            luigi.build([task], workers=3, local_scheduler=True, log_level="INFO")
        finally:
            if task._get_tmp_path_for_job().exists():
                shutil.rmtree(str(task._get_tmp_path_for_job()))
    
    def test_json_pickle_parameter_fail(self):
        self.set_job_id(TestTask9_Fail)
        task = TestTask9_Fail()
        try:
            with self.assertRaises(Exception) as context:
                luigi.build([task], workers=3, local_scheduler=True, log_level="INFO")
            print(context.exception)
        finally:
            if task._get_tmp_path_for_job().exists():
                shutil.rmtree(str(task._get_tmp_path_for_job()))

    def test_collect_failures_diffrent_task_fail(self):
        self.set_job_id(TestTask11)
        task = TestTask11()
        try:
            luigi.build([task], workers=5, local_scheduler=True, log_level="INFO")
            failures = task.collect_failures()
            print()
            print("Collected Failures:")
            for failure in failures:
                print(failure)
                print()
            print()
            self.assertGreater(len(failures), 1)
        finally:
            if task._get_tmp_path_for_job().exists():
                shutil.rmtree(str(task._get_tmp_path_for_job()))

    def test_collect_failures_one_task_fails_but_is_dependency_of_multiple(self):
        self.set_job_id(TestTask13)
        task = TestTask13()
        try:
            luigi.build([task], workers=3, local_scheduler=True, log_level="INFO")
            failures = task.collect_failures()
            print()
            print("Collected Failures:")
            for failure in failures:
                print(failure)
                print()
            print()
            self.assertEquals(len(failures), 1)
        finally:
            if task._get_tmp_path_for_job().exists():
                shutil.rmtree(str(task._get_tmp_path_for_job()))

if __name__ == '__main__':
    unittest.main()
