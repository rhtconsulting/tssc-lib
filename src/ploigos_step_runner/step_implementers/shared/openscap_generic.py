"""Step Implementer for the container-image-static-compliance-scan step for OpenSCAP.

Step Configuration
------------------

Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

 Configuration Key             | Required? | Default | Description
-------------------------------|-----------|---------|-----------
`container-image-tag`          | Yes       |         | Container image tag to scan.
`oscap-input-definitions-uri`  | Yes       |         | URI to the OpenSCAP definitions file \
                                                       to do the evaluation with. \
                                                       Must use protocol file://|http://|https://. \
                                                       Must have file extension .xml|.bz2.
`oscap-profile`                | No        |         | OpenSCAP profile to evaluate.
`oscap-tailoring-uri`          | No        |         | URI to OpenSCAP tailoring file \
                                                       to do the evaluation with. \
                                                       Must use protocol file://|http://|https://. \
                                                       Must have file extension .xml|.bz2.
`oscap-fetch-remote-resources` | No        | True    | For Source DataStream and XCCDF files \
                                                       that have remote references fetch them if \
                                                       True, else don't. \
                                                       <br/><br/> \
                                                       **WARNING**: evaluations will not be \
                                                       complete if input defintions require \
                                                       remote resources and this is not True. \
                                                       For disconnected environments the remote \
                                                       internal mirror.
`[container-image-pull-registry-type, container-image-registry-type]` \
                               | Yes       | 'containers-storage:' \
                                                     | \
                                           Container repository type for the pull image source. \
                                           See https://github.com/containers/skopeo for valid \
                                           options.

Results
-------

Results output by this step.

| Result Key      | Description
|-----------------|------------
| `html-report`   | HTML report generated by oscap eval
| `xml-report`    | XML report generated by oscap eval
| `stdout-report` | stdout report generated by oscap eval
"""

import os
import re
from distutils.util import strtobool
from io import StringIO

import sh
from ploigos_step_runner import StepResult, StepRunnerException
from ploigos_step_runner.step_implementer import StepImplementer
from ploigos_step_runner.utils.containers import (create_container_from_image,
                                                  mount_container)
from ploigos_step_runner.utils.file import \
    download_and_decompress_source_to_destination
from ploigos_step_runner.utils.io import \
    create_sh_redirect_to_multiple_streams_fn_callback

DEFAULT_CONFIG = {
    'oscap-fetch-remote-resources': True,
    'container-image-pull-registry-type': 'containers-storage:',
    'container-image-registry-type': 'containers-storage:'
}

REQUIRED_CONFIG_OR_PREVIOUS_STEP_RESULT_ARTIFACT_KEYS = [
    'oscap-input-definitions-uri',
    [
        'container-image-build-address',
        'container-image-push-address',
        'container-image-pull-address',
        'container-image-address',
        'container-image-tag'
    ],
    'container-image-pull-registry-type',

    # being flexible for different use cases of proceeding steps
    ['container-image-pull-registry-type', 'container-image-registry-type']
]


