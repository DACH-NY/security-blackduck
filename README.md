# Black Duck runner for Digital Asset

## Background

Blackduck scans work by running the synopsys-detect tool against the code in your repository after the build has been run, and it gathers a list of the third party components in use through a combination of the build tool's package management metadata and a recursion of libraries on the file system, matching their signature against Blackduck's knowledge base.

## Getting Access to Run a Blackduck Scan

Blackduck is available to be used by all internal DA users, but you need to login to the Blackduck site to setup your SSO account, create your personal token, and then request to be authorized to the relevant projects by the Security team

1. Create a personal Blackduck token by authenticating to the Blackduck site with your DA Google account
https://digitalasset.blackducksoftware.com/api/current-user/tokens

2. Click Create New Token and give yourself read and write access, giving a memorable name (<username>-<machine> or similar)
Copy the contents of this token and define in a local environment variable called BLACKDUCK_HUBDETECT_TOKEN
```export BLACKDUCK_HUB_DETECT_TOKEN=<token_you_have_just_created>```

3. Once you have created the token, send a mail to security@digitalasset.com to request access to the relevant GitHub projects you are working on with Blackduck.


## Running Locally
Once you are setup with access, you will be able to run a scan of your project locally and see the results in the Blackduck Hub @ https://digitalasset.blackducksoftware.com

### Basic Scan

1. First run the full build of your project using your build tool of choice (e.g. SBT, Maven, etc)

2. The most basic scan
```
bash <(curl -s https://raw.githubusercontent.com/DACH-NY/security-blackduck/master/synopsys-detect) \
ci-build <github_org_of_project>_<github_repo_of_project> <branch_name>
```

where
            `<github_org_of_project>` is typically either DACH-NY or digital-asset
            `<github_repo_or_project>` will be your actual repo name in one of these orgs
            `<branch_name>` is the name of the branch you are working on to be scanned


## Adding a scan in CI for your project

In order to run a Blackduck scan for your project in CI, you will need to add the command which invokes the Blackduck scan run to the file which defines your CI process.

A synopsys-detect helper script (present in this repository) is provided to keep your project up to date with the latest Blackduck software, and to provide helpers to avoid repetition of boilerplate configuration settings, and provide a consistent project naming across Digital Asset's project.

### Enabling scan in CircleCI

To enable the scan, add the command below to your CircleCI config file (usually .circleci/config.xml) as below
```
  - run:
       name: Run Blackduck Detect
       command: |
          bash <(curl -s https://raw.githubusercontent.com/DACH-NY/security-blackduck/master/synopsys-detect) \
          ci-build ${CIRCLE_PROJECT_USERNAME}_${CIRCLE_PROJECT_REPONAME} ${CIRCLE_BRANCH} \
          --logging.level.com.synopsys.integration=DEBUG  \
          --detect.notices.report=true \
          --detect.timeout=480
```
### Enabling scan in Azure

This is a more complex multi-part scan taken from the open source DAML repo, which is a polyglot repo inclusive of multiple technologies.  To scan this repo, the first pass scans for Haskell third party libraries, and the second pass scans for Bazel JVM libraries and NPM and Python libraries reported by the standard package management mechanisms.

