from io import StringIO
import json
import os.path
import sh

import unittest
from testfixtures import TempDirectory
from unittest.mock import patch

from tests.helpers.base_test_case import BaseTestCase
from tests.helpers.sops_integration_test_case import SOPSIntegrationTestCase
from tests.helpers.test_utils import Any

from ploigos_step_runner.config.config_value import ConfigValue
from ploigos_step_runner.config.decryptors.sops import SOPS
from ploigos_step_runner.utils.file import parse_yaml_or_json_file

@patch('sh.sops', create=True)
class TestSOPSConfigValueDecryptor(BaseTestCase):
    def test_can_decrypt_true(self, sops_mock):
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config-secret-stuff.yml'
        )

        config_value = ConfigValue(
            value='ENC[AES256_GCM,data:UGKfnzsSrciR7GXZJhOCMmFrz3Y6V3pZsd3P,iv:yuReqA+n+rRXVHMc+2US5t7yPx54sooZSXWV4KLjDIs=,tag:jueP7/ZWLfYrEuhh+4eS8g==,type:str]',
            parent_source=encrypted_config_file_path,
            path_parts=['step-runner-config', 'global-environment-defaults', 'DEV', 'kube-api-token']
        )

        sops_decryptor = SOPS()
        self.assertTrue(
            sops_decryptor.can_decrypt(config_value)
        )

    def test_can_decrypt_false(self, sops_mock):
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config-secret-stuff.yml'
        )

        config_value = ConfigValue(
            value='not a sops encrypted value',
            parent_source=encrypted_config_file_path,
            path_parts=['step-runner-config', 'global-environment-defaults', 'DEV', 'kube-api-token']
        )

        sops_decryptor = SOPS()
        self.assertFalse(
            sops_decryptor.can_decrypt(config_value)
        )

    def test_can_can_decrypt_not_string(self, sops_mock):
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config-secret-stuff.yml'
        )

        config_value = ConfigValue(
            value=True,
            parent_source=encrypted_config_file_path,
            path_parts=['step-runner-config', 'global-environment-defaults', 'DEV', 'kube-api-token']
        )

        sops_decryptor = SOPS()
        self.assertFalse(
            sops_decryptor.can_decrypt(config_value)
        )

    def test_decrypt_parent_source_file(self, sops_mock):
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config-secret-stuff.yml'
        )

        config_value = ConfigValue(
            value='ENC[AES256_GCM,data:UGKfnzsSrciR7GXZJhOCMmFrz3Y6V3pZsd3P,iv:yuReqA+n+rRXVHMc+2US5t7yPx54sooZSXWV4KLjDIs=,tag:jueP7/ZWLfYrEuhh+4eS8g==,type:str]',
            parent_source=encrypted_config_file_path,
            path_parts=['step-runner-config', 'global-environment-defaults', 'DEV', 'kube-api-token']
        )

        sops_decryptor = SOPS()

        sops_decryptor.decrypt(config_value)
        sops_mock.assert_called_once_with(
            '--decrypt',
            '--extract=["step-runner-config"]["global-environment-defaults"]["DEV"]["kube-api-token"]',
            None,
            encrypted_config_file_path,
            _in=None,
            _out=Any(StringIO),
            _err=Any(StringIO)
        )

    def test_decrypt_additional_sops_args(self, sops_mock):
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config-secret-stuff.yml'
        )

        config_value = ConfigValue(
            value='ENC[AES256_GCM,data:UGKfnzsSrciR7GXZJhOCMmFrz3Y6V3pZsd3P,iv:yuReqA+n+rRXVHMc+2US5t7yPx54sooZSXWV4KLjDIs=,tag:jueP7/ZWLfYrEuhh+4eS8g==,type:str]',
            parent_source=encrypted_config_file_path,
            path_parts=['step-runner-config', 'global-environment-defaults', 'DEV', 'kube-api-token']
        )

        sops_decryptor = SOPS(
            additional_sops_args=[
                '--aws-profile=foo'
            ]
        )

        sops_decryptor.decrypt(config_value)
        sops_mock.assert_called_once_with(
            '--decrypt',
            '--extract=["step-runner-config"]["global-environment-defaults"]["DEV"]["kube-api-token"]',
            None,
            encrypted_config_file_path,
            '--aws-profile=foo',
            _in=None,
            _out=Any(StringIO),
            _err=Any(StringIO)
        )

    def test_decrypt_parent_source_dict(self, sops_mock):
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config-secret-stuff.yml'
        )

        encrypted_config = parse_yaml_or_json_file(encrypted_config_file_path)
        encrypted_config_json = json.dumps(encrypted_config)

        config_value = ConfigValue(
            value='ENC[AES256_GCM,data:UGKfnzsSrciR7GXZJhOCMmFrz3Y6V3pZsd3P,iv:yuReqA+n+rRXVHMc+2US5t7yPx54sooZSXWV4KLjDIs=,tag:jueP7/ZWLfYrEuhh+4eS8g==,type:str]',
            parent_source=encrypted_config,
            path_parts=['step-runner-config', 'global-environment-defaults', 'DEV', 'kube-api-token']
        )

        sops_decryptor = SOPS()

        sops_decryptor.decrypt(config_value)
        sops_mock.assert_called_once_with(
            '--decrypt',
            '--extract=["step-runner-config"]["global-environment-defaults"]["DEV"]["kube-api-token"]',
            '--input-type=json',
            '/dev/stdin',
            _in=encrypted_config_json,
            _out=Any(StringIO),
            _err=Any(StringIO)
        )

    def test_decrypt_parent_source_file_does_not_exist(self, sops_mock):
        config_value = ConfigValue(
            value='ENC[AES256_GCM,data:UGKfnzsSrciR7GXZJhOCMmFrz3Y6V3pZsd3P,iv:yuReqA+n+rRXVHMc+2US5t7yPx54sooZSXWV4KLjDIs=,tag:jueP7/ZWLfYrEuhh+4eS8g==,type:str]',
            parent_source='does-not-exist.yml',
            path_parts=['step-runner-config', 'global-environment-defaults', 'DEV', 'kube-api-token']
        )

        sops_decryptor = SOPS()

        with self.assertRaisesRegex(
            ValueError,
            r"Given config value \(ConfigValue\(.*\)\) parent source \(does-not-exist.yml\)" \
            r" is of type \(str\) but is not a path to a file that exists"
        ):
            sops_decryptor.decrypt(config_value)

    def test_decrypt_parent_source_none(self, sops_mock):
        config_value = ConfigValue(
            value='ENC[AES256_GCM,data:UGKfnzsSrciR7GXZJhOCMmFrz3Y6V3pZsd3P,iv:yuReqA+n+rRXVHMc+2US5t7yPx54sooZSXWV4KLjDIs=,tag:jueP7/ZWLfYrEuhh+4eS8g==,type:str]',
            parent_source=None,
            path_parts=['step-runner-config', 'global-environment-defaults', 'DEV', 'kube-api-token']
        )

        sops_decryptor = SOPS()

        with self.assertRaisesRegex(
            ValueError,
            r"Given config value \(ConfigValue\(.*\)\) parent source \(None\) " \
            r"is expected to be of type dict or str but is of type: <class 'NoneType'>"
        ):
            sops_decryptor.decrypt(config_value)

    def test_decrypt_sops_error(self, sops_mock):
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config-secret-stuff.yml'
        )

        config_value = ConfigValue(
            value='ENC[AES256_GCM,data:UGKfnzsSrciR7GXZJhOCMmFrz3Y6V3pZsd3P,iv:yuReqA+n+rRXVHMc+2US5t7yPx54sooZSXWV4KLjDIs=,tag:jueP7/ZWLfYrEuhh+4eS8g==,type:str]',
            parent_source=encrypted_config_file_path,
            path_parts=['step-runner-config', 'global-environment-defaults', 'DEV', 'kube-api-token']
        )

        sops_decryptor = SOPS()

        sh.sops.side_effect = sh.ErrorReturnCode('sops', b'mock stdout', b'mock error about issue running sops')
        with self.assertRaisesRegex(
            RuntimeError,
            r"Error invoking sops when trying to decrypt config value \(ConfigValue\(.*\)\):"
        ):
            sops_decryptor.decrypt(config_value)

    def test_get_sops_value_path(self, sops_mock):
        config_value = ConfigValue(
            value='ENC[AES256_GCM,data:UGKfnzsSrciR7GXZJhOCMmFrz3Y6V3pZsd3P,iv:yuReqA+n+rRXVHMc+2US5t7yPx54sooZSXWV4KLjDIs=,tag:jueP7/ZWLfYrEuhh+4eS8g==,type:str]',
            parent_source=None,
            path_parts=["step-runner-config", "step-foo", 0, "config", "test1"]
        )

        sops_value_path = SOPS.get_sops_value_path(config_value)
        self.assertEqual(
            sops_value_path,
            '["step-runner-config"]["step-foo"][0]["config"]["test1"]')

