# import os
# import xml.etree.ElementTree as ET
# import subprocess
# import yaml
# import time
# from ploigos_step_runner.exceptions import StepRunnerException
# from ploigos_step_runner.results.step_result import StepResult
# from ploigos_step_runner.step_implementers.shared.gradle_generic import GradleGeneric

# DEFAULT_CONFIG = {
#     "build-file": "app/build.gradle",
#     "properties-file": "gradle.properties",
# }

# REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
#     "build-file",
#     "properties-file",
#     "gradle-token",
#     "gradle-token-alpha",
# ]


# class GradleDeploy(GradleGeneric):
#     """`StepImplementer` for the `uat` step using Gradle by invoking the 'test` gradle phase."""

#     def __init__(
#         self, workflow_result, parent_work_dir_path, config, environment=None
#     ):  # pylint: disable=too-many-arguments
#         super().__init__(
#             workflow_result=workflow_result,
#             parent_work_dir_path=parent_work_dir_path,
#             config=config,
#             environment=environment,
#             gradle_tasks=["artifactoryPublish"],
#         )
#         print(f"environment : {self.environment}")
#         print(f"config : {self.config}")

#     @staticmethod
#     def step_implementer_config_defaults():
#         """Getter for the StepImplementer's configuration defaults.

#         Returns
#         -------
#         dict
#             Default values to use for step configuration values.

#         Notes
#         -----
#         These are the lowest precedence configuration values.
#         """
#         return {**GradleGeneric.step_implementer_config_defaults(), **DEFAULT_CONFIG}

#     @staticmethod
#     def _required_config_or_result_keys():
#         """Getter for step configuration or previous step result artifacts that are required before
#         running this step.

#         See Also
#         --------
#         _validate_required_config_or_previous_step_result_artifact_keys

#         Returns
#         -------
#         array_list
#             Array of configuration keys or previous step result artifacts
#             that are required before running the step.
#         """
#         return REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS

#     def decrypt_sops_file(file_path):
#         """Decrypt a SOPS-encrypted file."""
#         try:
#             # Use sops to decrypt the file
#             result = subprocess.run(['sops', '-d', file_path], capture_output=True, check=True)
#             decrypted_content = result.stdout.decode('utf-8')
#             return yaml.safe_load(decrypted_content)  # Load as a Python dictionary
#         except subprocess.CalledProcessError as e:
#             print(f"Error decrypting file: {e}")
#             return None

#     def set_env_variables(config):
#         """Set environment variables from the config dictionary."""
#         for key, value in config.items():
#             os.environ[key] = str(value)
#             print(f"{key}: {value}")

#     def read_and_replace_password(self):
#         """Read a properties file, replace the Artifactory password, and save the changes."""
#         properties = {}
#         properties_file = self.get_value("properties_file")
#         artifactory_password = self.get_value("gradle-token-alpha")

#         # Read the properties file
#         with open(properties_file, "r") as file:
#             for line in file:
#                 # Skip comments and empty lines
#                 line = line.strip()
#                 if line and not line.startswith("#"):
#                     key, value = line.split("=", 1)  # Split on the first '='
#                     properties[key] = value

#         # Replace the Artifactory password value
#         if "artifactory_password" in properties:
#             properties["artifactory_password"] = artifactory_password

#         # Write the modified properties back to the file
#         with open(properties_file, "w") as file:
#             for key, value in properties.items():
#                 file.write(f"{key}={value}\n")

#         # print out the properties file
#         with open(properties_file, "r") as file:
#             content = file.read()
#             print("\n build.properties file: ")
#             print(content)

#     def _run_step(self):
#         """Runs the step implemented by this StepImplementer.

#         Returns
#         -------
#         StepResult
#             Object containing the dictionary results of this step.
#         """

#         #self.read_and_replace_password()
#        # time.sleep(5000)
#         #result = subprocess.run(['sops', '-d', '/home/jenkins/agent/workspace/ot-gradle_feature_gradle-publish/cicd/ploigos-step-runner-config/config-secrets.yml''], capture_output=True, check=True)
#         #decrypted_content = result.stdout.decode('utf-8')
#         #return yaml.safe_load(decrypted_content)
#         step_result = StepResult.from_step_implementer(self)

#         # Get config items
#         # maven_push_artifact_repo_id = self.get_value('maven-push-artifact-repo-id')
#         # maven_push_artifact_repo_url = self.get_value('maven-push-artifact-repo-url')
#         # version = self.get_value('version')

#         # push the artifacts
#         gradle_output_file_path = self.write_working_file("gradle_deploy_output.txt")

#         try:
#             # execute Gradle Artifactory publish step (params come from config)
#             print("Push packaged gradle artifacts")
#             # print("artifactory: " + self.get_value('artifactory-user'))
#             # print(project.findProperty(('artifactory_user')))
#             # artifactoryUser = project.findProperty('artifactory_user')
#             # print("artifactory Line 91")

#             self._run_gradle_step(gradle_output_file_path=gradle_output_file_path)
#             result = subprocess.run(['sops', '-d', '/home/jenkins/agent/workspace/ot-gradle_feature_gradle-publish/cicd/ploigos-step-runner-config/config-secrets.yml'], capture_output=True, check=True)
#             decrypted_content = result.stdout.decode('utf-8')
#             return yaml.safe_load(decrypted_content)
#             print(decrypted_content)
#             #config = decrypt_sops_file('/home/jenkins/agent/workspace/ot-gradle_feature_gradle-publish/cicd/ploigos-step-runner-config/config-secrets.yml')

