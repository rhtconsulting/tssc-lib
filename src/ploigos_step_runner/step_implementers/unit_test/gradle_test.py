import os
import xml.etree.ElementTree as ET

from src.ploigos_step_runner.exceptions import StepRunnerException
from src.ploigos_step_runner.results.step_result import StepResult
from src.ploigos_step_runner.step_implementers.shared.gradle_generic import GradleGeneric

DEFAULT_CONFIG = {}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'build-file'
]

class GradleTest(GradleGeneric):
    """`StepImplementer` for the `uat` step using Gradle by invoking the 'test` gradle phase.
    """

    TEST_RESULTS_ATTRIBUTES = ["time", "tests", "failures", "errors", "skipped"]
    TEST_RESULTS_ATTRIBUTES_REQUIRED = ["time", "tests", "failures"]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        workflow_result,
        parent_work_dir_path,
        config,
        environment=None
    ):
        super().__init__(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=environment,
            gradle_tasks=['test']
        )

    @staticmethod
    def step_implementer_config_defaults():
        """Getter for the StepImplementer's configuration defaults.

        Returns
        -------
        dict
            Default values to use for step configuration values.

        Notes
        -----
        These are the lowest precedence configuration values.
        """
        return {**GradleGeneric.step_implementer_config_defaults(), **DEFAULT_CONFIG}

    @staticmethod
    def _required_config_or_result_keys():
        """Getter for step configuration or previous step result artifacts that are required before
        running this step.

        See Also
        --------
        _validate_required_config_or_previous_step_result_artifact_keys

        Returns
        -------
        array_list
            Array of configuration keys or previous step result artifacts
            that are required before running the step.
        """
        return REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """

        step_result = StepResult.from_step_implementer(self)

        # run the tests
        print("Run unit tests")
        gradle_output_file_path = self.write_working_file('gradle_output.txt')
        try:
            # execute maven step (params come from config)
            self._run_gradle_step(
                gradle_output_file_path=gradle_output_file_path
            )
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = "Error running Gradle. " \
                                  f"More details maybe found in report artifacts: {error}"
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from Gradle.",
                name='gradle-output',
                value=gradle_output_file_path
            )

        # get test result dirs
        test_report_dirs = self.get_value(['test-reports-dir', 'test-reports-dirs'])
        if test_report_dirs:
            step_result.add_artifact(
                description="Test report generated when running unit tests.",
                name='test-report',
                value=test_report_dirs
            )

            # gather data
            all_test_results = {}
            for test_report_dir in test_report_dirs:
                for filename in os.listdir(test_report_dir):
                    if filename.endswith('.xml'):
                        fullname = os.path.join(test_report_dir, filename)
                        test_results = self._get_test_results_from_file(fullname, self.TEST_RESULTS_ATTRIBUTES)

        return step_result

    def _get_test_results_from_file(self, file, attributes):
        tree = ET.parse(file)
        root = tree.getroot()
        test_results = dict()
        for attribute in attributes:
            test_results[attribute] = self._get_test_result(root, attribute)

        return test_results

    def _get_test_result(self, root, attribute):
        
        value = root.find()
        return 2


    def _check_required_test_results(self, root, attributes):
        pass


