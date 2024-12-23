import os
import urllib
from unittest.mock import Mock, patch

from ploigos_step_runner.utils.file import (
    base64_encode,
    create_parent_dir,
    download_source_to_destination,
    download_and_decompress_source_to_destination,
    get_file_hash,
    parse_yaml_or_json_file,
    upload_file,
    is_compressed,
    get_file_extension,
)
from testfixtures import TempDirectory
from tests.helpers.base_test_case import BaseTestCase


class TestParseYAMLOrJASONFile(BaseTestCase):
    def test_import_yaml(self):
        sample_file_path = os.path.join(
            os.path.dirname(__file__), "files", "sample.yaml"
        )
        sample_dict = parse_yaml_or_json_file(sample_file_path)

        self.assertTrue(isinstance(sample_dict, dict))
        self.assertIsNotNone(sample_dict["step-runner-config"])
        self.assertEqual(
            sample_dict["step-runner-config"]["global-defaults"]["service-name"],
            "fruit",
        )
        self.assertEqual(
            sample_dict["step-runner-config"]["package"][0]["implementer"], "Maven"
        )

    def test_import_json(self):
        sample_file_path = os.path.join(
            os.path.dirname(__file__), "files", "sample.json"
        )
        sample_dict = parse_yaml_or_json_file(sample_file_path)

        self.assertTrue(isinstance(sample_dict, dict))
        self.assertIsNotNone(sample_dict["step-runner-config"])
        self.assertEqual(
            sample_dict["step-runner-config"]["global-defaults"]["service-name"],
            "fruit",
        )
        self.assertEqual(
            sample_dict["step-runner-config"]["package"][0]["implementer"], "Maven"
        )

    def test_import_bad(self):
        sample_file_path = os.path.join(os.path.dirname(__file__), "files", "bad.yaml")

        with self.assertRaisesRegex(
            ValueError, r"Error parsing file \(.+\) as YAML or JSON:"
        ):
            parse_yaml_or_json_file(sample_file_path)


class TestDownloadAndDecompressSourceToDestination(BaseTestCase):
    def test_https_bz2(self):
        with TempDirectory() as test_dir:
            destination_path = download_and_decompress_source_to_destination(
                source_uri="https://www.redhat.com/security/data/metrics/ds/v2/RHEL8/rhel-8.ds.xml.bz2",
                destination_dir=test_dir.path,
            )

            self.assertIsNotNone(destination_path)
            self.assertRegex(destination_path, rf"{test_dir.path}/rhel-8.ds.xml$")
            with open(destination_path) as downloaded_file:
                self.assertTrue(downloaded_file.read())

    def test_https_xml(self):
        with TempDirectory() as test_dir:
            destination_path = download_and_decompress_source_to_destination(
                source_uri="https://raw.githubusercontent.com/ploigos/ploigos-step-runner/1cda48c9c659f2eb862b9427f804ae25990a2379/tests/utils/files/cvrf-rhba-2020-0017.xml",
                destination_dir=test_dir.path,
            )

            self.assertIsNotNone(destination_path)
            self.assertRegex(
                destination_path, rf"{test_dir.path}/cvrf-rhba-2020-0017.xml$"
            )
            with open(destination_path) as downloaded_file:
                self.assertTrue(downloaded_file.read())

    def test_local_file_download_file_prefix(self):
        sample_file_path = os.path.join(
            os.path.dirname(__file__), "files", "cvrf-rhba-2020-0017.xml"
        )

        with TempDirectory() as test_dir:
            destination_path = download_and_decompress_source_to_destination(
                source_uri=f"file://{sample_file_path}", destination_dir=test_dir.path
            )

            self.assertIsNotNone(destination_path)
            self.assertRegex(
                destination_path, rf"{test_dir.path}/cvrf-rhba-2020-0017.xml$"
            )
            with open(destination_path) as downloaded_file, open(
                sample_file_path
            ) as sample_file:
                downloaded_file_contents = downloaded_file.read()
                self.assertTrue(downloaded_file_contents)
                self.assertEqual(downloaded_file_contents, sample_file.read())

    def test_local_file_download_forward_slash_prefix(self):
        sample_file_path = os.path.join(
            os.path.dirname(__file__), "files", "cvrf-rhba-2020-0017.xml"
        )

        with TempDirectory() as test_dir:
            destination_path = download_and_decompress_source_to_destination(
                source_uri=f"{sample_file_path}", destination_dir=test_dir.path
            )

            self.assertIsNotNone(destination_path)
            self.assertRegex(
                destination_path, rf"{test_dir.path}/cvrf-rhba-2020-0017.xml$"
            )
            with open(destination_path) as downloaded_file, open(
                sample_file_path
            ) as sample_file:
                downloaded_file_contents = downloaded_file.read()
                self.assertTrue(downloaded_file_contents)
                self.assertEqual(downloaded_file_contents, sample_file.read())

    def test_bad_protocol(self):
        with TempDirectory() as test_dir:
            with self.assertRaisesRegex(
                ValueError,
                r"Unexpected error, should have been caught by step validation."
                r" Source \(.+\) must start with known protocol \(/|file://\|http://\|https://\).",
            ):
                download_and_decompress_source_to_destination(
                    source_uri="bad://www.redhat.com/security/data/metrics/ds/v2/RHEL8/rhel-8.ds.xml.bz2",
                    destination_dir=test_dir.path,
                )

    def test_https_bad_uri(self):
        with TempDirectory() as test_dir:
            with self.assertRaisesRegex(
                RuntimeError,
                r"Error downloading file \(.+\): HTTP Error 404: Not Found",
            ):
                download_and_decompress_source_to_destination(
                    source_uri="https://www.redhat.com/security/data/metrics/ds/v2/RHEL8/does-not-exist.ds.xml.bz2",
                    destination_dir=test_dir.path,
                )


