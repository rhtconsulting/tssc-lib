import os
from unittest.mock import patch

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

@patch.object(GradleTest, '_run_gradle_step')
@patch.object(GradleTest, 'write_working_file', return_value='/mock/gradle_output.txt')
@patch.object(GradleTest, '_GradleTest__get_test_report_dirs', return_value='/mock/test-results-dir')
class TestStepImplementerGradleTest__get_test_result(
    BaseTestStepImplementerGradleTest
):
    def test_success_with_report_dir(
        self,
        mock_gather_evidence,
        mock_get_test_report_dir,
        mock_write_working_file,
        mock_run_gradle_step
    ):
        with TempDirectory() as test_dir:
            # setup test
            parent_work_dir_path = os.path.join(test_dir.path, 'working')
            build_file = os.path.join(test_dir.path, 'mock-build-file.xml')
            step_config = {
                'build-file': build_file
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                parent_work_dir_path=parent_work_dir_path,
            )

            # run test
            actual_step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='unit-test',
                sub_step_name='GradleTest',
                sub_step_implementer_name='GradleTest'
            )
            expected_step_result.add_artifact(
                description="Standard out and standard error from gradle.",
                name='maven-output',
                value='/mock/gradle_output.txt'
            )
            expected_step_result.add_artifact(
                description="Test report generated when running unit tests.",
                name='test-report',
                value='/mock/test-results-dir'
            )
            self.assertEqual(actual_step_result, expected_step_result)

            mock_run_maven_step.assert_called_once_with(
                mvn_output_file_path='/mock/gradle_output.txt'
            )
            mock_gather_evidence.assert_called_once_with(
                step_result=Any(StepResult),
                test_report_dirs='/mock/test-results-dir'                                                                    
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

class TestStepImplementerGradleTest__get_missing_required_test_attributes(
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

            test_results = {'time': '0.192', 'errors': '0', 'skipped': '0'}
            expected_results = ['tests', 'failures']
            self.assertEqual(step_implementer._get_missing_required_test_attributes(test_results, step_implementer.TEST_RESULTS_ATTRIBUTES_REQUIRED), expected_results)

class TestStepImplementerGradleTest__get_dict_with_keys_from_list(
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

            expected_results = {'time': 0, 'tests': 0, 'failures': 0, 'errors': 0, 'skipped': 0}
            self.assertEqual(step_implementer._get_dict_with_keys_from_list(step_implementer.TEST_RESULTS_ATTRIBUTES), expected_results)
        
class TestStepImplementerGradleTest__combine_test_results(
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

            current_results = {'time': '0.20', 'tests': '2', 'failures': '0', 'errors': '1', 'skipped': '0'}
            total_results = {'time': '5.00', 'tests': '10', 'failures': '2', 'errors': '1', 'skipped': '1'}
            end_results = {'time': 5.2, 'tests': 12, 'failures': 2, 'errors': 2, 'skipped': 1}
            self.assertEqual(step_implementer._combine_test_results(total_results, current_results), end_results)
