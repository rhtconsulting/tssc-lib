"""Abstract parent class for StepImplementers that use Gradle.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:
* static configuration
* runtime configuration
* previous step results

Configuration Key            | Required? | Default | Description
-----------------------------|-----------|---------|-----------
`build-file`                 | Yes       | `'build.gradle'` | builfile used when executing gradle.
`tasks`                      | Yes       |         | List of gradle tasks to execute.
`gradle-console-plain`       | No        | `True`  | `True` use old append style log output. \
                                                     `False` use new fancy screen redraw log output.
`gradle-additional-arguments`| No        | `[]`    | List of additional arguments to use.
"""# pylint: disable=line-too-long

import os

from ploigos_step_runner.results import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.utils.gradle import run_gradle

DEFAULT_CONFIG = {
    'build-file': 'build.gradle',
    'gradle-additional-arguments': [],
    'gradle-console-plain': True
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'build-file',
    'tasks'
]

class GradleGeneric(StepImplementer):
    """Abstract parent class for StepImplementers that use gradle.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        workflow_result,
        parent_work_dir_path,
        config,
        environment=None,
        gradle_tasks=None
    ):
        self.__gradle_tasks = gradle_tasks

        super().__init__(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=environment
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
        return DEFAULT_CONFIG

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
        * given 'build-file' exists

        Raises
        ------
        AssertionError
            If step configuration or previous step result artifacts have invalid required values
        """
        super()._validate_required_config_or_previous_step_result_artifact_keys()

        # if build-file has value verify file exists
        # If it doesn't have value and is required function will have already failed
        build_file = self.get_value('build-file')
        if build_file is not None:
            assert os.path.exists(build_file), \
                f'Given gradle build file does not exist: {build_file}'
                
    @property
    def gradle_tasks(self):
        """Property for getting the gradle tasks to execute which can either come
        from field set on this class via constructor, intended for use by sub classes that want
        to hard code the phases and goals for convenience, or comes from config value
        `gradle-tasks` set by the user.

        Returns
        -------
        str
            Gradle tasks to execute.
        """
        gradle_tasks = None
        if self.__gradle_tasks:
            gradle_tasks = self.__gradle_tasks
        else:
            gradle_tasks = self.get_value('gradle-tasks')

        return gradle_tasks
    
    def _run_gradle_step(
        self,
        gradle_output_file_path,
        step_implementer_additional_arguments=None
    ):
        """Runs gradle using the configuration given to this step runner.

        Parameters
        ----------
        gradle_output_file_path : str
            Path to file containing the gradle stdout and stderr output.
        step_implementer_additional_arguments : []
            Additional arguments hard coded by the step implementer.

        Raises
        ------
        StepRunnerException
            If gradle returns a none 0 exit code.
        """

        tasks = self.gradle_tasks
        build_file = self.get_value('build-file')
        gradle_console_plain = self.get_value('gradle_console_plain')

        additional_arguments = []
        if step_implementer_additional_arguments:
            additional_arguments = \
                step_implementer_additional_arguments + self.get_value('gradle-additional-arguments')
        else:
            additional_arguments = self.get_value('gradle-additional-arguments')

        run_gradle(
            gradle_output_file_path=gradle_output_file_path,
            tasks=tasks,
            additional_arguments=additional_arguments,
            build_file=build_file,
            gradle_console_plain=gradle_console_plain,
        )

    def _run_step(self): # pylint: disable=too-many-locals
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        # package the artifacts
        gradle_output_file_path = self.write_working_file('gradle_output.txt')
        try:
            # execute gradle step (params come from config)
            self._run_gradle_step(
                gradle_output_file_path=gradle_output_file_path
            )
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = "Error running gradle. " \
                f"More details maybe found in 'gradle-output' report artifact: {error}"
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from gradle.",
                name='gradle-output',
                value=gradle_output_file_path
            )

        return step_result