class TestDownloadSourceToDestination(BaseTestCase):
    def test_https_xml(self):
        with TempDirectory() as test_dir:
            destination_path = download_source_to_destination(
                source_uri="https://raw.githubusercontent.com/ploigos/ploigos-step-runner/1cda48c9c659f2eb862b9427f804ae25990a2379/tests/utils/files/cvrf-rhba-2020-0017.xml",
                destination_dir=test_dir.path,
            )

            self.assertIsNotNone(destination_path)
            self.assertRegex(
                destination_path, rf"{test_dir.path}/cvrf-rhba-2020-0017.xml$"
            )
            with open(destination_path) as downloaded_file:
                self.assertTrue(downloaded_file.read())

    def test_local_file_download_file_prefix(self):
        sample_file_path = os.path.join(
            os.path.dirname(__file__), "files", "cvrf-rhba-2020-0017.xml"
        )

        with TempDirectory() as test_dir:
            destination_path = download_source_to_destination(
                source_uri=f"file://{sample_file_path}", destination_dir=test_dir.path
            )

            self.assertIsNotNone(destination_path)
            self.assertRegex(
                destination_path, rf"{test_dir.path}/cvrf-rhba-2020-0017.xml$"
            )
            with open(destination_path) as downloaded_file, open(
                sample_file_path
            ) as sample_file:
                downloaded_file_contents = downloaded_file.read()
                self.assertTrue(downloaded_file_contents)
                self.assertEqual(downloaded_file_contents, sample_file.read())

    def test_local_file_download_forward_slash_prefix(self):
        sample_file_path = os.path.join(
            os.path.dirname(__file__), "files", "cvrf-rhba-2020-0017.xml"
        )

        with TempDirectory() as test_dir:
            destination_path = download_source_to_destination(
                source_uri=f"{sample_file_path}", destination_dir=test_dir.path
            )

            self.assertIsNotNone(destination_path)
            self.assertRegex(
                destination_path, rf"{test_dir.path}/cvrf-rhba-2020-0017.xml$"
            )
            with open(destination_path) as downloaded_file, open(
                sample_file_path
            ) as sample_file:
                downloaded_file_contents = downloaded_file.read()
                self.assertTrue(downloaded_file_contents)
                self.assertEqual(downloaded_file_contents, sample_file.read())

    def test_bad_protocol(self):
        with TempDirectory() as test_dir:
            with self.assertRaisesRegex(
                ValueError,
                r"Unexpected error, should have been caught by step validation."
                r" Source \(.+\) must start with known protocol \(/|file://\|http://\|https://\).",
            ):
                download_source_to_destination(
                    source_uri="bad://www.redhat.com/security/data/metrics/ds/v2/RHEL8/rhel-8.ds.xml.bz2",
                    destination_dir=test_dir.path,
                )

    def test_https_bad_uri(self):
        with TempDirectory() as test_dir:
            with self.assertRaisesRegex(
                RuntimeError,
                r"Error downloading file \(.+\): HTTP Error 404: Not Found",
            ):
                download_source_to_destination(
                    source_uri="https://www.redhat.com/security/data/metrics/ds/v2/RHEL8/does-not-exist.ds.xml.bz2",
                    destination_dir=test_dir.path,
                )


