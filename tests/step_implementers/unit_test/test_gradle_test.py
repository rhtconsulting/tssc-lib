import os

from pip._internal.utils.temp_dir import TempDirectory

from src.ploigos_step_runner.step_implementers.unit_test.gradle_test import GradleTest
from tests.helpers.base_step_implementer_test_case import BaseStepImplementerTestCase
import xml.etree.ElementTree as ET


class BaseTestStepImplementerGradleTest(
    BaseStepImplementerTestCase
):
    def create_step_implementer(
        self,
        step_config={},
        workflow_result=None,
        parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=GradleTest,
            step_config=step_config,
            step_name='unit-test',
            implementer='GradleTest',
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

class TestStepImplementerGradleTest__get_test_result(
    BaseTestStepImplementerGradleTest
):
    def test_result(self):
        with TempDirectory() as test_dir:
            # setup test
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            step_config = {
                'test-reports-dir': '/mock/user-given/test-reports-dir'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            file = "tests/step_implementers/unit_test/TEST-org.acme.rest.json.gradle.AppTest.xml"
            tree = ET.parse(file)
            root = tree.getroot()
            self.assertEqual(step_implementer._get_test_result(root=root, attribute="tests"), "2")

class TestStepImplementerGradleTest__get_test_results_from_file(
    BaseTestStepImplementerGradleTest
):
    def test_result(self):
        with TempDirectory() as test_dir:
            # setup test
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            step_config = {
                'test-reports-dir': '/mock/user-given/test-reports-dir'
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            file = "tests/step_implementers/unit_test/TEST-org.acme.rest.json.gradle.AppTest.xml"
            expected_results = {'time': '0.192', 'tests': '2', 'failures': '0', 'errors': '0', 'skipped': '0'}
            self.assertEqual(step_implementer._get_test_results_from_file(file=file, attributes=step_implementer.TEST_RESULTS_ATTRIBUTES), expected_results)
