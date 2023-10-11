"""`StepImplementer` for the `generate-metadata` step using Gradle.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key                    | Required? | Default          | Description
-------------------------------------|-----------|------------------|-----------
`build-file`                         | Yes       | `'build.gradle'` | The build file to read the app version out of

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key                     | Description
----------------------------------------|------------
`app-version`                           | Value to use for `version` portion of semantic version \
                                          (https://semver.org/). Uses the version read out of the given build.gradle file.

"""# pylint: disable=line-too-long

from ploigos_step_runner.results import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementers.shared import GradleGeneric
from ploigos_step_runner.utils.gradle import run_gradle, GradleGroovyParser

DEFAULT_CONFIG = {
    'build-file': 'build.gradle',
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'build-file'
]


class Gradle(GradleGeneric):
    """`StepImplementer` for the `generate-metadata` step using Gradle.
    """
    
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

    def _validate_required_config_or_previous_step_result_artifact_keys(self):
        """Validates that the required configuration keys or previous step result artifacts
        are set and have valid values.

        Validates that:
        * required configuration is given
        * given 'build.gradle' exists

        Raises
        ------
        AssertionError
            If step configuration or previous step result artifacts have invalid required values
        """
        super()._validate_required_config_or_previous_step_result_artifact_keys()
                
    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        try:
            step_result = StepResult.from_step_implementer(self)
            groovy_parser = GradleGroovyParser( self.get_value('build-file') )

            # get the version
            project_version = groovy_parser.get_version()
            if project_version:
                step_result.add_artifact(
                    name='app-version',
                    value=project_version
                )
            else:
                step_result.success = False
                step_result.message += 'Could not get project version from given build file' \
                    f' ({self.get_value("build-file")})'
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = str(error)

        return step_result