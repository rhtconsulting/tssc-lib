
import unittest
from unittest.mock import patch, Mock
from ploigos_step_runner.step_implementers.uat.gradle_integration_test import GradleIntegrationTest, DEFAULT_CONFIG, REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from tests.helpers.base_step_implementer_test_case import BaseStepImplementerTestCase
from ploigos_step_runner.step_implementers.shared.gradle_generic import GradleGeneric

class BaseTestStepImplementerGradleIntegrationTest(BaseStepImplementerTestCase):
    """
    Base test class for GradleIntegrationTest step implementer.
    Provides reusable setup and creation methods.
    """

    def create_step_implementer(self, step_config={}, workflow_results=None, parent_work_dir_path=""):
        """
        Factory method to create an instance of GradleIntegrationTest.

        Args:
        """
        return self.create_given_step_implementer(
            step_implementer=GradleIntegrationTest,
            step_config=step_config,
            step_name='gradle-uat-test',
            implementer='GradleIntegrationTest',
            workflow_result=workflow_results,
            parent_work_dir_path=parent_work_dir_path
        )
        
class TestGradleIntegrationTest(BaseTestStepImplementerGradleIntegrationTest):

    def setUp(self):
        """
        Setup mock data to initialize GradleIntegrationTest 
        """

        self.workflow_result = Mock()
        self.parent_work_dir_path = "/tmp/gradle_integration_test"
        self.step_config = {
            "build-file": "app/build.gradle",
            "gradle-tasks": ["UatTest"],
            "gradle-additional-arguments":["-x", "test"]
        }

        #create the step implementer

        self.step_impl =  self.create_step_implementer(
            step_config=self.step_config,
            workflow_results=self.workflow_result,
            parent_work_dir_path=self.parent_work_dir_path
        )


    @patch("ploigos_step_runner.step_implementers.shared.gradle_generic.GradleGeneric.write_working_file")
    @patch("ploigos_step_runner.step_implementers.shared.gradle_generic.GradleGeneric._run_gradle_step")
    def test_run_step_success(self, mock_run_gradle_step, mock_write_working_file):
        """
        Test successful execution of the _run_step method
        """

        # Mock write_working_file
        mock_write_working_file.return_value = "gradle_output.txt"
        mock_run_gradle_step.return_value = True

        # Call _run_step
        result = self.step_impl._run_step()

        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.artifacts['gradle-output'].name, "gradle-output")
        self.assertEqual(result.artifacts['gradle-output'].value, "gradle_output.txt")

        # Ensure mocks were called
        mock_write_working_file.assert_called_with("gradle_output.txt")
        mock_run_gradle_step.assert_called_once()


    @patch("ploigos_step_runner.step_implementers.shared.gradle_generic.GradleGeneric._run_gradle_step")
    def test_run_step_failure(self, mock_run_gradle_step):
        """
        Test failure scenario for GradleIntegrationTest step.
        """

        mock_run_gradle_step.side_effect = StepRunnerException("Gradle command failed")

        step_results =  self.step_impl._run_step()

        self.assertFalse(step_results.success)
        self.assertIn("Error running Gradle", step_results.message)

    def test_step_implementer_config_defaults(self):
        expected = {
            **GradleGeneric.step_implementer_config_defaults(),
            **DEFAULT_CONFIG
        }
        result = GradleIntegrationTest.step_implementer_config_defaults()
        assert result == expected, "step_implementer_config_defaults did not return the expected configuration"
    
    def test_required_config_or_result_keys(self):
        expected = REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS
        result = GradleIntegrationTest._required_config_or_result_keys()
        assert result == expected, "_required_config_or_result_keys did not return the expected keys"