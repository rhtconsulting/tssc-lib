# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import os
from unittest.mock import patch
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase

from ploigos_step_runner.step_implementers.generate_metadata import Gradle
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.exceptions import StepRunnerException

class TestStepImplementerGradleGenerateMetadata(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            step_name='',
            implementer='',
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=Gradle,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

    def test_step_implementer_config_defaults(self):
        defaults = Gradle.step_implementer_config_defaults()
        expected_defaults = {
            'build-file': 'app/build.gradle',
            'gradle-additional-arguments': [],
            'gradle-console-plain': True
        }
        self.assertEqual(defaults, expected_defaults)

    def test__required_config_or_result_keys(self):
        required_keys = Gradle._required_config_or_result_keys()
        expected_required_keys = ['build-file']
        self.assertEqual(required_keys, expected_required_keys)
        
    def test__validate_required_config_or_previous_step_result_artifact_keys_valid(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            temp_dir.write('build.gradle', b'''/*\n * This file was generated by the Gradle \'init\' task.\n 
                           *\n * This generated file contains a sample Java application project to get you 
                           started.\n * For more details on building Java & JVM projects, please refer to 
                           https://docs.gradle.org/8.3/userguide/building_java_projects.html in the Gradle 
                           documentation.\n */\n\nplugins {\n    // Apply the application plugin to add 
                           support for building a CLI application in Java.\n    id \'application\'\n    
                           id \"org.springframework.boot\" version \"2.7.16\"\n\n}\n\nrepositories {\n    
                           // Use Maven Central for resolving dependencies.\n    mavenCentral()\n}\n\ndependencies 
                           {\n    // Use JUnit test framework.\n    testImplementation \'junit:junit:4.13.2\'\n\n    
                           // This dependency is used by the application.\n    implementation 
                           \'com.google.guava:guava:32.1.1-jre\'\n    implementation 
                           \'org.springframework.boot:spring-boot-starter-web:2.7.16\'\n}\n\n// 
                           Apply a specific Java toolchain to ease working on different environments.\njava 
                           {\n    toolchain {\n        languageVersion = JavaLanguageVersion.of(11)\n    
                           }\n}\n\napplication {\n    // Define the main class for the application.\n    
                           mainClass = \'org.acme.rest.json.gradle.App\'\n}\n
                            ''')
            build_file_path = os.path.join(temp_dir.path, 'build.gradle')

            step_config = {
                'build-file': build_file_path
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Gradle',
                parent_work_dir_path=parent_work_dir_path,
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()
            
    def test__validate_required_config_or_previous_step_result_artifact_keys_package_file_does_not_exist(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            build_file_path = os.path.join(temp_dir.path, 'build.gradle')

            step_config = {
                'build-file': build_file_path
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Gradle',
                parent_work_dir_path=parent_work_dir_path,
            )

            with self.assertRaisesRegex(
                AssertionError,
                rf"Given gradle build file does not exist: {build_file_path}"
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

    def test_run_step_pass(self):
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            temp_dir.write('build.gradle', b'''/*\n * This file was generated by the Gradle \'init\' task.\n 
                           *\n * This generated file contains a sample Java application project to get you 
                           started.\n * For more details on building Java & JVM projects, please refer to 
                           https://docs.gradle.org/8.3/userguide/building_java_projects.html in the Gradle 
                           documentation.\n */\n\nplugins {\n    // Apply the application plugin to add 
                           support for building a CLI application in Java.\n    id \'application\'\n    
                           id \"org.springframework.boot\" version \"2.7.16\"\n\n}\nversion '1.0-SNAPSHOT'\n\n
                           repositories {\n    
                           // Use Maven Central for resolving dependencies.\n    mavenCentral()\n}\n\ndependencies 
                           {\n    // Use JUnit test framework.\n    testImplementation \'junit:junit:4.13.2\'\n\n    
                           // This dependency is used by the application.\n    implementation 
                           \'com.google.guava:guava:32.1.1-jre\'\n    implementation 
                           \'org.springframework.boot:spring-boot-starter-web:2.7.16\'\n}\n\n// 
                           Apply a specific Java toolchain to ease working on different environments.\njava 
                           {\n    toolchain {\n        languageVersion = JavaLanguageVersion.of(11)\n    
                           }\n}\n\napplication {\n    // Define the main class for the application.\n    
                           mainClass = \'org.acme.rest.json.gradle.App\'\n}\n
                            ''')
            pom_file_path = os.path.join(temp_dir.path, 'build.gradle')

            step_config = {
                'build-file': pom_file_path
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Gradle',
                parent_work_dir_path=parent_work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Gradle',
                sub_step_implementer_name='Gradle'
            )
            expected_step_result.add_artifact(name='app-version', value='1.0-SNAPSHOT')

            self.assertEqual(result, expected_step_result)
        
    @patch('ploigos_step_runner.step_implementers.generate_metadata.gradle.run_gradle')
    def test_run_step_fail_missing_version_in_build_file(
            self,
            mock_run_gradle
    ):
        mock_run_gradle.side_effect = StepRunnerException("no version found")

        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            temp_dir.write('build.gradle', b'''/*\n * This file was generated by the Gradle \'init\' task.\n 
                           *\n * This generated file contains a sample Java application project to get you 
                           started.\n * For more details on building Java & JVM projects, please refer to 
                           https://docs.gradle.org/8.3/userguide/building_java_projects.html in the Gradle 
                           documentation.\n */\n\nplugins {\n    // Apply the application plugin to add 
                           support for building a CLI application in Java.\n    id \'application\'\n    
                           id \"org.springframework.boot\" version \"2.7.16\"\n\n}\n\nrepositories {\n    
                           // Use Maven Central for resolving dependencies.\n    mavenCentral()\n}\n\ndependencies 
                           {\n    // Use JUnit test framework.\n    testImplementation \'junit:junit:4.13.2\'\n\n    
                           // This dependency is used by the application.\n    implementation 
                           \'com.google.guava:guava:32.1.1-jre\'\n    implementation 
                           \'org.springframework.boot:spring-boot-starter-web:2.7.16\'\n}\n\n// 
                           Apply a specific Java toolchain to ease working on different environments.\njava 
                           {\n    toolchain {\n        languageVersion = JavaLanguageVersion.of(11)\n    
                           }\n}\n\napplication {\n    // Define the main class for the application.\n    
                           mainClass = \'org.acme.rest.json.gradle.App\'\n}\n
                            ''')
            build_file_path = os.path.join(temp_dir.path, 'build.gradle')

            step_config = {
                'build-file': build_file_path
            }
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='generate-metadata',
                implementer='Gradle',
                parent_work_dir_path=parent_work_dir_path,
            )

            result = step_implementer._run_step()

            expected_step_result = StepResult(
                step_name='generate-metadata',
                sub_step_name='Gradle',
                sub_step_implementer_name='Gradle'
            )
            expected_step_result.success = False
            expected_step_result.message = f'Could not get project version from given build file' \
                    f' ({build_file_path})'

            self.assertEqual(result, expected_step_result)