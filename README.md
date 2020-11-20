# Black Duck runner for Digital Asset

## Background

Blackduck scans work by running the synopsys-detect tool against the code in your repository after the build has been run, and it gathers a list of the third party components in use through a combination of the build tool's package management metadata and a recursion of libraries on the file system, matching their signature against Blackduck's knowledge base.

## Adding a scan in CI for your project

In order to run a Blackduck scan for your project in CI, you will need to add the command which invokes the Blackduck scan run to file which define's your CI process.

A synopsys-detect helper script (present in this repository) is provided to keep your project up to date with the latest Blackduck software, and to provide helper's to avoid repetition of boilerplate configuration settings, and provide a consistent project naming across Digital Asset's project.

### Enabling scan in CircleCI

To enable the scan, add the command below to your CircleCI config file (usually .circleci/config.xml) as below
  - run:
          name: Run Blackduck Detect
          command: |
            bash <(curl -s https://raw.githubusercontent.com/DACH-NY/security-blackduck/master/synopsys-detect) ci-build digitalasset_ex-healthcare-claims-processing master --logging.level.com.synopsys.integration=DEBUG  --detect.notices.report=true --detect.report.timeout=480

### Enabling scan in Azure


### Frequency of scan

It is possible to run a scan on every pull request, but this is often excessively time consuming or wasteful as most pull requests do not introduce new third party library versions.  If you want to run the scan on every pull request, simply add in the task as outlined above into your main build pipeline.

It is also possible to only run the scan on master pull requests, but the disadvantage then is that you will not get early warning on any issues until changes are merged to master

The compromise that seems to work for most projects is to automatically have a daily scheduled job which runs the scan (so your scan results are reasonably up to date), causing that daily scan to fail if there is a policy failure, and email and/or slack notification of the daily scan failure triggers investigation and remediation of the problematic dependency by the project owner.

Additionally, you can create a rule that allows the blackduck scan to be run on any branch named blackduck-* so you are able to test and verify any changes you make to the scan job on a branch before being merged to master

### Enabling daily scheduled scan

In order to schedule as a daily run (rather than on every pull request), you can setup a scheduled daily job similar tot he below

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


### Generating NOTICES file

### Failing build on policy failure

### Scanning Docker Images

### Reference on all scan properties
A full list of all properties of Detect and input and output codes can be found at 

Detect https://blackducksoftware.github.io/synopsys-detect/6.0.0/ 
Blackduck Detect Wiki https://synopsys.atlassian.net/wiki/spaces/INTDOCS/pages/62423113/Synopsys+Detect

## Getting Access to Blackduck Hub


## Running Locally
