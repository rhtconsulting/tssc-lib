# pylint: disable=line-too-long
"""Ploigos Step Runner (psr) main entry point.

Command-Line Options
--------------------

    -h, --help
        show this help message and exit

    -s STEP, --step STEP
        Ploigos workflow step to run

    -e ENVIRONMENT, --environment  ENVIRONMENT
        The environment to run this step against.

    -c CONFIG [CONFIG ...], --config CONFIG [CONFIG ...]
        Ploigos workflow configuration files, or directories containing files, in yml or json

    --step-config STEP_CONFIG_KEY=STEP_CONFIG_VALUE [STEP_CONFIG_KEY=STEP_CONFIG_VALUE ...]
        Override step config provided by the given Ploigos
        config-file with these arguments.

Step Configuration
------------------

### Steps

* generate-metadata
* tag-source
* static-code-analysis
* package
* unit-test
* push-artifacts
* create-container-image
* push-container-image
* sign-container-image
* container-image-unit-test
* container-image-static-compliance-scan
* container-image-static-vulnerability-scan
* create-deployment-environment
* deploy
* validate-environment-configuration
* uat
* runtime-vulnerability-scan
* canary-test
* undeploy
* report
* publish-workflow-results
* automated-governance

### Variable Precedence

From least precedence to highest precedence.

    1. StepImplementer implementation provided configuration defaults
    2. Global Configuration Defaults (step-runner-config.global-defaults)
    3. Global Environment Configuration Defaults (step-runner-config.global-environment-defaults)
    4. Step Configuration (step-runner-config.{STEP_NAME}.config)
    5. Step Environment Configuration
         (step-runner-config.{STEP_NAME}.environment-config.{ENVIRONMENT_NAME})
    6. Step Configuration Runtime Overrides (--environment arugment to main entry point)

** Example 1 **

    ---
    step-runner-config:
      # List of decryptors to use to decrypt any encrypted configuration.
      config-decryptors:
      - implementer: SOPS
        #config:
        #  additional_sops_args: [
        #    '--any-valid-sops-cmd-arg-here=value',
        #    '--aws-profile=FOO'
        #  ]

      # Dictionary of configuration options which will be used in step configuration if that
      # step does not have a specific value for that configuration already or one is not
      # given by global-environment-defaults.
      global-defaults:
        # A sample config option with a default global value.
        # Overrides
        #   * StepImplementers default config values
        # Is Overriden by:
        #   * global-environment-defaults
        #   * step config
        #   * step environment config
        #   * step config runtime overrides
        sample-config-option-1: 'global default'

      # Dictionary of dictionaries where the first level keys are environment names and their
      # dictionary values are configuration defaults to use when invoking a step in the context
      # of that environment.
      #
      # NOTE: Environment names can be anything so long as they line up with the environment value
      # given to the `--environment` flag of the main entry point.
      #global-environment-defaults:
        # Sample configuration for an environment named 'SAMPLE-ENV-1'.
        #
        # NOTE: Environment names can be anything so long as they line up with the environment value
        # given to the `--environment` flag of the main entry point.
        #SAMPLE-ENV-1:
          # Sample config option that may differ from environment to environment.
          #sample-config-option-2: 'default for use in the SAMPLE-ENV-1 env"

        # Sample configuration for an environment named 'SAMPLE-ENV-2'.
        #
        # NOTE: Environment names can be anything so long as they line up with the environment value
        # given to the `--environment` flag of the main entry point.
        #SAMPLE-ENV-2:
          # Sample config option that may differ from environment to environment.
          #sample-config-option-2: 'default for use in the SAMPLE-ENV-2 env"

      # Sample step config for step named SAMPLE-STEP-1
      SAMPLE-STEP-1:
      - implementer: SampleStep1Implementer1
        config:
          sample-config-option-3: 'value for sample-config-option-3 for use in this step'
          additional-artifacts-dirs:
          - name: sample-user-supplied-artifact
            path: sample/path/to/user/supplied/artifact
        environment-config:
          SAMPLE-ENV-1:
            sample-config-option-4: 'value for use in this step in SAMPLE-ENV-1 environment'
          SAMPLE-ENV-2:
            sample-config-option-4: 'value for use in this step in SAMPLE-ENV-1 environment'

### Example Configuration Files

.. Note::
    Optional step configurations are listed commented out and with their default values.

** Example Config file for a Maven built Application **

    ---
    step-runner-config:
      # Optional
      # List of decryptors to use to decrypt any encrypted configuration.
      config-decryptors:
      - implementer: SOPS
        #config:
        #  additional_sops_args: [
        #    '--any-valid-sops-cmd-arg-here=value',
        #    '--aws-profile=FOO'
        #  ]

      # Optional
      # Dictionary of configuration options which will be used in step configuration if that
      # step does not have a specific value for that configuration already or one is not
      # given by global-environment-defaults.
      global-defaults:
        # Required.
        # Name of the application the artifact built and deployed by this workflow is part of.
        application-name: ''

        # Required.
        # Name of the service this artifact built and deployed by this workflow implements as
        # part of the application it is a part of.
        service-name: ''

        # Optional.
        # Maven server settings for settings.xml file
        #maven-servers:
        #  internal-mirror-1:
        #    id: ''
        #    username: ''
        #    password: ''
        #  internal-mirror-2:
        #    id: ''
        #    username: ''
        #    password: ''

        # Optional.
        # Maven repository settings for settings.xml file
        #maven-repositories:
        #  internal-mirror-1:
        #    id: ''
        #    url: ''
        #    snapshots: ''
        #    releases: ''
        #  internal-mirror-2:
        #    id: ''
        #    url: ''
        #    snapshots: ''
        #    releases: ''

        # Optional.
        # Maven mirror settings for settings.xml file
        #maven-mirrors:
        #  internal-mirror-1:
        #    id: ''
        #    url: ''
        #    mirror-of: ''
        #  internal-mirror-2:
        #    id: ''
        #    url: ''
        #    mirror-of: ''

        # Dictionary of container registries to authenticate with.
        # Suggest putting in global configuration so it can be used for creating and pushing
        # images. But can also or instead be put in the individual steps if say different
        # registires are used for building images then pushing them.
        #container-registries:
        #  registry.redhat.io:
        #    username: account_number|acount_name
        #    password: encrypt_me
        #  registry.internal.example.xyz:
        #    username: team_name+project_name
        #    password: encrypt_me

      # Optional
      # Dictionary of dictionaries where the first level keys are environment names and their
      # dictionary values are configuration defaults to use when invoking a step in the context
      # of that environment.
      #
      # NOTE: Environment names can be anything so long as they line up with the environment value
      # given to the `--environment` flag of the main entry point.
      global-environment-defaults:
        # Sample
        # Sample configuration for an environment named 'DEV'.
        #
        # NOTE: Environment names can be anything so long as they line up with the environment value
        # given to the `--environment` flag of the main entry point.
        DEV:
          #Optional
          #kube-api-token: ''

          # Required
          argocd-username: ''

          # Required
          argocd-password: ''

          # Required
          argocd-api: ''

          # Optional
          #argocd-sync-timeout-seconds: '60'

          # Optional
          #deployment-config-helm-chart-path: './'

        # Sample
        # Sample configuration for an environment named 'TEST'
        #
        # NOTE: Environment names can be anything so long as they line up with the environment value
        # given to the `--environment` flag of the main entry point.
        TEST:
          #Optional
          #kube-api-token: ''

          # Required
          argocd-username: ''

          # Required
          argocd-password: ''

          # Required
          argocd-api: ''

          # Optional
          #argocd-sync-timeout-seconds: '60'

          # Optional
          #deployment-config-helm-chart-path: './'

        # Sample
        # Sample configuration for an environment named 'PROD'
        #
        # NOTE: Environment names can be anything so long as they line up with the environment value
        # given to the `--environment` flag of the main entry point.
        #PROD:
        # Sample
        # Sample parameter that may differ from environment to environment.
        #kube-api-uri: 'api.prod.myorg.xyz"

      generate-metadata:
      - implementer: Maven
        config: {
          # Optional.
          #pom-file: 'pom.xml'
        }

      - implementer: Git
        config: {
          # Optional.
          #git-repo-root: './'

          # Optional.
          #build-string-length: 7
        }

      - implementer: SemanticVersion

      tag-source:
      - implementer: Git
        config: {
          # Optional.
          # Will use current directory to determine URL if not specified.
          #url: None

          # Optional.
          #username: None

          # Optional.
          #password: None
        }

      static-code-analysis:
      - implementer: SonarQube
        config: {
          # Required.
          # URL to the sonarqube server
          url: ''

          # Optional.
          # Properties file in root folder (eg: sonar-project.properties)
          #properties: ''

          # Optional.
          #user: None

          # Optional.
          #password: None
        }

      unit-test:
      - implementer: MavenTest
        config: {
          # Optional.
          # pom_file: 'pom.xml'

          # Optional.
          # tls-verify: True

          # Optional.
          # maven-profiles: []

          # Optional.
          # maven-no-transfer-progress: True

          # Optional.
          # maven-additional-arguments: []

          # Optional.
          # NOTE: Will attempt to dynamically determine from pom if not given.
          # test-reports-dir: 'target/surefire-reports
        }

      package:
      - implementer: MavenPackage
        config: {
          # Optional.
          #pom-file: 'pom.xml'

          # Optional
          #artifact-extensions: ['jar', 'war', 'ear']

          # Optional
          #artifact-parent-dir: 'target'
        }

      push-artifacts:
      - implementer: MavenDeploy
        config: {
          # Required.
          # URL to the artifact repository to push the artifact to.
          maven-push-artifact-repo-url: ''

          # Required.
          # Id to the artifact repository to push the artifact to.
          maven-push-artifact-repo-id: ''
      - implementer: GradelDeploy
        config: {
          # Required.
          # URL to the artifact repository to push the artifact to.
          # maven-push-artifact-repo-url: ''

          # Required.
          # Id to the artifact repository to push the artifact to.
          # maven-push-artifact-repo-id: ''

        }

      create-container-image:
      - implementer: Buildah
        config: {
          # Optional.
          #imagespecfile: 'Dockerfile'

          # Optional.
          #context: '.'

          # Optional.
          #tls-verify: true

          # Optional.
          #format: 'oci'
        }

      generate-evidence:
      - implementer: GenerateEvidence
        config: {
          evidence-destination-url: 'http:/example-evidence-destination-url',
          evidence-destination-username: 'username'
        }
      - implementer: RekorSignEvidence
        config: {
          rekor-server-url: 'http://example-rekor-server-url-url/',
          signer-pgp-private-key: '/path/to/signer-pgp-private-key-path'
        }

      audit-attestation:
      - implementer: OpenPolicyAgent
        config: {
          workflow-policy-uri: 'http://example-workflow-policy-uri/uri',
          evidence-uri: 'http://example-evidence-uri/uri'
        }

      push-container-image:
      - implementer: Skopeo
        config: {
          destination: '' # Required. Container image repository destination to push image to
          #src-tls-verify: true # Optional
          #dest-tls-verify: true # Optional
        }

      sign-container-image:
      # sample signing container image but not pushing the signature anywhere
      #   signature will be included in workflow results archive.
      - implementer: PodmanSign
        config: {}

      # sample signing container image and pushing container image signature to remote repository
      #- implementer: PodmanSign
      #  config:
      #    container-image-signature-destination-url: https://repository.ploigos.com/container-image-signatures
      #    container-image-signature-destination-username: test-user
      #    container-image-signature-destination-password: pass123 # this value should be put in an encrypted config file

      # sample signing container image and pushing container image signature to local file
      #- implementer: PodmanSign
      #  config:
      #    container-image-signature-destination-url: file://image-signatures-mount/

      container-image-static-compliance-scan:
      # sample scans using DataStream file (preferred)
      - name: OpenSCAP - Compliance - Example Compliance Profile for UBI8 Container Images [Based on xccdf_org.ssgproject.content_profile_standard]
        implementer: OpenSCAP
        config:
          oscap-input-definitions-uri: https://atopathways.redhatgov.io/compliance-as-code/scap/ssg-rhel8-ds.xml
          oscap-tailoring-uri: https://raw.githubusercontent.com/ploigos/ploigos-example-oscap-content/main/xccdf_com.redhat.ploigos_profile_example_ubi8-tailoring-xccdf.xml
          oscap-profile: xccdf_com.redhat.ploigos_profile_example_ubi8
      #- name: OpenSCAP - Compliance (Protection Profile for General Purpose Operating Systems) - DataStream
      #  implementer: OpenSCAP
      #  config:
      #    oscap-input-definitions-uri: https://atopathways.redhatgov.io/compliance-as-code/scap/ssg-rhel8-ds.xml
      #    oscap-profile: xccdf_org.ssgproject.content_profile_ospp
      #- name: OpenSCAP - Compliance (DISA STIG for Red hat Enterprise Linux 8) - DataStream
      #  implementer: OpenSCAP
      #  config:
      #    oscap-input-definitions-uri: https://atopathways.redhatgov.io/compliance-as-code/scap/ssg-rhel8-ds.xml
      #    oscap-profile: xccdf_org.ssgproject.content_profile_stig

      # sample scans using XCCDF file (okay if you don't have access to DataStream)
      #- name: OpenSCAP - Compliance (DISA STIG for Red hat Enterprise Linux 8) - XCCDF
      #  implementer: OpenSCAP
      #  config:
      #    oscap-input-definitions-uri: https://atopathways.redhatgov.io/compliance-as-code/scap/ssg-rhel8-xccdf.xml
      #    oscap-profile: stig
      #- name: OpenSCAP - Compliance (Protection Profile for General Purpose Operating Systems) - XCCDF
      #  implementer: OpenSCAP
      #  config:
      #    oscap-input-definitions-uri: https://atopathways.redhatgov.io/compliance-as-code/scap/ssg-rhel8-xccdf.xml
      #    oscap-profile: ospp

      container-image-static-vulnerability-scan:
      # sample vulnerability scan using XCCDF file (preferred)
      - name: OpenSCAP - Vulnerability - DataStream
        implementer: OpenSCAP
        config:
          oscap-input-definitions-uri: https://www.redhat.com/security/data/metrics/ds/v2/RHEL8/rhel-8.ds.xml.bz2

      # sample scans using OVAL file (if you must, but XCCDF is muuuuch better if availabe)
      #- name: OpenSCAP - Vulnerability - OVAL
      #  implementer: OpenSCAP
      #  config:
      #    oscap-input-definitions-uri: https://www.redhat.com/security/data/oval/v2/RHEL8/rhel-8.oval.xml.bz2
      # sample scan using DataStream file

      deploy:
      - implementer: ArgoCD
        config:
          # argocd specific variables are set per environment above

          # Required
          helm-config-repo: ''

          # Optional
          #values-yaml-directory: './cicd/Deployment/'

          # Optional
          #value-yaml-template: 'values.yaml.j2'

          # Required
          git-email: ''

          # Optional
          #git-name: 'ploigos'

          # Optional
          #git-username: None

          # Optional
          #git-password: None

          # Any template parameters required by values.yaml.j2 can be listed below. Note dashes will
          # be converted to underscores to be compliant with the jinja template variable
          # specification
          readiness-probe-path: ''

      validate-environment-configuration:
      - implementer: ConfiglintFromArgocd
        config: {}
      - implementer: Configlint
        config: {
          # Optional.
          # Path to the rules file
          #rules: ''
        }

      uat:
      - implementer: MavenIntegrationTest
        config:
          target-host-url-maven-argument-name: 'target.base.url'
          maven-additional-arguments:
          - -Dselenium.hub.url=http://selenium.plogios.xyz:4242

          # Optional.
          # pom_file: 'pom.xml'

          # Optional.
          # tls-verify: True

          # Optional.
          # maven-profiles: []

          # Optional.
          # maven-no-transfer-progress: True

          # Optional.
          # maven-additional-arguments: []

          # Optional.
          # NOTE: Will attempt to dynamically determine from pom if not given.
          # test-reports-dir: 'target/surefire-reports

      report:
      - implementer: ResultArtifactsArchive
        config:
          results-archive-destination-url: https://artifact-repo.plogios.com/release-engineering-workflow-result-artifacts-archives/
          results-archive-destination-username: mock-name

          # NOTE: should encrypt this
          results-archive-destination-password: mock-pass

** Example Config file for a NPM built Application **

    ---
    step-runner-config:
      # Optional
      # List of decryptors to use to decrypt any encrypted configuration.
      config-decryptors:
      - implementer: SOPS
        #config:
        #  additional_sops_args: [
        #    '--any-valid-sops-cmd-arg-here=value',
        #    '--aws-profile=FOO'
        #  ]

      # Optional
      # Dictionary of configuration options which will be used in step configuration if that
      # step does not have a specific value for that configuration already or one is not
      # given by global-environment-defaults.
      global-defaults:
        # Required.
        # Name of the application the artifact built and deployed by this workflow is part of.
        application-name: ''

        # Required.
        # Name of the service this artifact built and deployed by this workflow implements as
        # part of the application it is a part of.
        service-name: ''

        # Optional.
        # Dictionary of container registries to authenticate with.
        # Suggest putting in global configuration so it can be used for creating and pushing
        # images. But can also or instead be put in the individual steps if say different
        # registires are used for building images then pushing them.
        #container-registries:
        #  registry.redhat.io:
        #    username: account_number|acount_name
        #    password: encrypt_me
        #  registry.internal.example.xyz:
        #    username: team_name+project_name
        #    password: encrypt_me

      # Optional
      # Dictionary of dictionaries where the first level keys are environment names and their
      # dictionary values are configuration defaults to use when invoking a step in the context
      # of that environment.
      #
      # NOTE: Environment names can be anything so long as they line up with the environment value
      # given to the `--environment` flag of the main entry point.
      global-environment-defaults:
        # Optional Sample
        # Sample configuration for an environment named 'DEV'.
        #
        # NOTE: Environment names can be anything so long as they line up with the environment value
        # given to the `--environment` flag of the main entry point.
        DEV:
          #Optional
          #kube-api-token: ''

          # Required
          argocd-username: ''

          # Required
          argocd-password: ''

          # Required
          argocd-api: ''

          # Optional
          #argocd-sync-timeout-seconds: '60'

          # Optional
          #deployment-config-helm-chart-path: './'

        # Sample
        # Sample configuration for an environment named 'TEST'
        #
        # NOTE: Environment names can be anything so long as they line up with the environment value
        # given to the `--environment` flag of the main entry point.
        TEST:
          #Optional
          #kube-api-token:

          # Required
          argocd-username: ''

          # Required
          argocd-password: ''

          # Required
          argocd-api: ''

          # Optional
          #argocd-sync-timeout-seconds: '60'

          # Optional
          #deployment-config-helm-chart-path: './'

        # Sample
        # Sample configuration for an environment named 'PROD'
        #
        # NOTE: Environment names can be anything so long as they line up with the environment value
        # given to the `--environment` flag of the main entry point.
        #PROD:
        # Sample
        # Sample parameter that may differ from environment to environment.
        #kube-api-uri: 'api.prod.myorg.xyz"

      generate-metadata:
      # WARNING: not yet implemented
      - implementer: NPM
        config: {}

      - implementer: Git
        config: {
          # Optional.
          #git-repo-root: './'

          # Optional.
          #build-string-length: 7
        }

      - implementer: SemanticVersion

      tag-source:
      - implementer: Git
        config: {
          # Optional.
          # Will use current directory to determine URL if not specified.
          #url: None

          # Optional.
          #username: None

          # Optional.
          #password: None
        }

      static-code-analysis:
      - implementer: SonarQube
        config: {
          # Required.
          # URL to the sonarqube server
          url: ''

          # Optional.
          # Properties file in root folder (eg: sonar-project.properties)
          #properties: ''

          # Optional.
          #user: None

          # Optional.
          #password: None
        }

      package:
      # WARNING: not yet implemented
      - implementer: NPM
        config: {}

      unit-test:
      - implementer: NpmXunitTest
        config:
          test-reports-dir: test_results

          # Optional.
          # npm-envs:
          #   ENV_VAR1: VALUE1
          #   ENV_VAR2: VALUE2

          # Optional.
          #npm-test-script: test

      - implementer: NpmTest
        config:
          # Optional.
          # npm-envs:
          #   ENV_VAR1: VALUE1
          #   ENV_VAR2: VALUE2
          
      - implementer: GradleTest
        config: {}
  
      push-artifacts:
      # WARNING: not yet implemented
      - implementer: NPM
        config: {}

      create-container-image:
      - implementer: Buildah
        config: {
          # Optional.
          #imagespecfile: 'Dockerfile'

          # Optional.
          #context: '.'

          # Optional.
          #tls-verify: true

          # Optional.
          #format: 'oci'
        }

      generate-evidence:
      - implementer: GenerateEvidence
        config: {
          evidence-destination-url: 'http:/example-evidence-destination-url',
          evidence-destination-username: 'username'
        }
      - implementer: RekorSignEvidence
        config: {
          rekor-server-url: 'http://example-rekor-server-url-url/',
          signer-pgp-private-key: '/path/to/signer-pgp-private-key-path'
        }

      audit-attestation:
      - implementer: OpenPolicyAgent
        config: {
          workflow-policy-uri: 'http://example-workflow-policy-uri/uri',
          evidence-uri: 'http://example-evidence-uri/uri'
        }

      push-container-image:
      - implementer: Skopeo
        config: {
          destination: '' # Required. Container image repository destination to push image to
          #src-tls-verify: true # Optional
          #dest-tls-verify: true # Optional
        }

      sign-container-image:
      # sample signing container image but not pushing the signature anywhere
      #   signature will be included in workflow results archive.
      - implementer: PodmanSign
        config: {}

      # sample signing container image and pushing container image signature to remote repository
      #- implementer: PodmanSign
      #  config:
      #    container-image-signature-destination-url: https://repository.ploigos.com/container-image-signatures
      #    container-image-signature-destination-username: test-user
      #    container-image-signature-destination-password: pass123 # this value should be put in an encrypted config file

      # sample signing container image and pushing container image signature to local file
      #- implementer: PodmanSign
      #  config:
      #    container-image-signature-destination-url: file://image-signatures-mount/

      container-image-static-compliance-scan:
      # sample scans using DataStream file (preferred)
      - name: OpenSCAP - Compliance - Example Compliance Profile for UBI8 Container Images [Based on xccdf_org.ssgproject.content_profile_standard]
        implementer: OpenSCAP
        config:
          oscap-input-definitions-uri: https://atopathways.redhatgov.io/compliance-as-code/scap/ssg-rhel8-ds.xml
          oscap-tailoring-uri: https://raw.githubusercontent.com/ploigos/ploigos-example-oscap-content/main/xccdf_com.redhat.ploigos_profile_example_ubi8-tailoring-xccdf.xml
          oscap-profile: xccdf_com.redhat.ploigos_profile_example_ubi8
      #- name: OpenSCAP - Compliance (Protection Profile for General Purpose Operating Systems) - DataStream
      #  implementer: OpenSCAP
      #  config:
      #    oscap-input-definitions-uri: https://atopathways.redhatgov.io/compliance-as-code/scap/ssg-rhel8-ds.xml
      #    oscap-profile: xccdf_org.ssgproject.content_profile_ospp
      #- name: OpenSCAP - Compliance (DISA STIG for Red hat Enterprise Linux 8) - DataStream
      #  implementer: OpenSCAP
      #  config:
      #    oscap-input-definitions-uri: https://atopathways.redhatgov.io/compliance-as-code/scap/ssg-rhel8-ds.xml
      #    oscap-profile: xccdf_org.ssgproject.content_profile_stig

      # sample scans using XCCDF file (okay if you don't have access to DataStream)
      #- name: OpenSCAP - Compliance (DISA STIG for Red hat Enterprise Linux 8) - XCCDF
      #  implementer: OpenSCAP
      #  config:
      #    oscap-input-definitions-uri: https://atopathways.redhatgov.io/compliance-as-code/scap/ssg-rhel8-xccdf.xml
      #    oscap-profile: stig
      #- name: OpenSCAP - Compliance (Protection Profile for General Purpose Operating Systems) - XCCDF
      #  implementer: OpenSCAP
      #  config:
      #    oscap-input-definitions-uri: https://atopathways.redhatgov.io/compliance-as-code/scap/ssg-rhel8-xccdf.xml
      #    oscap-profile: ospp

      container-image-static-vulnerability-scan:
      # sample vulnerability scan using XCCDF file (preferred)
      - name: OpenSCAP - Vulnerability - DataStream
        implementer: OpenSCAP
        config:
          oscap-input-definitions-uri: https://www.redhat.com/security/data/metrics/ds/v2/RHEL8/rhel-8.ds.xml.bz2

      # sample scans using OVAL file (if you must, but XCCDF is muuuuch better if availabe)
      #- name: OpenSCAP - Vulnerability - OVAL
      #  implementer: OpenSCAP
      #  config:
      #    oscap-input-definitions-uri: https://www.redhat.com/security/data/oval/v2/RHEL8/rhel-8.oval.xml.bz2
      # sample scan using DataStream file

      deploy:
      - implementer: ArgoCD
        config:
          # argocd specific variables are set per environment above

          # Required
          helm-config-repo: ''

          # Optional
          #values-yaml-directory: './cicd/Deployment/'

          # Optional
          #value-yaml-template: 'values.yaml.j2'

          # Optional
          #deployment-config-helm-chart-path: './'

          # Required
          git-email: ''

          # Optional
          #git-name: 'ploigos'

          # Optional
          #git-username: None

          # Optional
          #git-password: None

          # Any template parameters required by values.yaml.j2 can be listed below.
          # Note dashes will be converted to underscores to be compliant with the jinja
          # template variable specification
          readiness-probe-path: ''

      uat:
      - implementer: NpmXunitIntegrationTest
        config:
          target-host-env-var-name: APP_ROUTE
          test-reports-dir: uat-reports

          # Optional.
          # npm-test-script: test:uat

          # Optional.
          # npm-envs:
          #   WEB_DRIVER_URL: http://selenium-grid.devsecops:4444/wd/hub
          #   BROWSER: chrome
          #   USER1: test1
          #   USER2: test2

      report:
      - implementer: ResultArtifactsArchive
        config:
          results-archive-destination-url: https://artifact-repo.plogios.com/release-engineering-workflow-result-artifacts-archives/
          results-archive-destination-username: mock-name

          # NOTE: should encrypt this
          results-archive-destination-password: mock-pass

Examples
--------

Getting Help

>>> psr --help


Example Running the 'generate-metadata' step

>>> psr
...     --config=my-app-step-runner-config.yml \
...     --step=generate-metadata

"""

import __main__