#         except StepRunnerException as error:
#             step_result.success = False
#             step_result.message = (
#                 "Error running 'gradle deploy' to push artifacts. "
#                 f"More details maybe found in 'gradle-output' report artifact: {error}"
#             )
#             step_result.message = f"environment : {self.environment}"
#             step_result.message = f"config : {self.config}"

#         finally:
#             step_result.add_artifact(
#                 description="Standard out and standard error from running gradle to "
#                 "push artifacts to repository.",
#                 name="gradle-push-artifacts-output",
#                 value=gradle_output_file_path,
#             )

#         return step_result

import os
import xml.etree.ElementTree as ET
import subprocess
import yaml

from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.results.step_result import StepResult
from ploigos_step_runner.step_implementers.shared.gradle_generic import GradleGeneric
from dotenv import load_dotenv

#load Env variable from .env file
load_dotenv()

USER_NAME = os.getenv("USER_NAME")
USER_PASSWORD = os.getenv("USER_PASSWORD")
current_dir = os.path.abspath(os.path.join(__file__, "..")).replace('\\','/')
#gradle_filepath = current_dir + "/../../../../reference-spring-boot-gradle/app/src"
gradle_filepath = current_dir + "/../../../../../reference-spring-boot-gradle/app"
BUILD_GRADLE_BACKUP = None

DEFAULT_CONFIG = {
    "build-file": "app/build.gradle",
    "properties-file": "gradle.properties",
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    "build-file",
    "properties-file",
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

    # def decrypt_sops_file(file_path):
    #     """Decrypt a SOPS-encrypted file."""
    #     try:
    #         # Use sops to decrypt the file
    #         result = subprocess.run(['sops', '-d', file_path], capture_output=True, check=True)
    #         decrypted_content = result.stdout.decode('utf-8')
    #         return yaml.safe_load(decrypted_content)  # Load as a Python dictionary
    #     except subprocess.CalledProcessError as e:
    #         print(f"Error decrypting file: {e}")
    #         return None

    # def set_env_variables(config):
    #     """Set environment variables from the config dictionary."""
    #     for key, value in config.items():
    #         os.environ[key] = str(value)
    #         print(f"{key}: {value}")

    # def read_and_replace_password(self):
    #     """Read a properties file, replace the Artifactory password, and save the changes."""
    #     properties = {}
    #     properties_file = self.get_value("properties_file")
    #     artifactory_password = self.get_value("gradle-token-alpha")

    #     # Read the properties file
    #     with open(properties_file, "r") as file:
    #         for line in file:
    #             # Skip comments and empty lines
    #             line = line.strip()
    #             if line and not line.startswith("#"):
    #                 key, value = line.split("=", 1)  # Split on the first '='
    #                 properties[key] = value

    #     # Replace the Artifactory password value
    #     if "artifactory_password" in properties:
    #         properties["artifactory_password"] = artifactory_password

    #     # Write the modified properties back to the file
    #     with open(properties_file, "w") as file:
    #         for key, value in properties.items():
    #             file.write(f"{key}={value}\n")

    #     # print out the properties file
    #     with open(properties_file, "r") as file:
    #         content = file.read()
    #         print("\n build.properties file: ")
    #         print(content)

    def read_file(file_path):
        """Reads a file from the given file path and prints its contents."""
        try:
            # Open the file in read mode
            with open(file_path, 'r') as file:
                # Read the contents of the file
                content = file.read()
                # Print the file content
                # print(content)
                return content
        except FileNotFoundError:
            print(f"Error: The file at path {file_path} does not exist.")
        except IOError as e:
            print(f"Error reading the file: {e}")
        return None

    def write_file(file_path,content):
        # Define the contents of the deploy.gradle file
        try:
            # Open the file in write mod
            with open(file_path, 'w') as file:
                # Write the gradle content to the file
                file.write(content)
            print(f"'{file_path}' has been created successfully!")
            return True
        except Exception as e:
            print(f"An error occurred while writing to the file: {e}")
            return False


    def _run_step(self):
        """Runs the step implemented by this StepImplementer.

        Returns
        -------
        StepResult
            Object containing the dictionary results of this step.
        """

        self.read_and_replace_password(self)
        step_result = StepResult.from_step_implementer(self)
        global BUILD_GRADLE_BACKUP
        
        BUILD_GRADLE_BACKUP = self.read_file(gradle_filepath + "/build.gradle")

        build_gradle_content = BUILD_GRADLE_BACKUP.replace("artifactory_user",USER_NAME).replace("artifactory_password",USER_PASSWORD)
        print("Updating credentials in build.gradle file")
        write_file(gradle_filepath + "/build.gradle", build_gradle_content)


        # Get config items
        # maven_push_artifact_repo_id = self.get_value('maven-push-artifact-repo-id')
        # maven_push_artifact_repo_url = self.get_value('maven-push-artifact-repo-url')
        # version = self.get_value('version')

        # push the artifacts
        gradle_output_file_path = self.write_working_file("gradle_deploy_output.txt")

        try:
            # execute Gradle Artifactory publish step (params come from config)
            print("Push packaged gradle artifacts")
            # print("artifactory: " + self.get_value('artifactory-user'))
            # print(project.findProperty(('artifactory_user')))
            # artifactoryUser = project.findProperty('artifactory_user')
            # print("artifactory Line 91")

            self._run_gradle_step(gradle_output_file_path=gradle_output_file_path)
            # config = decrypt_sops_file('/home/jenkins/agent/workspace/ot-gradle_feature_gradle-publish/cicd/ploigos-step-runner-config/config-secrets.yml')

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
            #print("Updating credentials in build.gradle file")
            #write_file(gradle_filepath + "/build.gradle", build_gradle_content)

        return step_result