class OpenSCAPGeneric(StepImplementer):
    """A generic OpenSCAP step implementer that can be used for more then one step.

    Expected uses:
    * container-image-static-compliance-scan
    * container-image-static-vulnerability-scan
    """

    # Example Input:
    #    Title	RHSA-2020:4186: spice and spice-gtk security update (Important)
    #    Rule	xccdf_com.redhat.rhsa_rule_oval-com.redhat.rhsa-def-20204186
    #    Ident	RHSA-2020:4186
    #    Ident	CVE-2020-14355
    #    Result	pass
    #
    #    Title	RHSA-2020:3658: librepo security update (Important)
    #    Rule	xccdf_com.redhat.rhsa_rule_oval-com.redhat.rhsa-def-20203658
    #    Ident	RHSA-2020:3658
    #    Ident	CVE-2020-14352
    #    Result	fail
    #
    # Matches:
    #    (Title	RHSA-2020:4186: spice and spice-gtk security update (Important)
    #    Rule	xccdf_com.redhat.rhsa_rule_oval-com.redhat.rhsa-def-20204186
    #    Ident	RHSA-2020:4186
    #    Ident	CVE-2020-14355
    #    Result	(pass))
    #
    #    (Title	RHSA-2020:3658: librepo security update (Important)
    #    Rule	xccdf_com.redhat.rhsa_rule_oval-com.redhat.rhsa-def-20203658
    #    Ident	RHSA-2020:3658
    #    Ident	CVE-2020-14352
    #    Result	(fail))
    #
    # Named Groups:
    #    [0]ruleblock
    #        Title	RHSA-2020:4186: spice and spice-gtk security update (Important)
    #        Rule	xccdf_com.redhat.rhsa_rule_oval-com.redhat.rhsa-def-20204186
    #        Ident	RHSA-2020:4186
    #        Ident	CVE-2020-14355
    #        Result	pass
    #    [0]ruleresult
    #        pass
    #
    #    [1]ruleblock
    #        Title	RHSA-2020:3658: librepo security update (Important)
    #        Rule	xccdf_com.redhat.rhsa_rule_oval-com.redhat.rhsa-def-20203658
    #        Ident	RHSA-2020:3658
    #        Ident	CVE-2020-14352
    #        Result	fail
    #    [1]ruleresult
    #        fail
    OSCAP_XCCDF_STDOUT_PATTERN = re.compile(
        r'(?P<ruleblock>Title.+?Result\s+(?P<ruleresult>[^\n]+))\n',
        re.DOTALL
    )
    OSCAP_XCCDF_STDOUT_FAIL_PATTERN = re.compile(r'fail')

    # NOTE: oval output far less useful then xccdf output but it is all but given some content
    #       is only given in oval format and therefor supporting this is important
    #
    # Example Input:
    #   Definition oval:com.redhat.rhsa:def:20202031: false
    #   Definition oval:com.redhat.rhsa:def:20201998: true
    #
    # Matches:
    #   (Definition oval:com.redhat.rhsa:def:20202031: (false))
    #   (Definition oval:com.redhat.rhsa:def:20201998: (true))
    #
    # Named Groups:
    #   [0]ruleblock
    #       Definition oval:com.redhat.rhsa:def:20202031: false
    #   [0]ruleresult
    #       false
    #
    #   [1]ruleblock
    #       Definition oval:com.redhat.rhsa:def:20201998: true
    #   [1]ruleresult
    #       true
    OSCAP_OVAL_STDOUT_PATTERN = re.compile(
        r'(?P<ruleblock>^.*:\s*(?P<ruleresult>true|false)\s*$)$',
        re.MULTILINE
    )
    OSCAP_OVAL_STDOUT_FAIL_PATTERN = re.compile(r'true')

    OSCAP_INFO_DOC_TYPE_PATTERN = re.compile(r'Document type: (?P<doctype>.+)')

    @staticmethod
    def step_implementer_config_defaults():
        """
        Getter for the StepImplementer's configuration defaults.

        Notes
        -----
        These are the lowest precedence configuration values.

        Returns
        -------
        dict
            Default values to use for step configuration values.
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
        * oscap-input-definitions-uri
          - starts with file://|http://|https://
          - ends with .xml|.bz2

        Raises
        ------
        AssertionError
            If step configuration or previous step result artifacts have invalid required values
        """
        super()._validate_required_config_or_previous_step_result_artifact_keys()  # pylint: disable=protected-access

        # validate that the given 'oscap-input-definitions-uri' starts with file://|http://|https://
        oscap_input_definitions_uri = self.get_value('oscap-input-definitions-uri')
        assert (re.match(r'^file://|http://|https://', oscap_input_definitions_uri)), \
            f"Open SCAP input definitions source ({oscap_input_definitions_uri})" \
            f" must start with known protocol (file://|http://|https://)."

        # validate that the given 'oscap-input-definitions-uri' is an xml or bz2 file
        oscap_input_definitions_uri_extension = os.path.splitext(oscap_input_definitions_uri)[1]
        assert (re.match(r'\.xml|\.bz2', oscap_input_definitions_uri_extension)), \
            f"Open SCAP input definitions source ({oscap_input_definitions_uri})" \
            f" must be of known type (xml|bz2), got: {oscap_input_definitions_uri_extension}"

    def _run_step(self):  # pylint: disable=too-many-locals,too-many-statements
        """Runs the OpenSCAP eval for a given input file against a given container.
        """
        step_result = StepResult.from_step_implementer(self)

        # get config
        image_address = self.get_value([
            'container-image-build-address',
            'container-image-push-address',
            'container-image-pull-address',
            'container-image-address',
            'container-image-tag'
        ])
        oscap_profile = self.get_value('oscap-profile')
        oscap_fetch_remote_resources = self.get_value('oscap-fetch-remote-resources')
        pull_repository_type = self.get_value([
            'container-image-pull-registry-type',
            'container-image-registry-type'
        ])

        try:
            # create container from image that can be mounted
            print(f"\nCreate container from image ({image_address})")
            container_name = create_container_from_image(
                image_address=image_address,
                repository_type=pull_repository_type
            )
            print(f"Created container ({container_name}) from image ({image_address})")

            # baking `buildah unshare` command to wrap other buildah commands with
            # so that container does not need to be running in a privileged mode to be able
            # to function
            buildah_unshare_command = sh.buildah.bake('unshare')  # pylint: disable=no-member

            # mount the container filesystem and get mount path
            #
            # NOTE: run in the context of `buildah unshare` so that container does not
            #       need to be run in a privileged mode
            print(f"\nMount container: {container_name}")
            container_mount_path = mount_container(
                buildah_unshare_command=buildah_unshare_command,
                container_id=container_name
            )
            print(f"Mounted container ({container_name}) with mount path: '{container_mount_path}'")

            try:
                # download the open scap input file
                oscap_input_definitions_uri = self.get_value('oscap-input-definitions-uri')
                print(f"\nDownload input definitions: {oscap_input_definitions_uri}")
                oscap_input_file = download_and_decompress_source_to_destination(
                    source_uri=oscap_input_definitions_uri,
                    destination_dir=self.work_dir_path
                )
                print(f"Downloaded input definitions to: {oscap_input_file}")
            except (RuntimeError, ValueError) as error:
                raise StepRunnerException(
                    f"Error downloading OpenSCAP input file: {error}"
                ) from error

            try:
                # if specified download oscap tailoring file
                oscap_tailoring_file = None
                oscap_tailoring_file_uri = self.get_value('oscap-tailoring-uri')
                if oscap_tailoring_file_uri:
                    print(f"\nDownload oscap tailoring file: {oscap_tailoring_file_uri}")
                    oscap_tailoring_file = download_and_decompress_source_to_destination(
                        source_uri=oscap_tailoring_file_uri,
                        destination_dir=self.work_dir_path
                    )
                    print(f"Download oscap tailoring file to: {oscap_tailoring_file}")
            except (RuntimeError, ValueError) as error:
                raise StepRunnerException(
                    f"Error downloading OpenSCAP tailoring file: {error}"
                ) from error

            # determine oscap eval type based on document type
            print(f"\nDetermine OpenSCAP document type of input file: {oscap_input_file}")
            oscap_document_type = OpenSCAPGeneric.__get_oscap_document_type(
                oscap_input_file=oscap_input_file
            )
            print(
                "Determined OpenSCAP document type of input file"
                f" ({oscap_input_file}): {oscap_document_type}"
            )
            print(
                f"\nDetermine OpenSCAP eval type for input file ({oscap_input_file}) "
                f"of document type: {oscap_document_type}"
            )
            oscap_eval_type = OpenSCAPGeneric.__get_oscap_eval_type_based_on_document_type(
                oscap_document_type=oscap_document_type
            )
            print(
                "Determined OpenSCAP eval type of input file"
                f" ({oscap_input_file}): {oscap_eval_type}"
            )

            # Execute scan in the context of buildah unshare
            #
            # NOTE: run in the context of `buildah unshare` so that container does not
            #       need to be run in a privilaged mode
            oscap_out_file_path = self.write_working_file(f'oscap-{oscap_eval_type}-out')
            oscap_xml_results_file_path = self.write_working_file(
                f'oscap-{oscap_eval_type}-results.xml'
            )
            oscap_html_report_path = self.write_working_file(f'oscap-{oscap_eval_type}-report.html')
            print("\nRun oscap scan")
            oscap_eval_success, oscap_eval_fails = OpenSCAPGeneric.__run_oscap_scan(
                buildah_unshare_command=buildah_unshare_command,
                oscap_eval_type=oscap_eval_type,
                oscap_input_file=oscap_input_file,
                oscap_out_file_path=oscap_out_file_path,
                oscap_xml_results_file_path=oscap_xml_results_file_path,
                oscap_html_report_path=oscap_html_report_path,
                container_mount_path=container_mount_path,
                oscap_profile=oscap_profile,
                oscap_tailoring_file=oscap_tailoring_file,
                oscap_fetch_remote_resources=oscap_fetch_remote_resources
            )
            print(f"OpenSCAP scan completed with eval success: {oscap_eval_success}")

            # save scan results
            step_result.success = oscap_eval_success
            if not oscap_eval_success:
                step_result.message = f"OSCAP eval found issues:\n{oscap_eval_fails}"

            step_result.add_artifact(
                name='html-report',
                value=oscap_html_report_path
            )
            step_result.add_artifact(
                name='xml-report',
                value=oscap_xml_results_file_path
            )
            step_result.add_artifact(
                name='stdout-report',
                value=oscap_out_file_path
            )
        except (StepRunnerException, RuntimeError) as error:
            step_result.success = False
            step_result.message = str(error)

        return step_result

    @staticmethod
    def __get_oscap_document_type(oscap_input_file):
        """Gets the OpenSCAP document type for a given input file.

        Parameters
        ----------
        oscap_input_file : path
            Path to OSCAP file to determine the OpenSCAP document type of.

        Returns
        -------
        str
            OpenSCAP document type. For example:
            * Source Data Stream
            * XCCDF Checklist
            * OVAL Definitions

        Raises
        ------
        StepRunnerException
            If error getting document type of oscap input file.
        """

        oscap_document_type = None
        try:
            oscap_info_out_buff = StringIO()
            sh.oscap.info(  # pylint: disable=no-member
                oscap_input_file,
                _out=oscap_info_out_buff
            )
            oscap_info_out = oscap_info_out_buff.getvalue().rstrip()
            oscap_document_type_match = OpenSCAPGeneric.OSCAP_INFO_DOC_TYPE_PATTERN.search(
                oscap_info_out
            )
            oscap_document_type = oscap_document_type_match.groupdict()['doctype']
        except sh.ErrorReturnCode as error:
            raise StepRunnerException(
                f"Error getting document type of oscap input file"
                f" ({oscap_input_file}): {error}"
            ) from error

        return oscap_document_type

    @staticmethod
    def __get_oscap_eval_type_based_on_document_type(oscap_document_type):
        """Given an OSCAP document type returns the type of oscap eval that should be used.

        Parameters
        ----------
        oscap_document_type : str
            OSCAP Document type to get the oscap eval type for.

        Returns
        -------
        str
            OSCAP eval type to perform on document with given oscap document type.
        """
        oscap_eval_type = None

        if oscap_document_type == 'Source Data Stream':
            oscap_eval_type = 'xccdf'
        elif oscap_document_type == 'XCCDF Checklist':
            oscap_eval_type = 'xccdf'
        elif oscap_document_type == 'OVAL Definitions':
            oscap_eval_type = 'oval'

        return oscap_eval_type

    @staticmethod
    def __run_oscap_scan(  # pylint: disable=too-many-arguments,too-many-locals,too-many-branches,too-many-statements
        buildah_unshare_command,
        oscap_eval_type,
        oscap_input_file,
        oscap_out_file_path,
        oscap_xml_results_file_path,
        oscap_html_report_path,
        container_mount_path,
        oscap_profile=None,
        oscap_tailoring_file=None,
        oscap_fetch_remote_resources=True
    ):
        """Run an oscap scan in the context of a buildah unshare to run "rootless".

        Parameters
        ----------
        buildah_unshare_command : sh.buildah.unshare.bake()
            A baked sh.buildah.unshare command to use to run this command in the context off
            so that this can be done "rootless".
        oscap_eval_type : str
            The type of oscap eval to perform. Must be a valid oscap eval type.
            EX: xccdf, oval
        oscap_input_file : str
            Path to rules file passed to the oscap command.
        oscap_out_file_path : str
            Path to write the stdout and stderr of running the oscap command to.
        oscap_xml_results_file_path : str
            Write the scan results into this file.
        oscap_html_report_path : str
            Write the human readable (HTML) report into this file.
        container_mount_path : str
            Path to the mounted container to scan.
        oscap_tailoring_file : str
            XCCF Tailoring file.
            See:
            - https://www.open-scap.org/security-policies/customization/
            - https://www.open-scap.org/resources/documentation/customizing-scap-security-guide-for-your-use-case/ # pylint: disable=line-too-long
            - https://static.open-scap.org/openscap-1.2/oscap_user_manual.html#_how_to_tailor_source_data_stream # pylint: disable=line-too-long
        oscap_profile : str
            OpenSCAP profile to evaluate. Must be a valid profile in the given oscap_input_file.
            EX: if you perform an `oscap info oscap_input_file` the profile must be listed.

        Returns
        -------
        oscap_eval_success : bool
            True if oscap eval passed all rules
            False if oscap eval failed any rules
        oscap_eval_fails : str
            If oscap_eval_success is True then indeterminate.
            If oscap_eval_success is False then string of all of the failed rules.

        Raises
        ------
        StepRunnerException
            If unexpected error running oscap scan.
        """

        oscap_profile_flag = None
        if oscap_profile is not None:
            oscap_profile_flag = f"--profile={oscap_profile}"

        oscap_fetch_remote_resources_flag = None
        if isinstance(oscap_fetch_remote_resources, str):
            oscap_fetch_remote_resources = strtobool(oscap_fetch_remote_resources)
        if oscap_fetch_remote_resources:
            oscap_fetch_remote_resources_flag = "--fetch-remote-resources"

        oscap_tailoring_file_flag = None
        if oscap_tailoring_file is not None:
            oscap_tailoring_file_flag = f"--tailoring-file={oscap_tailoring_file}"

        oscap_eval_success = None
        oscap_eval_out_buff = StringIO()
        oscap_eval_out = ""
        oscap_eval_fails = None
        try:
            oscap_chroot_command = buildah_unshare_command.bake("oscap-chroot")
            with open(oscap_out_file_path, 'w', encoding='utf-8') as oscap_out_file:
                out_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                    oscap_eval_out_buff,
                    oscap_out_file
                ])
                err_callback = create_sh_redirect_to_multiple_streams_fn_callback([
                    oscap_eval_out_buff,
                    oscap_out_file
                ])
                oscap_chroot_command(
                    container_mount_path,
                    oscap_eval_type,
                    'eval',
                    oscap_profile_flag,
                    oscap_fetch_remote_resources_flag,
                    oscap_tailoring_file_flag,
                    f'--results={oscap_xml_results_file_path}',
                    f'--report={oscap_html_report_path}',
                    oscap_input_file,
                    _out=out_callback,
                    _err=err_callback,
                    _tee='err'
                )
                oscap_eval_success = True
        except sh.ErrorReturnCode_1 as error:  # pylint: disable=no-member
            oscap_eval_success = error
        except sh.ErrorReturnCode_2 as error:  # pylint: disable=no-member
            # XCCDF: If there is at least one rule with either fail or unknown result,
            #           oscap-scan finishes with return code 2.
            # OVAL:  Never returned
            #
            # Source: https://www.systutorials.com/docs/linux/man/8-oscap/
            if oscap_eval_type == 'xccdf':
                oscap_eval_success = False
            else:
                oscap_eval_success = error
        except sh.ErrorReturnCode as error:
            oscap_eval_success = error

        # get the oscap output
        oscap_eval_out = oscap_eval_out_buff.getvalue()

        # parse the oscap output
        # NOTE: oscap is puts carrage returns (\r / ^M) in their output, remove them
        oscap_eval_out = re.sub('\r', '', oscap_eval_out)

        # print the oscap output no matter the results
        print(oscap_eval_out)

        # if unexpected error throw error
        if isinstance(oscap_eval_success, Exception):
            raise StepRunnerException(
                f"Error running 'oscap {oscap_eval_type} eval': {oscap_eval_success} "
            ) from oscap_eval_success

        # NOTE: oscap oval eval returns exit code 0 whether or not any rules failed
        #       need to search output to determine if there were any rule failures
        if oscap_eval_type == 'oval' and oscap_eval_success:
            oscap_eval_fails = ""
            for match in OpenSCAPGeneric.OSCAP_OVAL_STDOUT_PATTERN.finditer(oscap_eval_out):
                # NOTE: need to do regex and not == because may contain xterm color chars
                if OpenSCAPGeneric.OSCAP_OVAL_STDOUT_FAIL_PATTERN.search(
                        match.groupdict()['ruleresult']
                ):
                    oscap_eval_fails += match.groupdict()['ruleblock']
                    oscap_eval_fails += "\n"
                    oscap_eval_success = False

        # if failed xccdf eval then parse out the fails
        if oscap_eval_type == 'xccdf' and not oscap_eval_success:
            oscap_eval_fails = ""
            for match in OpenSCAPGeneric.OSCAP_XCCDF_STDOUT_PATTERN.finditer(oscap_eval_out):
                # NOTE: need to do regex and not == because may contain xterm color chars
                if re.search(r'fail', match.groupdict()['ruleresult']):
                    oscap_eval_fails += "\n"
                    oscap_eval_fails += match.groupdict()['ruleblock']
                    oscap_eval_fails += "\n"

        return oscap_eval_success, oscap_eval_fails
