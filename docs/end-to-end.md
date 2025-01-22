# End-to-End Ploigos Step Runner (PSR) Example

Below is an end-to-end example pipeline that leverages PSR.

## Example Scenario

- We have two applications
    - First is a Java Spring backend API built with Maven
    - Second is a JavaScript React frontend built with NPM
- We want to build a pipeline that has 5 stages
    - Generate Metadata
    - Unit test
    - Package
    - Create Container Image
    - Push Container Image
- We want to use Jenkins as the workflow runner

## Step 1: Configure *psr.yaml* for Maven

Create a *psr.yaml* file in the source code repo for the Spring application:

```yaml
step-runner-config:

  global-defaults:
    organization: ploigos
    service-name: java-app
    application-name: java-app

  generate-metadata:
  - implementer: Maven
  - implementer: Git
  - implementer: SemanticVersion

  unit-test:
    - implementer: MavenTest

  package:
  - implementer: MavenPackage

  create-container-image:
  - implementer: Buildah
    config:
      containers-config-auth-file: /var/jenkins_home/container-auth.json

  push-container-image:
  - implementer: Skopeo
    config:
      destination-url: docker-nexus.apps.mycluster.io
      container-image-push-repository: ploigos/java-app
```

> :notebook: The order in psr.yaml does not matter. Additionally, even if a
> step appears in psr.yaml, the step must be explicitly called by the workflow
> runner. psr.yaml contains configurations for your steps when they are
> executed by the pipeline. The pipeline definition for your workflow runner
> will dictate what steps are called and in what order.

## Step 2: Configure *psr.yaml* for NPM

Create a *psr.yaml* file in the source code repo for the NPM application:

```yaml
step-runner-config:

  global-defaults:
    organization: ploigos
    service-name: javascript-app
    application-name: javascript-app

  generate-metadata:
  - implementer: Npm
  - implementer: Git
  - implementer: SemanticVersion

  unit-test:
    - implementer: NpmTest
    - implementer: GradleTest

  package:
  - implementer: NpmPackage

  create-container-image:
  - implementer: Buildah
    config:
      containers-config-auth-file: /var/jenkins_home/container-auth.json

  push-container-image:
  - implementer: Skopeo
    config:
      destination-url: docker-nexus.apps.mycluster.io
      container-image-push-repository: ploigos/javascript-app

```

## Step 3: Create a Pipeline using any CI/CD Workflow Runner

PSR runs inside of a CI/CD pipeline, but it does not orchestrate the pipeline.
You need another tool for that, and PSR does not care which one you choose.
Portability between CI/CD workflow runners is one benefit of the PSR. For this
example we will create a simple Jenkins pipeline.

> :notebook: This is a simple example. Real-world pipelines are usually a bit more
> complex. For examples of production-quality pipelines that you can copy, see our
> tool-specific libraries:
> * [GitHub Actions](https://github.com/ploigos/ploigos-github-workflows/)
> * [GitLab](https://github.com/ploigos/ploigos-gitlab-library/)
> * [Jenkins](https://github.com/ploigos/ploigos-jenkins-library/)
> * [Tekton](https://github.com/ploigos/ploigos-charts/)

Jenkins will call the PSR command with two options:

- `-s <step>` is the name of the step that will be executed
- `-c psr.yaml` is the path to the PSR configuration file for the application

Create a Jenkinsfile in both source code repos that contains the same pipeline
definition:

```Jenkinsfile
pipeline {
   agent {
        kubernetes {
            cloud 'openshift'
            defaultContainer 'default'
            yamlFile 'kubernetes-pod.yaml'
        }
    }
    stages {
        stage('Generate Metadata') {
            steps {
                sh "psr -s generate-metadata -c psr.yaml"
            }
        }
        stage('Unit Test') {
            steps {
                sh "psr -s unit-test -c psr.yaml"
            }
        }
        stage('Package') {
            steps {
                sh "psr -s package -c psr.yaml"
            }
        }
        stage('Create Container Image') {
            steps {
                sh "psr -s create-container-image -c psr.yaml"
            }
        }
        stage('Push Container Image') {
            steps {
                sh "psr -s push-container-image -c psr.yaml"
            }
        }
    }
}
```

This Jenkinsfile will be used for both the Maven and NPM applications. PSR
provides each step and one or many implementers for that step. The PSR commands
remain the same between applications because the Java (Maven) and JavaScript
(NPM) applications reference different implementers in their psr.yaml files.

## Appendix A: Pipeline Flow for Maven App

```mermaid
sequenceDiagram
    participant wr as Workflow Runner
    participant psr as PSR
    participant tool as External Tool

    Note over wr,tool: Generate Metadata Step
    wr->>psr: `psr -s generate-metadata -c psr.yaml`
    psr->>tool: Gathers Git and Maven Metadata
    tool->>psr: Metadata
    psr->>wr: Artifacts Object

    Note over wr,tool: Unit Test Step
    wr->>psr: `psr -s unit-test -c psr.yaml`
    psr->>tool: Tests with JUnit
    tool->>psr: Test Results + Logs
    psr->>wr: Artifacts Object

    Note over wr,tool: Package Step
    wr->>psr: `psr -s package -c psr.yaml`
    psr->>tool: Builds with Maven
    tool->>psr: JAR File + Logs
    psr->>wr: Artifacts Object

    Note over wr,tool: Create Container Image Step
    wr->>psr: `psr -s create-container-image -c psr.yaml`
    psr->>tool: Creates Container Image with Buildah
    tool->>psr: Container Image + Logs
    psr->>wr: Artifacts Object

    Note over wr,tool: Push Container Image Step
    wr->>psr: `psr -s push-container-image -c psr.yaml`
    psr->>tool: Pushes Container Image with Skopeo
    tool->>psr: Container Image + Logs
    psr->>wr: Artifacts Object
```

## Appendix B: Pipeline Flow for NPM App

```mermaid
sequenceDiagram
    participant wr as Workflow Runner
    participant psr as PSR
    participant tool as External Tool

    Note over wr,tool: Generate Metadata Step
    wr->>psr: `psr -s generate-metadata -c psr.yaml`
    psr->>tool: Gathers Git and NPM Metadata
    tool->>psr: Metadata
    psr->>wr: Artifacts Object

    Note over wr,tool: Unit Test Step
    wr->>psr: `psr -s unit-test -c psr.yaml`
    psr->>tool: Tests with NpmXunitTest
    tool->>psr: Test Results + Logs
    psr->>wr: Artifacts Object

    Note over wr,tool: Package Step
    wr->>psr: `psr -s package -c psr.yaml`
    psr->>tool: Builds with NPM
    tool->>psr: Build Outputs + Logs
    psr->>wr: Artifacts Object

    Note over wr,tool: Create Container Image Step
    wr->>psr: `psr -s create-container-image -c psr.yaml`
    psr->>tool: Creates Container Image with Buildah
    tool->>psr: Container Image + Logs
    psr->>wr: Artifacts Object

    Note over wr,tool: Push Container Image Step
    wr->>psr: `psr -s push-container-image -c psr.yaml`
    psr->>tool: Pushes Container Image with Skopeo
    tool->>psr: Container Image + Logs
    psr->>wr: Artifacts Object
```
