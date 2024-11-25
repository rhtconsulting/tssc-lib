import os
import re
from contextlib import redirect_stdout
from io import IOBase, StringIO
from unittest.mock import patch

import sh
from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase
from tests.helpers.test_utils import Any, create_sh_side_effect
from ploigos_step_runner.results import StepResult
from ploigos_step_runner.exceptions import StepRunnerException
from ploigos_step_runner.step_implementers.shared.openscap_generic import OpenSCAPGeneric


class BaseTestStepImplementerSharedOpenSCAPGeneric(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            step_name='',
            implementer='',
            workflow_result=None,
            parent_work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=OpenSCAPGeneric,
            step_config=step_config,
            step_name=step_name,
            implementer=implementer,
            workflow_result=workflow_result,
            parent_work_dir_path=parent_work_dir_path
        )

class TestStepImplementerSharedOpenSCAPGeneric_step_implementer_config_defaults(
    BaseTestStepImplementerSharedOpenSCAPGeneric
):
    def test_result(self):
        defaults = OpenSCAPGeneric.step_implementer_config_defaults()
        expected_defaults = {
            'oscap-fetch-remote-resources': True,
            'container-image-pull-registry-type': 'containers-storage:',
            'container-image-registry-type': 'containers-storage:'
        }
        self.assertEqual(defaults, expected_defaults)

class TestStepImplementerSharedOpenSCAPGeneric__required_config_or_result_keys(
    BaseTestStepImplementerSharedOpenSCAPGeneric
):
    def test_result(self):
        required_keys = OpenSCAPGeneric._required_config_or_result_keys()
        expected_required_keys = [
            'oscap-input-definitions-uri',
            [
                'container-image-build-address',
                'container-image-push-address',
                'container-image-pull-address',
                'container-image-address',
                'container-image-tag'
            ],
            'container-image-pull-registry-type',
            ['container-image-pull-registry-type', 'container-image-registry-type']
        ]
        self.assertEqual(required_keys, expected_required_keys)

@patch("ploigos_step_runner.step_implementer.StepImplementer._validate_required_config_or_previous_step_result_artifact_keys")
class TestStepImplementerSharedOpenSCAPGeneric__validate_required_config_or_previous_step_result_artifact_keys(
    BaseTestStepImplementerSharedOpenSCAPGeneric
):
    def test__valid(self, mock_super_validate):
        step_config = {
            'oscap-input-definitions-uri': 'https://www.redhat.com/security/data/oval/v2/RHEL8/rhel-8.oval.xml.bz2',
            'image-tar-file': 'does-not-matter'
        }

        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='OpenSCAP',
                parent_work_dir_path=parent_work_dir_path
            )

            step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            mock_super_validate.assert_called_once_with()

    def test_invalid_protocal(self, mock_super_validate):
        oscap_input_definitions_uri = 'foo://www.redhat.com/security/data/oval/v2/RHEL8/rhel-8.oval.xml.bz2'
        step_config = {
            'oscap-input-definitions-uri': oscap_input_definitions_uri,
            'image-tar-file': 'does-not-matter'
        }
        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='OpenSCAP',
                parent_work_dir_path=parent_work_dir_path
            )

            with self.assertRaisesRegex(
                    AssertionError,
                    re.compile(
                        r'Open SCAP input definitions source '
                        rf'\({oscap_input_definitions_uri}\) must start with known protocol '
                        r'\(file://\|http://\|https://\)\.'
                    )
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            mock_super_validate.assert_called_once_with()

    def test_invalid_extension(self, mock_super_validate):
        oscap_input_definitions_uri = 'https://www.redhat.com/security/data/oval/v2/RHEL8/rhel-8.oval.xml.foo'
        step_config = {
            'oscap-input-definitions-uri': oscap_input_definitions_uri,
            'image-tar-file': 'does-not-matter'
        }

        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='OpenSCAP',
                parent_work_dir_path=parent_work_dir_path,
            )

            with self.assertRaisesRegex(
                AssertionError,
                re.compile(
                    r'Open SCAP input definitions source '
                    rf'\({oscap_input_definitions_uri}\) must be of known type \(xml\|bz2\), got: \.foo'
                )
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            mock_super_validate.assert_called_once_with()

    def test_invalid_severity(self, mock_super_validate):
        oscap_severity = 'bad'
        step_config = {
            'oscap-input-definitions-uri': 'https://www.redhat.com/security/data/oval/v2/RHEL8/rhel-8.oval.xml.bz2',
            'image-tar-file': 'does-not-matter',
            'oscap-severity': oscap_severity
        }

        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='OpenSCAP',
                parent_work_dir_path=parent_work_dir_path
            )

            with self.assertRaisesRegex(
                AssertionError,
                re.compile(
                    rf'Open SCAP severity \({oscap_severity}\)' \
                    r' must be of know severity \(low\|moderate\|important\|critical\).'
                )
            ):
                step_implementer._validate_required_config_or_previous_step_result_artifact_keys()

            mock_super_validate.assert_called_once_with()

class TestStepImplementerSharedOpenSCAPGeneric___get_oscap_document_type(
    BaseTestStepImplementerSharedOpenSCAPGeneric
):
    @patch('sh.oscap', create=True)
    def test_sds(self, oscap_mock):
        oscap_input_file = '/does/not/matter.xml'

        sh.oscap.info.side_effect = create_sh_side_effect(
            mock_stdout="""
Document type: Source Data Stream
Imported: 2020-10-07T05:34:29

Stream: scap_org.open-scap_datastream_from_xccdf_com.redhat.rhsa-all.xml-xccdf12
Generated: (null)
Version: 1.2
Checklists:
	Ref-Id: scap_org.open-scap_cref_com.redhat.rhsa-all.xml-xccdf12
		Status: incomplete
		Resolved: true
		Profiles:
		Referenced check files:
			com.redhat.rhsa-all.xml
				system: http://oval.mitre.org/XMLSchema/oval-definitions-5
Checks:
	Ref-Id: scap_org.open-scap_cref_com.redhat.rhsa-all.xml
No dictionaries."""
        )

        oscap_document_type = OpenSCAPGeneric._OpenSCAPGeneric__get_oscap_document_type(
            oscap_input_file=oscap_input_file
        )

        sh.oscap.info.assert_called_once_with(
            oscap_input_file,
            _out=Any(IOBase)
        )

        self.assertEqual(oscap_document_type, 'Source Data Stream')

    @patch('sh.oscap', create=True)
    def test_oval(self, oscap_mock):
        oscap_input_file = '/does/not/matter.xml'

        sh.oscap.info.side_effect = create_sh_side_effect(
            mock_stdout="""
Document type: OVAL Definitions
OVAL version: 5.10
Generated: 2020-10-06T23:36:01
Imported: 2020-10-06T23:36:04"""
        )

        oscap_document_type = OpenSCAPGeneric._OpenSCAPGeneric__get_oscap_document_type(
            oscap_input_file=oscap_input_file
        )

        oscap_document_type = OpenSCAPGeneric._OpenSCAPGeneric__get_oscap_document_type(
            oscap_input_file=oscap_input_file
        )

        self.assertEqual(oscap_document_type, 'OVAL Definitions')

    @patch('sh.oscap', create=True)
    def test_xccdf(self, oscap_mock):
        oscap_input_file = '/does/not/matter.xml'

        sh.oscap.info.side_effect = create_sh_side_effect(
            mock_stdout="""
Document type: XCCDF Checklist
Checklist version: 1.1
Imported: 2020-02-11T13:41:07
Status: draft
Generated: 2020-02-11
Resolved: true
Profiles:
	Title: Protection Profile for General Purpose Operating Systems
		Id: ospp
	Title: PCI-DSS v3.2.1 Control Baseline for Red Hat Enterprise Linux 8
		Id: pci-dss
	Title: [DRAFT] DISA STIG for Red Hat Enterprise Linux 8
		Id: stig
	Title: Australian Cyber Security Centre (ACSC) Essential Eight
		Id: e8
Referenced check files:
	ssg-rhel8-oval.xml
		system: http://oval.mitre.org/XMLSchema/oval-definitions-5
	ssg-rhel8-ocil.xml
		system: http://scap.nist.gov/schema/ocil/2
	https://www.redhat.com/security/data/oval/com.redhat.rhsa-RHEL8.xml
		system: http://oval.mitre.org/XMLSchema/oval-definitions-5"""
        )

        oscap_document_type = OpenSCAPGeneric._OpenSCAPGeneric__get_oscap_document_type(
            oscap_input_file=oscap_input_file
        )

        sh.oscap.info.assert_called_once_with(
            oscap_input_file,
            _out=Any(IOBase)
        )

        self.assertEqual(oscap_document_type, 'XCCDF Checklist')

    @patch('sh.oscap', create=True)
    def test_error(self, oscap_mock):
        oscap_input_file = '/does/not/matter.xml'

        sh.oscap.info.side_effect = sh.ErrorReturnCode(
            'oscap info',
            b'mock out',
            b'mock error'
        )

        with self.assertRaisesRegex(
                StepRunnerException,
                re.compile(
                    r"Error getting document type of oscap"
                    rf" input file \({oscap_input_file}\):"
                    r".*RAN: oscap info"
                    r".*STDOUT:"
                    r".*mock out"
                    r".*STDERR:"
                    r".*mock error",
                    re.DOTALL
                )
        ):
            OpenSCAPGeneric._OpenSCAPGeneric__get_oscap_document_type(
                oscap_input_file=oscap_input_file
            )

        sh.oscap.info.assert_called_once_with(
            oscap_input_file,
            _out=Any(IOBase)
        )

