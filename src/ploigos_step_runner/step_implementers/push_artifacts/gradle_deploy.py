import os
import xml.etree.ElementTree as ET
import subprocess
import yaml
import time
from pathlib import Path
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.results.step_result import StepResult
from ploigos_step_runner.step_implementers.shared.gradle_generic import GradleGeneric

DEFAULT_CONFIG = {
    "build-file": "app/build.gradle",
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    "build-file",
    "gradle-token",
    "gradle-token-alpha",
]


class GradleDeploy(GradleGeneric):
    """`StepImplementer` for the `uat` step using Gradle by invoking the 'test` gradle phase."""

    def __init__(
        self, workflow_result, parent_work_dir_path, config, environment=None
    ):  # pylint: disable=too-many-arguments
        super().__init__(
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path,
            config=config,
            environment=environment,
            gradle_tasks=["artifactoryPublish"],
        )
        print(f"environment : {self.environment}")
        print(f"config : {self.config}")

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

    def read_and_replace_password(self):
        """Read a properties file, replace the Artifactory password, and save the changes."""
        properties = {}

        current_path = os.path.join(os.getcwd(), "app/build")
        print("current_path")
        print(current_path)
        files_via_Path = os.listdir(current_path)
        for file in files_via_Path:
            print("\n files_via_Path ::" + file)

        current_working_directory = os.getcwd()
        print("current_working_directory")
        print(current_working_directory)
        files_via_current_cwd = os.listdir(current_working_directory)
        for file in files_via_current_cwd:
            print("\n files_via_current_cwd ::" + file)

        properties_file = os.path.join(os.getcwd(), "gradle.properties")
        artifactory_password = self.get_value("gradle-token-alpha")

        # # Read the properties file
        with open(properties_file, "r") as file:
            for line in file:
                # Skip comments and empty lines
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)  # Split on the first '='
                    properties[key] = value

        # Replace the Artifactory password value
        if "artifactory_password" in properties:
            properties["artifactory_password"] = artifactory_password

        # Write the modified properties back to the file
        with open(properties_file, "w") as file:
            for key, value in properties.items():
                file.write(f"{key}={value}\n")

        # print out the properties file
        with open(properties_file, "r") as file:
            content = file.read()
            print("\n build.properties file: ")
            print(content)

    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """

        self.read_and_replace_password()
        step_result = StepResult.from_step_implementer(self)

        # push the artifacts
        gradle_output_file_path = self.write_working_file("gradle_deploy_output.txt")

        try:
            # execute Gradle Artifactory publish step (params come from config)
            print("Push packaged gradle artifacts")

            self._run_gradle_step(gradle_output_file_path=gradle_output_file_path)

        except StepRunnerException as error:
            step_result.success = False
            step_result.message = (
                "Error running 'gradle deploy' to push artifacts. "
                f"More details maybe found in 'gradle-output' report artifact: {error}"
            )
            step_result.message = f"environment : {self.environment}"
            step_result.message = f"config : {self.config}"

        finally:
            step_result.add_artifact(
                description="Standard out and standard error from running gradle to "
                "push artifacts to repository.",
                name="gradle-push-artifacts-output",
                value=gradle_output_file_path,
            )

        return step_result
