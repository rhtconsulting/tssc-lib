"""
Step Implementer for the 'uat' step using Gradle by invoking UAT tasks.

This step implementer is designed to execute user acceptance testing (UAT) tasks using Gradle.
The implementer assume that the required configurations, build files and gradle tasks
are provided and properly setup.

Configurations:
----------------

 step-runner-config:
  uat:
    - implementer: GradleIntegrationTest
      config:
        build-file: <Path to Gradle build file>
        gradle-tasks: 
          - UatTest
        gradle-additional-arguments: ""

        
Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key | Description
--------------------|------------
`gradle_output.txt` | Path to Stdout and Stderr from invoking Gradle.
"""

from ploigos_step_runner.results import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementers.shared.gradle_generic import GradleGeneric

DEFAULT_CONFIG = {
    'gradle-additional-arguments': ['-x test'] # Skip other tests by default
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'build-file',
    'gradle-tasks',
]

class GradleIntegrationTest(GradleGeneric):
    """
    StepImplementer for the `uat` step using Gradle by invoking UAT tasks.
    """

    def __init__(self, workflow_result, parent_work_dir_path, config, environment=None):
        """
        Initialize the GradleIntegrationTest class.

        Parameters:
        - workflow_result: Shared state object for the workflow.
        - parent_work_dir_path: Working directory for this step.
        - config: Step Configuration.
        - environment: Execution environment variables.
        """

        super().__init__(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=environment,
        )
    
    @staticmethod
    def step_implementer_config_defaults():
        """
        Provide default configurations for this step implementer.

        Returns:
        - dict: Default configuration values.
        """

        return {**GradleGeneric.step_implementer_config_defaults(), **DEFAULT_CONFIG}
    
    @staticmethod
    def _required_config_or_result_keys():
        """
        Define required configuration keys for this step implementer
        
        Returns:
        - list: Required configuration keys or step results artifact keys.
        """

        return REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS
    
    def _run_step(self):
        """
        Run the Gradle UAT step.

        Returns:
        - StepResult: Results of this step.
        """

        step_result = StepResult.from_step_implementer(self)


        gradle_output_file_path = self.write_working_file('gradle_output.txt')


        try:
            
            self._run_gradle_step(
                gradle_output_file_path=gradle_output_file_path,
            )


        except StepRunnerException as error:
            step_result.success = False
            step_result.message = (
                f"Error running Gradle. More details may be found in report artifacts: {error}"
            )
        finally:

            # Add Gradle output to the step results
            step_result.add_artifact(
                description="Standard out and standard error from Gradle.",
                name="gradle-output",
                value=gradle_output_file_path,
            )

        # Return the result of the step

        return step_result