class TestStepImplementerSharedOpenSCAPGeneric___get_oscap_eval_type_based_on_document_type(
    BaseTestStepImplementerSharedOpenSCAPGeneric
):
    def test_sds(self):
        oscap_document_type = 'Source Data Stream'

        oscap_eval_type = \
            OpenSCAPGeneric._OpenSCAPGeneric__get_oscap_eval_type_based_on_document_type(
                oscap_document_type=oscap_document_type
            )

        self.assertEqual(oscap_eval_type, 'xccdf')

    def test_xccdf(self):
        oscap_document_type = 'XCCDF Checklist'

        oscap_eval_type = \
            OpenSCAPGeneric._OpenSCAPGeneric__get_oscap_eval_type_based_on_document_type(
                oscap_document_type=oscap_document_type
            )

        self.assertEqual(oscap_eval_type, 'xccdf')

    def test_oval(self):
        oscap_document_type = 'OVAL Definitions'

        oscap_eval_type = \
            OpenSCAPGeneric._OpenSCAPGeneric__get_oscap_eval_type_based_on_document_type(
                oscap_document_type=oscap_document_type
            )

        self.assertEqual(oscap_eval_type, 'oval')

    def test_unknown(self):
        oscap_document_type = 'What is this nonsense?'

        oscap_eval_type = \
            OpenSCAPGeneric._OpenSCAPGeneric__get_oscap_eval_type_based_on_document_type(
                oscap_document_type=oscap_document_type
            )

        self.assertEqual(oscap_eval_type, None)