class TestUploadFile(BaseTestCase):
    def __create_http_response_side_effect(self, read_return):
        def http_response_side_effect(request):
            mock_response = Mock()
            mock_response.read.return_value = read_return
            mock_response.status = "201"
            mock_response.reason = "Created"
            return mock_response

        return http_response_side_effect

    def test_source_file_does_not_exist(self):
        with self.assertRaisesRegex(
            ValueError, r"Given file path \(/does/not/exist\) to upload does not exist."
        ):
            upload_file(file_path="/does/not/exist", destination_uri="/does/not/matter")

    def test_invalid_destination_uri(self):
        sample_file_path = os.path.join(
            os.path.dirname(__file__), "files", "sample.yaml"
        )

        with self.assertRaisesRegex(
            ValueError,
            r"Unexpected error, should have been caught by step validation."
            r" Destination \(wont-work:///does/not/matter\) must start with known protocol"
            r"\(/|file://|http://|https://\).",
        ):
            upload_file(
                file_path=sample_file_path,
                destination_uri="wont-work:///does/not/matter",
            )

    def test_file_prefix(self):
        sample_file_path = os.path.join(
            os.path.dirname(__file__), "files", "sample.yaml"
        )

        with TempDirectory() as test_dir:
            destination_dir_path = os.path.join(test_dir.path, "test_dest")
            actual_result = upload_file(
                file_path=sample_file_path,
                destination_uri=f"file://{destination_dir_path}",
            )

            expected_result = os.path.join(destination_dir_path, "sample.yaml")
            self.assertEqual(expected_result, actual_result)

            with open(actual_result, "r") as uploaded_file, open(
                sample_file_path, "r"
            ) as original_file:
                self.assertEqual(original_file.read(), uploaded_file.read())

    def test_forward_slash_prefix(self):
        sample_file_path = os.path.join(
            os.path.dirname(__file__), "files", "sample.yaml"
        )

        with TempDirectory() as test_dir:
            destination_dir_path = os.path.join(test_dir.path, "test_dest")
            actual_result = upload_file(
                file_path=sample_file_path, destination_uri=f"{destination_dir_path}"
            )

            expected_result = os.path.join(destination_dir_path, "sample.yaml")
            self.assertEqual(expected_result, actual_result)

            with open(actual_result, "r") as uploaded_file, open(
                sample_file_path, "r"
            ) as original_file:
                self.assertEqual(original_file.read(), uploaded_file.read())

    @patch.object(urllib.request.OpenerDirector, "open")
    def test_http_prefix_no_auth(self, opener_open_mock):
        opener_open_mock.side_effect = self.__create_http_response_side_effect(
            b"hello world 42"
        )

        sample_file_path = os.path.join(
            os.path.dirname(__file__), "files", "sample.yaml"
        )

        actual_result = upload_file(
            file_path=sample_file_path, destination_uri="http://ploigos.com/test/foo42"
        )
        self.assertEqual(
            "status=201, reason=Created, body=hello world 42", actual_result
        )

    @patch.object(urllib.request.OpenerDirector, "open")
    def test_https_prefix_no_auth(self, opener_open_mock):
        opener_open_mock.side_effect = self.__create_http_response_side_effect(
            b"hello world 42"
        )

        sample_file_path = os.path.join(
            os.path.dirname(__file__), "files", "sample.yaml"
        )

        actual_result = upload_file(
            file_path=sample_file_path, destination_uri="https://ploigos.com/test/foo42"
        )
        self.assertEqual(
            "status=201, reason=Created, body=hello world 42", actual_result
        )

    @patch.object(urllib.request.OpenerDirector, "open")
    @patch("urllib.request.HTTPPasswordMgrWithDefaultRealm")
    def test_https_prefix_auth(self, pass_manager_mock, opener_open_mock):
        opener_open_mock.side_effect = self.__create_http_response_side_effect(
            b"hello world 42"
        )

        sample_file_path = os.path.join(
            os.path.dirname(__file__), "files", "sample.yaml"
        )

        actual_result = upload_file(
            file_path=sample_file_path,
            destination_uri="https://ploigos.com/test/foo42",
            username="test_user",
            password="pass123",
        )
        self.assertEqual(
            "status=201, reason=Created, body=hello world 42", actual_result
        )

        pass_manager_mock().add_password.assert_called_once_with(
            None, "ploigos.com", "test_user", "pass123"
        )

    @patch.object(urllib.request.OpenerDirector, "open")
    def test_https_prefix_http_error(self, opener_open_mock):
        opener_open_mock.side_effect = urllib.error.HTTPError(
            url="https://ploigos.com/test/foo42",
            code=442,
            msg="mock error",
            hdrs=None,
            fp=None,
        )

        sample_file_path = os.path.join(
            os.path.dirname(__file__), "files", "sample.yaml"
        )

        with self.assertRaisesRegex(
            RuntimeError,
            rf"Error uploading file \({sample_file_path}\)"
            r" to destination \(https://ploigos.com/test/foo42\) with user name"
            r" \(None\) and password \(None\): HTTP Error 442: mock error",
        ):
            upload_file(
                file_path=sample_file_path,
                destination_uri="https://ploigos.com/test/foo42",
            )