class TestSOPSConfigValueDecryptorSOPSIntegrationTests(SOPSIntegrationTestCase):
    def test_can_decrypt_true(self):
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config-secret-stuff.yml'
        )

        config_value = ConfigValue(
            value='ENC[AES256_GCM,data:UGKfnzsSrciR7GXZJhOCMmFrz3Y6V3pZsd3P,iv:yuReqA+n+rRXVHMc+2US5t7yPx54sooZSXWV4KLjDIs=,tag:jueP7/ZWLfYrEuhh+4eS8g==,type:str]',
            parent_source=encrypted_config_file_path,
            path_parts=['step-runner-config', 'global-environment-defaults', 'DEV', 'kube-api-token']
        )

        sops_decryptor = SOPS()
        self.assertTrue(
            sops_decryptor.can_decrypt(config_value)
        )

    def test_can_decrypt_false(self):
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config-secret-stuff.yml'
        )

        config_value = ConfigValue(
            value='not a sops encrypted value',
            parent_source=encrypted_config_file_path,
            path_parts=['step-runner-config', 'global-environment-defaults', 'DEV', 'kube-api-token']
        )

        sops_decryptor = SOPS()
        self.assertFalse(
            sops_decryptor.can_decrypt(config_value)
        )

    def test_decrypt_parent_source_file(self):
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config-secret-stuff.yml'
        )

        config_value = ConfigValue(
            value='ENC[AES256_GCM,data:UGKfnzsSrciR7GXZJhOCMmFrz3Y6V3pZsd3P,iv:yuReqA+n+rRXVHMc+2US5t7yPx54sooZSXWV4KLjDIs=,tag:jueP7/ZWLfYrEuhh+4eS8g==,type:str]',
            parent_source=encrypted_config_file_path,
            path_parts=['step-runner-config', 'global-environment-defaults', 'DEV', 'kube-api-token']
        )

        sops_decryptor = SOPS()

        decrypted_value = sops_decryptor.decrypt(config_value)

        self.assertEqual(
            decrypted_value,
            'super secret kube api token'
        )

    def test_decrypt_parent_source_dict(self):
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config-secret-stuff.yml'
        )

        encrypted_config = parse_yaml_or_json_file(encrypted_config_file_path)

        config_value = ConfigValue(
            value='ENC[AES256_GCM,data:UGKfnzsSrciR7GXZJhOCMmFrz3Y6V3pZsd3P,iv:yuReqA+n+rRXVHMc+2US5t7yPx54sooZSXWV4KLjDIs=,tag:jueP7/ZWLfYrEuhh+4eS8g==,type:str]',
            parent_source=encrypted_config,
            path_parts=['step-runner-config', 'global-environment-defaults', 'DEV', 'kube-api-token']
        )

        sops_decryptor = SOPS()

        decrypted_value = sops_decryptor.decrypt(config_value)

        self.assertEqual(
            decrypted_value,
            'super secret kube api token'
        )

    def test_decrypt_parent_source_file_does_not_exist(self):
        config_value = ConfigValue(
            value='ENC[AES256_GCM,data:UGKfnzsSrciR7GXZJhOCMmFrz3Y6V3pZsd3P,iv:yuReqA+n+rRXVHMc+2US5t7yPx54sooZSXWV4KLjDIs=,tag:jueP7/ZWLfYrEuhh+4eS8g==,type:str]',
            parent_source='does-not-exist.yml',
            path_parts=['step-runner-config', 'global-environment-defaults', 'DEV', 'kube-api-token']
        )

        sops_decryptor = SOPS()

        with self.assertRaisesRegex(
            ValueError,
            r"Given config value \(ConfigValue\(.*\)\) parent source \(does-not-exist.yml\)" \
            r" is of type \(str\) but is not a path to a file that exists"
        ):
            sops_decryptor.decrypt(config_value)

    def test_decrypt_parent_source_none(self):
        config_value = ConfigValue(
            value='ENC[AES256_GCM,data:UGKfnzsSrciR7GXZJhOCMmFrz3Y6V3pZsd3P,iv:yuReqA+n+rRXVHMc+2US5t7yPx54sooZSXWV4KLjDIs=,tag:jueP7/ZWLfYrEuhh+4eS8g==,type:str]',
            parent_source=None,
            path_parts=['step-runner-config', 'global-environment-defaults', 'DEV', 'kube-api-token']
        )

        sops_decryptor = SOPS()

        # with self.assertRaisesRegex(
        #     ValueError,
        #     r"Given config value \(ConfigValue\(.*\)\) parent source \(None\) " \
        #     r"is expected to be of type dict or str but is of type: <class 'NoneType'>"
        # ):
            sops_decryptor.decrypt(config_value)

    def test_decrypt_no_valid_key(self):
        encrypted_config_file_path = os.path.join(
            os.path.dirname(__file__),
            'files',
            'step-runner-config-secret-stuff.yml'
        )

        config_value = ConfigValue(
            value='ENC[AES256_GCM,data:UGKfnzsSrciR7GXZJhOCMmFrz3Y6V3pZsd3P,iv:yuReqA+n+rRXVHMc+2US5t7yPx54sooZSXWV4KLjDIs=,tag:jueP7/ZWLfYrEuhh+4eS8g==,type:str]',
            parent_source=encrypted_config_file_path,
            path_parts=['step-runner-config', 'global-environment-defaults', 'DEV', 'kube-api-token']
        )

        sops_decryptor = SOPS()

        # delete the gpg key needed to decrypt the value
        self.delete_gpg_key()

        # attempt to decrypt the value
        with self.assertRaisesRegex(
            RuntimeError,
            r"Error invoking sops when trying to decrypt config value \(ConfigValue\(.*\)\):"
        ):
            sops_decryptor.decrypt(config_value)