class TestStepImplementerSharedOpenSCAPGeneric___run_oscap_scan(
    BaseTestStepImplementerSharedOpenSCAPGeneric
):
    def __run_test_xccdf_do_not_fetch_remote_with_profile_all_pass(
            self,
            buildah_mock,
            oscap_eval_type,
            oscap_fetch_remote_resources,
            oscap_stdout,
            oscap_stdout_expected,
            oscap_profile=None,
            oscap_tailoring_file=None,
            oscap_eval_success_expected=True,
            exit_code=0,
            oscap_eval_fails_expected=None,
            oscap_failure_met_threshold_expected=False,
            oscap_severity=None
    ):
        with TempDirectory() as temp_dir:
            buildah_unshare_command = sh.buildah.bake('unshare')
            oscap_input_file = '/does/not/matter/input.xml'
            oscap_out_file_path = os.path.join(temp_dir.path, 'out')
            oscap_xml_results_file_path = '/does/not/matter/results.xml'
            oscap_html_report_path = '/does/not/matter/results.html'
            container_mount_path = '/does/not/matter/coutainer_mount'

            exception = None
            if exit_code == 2:
                exception = sh.ErrorReturnCode_2(
                    'oscap-chroot eval',
                    bytes(oscap_stdout, 'utf-8'),
                    bytes(f'mock error - exit code {exit_code}', 'utf-8')
                )
            elif exit_code == 1:
                exception = sh.ErrorReturnCode_1(
                    'oscap-chroot eval',
                    bytes(oscap_stdout, 'utf-8'),
                    bytes(f'mock error - exit code {exit_code}', 'utf-8')
                )
            elif exit_code:
                exception = sh.ErrorReturnCode(
                    'oscap-chroot eval',
                    bytes(oscap_stdout, 'utf-8'),
                    bytes(f'mock error - exit code {exit_code}', 'utf-8')
                )

            buildah_mock.bake('unshare').bake('oscap-chroot').side_effect = create_sh_side_effect(
                mock_stdout=oscap_stdout,
                exception=exception
            )

            stdout_buff = StringIO()

            oscap_severity_index = OpenSCAPGeneric._OpenSCAPGeneric__parse_sev_to_int(oscap_severity=oscap_severity)

            with redirect_stdout(stdout_buff):
                oscap_eval_success, oscap_eval_fails, oscap_failure_met_threshold = OpenSCAPGeneric._OpenSCAPGeneric__run_oscap_scan(
                    buildah_unshare_command=buildah_unshare_command,
                    oscap_eval_type=oscap_eval_type,
                    oscap_input_file=oscap_input_file,
                    oscap_out_file_path=oscap_out_file_path,
                    oscap_xml_results_file_path=oscap_xml_results_file_path,
                    oscap_html_report_path=oscap_html_report_path,
                    container_mount_path=container_mount_path,
                    oscap_profile=oscap_profile,
                    oscap_tailoring_file=oscap_tailoring_file,
                    oscap_fetch_remote_resources=oscap_fetch_remote_resources,
                    oscap_severity_index=oscap_severity_index
                )
            print(f"{stdout_buff.getvalue()}")
            if oscap_profile:
                oscap_profile_flag = f"--profile={oscap_profile}"
            else:
                oscap_profile_flag = None

            if oscap_fetch_remote_resources:
                oscap_fetch_remote_resources_flag = "--fetch-remote-resources"
            else:
                oscap_fetch_remote_resources_flag = None

            if oscap_tailoring_file:
                oscap_tailoring_file_flag = f"--tailoring-file={oscap_tailoring_file}"
            else:
                oscap_tailoring_file_flag = None

            buildah_mock.bake('unshare').bake.assert_called_with('oscap-chroot')
            buildah_mock.bake('unshare').bake('oscap-chroot').assert_called_once_with(
                container_mount_path,
                oscap_eval_type,
                'eval',
                oscap_profile_flag,
                oscap_fetch_remote_resources_flag,
                oscap_tailoring_file_flag,
                f'--results={oscap_xml_results_file_path}',
                f'--report={oscap_html_report_path}',
                oscap_input_file,
                _out=Any(IOBase),
                _err=Any(IOBase),
                _tee='err'
            )

            self.assertEqual(oscap_eval_success, oscap_eval_success_expected)

            if oscap_eval_fails_expected:
                self.assertEqual(oscap_eval_fails, oscap_eval_fails_expected)

            self.assertEqual(oscap_failure_met_threshold, oscap_failure_met_threshold_expected)

            stdout = stdout_buff.getvalue()
            self.assertEqual(stdout, oscap_stdout_expected)

    @patch('sh.buildah', create=True)
    def test_xccdf_do_no_fetch_remote_with_profile_all_pass(self, buildah_mock):
        self.__run_test_xccdf_do_not_fetch_remote_with_profile_all_pass(
            buildah_mock=buildah_mock,
            oscap_eval_type='xccdf',
            oscap_profile='this.is.real.i.sware',
            oscap_fetch_remote_resources=False,
            oscap_stdout="""
Title\r	Enable Kernel Page-Table Isolation (KPTI)
Rule\r	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident\r	CCE-82194-2
Result\r	pass

Title\r	Install dnf-automatic Package
Rule\r	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident\r	CCE-82985-3
Result\r	pass""",
            oscap_stdout_expected="""
Title	Enable Kernel Page-Table Isolation (KPTI)
Rule	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident	CCE-82194-2
Result	pass

Title	Install dnf-automatic Package
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	pass
"""
        )

    @patch('sh.buildah', create=True)
    def test_xccdf_do_yes_fetch_remote_with_profile_all_pass(self, buildah_mock):
        self.__run_test_xccdf_do_not_fetch_remote_with_profile_all_pass(
            buildah_mock=buildah_mock,
            oscap_eval_type='xccdf',
            oscap_profile='this.is.real.i.sware',
            oscap_fetch_remote_resources=True,
            oscap_stdout="""
Title\r	Enable Kernel Page-Table Isolation (KPTI)
Rule\r	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident\r	CCE-82194-2
Result\r	pass

Title\r	Install dnf-automatic Package
Rule\r	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident\r	CCE-82985-3
Result\r	pass""",
            oscap_stdout_expected="""
Title	Enable Kernel Page-Table Isolation (KPTI)
Rule	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident	CCE-82194-2
Result	pass

Title	Install dnf-automatic Package
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	pass
"""
        )

    @patch('sh.buildah', create=True)
    def test_xccdf_do_yes_fetch_remote_no_profile_all_pass(self, buildah_mock):
        self.__run_test_xccdf_do_not_fetch_remote_with_profile_all_pass(
            buildah_mock=buildah_mock,
            oscap_eval_type='xccdf',
            oscap_profile=None,
            oscap_fetch_remote_resources=True,
            oscap_stdout="""
Title\r	Enable Kernel Page-Table Isolation (KPTI)
Rule\r	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident\r	CCE-82194-2
Result\r	pass

Title\r	Install dnf-automatic Package
Rule\r	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident\r	CCE-82985-3
Result\r	pass""",
            oscap_stdout_expected="""
Title	Enable Kernel Page-Table Isolation (KPTI)
Rule	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident	CCE-82194-2
Result	pass

Title	Install dnf-automatic Package
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	pass
"""
        )

    @patch('sh.buildah', create=True)
    def test_xccdf_do_not_fetch_remote_with_profile_with_fail_above_threshold(self, buildah_mock):
        self.__run_test_xccdf_do_not_fetch_remote_with_profile_all_pass(
            buildah_mock=buildah_mock,
            oscap_eval_type='xccdf',
            oscap_profile='this.is.real.i.sware',
            oscap_fetch_remote_resources=False,
            oscap_eval_success_expected=False,
            exit_code=2,
            oscap_stdout="""
Title\r	Enable Kernel Page-Table Isolation (KPTI)
Rule\r	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident\r	CCE-82194-2
Result\r	notapplicable

Title\r	Install dnf-automatic Package (Moderate)
Rule\r	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident\r	CCE-82985-3
Result\r	fail

Title\r	Ensure gpgcheck Enabled for All yum Package Repositories
Rule\r	xccdf_org.ssgproject.content_rule_ensure_gpgcheck_never_disabled
Ident\r	CCE-80792-5
Result\r	pass""",
            oscap_stdout_expected="""
Title	Enable Kernel Page-Table Isolation (KPTI)
Rule	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident	CCE-82194-2
Result	notapplicable

Title	Install dnf-automatic Package (Moderate)
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	fail

Title	Ensure gpgcheck Enabled for All yum Package Repositories
Rule	xccdf_org.ssgproject.content_rule_ensure_gpgcheck_never_disabled
Ident	CCE-80792-5
Result	pass
""",
            oscap_eval_fails_expected="""
Title	Install dnf-automatic Package (Moderate)
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	fail
""",
            oscap_failure_met_threshold_expected=True,
            oscap_severity='Low'
        )

    @patch('sh.buildah', create=True)
    def test_xccdf_do_not_fetch_remote_with_profile_with_fail_at_threshold(self, buildah_mock):
        self.__run_test_xccdf_do_not_fetch_remote_with_profile_all_pass(
            buildah_mock=buildah_mock,
            oscap_eval_type='xccdf',
            oscap_profile='this.is.real.i.sware',
            oscap_fetch_remote_resources=False,
            oscap_eval_success_expected=False,
            exit_code=2,
            oscap_stdout="""
Title\r	Enable Kernel Page-Table Isolation (KPTI)
Rule\r	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident\r	CCE-82194-2
Result\r	notapplicable

Title\r	Install dnf-automatic Package (Moderate)
Rule\r	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident\r	CCE-82985-3
Result\r	fail

Title\r	Ensure gpgcheck Enabled for All yum Package Repositories
Rule\r	xccdf_org.ssgproject.content_rule_ensure_gpgcheck_never_disabled
Ident\r	CCE-80792-5
Result\r	pass""",
            oscap_stdout_expected="""
Title	Enable Kernel Page-Table Isolation (KPTI)
Rule	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident	CCE-82194-2
Result	notapplicable

Title	Install dnf-automatic Package (Moderate)
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	fail

Title	Ensure gpgcheck Enabled for All yum Package Repositories
Rule	xccdf_org.ssgproject.content_rule_ensure_gpgcheck_never_disabled
Ident	CCE-80792-5
Result	pass
""",
            oscap_eval_fails_expected="""
Title	Install dnf-automatic Package (Moderate)
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	fail
""",
            oscap_failure_met_threshold_expected=True,
            oscap_severity='Moderate'
        )

    @patch('sh.buildah', create=True)
    def test_xccdf_do_not_fetch_remote_with_profile_with_fail_below_threshold(self, buildah_mock):
        self.__run_test_xccdf_do_not_fetch_remote_with_profile_all_pass(
            buildah_mock=buildah_mock,
            oscap_eval_type='xccdf',
            oscap_profile='this.is.real.i.sware',
            oscap_fetch_remote_resources=False,
            oscap_eval_success_expected=False,
            exit_code=2,
            oscap_stdout="""
Title\r	Enable Kernel Page-Table Isolation (KPTI)
Rule\r	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident\r	CCE-82194-2
Result\r	notapplicable

Title\r	Install dnf-automatic Package (Moderate)
Rule\r	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident\r	CCE-82985-3
Result\r	fail

Title\r	Ensure gpgcheck Enabled for All yum Package Repositories
Rule\r	xccdf_org.ssgproject.content_rule_ensure_gpgcheck_never_disabled
Ident\r	CCE-80792-5
Result\r	pass""",
            oscap_stdout_expected="""
Title	Enable Kernel Page-Table Isolation (KPTI)
Rule	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident	CCE-82194-2
Result	notapplicable

Title	Install dnf-automatic Package (Moderate)
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	fail

Title	Ensure gpgcheck Enabled for All yum Package Repositories
Rule	xccdf_org.ssgproject.content_rule_ensure_gpgcheck_never_disabled
Ident	CCE-80792-5
Result	pass
""",
            oscap_eval_fails_expected="""
Title	Install dnf-automatic Package (Moderate)
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	fail
""",
            oscap_failure_met_threshold_expected=False,
            oscap_severity='Critical'
        )

    @patch('sh.buildah', create=True)
    def test_xccdf_do_yes_fetch_remote_with_profile_with_fail(self, buildah_mock):
        self.__run_test_xccdf_do_not_fetch_remote_with_profile_all_pass(
            buildah_mock=buildah_mock,
            oscap_eval_type='xccdf',
            oscap_profile='this.is.real.i.sware',
            oscap_fetch_remote_resources=True,
            oscap_eval_success_expected=False,
            exit_code=2,
            oscap_stdout="""
Title\r	Enable Kernel Page-Table Isolation (KPTI)
Rule\r	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident\r	CCE-82194-2
Result\r	notapplicable

Title\r	Install dnf-automatic Package
Rule\r	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident\r	CCE-82985-3
Result\r	fail

Title\r	Ensure gpgcheck Enabled for All yum Package Repositories
Rule\r	xccdf_org.ssgproject.content_rule_ensure_gpgcheck_never_disabled
Ident\r	CCE-80792-5
Result\r	pass""",
            oscap_stdout_expected="""
Title	Enable Kernel Page-Table Isolation (KPTI)
Rule	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident	CCE-82194-2
Result	notapplicable

Title	Install dnf-automatic Package
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	fail

Title	Ensure gpgcheck Enabled for All yum Package Repositories
Rule	xccdf_org.ssgproject.content_rule_ensure_gpgcheck_never_disabled
Ident	CCE-80792-5
Result	pass
""",
            oscap_eval_fails_expected="""
Title	Install dnf-automatic Package
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	fail
""",
            oscap_failure_met_threshold_expected=True
        )


    @patch('sh.buildah', create=True)
    def test_str_oscap_fetch_remote_resources_flag(self, buildah_mock):
        self.__run_test_xccdf_do_not_fetch_remote_with_profile_all_pass(
            buildah_mock=buildah_mock,
            oscap_eval_type='xccdf',
            oscap_profile='this.is.real.i.sware',
            oscap_fetch_remote_resources="True",
            oscap_stdout="""
Title\r	Enable Kernel Page-Table Isolation (KPTI)
Rule\r	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident\r	CCE-82194-2
Result\r	pass

Title\r	Install dnf-automatic Package
Rule\r	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident\r	CCE-82985-3
Result\r	pass""",
            oscap_stdout_expected="""
Title	Enable Kernel Page-Table Isolation (KPTI)
Rule	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident	CCE-82194-2
Result	pass

Title	Install dnf-automatic Package
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	pass
"""
        )

    @patch('sh.buildah', create=True)
    def test_oval_do_no_fetch_remote_with_profile_all_pass(self, buildah_mock):
        self.__run_test_xccdf_do_not_fetch_remote_with_profile_all_pass(
            buildah_mock=buildah_mock,
            oscap_eval_type='oval',
            oscap_fetch_remote_resources=False,
            oscap_stdout="""
Definition oval:com.redhat.rhsa:def:20203699: false
Definition oval:com.redhat.rhsa:def:20203669: false
Definition oval:com.redhat.rhsa:def:20203665: false
Definition oval:com.redhat.rhsa:def:20203662: false""",
            oscap_stdout_expected="""
Definition oval:com.redhat.rhsa:def:20203699: false
Definition oval:com.redhat.rhsa:def:20203669: false
Definition oval:com.redhat.rhsa:def:20203665: false
Definition oval:com.redhat.rhsa:def:20203662: false
"""
        )

    @patch('sh.buildah', create=True)
    def test_oval_do_no_fetch_remote_with_profile_all_pass(self, buildah_mock):
        self.__run_test_xccdf_do_not_fetch_remote_with_profile_all_pass(
            buildah_mock=buildah_mock,
            oscap_eval_type='oval',
            oscap_fetch_remote_resources=False,
            oscap_eval_success_expected=False,
            oscap_stdout="""
Definition oval:com.redhat.rhsa:def:20203699: false
Definition oval:com.redhat.rhsa:def:20203669: true
Definition oval:com.redhat.rhsa:def:20203665: false
Definition oval:com.redhat.rhsa:def:20203662: true""",
            oscap_stdout_expected="""
Definition oval:com.redhat.rhsa:def:20203699: false
Definition oval:com.redhat.rhsa:def:20203669: true
Definition oval:com.redhat.rhsa:def:20203665: false
Definition oval:com.redhat.rhsa:def:20203662: true
""",
            oscap_eval_fails_expected="""Definition oval:com.redhat.rhsa:def:20203669: true
Definition oval:com.redhat.rhsa:def:20203662: true
""",
            oscap_failure_met_threshold_expected=True
        )

    @patch('sh.buildah', create=True)
    def test_xccdf_exit_code_1(self, buildah_mock):
        with self.assertRaisesRegex(
                StepRunnerException,
                re.compile(
                    r"Error running 'oscap xccdf eval':"
                    r".*RAN: oscap-chroot eval"
                    r".*STDOUT:"
                    r".*Title\s*Enable Kernel Page-Table Isolation \(KPTI\)"
                    r"\s*Rule\s*xccdf_org.ssgproject.content_rule_grub2_pti_argument"
                    r"\s*Ident\s*CCE-82194-2"
                    r"\s*Result\s*notapplicable"
                    r".*Title\s*Install dnf-automatic Package"
                    r"\s*Rule\s*xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed"
                    r"\s*Ident\s*CCE-82985-3"
                    r"\s*Result\s*fail"
                    r".*Title\s*Ensure gpgcheck Enabled for All yum Package Repositories"
                    r"\s*Rule\s*xccdf_org.ssgproject.content_rule_ensure_gpgcheck_never_disabled"
                    r"\s*Ident\s*CCE-80792-5"
                    r"\s*Result\s*pass"
                    r".*STDERR:"
                    r".*mock error - exit code 1",
                    re.DOTALL
                )
        ):
            self.__run_test_xccdf_do_not_fetch_remote_with_profile_all_pass(
                buildah_mock=buildah_mock,
                oscap_eval_type='xccdf',
                oscap_profile='this.is.real.i.sware',
                oscap_fetch_remote_resources=True,
                oscap_eval_success_expected=False,
                exit_code=1,
                oscap_stdout="""
    Title\r	Enable Kernel Page-Table Isolation (KPTI)
    Rule\r	xccdf_org.ssgproject.content_rule_grub2_pti_argument
    Ident\r	CCE-82194-2
    Result\r	notapplicable

    Title\r	Install dnf-automatic Package
    Rule\r	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
    Ident\r	CCE-82985-3
    Result\r	fail

    Title\r	Ensure gpgcheck Enabled for All yum Package Repositories
    Rule\r	xccdf_org.ssgproject.content_rule_ensure_gpgcheck_never_disabled
    Ident\r	CCE-80792-5
    Result\r	pass""",
                oscap_stdout_expected="""
    Title	Enable Kernel Page-Table Isolation (KPTI)
    Rule	xccdf_org.ssgproject.content_rule_grub2_pti_argument
    Ident	CCE-82194-2
    Result	notapplicable

    Title	Install dnf-automatic Package
    Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
    Ident	CCE-82985-3
    Result	fail

    Title	Ensure gpgcheck Enabled for All yum Package Repositories
    Rule	xccdf_org.ssgproject.content_rule_ensure_gpgcheck_never_disabled
    Ident	CCE-80792-5
    Result	pass
    """,
                oscap_failure_met_threshold_expected=True
            )

    @patch('sh.buildah', create=True)
    def test_oval_exit_code_1(self, buildah_mock):
        with self.assertRaisesRegex(
                StepRunnerException,
                re.compile(
                    r"Error running 'oscap oval eval': "
                    r".*RAN: oscap-chroot eval"
                    r".*STDOUT:"
                    r".*Definition oval:com.redhat.rhsa:def:20203699: false"
                    r".*Definition oval:com.redhat.rhsa:def:20203669: true"
                    r".*Definition oval:com.redhat.rhsa:def:20203665: false"
                    r".*Definition oval:com.redhat.rhsa:def:20203662: true"
                    r".*STDERR:"
                    r".*mock error - exit code 1",
                    re.DOTALL
                )
        ):
            self.__run_test_xccdf_do_not_fetch_remote_with_profile_all_pass(
                buildah_mock=buildah_mock,
                oscap_eval_type='oval',
                oscap_fetch_remote_resources=False,
                oscap_eval_success_expected=False,
                exit_code=1,
                oscap_stdout="""
    Definition oval:com.redhat.rhsa:def:20203699: false
    Definition oval:com.redhat.rhsa:def:20203669: true
    Definition oval:com.redhat.rhsa:def:20203665: false
    Definition oval:com.redhat.rhsa:def:20203662: true""",
                oscap_stdout_expected="""
    Definition oval:com.redhat.rhsa:def:20203699: false
    Definition oval:com.redhat.rhsa:def:20203669: true
    Definition oval:com.redhat.rhsa:def:20203665: false
    Definition oval:com.redhat.rhsa:def:20203662: true
    """,
                oscap_failure_met_threshold_expected=True
            )

    @patch('sh.buildah', create=True)
    def test_oval_exit_code_2(self, buildah_mock):
        with self.assertRaisesRegex(
                StepRunnerException,
                re.compile(
                    r"Error running 'oscap oval eval': "
                    r".*RAN: oscap-chroot eval"
                    r".*STDOUT:"
                    r".*Definition oval:com.redhat.rhsa:def:20203699: false"
                    r".*Definition oval:com.redhat.rhsa:def:20203669: true"
                    r".*Definition oval:com.redhat.rhsa:def:20203665: false"
                    r".*Definition oval:com.redhat.rhsa:def:20203662: true"
                    r".*STDERR:"
                    r".*mock error - exit code 2",
                    re.DOTALL
                )
        ):
            self.__run_test_xccdf_do_not_fetch_remote_with_profile_all_pass(
                buildah_mock=buildah_mock,
                oscap_eval_type='oval',
                oscap_fetch_remote_resources=False,
                oscap_eval_success_expected=False,
                exit_code=2,
                oscap_stdout="""
    Definition oval:com.redhat.rhsa:def:20203699: false
    Definition oval:com.redhat.rhsa:def:20203669: true
    Definition oval:com.redhat.rhsa:def:20203665: false
    Definition oval:com.redhat.rhsa:def:20203662: true""",
                oscap_stdout_expected="""
    Definition oval:com.redhat.rhsa:def:20203699: false
    Definition oval:com.redhat.rhsa:def:20203669: true
    Definition oval:com.redhat.rhsa:def:20203665: false
    Definition oval:com.redhat.rhsa:def:20203662: true
    """,
                oscap_failure_met_threshold_expected=True

            )

    @patch('sh.buildah', create=True)
    def test_oval_exit_code_unknown(self, buildah_mock):
        with self.assertRaisesRegex(
                StepRunnerException,
                re.compile(
                    r"Error running 'oscap oval eval': "
                    r".*RAN: oscap-chroot eval"
                    r".*STDOUT:"
                    r".*Definition oval:com.redhat.rhsa:def:20203699: false"
                    r".*Definition oval:com.redhat.rhsa:def:20203669: true"
                    r".*Definition oval:com.redhat.rhsa:def:20203665: false"
                    r".*Definition oval:com.redhat.rhsa:def:20203662: true"
                    r".*STDERR:"
                    r".*mock error - exit code 42",
                    re.DOTALL
                )
        ):
            self.__run_test_xccdf_do_not_fetch_remote_with_profile_all_pass(
                buildah_mock=buildah_mock,
                oscap_eval_type='oval',
                oscap_fetch_remote_resources=False,
                oscap_eval_success_expected=False,
                exit_code=42,
                oscap_stdout="""
    Definition oval:com.redhat.rhsa:def:20203699: false
    Definition oval:com.redhat.rhsa:def:20203669: true
    Definition oval:com.redhat.rhsa:def:20203665: false
    Definition oval:com.redhat.rhsa:def:20203662: true""",
                oscap_stdout_expected="""
    Definition oval:com.redhat.rhsa:def:20203699: false
    Definition oval:com.redhat.rhsa:def:20203669: true
    Definition oval:com.redhat.rhsa:def:20203665: false
    Definition oval:com.redhat.rhsa:def:20203662: true
    """,
                oscap_failure_met_threshold_expected=True
            )

    @patch('sh.buildah', create=True)
    def test_xccdf_with_tailoring_file(self, buildah_mock):
        self.__run_test_xccdf_do_not_fetch_remote_with_profile_all_pass(
            buildah_mock=buildah_mock,
            oscap_eval_type='xccdf',
            oscap_profile='this.is.real.i.sware',
            oscap_fetch_remote_resources=False,
            oscap_tailoring_file="/does/not/matter/tailoring.xccdf.xml",
            oscap_stdout="""
Title\r	Enable Kernel Page-Table Isolation (KPTI)
Rule\r	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident\r	CCE-82194-2
Result\r	pass

Title\r	Install dnf-automatic Package
Rule\r	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident\r	CCE-82985-3
Result\r	pass""",
            oscap_stdout_expected="""
Title	Enable Kernel Page-Table Isolation (KPTI)
Rule	xccdf_org.ssgproject.content_rule_grub2_pti_argument
Ident	CCE-82194-2
Result	pass

Title	Install dnf-automatic Package
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	pass
"""
        )

