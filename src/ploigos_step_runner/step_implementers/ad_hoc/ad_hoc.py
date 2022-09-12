"""`StepImplementer` for the `ad-hoc` step using AdHoc.

Step Configuration
------------------
Step configuration expected as input to this step.
Could come from:

  * static configuration
  * runtime configuration
  * previous step results

Configuration Key             | Required? | Default                  | Description
------------------------------|-----------|--------------------------|-----------
`command`                     | Yes       |                          | Command to execute

Result Artifacts
----------------
Results artifacts output by this step.

Result Artifact Key    | Description
-----------------------|------------
`stdout`               | stdout from the command run
`stderr`               | stderr from the command run
"""# pylint: disable=line-too-long

import re
import sys

import sh

from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.utils.io import \
    create_sh_redirect_to_multiple_streams_fn_callback
import ploigos_step_runner.utils.bash as bash

DEFAULT_CONFIG = {}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'command'
]

class AdHoc(StepImplementer):  # pylint: disable=too-few-public-methods
    """
    StepImplementer for the ad-hoc step for AdHoc.
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
        return {**DEFAULT_CONFIG}

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
        step_result = StepResult.from_step_implementer(self)
        output_file_path = self.write_working_file('ad_hoc_output.txt')

        step_result.add_artifact(
            description="Standard out and standard error from ad-hoc command run.",
            name='command-output',
            value=output_file_path
        )

        command = self.get_value('command')

        try:
            bash.run_bash(output_file_path, command)
        except StepRunnerException as error:
            step_result.success = False
            step_result.message = str(error)

        return step_result
