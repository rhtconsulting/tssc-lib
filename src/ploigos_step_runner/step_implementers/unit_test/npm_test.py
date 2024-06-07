"""`StepImplementer` for the `unit-test` step using npm

"""
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.step_implementers.shared.npm_generic import NpmGeneric

class NpmTest(NpmGeneric):
    """`StepImplementer` for the `unit-test` step using npm.
    """

    def __init__(self, workflow_result, parent_work_dir_path, config, environment):
        super().__init__(
            workflow_result,
            parent_work_dir_path,
            config,
            environment=environment,
            npm_args='test'
        )

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
        return []

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """
        step_result = StepResult.from_step_implementer(self)

        npm_output_file_path = self.write_working_file('npm_test_output.txt')
        try:
            if self.get_value('install-first'):
                self._run_npm_step(
                    npm_output_file_path=npm_output_file_path,
                    npm_args='install'
                )

            self._run_npm_step(
                npm_output_file_path=npm_output_file_path
            )

        except StepRunnerException as error:
            step_result.message = "Unit test failures. See 'npm-output'" \
                f" report artifacts for details: {error}"
            step_result.success = False
        finally:
            step_result.add_artifact(
                description="Standard out and standard error from 'npm test'.",
                name='npm-output',
                value=npm_output_file_path
            )

        return step_result