class TestStepImplementerSharedOpenSCAPGeneric__run_step(
    BaseTestStepImplementerSharedOpenSCAPGeneric
):
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__run_oscap_scan')
    @patch('ploigos_step_runner.step_implementers.shared.openscap_generic.mount_container')
    @patch(
        'ploigos_step_runner.step_implementers.shared.openscap_generic.create_container_from_image',
        return_value='mock-image-working-container-mock-1'
    )
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__get_oscap_document_type')
    @patch('sh.buildah', create=True)
    def test_pass(
        self,
        buildah_mock,
        get_oscap_document_type_mock,
        create_container_from_image_mock,
        mount_container_mock,
        run_oscap_scan_mock
    ):
        oscap_document_type = 'Source Data Stream'
        oscap_eval_type = 'xccdf'
        oscap_input_definitions_uri = 'https://www.redhat.com/security/data/metrics/ds/v2/RHEL8/rhel-8.ds.xml.bz2'
        container_image_tag = 'localhost/mock-org/mock-image:v0.42.0-mock'
        step_config = {
            'oscap-input-definitions-uri': oscap_input_definitions_uri,
            'oscap-profile': 'foo',
            'container-image-tag': container_image_tag
        }
        oscap_eval_success = True
        oscap_eval_fails = None
        oscap_failure_met_threshold = False

        with TempDirectory() as temp_dir:
            # setup test
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            mount_path = '/does/not/matter/container-mount'

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='OpenSCAP',
                parent_work_dir_path=parent_work_dir_path
            )

            get_oscap_document_type_mock.return_value = oscap_document_type
            mount_container_mock.return_value = mount_path
            run_oscap_scan_mock.return_value = [
                oscap_eval_success,
                oscap_eval_fails,
                oscap_failure_met_threshold
            ]

            # run test
            stdout_buff = StringIO()
            with redirect_stdout(stdout_buff):
                step_result = step_implementer._run_step()

            # verify results
            expected_results = StepResult(
                step_name='test',
                sub_step_name='OpenSCAP',
                sub_step_implementer_name='OpenSCAP'
            )
            expected_results.success=True
            expected_results.add_artifact(
                name='html-report',
                value=f"{step_implementer.work_dir_path}/oscap-xccdf-report.html"
            )
            expected_results.add_artifact(
                name='xml-report',
                value=f"{step_implementer.work_dir_path}/oscap-xccdf-results.xml"
            )
            expected_results.add_artifact(
                name='stdout-report',
                value=f"{step_implementer.work_dir_path}/oscap-xccdf-out"
            )
            self.assertEqual(expected_results, step_result)

            stdout = stdout_buff.getvalue()
            expected_container_name = 'mock-image-working-container-mock-1'
            self.assertRegex(
                stdout,
                re.compile(
                    rf".*Create container from image \({container_image_tag}\)"
                    rf".*Created container \({expected_container_name}\) from image \({container_image_tag}\)"
                    rf".*Mount container: {expected_container_name}"
                    rf".*Mounted container \({expected_container_name}\) with mount path: '{mount_path}'"
                    rf".*Download input definitions: {oscap_input_definitions_uri}"
                    rf".*Downloaded input definitions to: /.+/working/test/rhel\-8.ds.xml"
                    rf".*Determine OpenSCAP document type of input file: /.+/working/test/rhel\-8\.ds\.xml"
                    rf".*Determined OpenSCAP document type of input file \(/.+/working/test/rhel\-8\.ds\.xml\): {oscap_document_type}"
                    rf".*Determine OpenSCAP eval type for input file \(/.+/working/test/rhel\-8\.ds\.xml\) of document type: {oscap_document_type}"
                    rf".*Determined OpenSCAP eval type of input file \(/.+/working/test/rhel\-8\.ds\.xml\): {oscap_eval_type}"
                    rf".*Run oscap scan"
                    rf".*OpenSCAP scan completed with eval success",
                    re.DOTALL
                )
            )

    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__run_oscap_scan')
    @patch('ploigos_step_runner.step_implementers.shared.openscap_generic.mount_container')
    @patch(
        'ploigos_step_runner.step_implementers.shared.openscap_generic.create_container_from_image',
        return_value='mock-image-working-container-mock-1'
    )
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__get_oscap_document_type')
    @patch('sh.buildah', create=True)
    def test_fail(
        self,
        buildah_mock,
        get_oscap_document_type_mock,
        create_container_from_image_mock,
        mount_container_mock,
        run_oscap_scan_mock
    ):
        oscap_document_type = 'Source Data Stream'
        oscap_eval_type = 'xccdf'
        oscap_input_definitions_uri = 'https://www.redhat.com/security/data/metrics/ds/v2/RHEL8/rhel-8.ds.xml.bz2'
        container_image_tag = 'localhost/mock-org/mock-image:v0.42.0-mock'
        step_config = {
            'oscap-input-definitions-uri': oscap_input_definitions_uri,
            'oscap-profile': 'foo',
            'container-image-tag': container_image_tag
        }
        oscap_eval_success = False
        oscap_eval_fails = """
Title	Install dnf-automatic Package
Rule	xccdf_org.ssgproject.content_rule_package_dnf-automatic_installed
Ident	CCE-82985-3
Result	fail
"""
        oscap_failure_met_threshold = True

        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            mount_path = '/does/not/matter/container-mount'

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='OpenSCAP',
                parent_work_dir_path=parent_work_dir_path
            )

            get_oscap_document_type_mock.return_value = oscap_document_type
            mount_container_mock.return_value = mount_path
            run_oscap_scan_mock.return_value = [
                oscap_eval_success,
                oscap_eval_fails,
                oscap_failure_met_threshold
            ]

            stdout_buff = StringIO()
            with redirect_stdout(stdout_buff):
                step_result = step_implementer._run_step()

            expected_results = StepResult(
                step_name='test',
                sub_step_name='OpenSCAP',
                sub_step_implementer_name='OpenSCAP'
            )
            expected_results.success = False
            expected_results.message = "OSCAP eval found issues:\n\n" \
                "Title\tInstall dnf-automatic Package\n" \
                "Rule\txccdf_org.ssgproject.content_rule_package_dnf-automatic_installed" \
                "\nIdent\tCCE-82985-3\nResult\tfail\n"
            expected_results.add_artifact(
                name='html-report',
                value=f"{step_implementer.work_dir_path}/oscap-xccdf-report.html"
            )
            expected_results.add_artifact(
                name='xml-report',
                value=f"{step_implementer.work_dir_path}/oscap-xccdf-results.xml"
            )
            expected_results.add_artifact(
                name='stdout-report',
                value=f"{step_implementer.work_dir_path}/oscap-xccdf-out"
            )
            self.assertEqual(expected_results, step_result)

            stdout = stdout_buff.getvalue()
            expected_container_name = 'mock-image-working-container-mock-1'
            self.assertRegex(
                stdout,
                re.compile(
                    rf".*Create container from image \({container_image_tag}\)"
                    rf".*Created container \({expected_container_name}\) from image \({container_image_tag}\)"
                    rf".*Mount container: {expected_container_name}"
                    rf".*Mounted container \({expected_container_name}\) with mount path: '{mount_path}'"
                    rf".*Download input definitions: {oscap_input_definitions_uri}"
                    rf".*Downloaded input definitions to: /.+/working/test/rhel\-8.ds.xml"
                    rf".*Determine OpenSCAP document type of input file: /.+/working/test/rhel\-8\.ds\.xml"
                    rf".*Determined OpenSCAP document type of input file \(/.+/working/test/rhel\-8\.ds\.xml\): {oscap_document_type}"
                    rf".*Determine OpenSCAP eval type for input file \(/.+/working/test/rhel\-8\.ds\.xml\) of document type: {oscap_document_type}"
                    rf".*Determined OpenSCAP eval type of input file \(/.+/working/test/rhel\-8\.ds\.xml\): {oscap_eval_type}"
                    rf".*Run oscap scan"
                    rf".*OpenSCAP scan completed with eval success: False",
                    re.DOTALL
                )
            )

    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__run_oscap_scan')
    @patch('ploigos_step_runner.step_implementers.shared.openscap_generic.mount_container')
    @patch(
        'ploigos_step_runner.step_implementers.shared.openscap_generic.create_container_from_image',
        return_value='mock-image-working-container-mock-1'
    )
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__get_oscap_document_type')
    @patch('sh.buildah', create=True)
    def test_pass_with_tailoring_file_download(
        self,
        buildah_mock,
        get_oscap_document_type_mock,
        create_container_from_image_mock,
        mount_container_mock,
        run_oscap_scan_mock
    ):
        oscap_document_type = 'Source Data Stream'
        oscap_eval_type = 'xccdf'
        oscap_input_definitions_uri = 'https://www.redhat.com/security/data/metrics/ds/v2/RHEL8/rhel-8.ds.xml.bz2'
        container_image_tag = 'localhost/mock-org/mock-image:v0.42.0-mock'
        oscap_tailoring_uri = 'https://raw.githubusercontent.com/ploigos/ploigos-example-oscap-content/main/xccdf_com.redhat.ploigos_profile_example_ubi8-tailoring-xccdf.xml'
        step_config = {
            'oscap-input-definitions-uri': oscap_input_definitions_uri,
            'oscap-tailoring-uri': oscap_tailoring_uri,
            'oscap-profile': 'foo',
            'container-image-tag': container_image_tag
        }
        oscap_eval_success = True
        oscap_eval_fails = None
        oscap_failure_met_threshold = False

        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            mount_path = '/does/not/matter/container-mount'

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='OpenSCAP',
                parent_work_dir_path=parent_work_dir_path
            )

            get_oscap_document_type_mock.return_value = oscap_document_type
            mount_container_mock.return_value = mount_path
            run_oscap_scan_mock.return_value = [
                oscap_eval_success,
                oscap_eval_fails,
                oscap_failure_met_threshold
            ]

            stdout_buff = StringIO()
            with redirect_stdout(stdout_buff):
                step_result = step_implementer._run_step()

            expected_results = StepResult(
                step_name='test',
                sub_step_name='OpenSCAP',
                sub_step_implementer_name='OpenSCAP'
            )
            expected_results.success=True
            expected_results.add_artifact(
                name='html-report',
                value=f"{step_implementer.work_dir_path}/oscap-xccdf-report.html"
            )
            expected_results.add_artifact(
                name='xml-report',
                value=f"{step_implementer.work_dir_path}/oscap-xccdf-results.xml"
            )
            expected_results.add_artifact(
                name='stdout-report',
                value=f"{step_implementer.work_dir_path}/oscap-xccdf-out"
            )
            self.assertEqual(expected_results, step_result)

            stdout = stdout_buff.getvalue()

            expected_container_name = 'mock-image-working-container-mock-1'
            self.assertRegex(
                stdout,
                re.compile(
                    rf".*Create container from image \({container_image_tag}\)"
                    rf".*Created container \({expected_container_name}\) from image \({container_image_tag}\)"
                    rf".*Mount container: {expected_container_name}"
                    rf".*Mounted container \({expected_container_name}\) with mount path: '{mount_path}'"
                    rf".*Download input definitions: {oscap_input_definitions_uri}"
                    rf".*Downloaded input definitions to: /.+/working/test/rhel\-8.ds.xml"
                    rf".*Download oscap tailoring file: {oscap_tailoring_uri}"
                    rf".*Download oscap tailoring file to: /.+/working/test/xccdf_com.redhat\.ploigos_profile_example_ubi8\-tailoring\-xccdf\.xml"
                    rf".*Determine OpenSCAP document type of input file: /.+/working/test/rhel\-8\.ds\.xml"
                    rf".*Determined OpenSCAP document type of input file \(/.+/working/test/rhel\-8\.ds\.xml\): {oscap_document_type}"
                    rf".*Determine OpenSCAP eval type for input file \(/.+/working/test/rhel\-8\.ds\.xml\) of document type: {oscap_document_type}"
                    rf".*Determined OpenSCAP eval type of input file \(/.+/working/test/rhel\-8\.ds\.xml\): {oscap_eval_type}"
                    rf".*Run oscap scan"
                    rf".*OpenSCAP scan completed with eval success",
                    re.DOTALL
                )
            )

    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__run_oscap_scan')
    @patch('ploigos_step_runner.step_implementers.shared.openscap_generic.mount_container')
    @patch(
        'ploigos_step_runner.step_implementers.shared.openscap_generic.create_container_from_image',
        return_value='mock-image-working-container-mock-1'
    )
    @patch('ploigos_step_runner.step_implementers.shared.openscap_generic.clone_repo')
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__get_oscap_document_type')
    def test_pass_with_tailoring_file_clone(
        self,
        get_oscap_document_type_mock,
        clone_repo_mock,
        create_container_from_image_mock,
        mount_container_mock,
        run_oscap_scan_mock
    ):
        # Set up mock values, to be repeatedly referenced throughout test
        step_name = 'test'
        implementer = 'OpenSCAP'
        tailoring_repo_subdir = OpenSCAPGeneric._get_tailoring_repo_subdir()

        oscap_document_type = 'Source Data Stream'
        oscap_eval_type = 'xccdf'
        oscap_profile = 'foo'
        oscap_input_definitions_file_uncompressed = 'rhel-8.ds.xml'
        oscap_input_definitions_uri = f"https://www.redhat.com/security/data/metrics/ds/v2/RHEL8/{oscap_input_definitions_file_uncompressed}.bz2"
        container_image_tag = 'localhost/mock-org/mock-image:v0.42.0-mock'

        oscap_tailoring_repo_uri = 'https://github.com/ploigos/ploigos-example-oscap-content.git'
        oscap_tailoring_repo_file = 'xccdf_com.redhat.ploigos_profile_example_ubi8-tailoring-xccdf.xml'
        git_username = 'username'
        git_password = 'super-secret'
        default_repository_type = 'containers-storage:'

        oscap_eval_success = True
        oscap_eval_fails = None
        oscap_failure_met_threshold = False
        mount_path = '/does/not/matter/container-mount'
        get_oscap_document_type_mock.return_value = oscap_document_type

        # Set up mock behaviors / return values
        mount_container_mock.return_value = mount_path
        run_oscap_scan_mock.return_value = [
            oscap_eval_success,
            oscap_eval_fails,
            oscap_failure_met_threshold
        ]

        # Define the step config
        step_config = {
            'oscap-input-definitions-uri': oscap_input_definitions_uri,
            'oscap-tailoring-repo-uri': oscap_tailoring_repo_uri,
            'oscap-tailoring-repo-file': oscap_tailoring_repo_file,
            'git-username': git_username,
            'git-password': git_password,
            'oscap-profile': oscap_profile,
            'container-image-tag': container_image_tag
        }

        with TempDirectory() as temp_dir:
            # Set up additional mock values (that require the use of temp_dir)
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            expected_definitions_file = f"{parent_work_dir_path}" \
                                        f"/{step_name}" \
                                        f"/{oscap_input_definitions_file_uncompressed}"
            oscap_tailoring_repo_local_dir = f"{parent_work_dir_path}" \
                                             f"/{step_name}" \
                                             f"/{tailoring_repo_subdir}"
            expected_tailoring_file = f"{oscap_tailoring_repo_local_dir}" \
                                      f"/{oscap_tailoring_repo_file}"

            # Construct the step implementer, to execute our test
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name=step_name,
                implementer=implementer,
                parent_work_dir_path=parent_work_dir_path
            )

            # Execute the test (with redirected stdout for verification later)
            stdout_buff = StringIO()
            with redirect_stdout(stdout_buff):
                step_result = step_implementer._run_step()

            # Verification of test execution
            expected_results = StepResult(
                step_name=step_name,
                sub_step_name=implementer,
                sub_step_implementer_name=implementer
            )
            expected_results.success = True
            expected_results.add_artifact(
                name='html-report',
                value=f"{step_implementer.work_dir_path}/oscap-xccdf-report.html"
            )
            expected_results.add_artifact(
                name='xml-report',
                value=f"{step_implementer.work_dir_path}/oscap-xccdf-results.xml"
            )
            expected_results.add_artifact(
                name='stdout-report',
                value=f"{step_implementer.work_dir_path}/oscap-xccdf-out"
            )
            self.assertEqual(expected_results, step_result)

            stdout = stdout_buff.getvalue()

            expected_container_name = 'mock-image-working-container-mock-1'
            self.assertRegex(
                stdout,
                re.compile(
                    rf".*Create container from image \({container_image_tag}\)"
                    rf".*Created container \({expected_container_name}\) from image \({container_image_tag}\)"
                    rf".*Mount container: {expected_container_name}"
                    rf".*Mounted container \({expected_container_name}\) with mount path: '{mount_path}'"
                    rf".*Download input definitions: {oscap_input_definitions_uri}"
                    rf".*Downloaded input definitions to: /.+/working/test/rhel\-8.ds.xml"
                    rf".*Cloning repo with oscap tailoring file: {oscap_tailoring_repo_uri}"
                    rf".*Cloned oscap repo; tailoring file located at: {expected_tailoring_file}"
                    rf".*Determine OpenSCAP document type of input file: {expected_definitions_file}"
                    rf".*Determined OpenSCAP document type of input file \({expected_definitions_file}\): {oscap_document_type}"
                    rf".*Determine OpenSCAP eval type for input file \({expected_definitions_file}\) of document type: {oscap_document_type}"
                    rf".*Determined OpenSCAP eval type of input file \({expected_definitions_file}\): {oscap_eval_type}"
                    rf".*Run oscap scan"
                    rf".*OpenSCAP scan completed with eval success: True",
                    re.DOTALL
                )
            )

            clone_repo_mock.assert_called_once_with(
                oscap_tailoring_repo_local_dir,
                oscap_tailoring_repo_uri,
                git_username,
                git_password
            )
            create_container_from_image_mock.assert_called_once_with(
                image_address=container_image_tag,
                repository_type=default_repository_type
            )


    @patch('ploigos_step_runner.step_implementers.shared.openscap_generic.download_and_decompress_source_to_destination')
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__run_oscap_scan')
    @patch('ploigos_step_runner.step_implementers.shared.openscap_generic.mount_container')
    @patch(
        'ploigos_step_runner.step_implementers.shared.openscap_generic.create_container_from_image',
        return_value='mock-image-working-container-mock-1'
    )
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__get_oscap_document_type')
    @patch('sh.buildah', create=True)
    def test_fail_downloading_open_scap_input_file(
        self,
        buildah_mock,
        get_oscap_document_type_mock,
        create_container_from_image_mock,
        mount_container_mock,
        run_oscap_scan_mock,
        download_and_decompress_source_to_destination_mock
    ):
        oscap_document_type = 'Source Data Stream'
        oscap_eval_type = 'xccdf'
        oscap_input_definitions_uri = 'https://www.redhat.com/security/data/metrics/ds/v2/RHEL8/rhel-8.ds.xml.bz2'
        container_image_tag = 'localhost/mock-org/mock-image:v0.42.0-mock'
        step_config = {
            'oscap-input-definitions-uri': oscap_input_definitions_uri,
            'oscap-profile': 'foo',
            'container-image-tag': container_image_tag
        }
        oscap_eval_success = True
        oscap_eval_fails = None
        oscap_failure_met_threshold = False

        with TempDirectory() as temp_dir:
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            mount_path = '/does/not/matter/container-mount'

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='OpenSCAP',
                parent_work_dir_path=parent_work_dir_path
            )

            get_oscap_document_type_mock.return_value = oscap_document_type
            mount_container_mock.return_value = mount_path
            run_oscap_scan_mock.return_value = [
                oscap_eval_success,
                oscap_eval_fails,
                oscap_failure_met_threshold
            ]

            mock_error_msg = 'mock error downloading open scap file'
            download_and_decompress_source_to_destination_mock.side_effect = RuntimeError(
                mock_error_msg
            )

            # run test
            stdout_buff = StringIO()
            with redirect_stdout(stdout_buff):
                step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='test',
                sub_step_name='OpenSCAP',
                sub_step_implementer_name='OpenSCAP'
            )
            expected_step_result.success = False
            expected_step_result.message = 'Error downloading OpenSCAP input file: ' \
                f'{mock_error_msg}'
            self.assertEqual(expected_step_result, step_result)

            stdout = stdout_buff.getvalue()
            expected_container_name = 'mock-image-working-container-mock-1'
            self.assertRegex(
                stdout,
                re.compile(
                    rf".*Create container from image \({container_image_tag}\)"
                    rf".*Created container \({expected_container_name}\) from image \({container_image_tag}\)"
                    rf".*Mount container: {expected_container_name}"
                    rf".*Mounted container \({expected_container_name}\) with mount path: '{mount_path}'"
                    rf".*Download input definitions: {oscap_input_definitions_uri}",
                    re.DOTALL
                )
            )

    @patch('ploigos_step_runner.step_implementers.shared.openscap_generic.download_and_decompress_source_to_destination')
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__run_oscap_scan')
    @patch('ploigos_step_runner.step_implementers.shared.openscap_generic.mount_container')
    @patch(
        'ploigos_step_runner.step_implementers.shared.openscap_generic.create_container_from_image',
        return_value='mock-image-working-container-mock-1'
    )
    @patch.object(OpenSCAPGeneric, '_OpenSCAPGeneric__get_oscap_document_type')
    @patch('sh.buildah', create=True)
    def test_fail_downloading_open_scap_tailoring_file(
        self,
        buildah_mock,
        get_oscap_document_type_mock,
        create_container_from_image_mock,
        mount_container_mock,
        run_oscap_scan_mock,
        download_and_decompress_source_to_destination_mock
    ):
        oscap_document_type = 'Source Data Stream'
        oscap_eval_type = 'xccdf'
        oscap_input_definitions_uri = 'https://www.redhat.com/security/data/metrics/ds/v2/RHEL8/rhel-8.ds.xml.bz2'
        container_image_tag = 'localhost/mock-org/mock-image:v0.42.0-mock'
        oscap_tailoring_uri = 'https://raw.githubusercontent.com/ploigos/ploigos-example-oscap-content/main/xccdf_com.redhat.ploigos_profile_example_ubi8-tailoring-xccdf.xml'
        step_config = {
            'oscap-input-definitions-uri': oscap_input_definitions_uri,
            'oscap-profile': 'foo',
            'oscap-tailoring-uri': oscap_tailoring_uri,
            'container-image-tag': container_image_tag
        }
        oscap_eval_success = True
        oscap_eval_fails = None
        oscap_failure_met_threshold = False

        with TempDirectory() as temp_dir:
            # setup test
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            mount_path = '/does/not/matter/container-mount'

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name='test',
                implementer='OpenSCAP',
                parent_work_dir_path=parent_work_dir_path
            )

            get_oscap_document_type_mock.return_value = oscap_document_type
            mount_container_mock.return_value = mount_path
            run_oscap_scan_mock.return_value = [
                oscap_eval_success,
                oscap_eval_fails,
                oscap_failure_met_threshold
            ]

            # run test with mock error
            mock_error_msg = 'mock error downloading open scap file'
            download_and_decompress_source_to_destination_mock.side_effect = [
                "foo",
                RuntimeError(mock_error_msg)
            ]

            stdout_buff = StringIO()
            with redirect_stdout(stdout_buff):
                step_result = step_implementer._run_step()

            # verify results
            expected_step_result = StepResult(
                step_name='test',
                sub_step_name='OpenSCAP',
                sub_step_implementer_name='OpenSCAP'
            )
            expected_step_result.success = False
            expected_step_result.message = 'Error downloading OpenSCAP tailoring file: ' \
                f'{mock_error_msg}'
            self.assertEqual(expected_step_result, step_result)

            stdout = stdout_buff.getvalue()
            expected_container_name = 'mock-image-working-container-mock-1'
            self.assertRegex(
                stdout,
                re.compile(
                    rf".*Create container from image \({container_image_tag}\)"
                    rf".*Created container \({expected_container_name}\) from image \({container_image_tag}\)"
                    rf".*Mount container: {expected_container_name}"
                    rf".*Mounted container \({expected_container_name}\) with mount path: '{mount_path}'"
                    rf".*Download input definitions: {oscap_input_definitions_uri}"
                    rf".*Downloaded input definitions to: foo"
                    rf".*Download oscap tailoring file: {oscap_tailoring_uri}",
                    re.DOTALL
                )
            )