class TestFileMisc(BaseTestCase):
    def test_create_parent_dir(self):
        with TempDirectory() as test_dir:
            file_path = os.path.join(test_dir.path, "hello/world/does/not/exit/foo.yml")

            self.assertFalse(os.path.exists(file_path))
            self.assertFalse(os.path.exists(os.path.dirname(file_path)))

            create_parent_dir(file_path)
            self.assertFalse(os.path.exists(file_path))
            self.assertTrue(os.path.exists(os.path.dirname(file_path)))

    def test_base64_encode(self):
        with TempDirectory() as test_dir:
            sample_file_path = os.path.join(
                os.path.dirname(__file__), "files", "sample.txt"
            )

            result = base64_encode(sample_file_path)
            self.assertEqual(result, "c2FtcGxlIHRleHQgZmlsZQ==")

    def test_get_file_hash(self):
        with TempDirectory() as test_dir:
            sample_file_path = os.path.join(
                os.path.dirname(__file__), "files", "sample.txt"
            )

            result = get_file_hash(sample_file_path)
            self.assertEqual(
                result,
                "09daa01246aa5ee9c29f64f644627a0ea83247857dfea2665689e26b166eef47",
            )

    def test_get_file_extension(self):
        """This test verifies that the extension of a file is correctly retrieved."""

        # Set up test / mock data
        file_path = "/path/to/my/file.xml"

        # Run the test
        file_extension = get_file_extension(file_path)

        # Verification of results
        self.assertEqual(file_extension, ".xml")

    def test_is_compressed_true(self):
        """This test verifies that a file with an extension listed in the file
        module's SUPPORTED_COMPRESSION_EXTENSIONS is recognized as compressed.
        """

        # Set up test / mock data
        file_path = "/path/to/test-compressed-file.bz2"

        # Run the test
        compressed = is_compressed(file_path)

        # Verification of results
        self.assertTrue(compressed)

    def test_is_compressed_false_unsupported(self):
        """This test verifies that a file with an extension not listed in the file
        module's SUPPORTED_COMPRESSION_EXTENSIONS is not recognized as compressed.
        """

        # Set up test / mock data
        file_path = "/path/to/test-unsupported-but-compressed.iso"

        # Run the test
        compressed = is_compressed(file_path)

        # Verification of results
        self.assertFalse(compressed)