```
  - job: blackduck_scan
    timeoutInMinutes: 1200
    steps:
      - checkout: self
      - bash: |
          # Perform steps for your build process and any environmental setup here
        displayName: 'Build'
      - bash: |
          bash <(curl -s https://raw.githubusercontent.com/DACH-NY/security-blackduck/master/synopsys-detect) \
          ci-build <github_org_of_project>_<github_repo_of_project> $(System.PullRequest.SourceBranch) \
          --logging.level.com.synopsys.integration=DEBUG \
          --detect.tools=BAZEL \
          --detect.bazel.target=//... \
          --detect.bazel.dependency.type=haskell_cabal_library \
          --detect.notices.report=true \
          --detect.timeout=1500
        displayName: 'Blackduck Haskell Scan'
        env:
          BLACKDUCK_HUBDETECT_TOKEN: $(BLACKDUCK_HUBDETECT_TOKEN)
      - bash: |
          set -euo pipefail
          eval "$(./dev-env/bin/dade-assist)"
          bash <(curl -s https://raw.githubusercontent.com/DACH-NY/security-blackduck/master/synopsys-detect) \
          ci-build digital-asset_daml master \
          --logging.level.com.synopsys.integration=DEBUG \
          --detect.npm.include.dev.dependencies=false \
          --detect.excluded.detector.types=NUGET \
          --detect.excluded.detector.types=GO_MOD \
          --detect.yarn.prod.only=true \
          --detect.python.python3=true \
          --detect.tools=DETECTOR,BAZEL,DOCKER \
          --detect.bazel.target=//... \
          --detect.bazel.dependency.type=maven_install \
          --detect.detector.search.exclusion.paths=language-support/ts/codegen/tests/ts,language-support/ts,language-support/scala/examples/iou-no-codegen,language-support/scala/examples/quickstart-scala,docs/source/app-dev/bindings-java/code-snippets,docs/source/app-dev/bindings-java/quickstart/template-root,language-support/scala/examples/quickstart-scala,language-support/scala/examples/iou-no-codegen \
          --detect.cleanup=false \
          --detect.policy.check.fail.on.severities=MAJOR,CRITICAL,BLOCKER \
          --detect.notices.report=true \
          --detect.cleanup.bdio.files=true \
          --detect.timeout=4500
        displayName: 'Blackduck Scan'
        env:
          BLACKDUCK_HUBDETECT_TOKEN: $(BLACKDUCK_HUBDETECT_TOKEN)
```

### Frequency of scan

It is possible to run a scan on every pull request, but this is often excessively time consuming or wasteful as most pull requests do not introduce new third party library versions.  If you want to run the scan on every pull request, simply add in the task as outlined above into your main build pipeline.

It is also possible to only run the scan on master pull requests, but the disadvantage then is that you will not get early warning on any issues until changes are merged to master

The compromise that seems to work for most projects is to automatically have a daily scheduled job which runs the scan (so your scan results are reasonably up to date), causing that daily scan to fail if there is a policy failure, and email and/or slack notification of the daily scan failure triggers investigation and remediation of the problematic dependency by the project owner.

Additionally, you can create a rule that allows the blackduck scan to be run on any branch named blackduck-* so you are able to test and verify any changes you make to the scan job on a branch before being merged to master

### Enabling daily scheduled scan

In order to schedule as a daily run (rather than on every pull request), you can setup a scheduled daily job similar tot he below
```
jobs:
           
  blackduck-build:
    working_directory: ~/builddir
    docker:
      - image: circleci/openjdk:8-jdk
    environment:
      SBT_VERSION: 1.3.10
    resource_class: xlarge
    steps:
      - setup-build
      - run-build
      - blackduck-scan

workflows:
  version: 2
  workflow:
    jobs:
      - build

  blackduck:
    triggers:
      - schedule:
          cron: "30 8 * * 1-5"
          filters:
             branches:
                only:
                  - master
    jobs:
      - blackduck-build:
          context: blackduck
```

### Generating NOTICES file