class TestStepImplementerSharedOpenSCAPGeneric__get_tailoring_file_from_git_repo(
    BaseTestStepImplementerSharedOpenSCAPGeneric
):
    @patch('ploigos_step_runner.step_implementers.shared.openscap_generic.clone_repo')
    def test__get_tailoring_file_from_git_repo_success(
            self,
            clone_repo_mock
    ):
        # Set up mock values, to be repeatedly referenced throughout test
        step_name = 'test'
        implementer = 'OpenSCAP'
        tailoring_repo_subdir = OpenSCAPGeneric._get_tailoring_repo_subdir()

        oscap_input_definition_uri = 'https://www.redhat.com/security/data/oval/v2/RHEL8/rhel-8.oval.xml.bz2'
        image_tar_file = 'does-not-matter'
        oscap_tailoring_repo_uri = 'http://git.example.org/myrepo.git'
        oscap_tailoring_repo_file = 'my-tailoring-file.xml'
        git_username = 'username'
        git_password = 'super-secret'

        # Define the step config
        step_config = {
            'oscap-input-definitions-uri': oscap_input_definition_uri,
            'image-tar-file': image_tar_file,
            'oscap-tailoring-repo-uri': oscap_tailoring_repo_uri,
            'oscap-tailoring-repo-file': oscap_tailoring_repo_file,
            'git-username': git_username,
            'git-password': git_password
        }

        # Test execution requires a temp dir; continue test definition and execution under here
        with TempDirectory() as temp_dir:
            # Set up additional mock values (that require the use of temp_dir)
            parent_work_dir_path = os.path.join(temp_dir.path, 'working')
            oscap_tailoring_repo_local_dir = f"{parent_work_dir_path}" \
                                             f"/{step_name}" \
                                             f"/{tailoring_repo_subdir}"
            expected_tailoring_file = f'{oscap_tailoring_repo_local_dir}' \
                                      f'/{oscap_tailoring_repo_file}'

            # Construct the step implementer, to execute our test
            step_implementer = self.create_step_implementer(
                step_config=step_config,
                step_name=step_name,
                implementer=implementer,
                parent_work_dir_path=parent_work_dir_path
            )

            # Execute the test
            actual_tailoring_file = step_implementer._get_tailoring_file_from_git_repo()

            # Verification of test execution
            self.assertEqual(
                actual_tailoring_file,
                expected_tailoring_file,
                f"The tailoring values do not match; "
                f"expected: {expected_tailoring_file} "
                f"actual: {actual_tailoring_file}"
            )

            clone_repo_mock.assert_called_once_with(
                oscap_tailoring_repo_local_dir,
                oscap_tailoring_repo_uri,
                git_username,
                git_password
            )
