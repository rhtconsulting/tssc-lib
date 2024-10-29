import os
import xml.etree.ElementTree as ET

from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.results.step_result import StepResult
from ploigos_step_runner.step_implementers.shared.gradle_generic import GradleGeneric

DEFAULT_CONFIG = {
    'build-file': 'app/build.gradle',
}


REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'build-file'
]

class GradleDeploy(GradleGeneric):
    """`StepImplementer` for the `uat` step using Gradle by invoking the 'test` gradle phase.
    """


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
            gradle_tasks=['artifactoryPublish']
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

        # Get config items
        # maven_push_artifact_repo_id = self.get_value('maven-push-artifact-repo-id')
        # maven_push_artifact_repo_url = self.get_value('maven-push-artifact-repo-url')
        # version = self.get_value('version')

        # push the artifacts
        gradle_output_file_path = self.write_working_file('gradle_deploy_output.txt')

        try:
            # execute Gradle Artifactory publish step (params come from config)
            print("Push packaged gradle artifacts")
            self._run_gradle_step(
                print("artifactory user: " + self.get_value('artifactory-user'))
                gradle_output_file_path=gradle_output_file_path
            )
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = "Error running 'gradle deploy' to push artifacts. " \
                f"More details maybe found in 'gradle-output' report artifact: {error}"
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from running gradle to " \
                    "push artifacts to repository.",
                name='gradle-push-artifacts-output',
                value=gradle_output_file_path

            )

        return step_result