Whether the NOTICES file is generated or not as part of the scan is determined by the `--detect.notices.report` property, which is set to false by default (do not generate the file.

To generate the file, set this property to true, and the scan will wait for all Blackduck Hub server-side processing to conclude, and the full NOTICES file report to be returned before exiting the scan job.  The NOTICES file will be output to the present working directory as `*_Black_Duck_Notices_Report.txt`.  In most projects, we rename this output file to NOTICES and keep it in the root of the repo.

To automatically update this notices file when it changes, an approach similar to the below can be taken, assuming your CI service account has the ability to commit code back to a working non-master branch on the repo

```
#convert windows line endings to unix, strip version line, rename notices file
tr -d '\015' <*_Black_Duck_Notices_Report.txt | grep -v ${CIRCLE_PROJECT_USERNAME}_${CIRCLE_PROJECT_REPONAME} >NOTICES
git config user.email "no-reply@digitalasset.com"
git config user.name "CircleCI Release Build"

if [[ $(git add --dry-run NOTICES) ]]; then
            echo "There is a change to notices file, committing it back to source"
            git add NOTICES
            git commit -m'[skip ci] Update NOTICES file'
            git push --set-upstream origin ${CIRCLE_BRANCH}
else
            echo "No change to NOTICES file"
fi
```

### Capturing output

Please include store_artifacts to capture output of the job for troubleshooting and support purposes, in case things are not working as planned

```
- store_artifacts:
    name: Store the Blackduck run artifacts
    path: /home/circleci/blackduck/runs
```

### Failing build on policy failure

The addition of the following line will cause the scan build to fail if there are policy violations as a result of the scan

```
--detect.policy.check.fail.on.severities=MAJOR,CRITICAL,BLOCKER \
```

### Scanning Docker Images

Docker images will not be detected and scanned by default if you have Dockerfiles in your repository, you need to explicitly tell Blackduck what docker images to look for to scan

An example for running a scan against a publicly available container on DockerHub is
```
bash <(curl -s https://raw.githubusercontent.com/DACH-NY/security-blackduck/master/synopsys-detect) ci-build digital-asset_daml-on-fabric hyperledger/fabric-ccenv:2.1.0 --detect.docker.image=hyperledger/fabric-ccenv:2.1.0 --logging.level.com.synopsys.integration=DEBUG --detect.tools=DOCKER --cleanup.inspector.container=true
```

The same approach can be taken to scan your repository's own images available locally, but you need to run this scan only after you have run `docker build`

You can also target your scan to only focus on layers below a particular layer ID to not detect vulnerabilities on base layers that come from an image on which you depend, but rather to focus on vulnerabilities of layers you have added on top of the base layers.

Full details on Blackduck's Docker Scanning capabilities can be found @ 

https://blackducksoftware.github.io/blackduck-docker-inspector/latest/advanced/

### Example with exclusions and targeted scans

## Bazel Haskell Scan

Notices the defintion of BAZEL as detect.tools and the specification of `haskell_cabal_library` as the detect.bazel.dependency to look specifically for Haskell third party libraries

```
bash <(curl -s https://raw.githubusercontent.com/DACH-NY/security-blackduck/master/synopsys-detect) \
ci-build <github_org_of_project>_<github_repo_of_project> <branch_name> \
--logging.level.com.synopsys.integration=DEBUG \
--detect.tools=BAZEL \
--detect.bazel.target=//... \
--detect.bazel.dependency.type=haskell_cabal_library \
--detect.notices.report=true \
--detect.timeout=1500
```

## Bazel JVM Scan

Notices the defintion of BAZEL as detect.tools and the specification of `maven_install` as the detect.bazel.dependency to look specifically for JVM third party libraries -- this will detect both Java and Scala libraries, in fact any third party library that is packaged as a maven-compliant dependency.

```
bash <(curl -s https://raw.githubusercontent.com/DACH-NY/security-blackduck/master/synopsys-detect) \
ci-build <github_org_of_project>_<github_repo_of_project> <branch_name> \
--logging.level.com.synopsys.integration=DEBUG \
--detect.tools=BAZEL \
--detect.bazel.target=//... \
--detect.bazel.dependency.type=maven_install \
--detect.notices.report=true \
--detect.timeout=1500
```

### Reference on all scan properties
A full list of all properties of Detect and input and output codes can be found at 

Detect https://blackducksoftware.github.io/synopsys-detect/6.0.0/ 
Blackduck Detect Wiki https://synopsys.atlassian.net/wiki/spaces/INTDOCS/pages/62423113/Synopsys+Detect

## Getting Access to Blackduck Hub

Once you have created the token, send a mail to security@digitalasset.com to request access to the relevant GitHub projects you are working on with Blackduck.
