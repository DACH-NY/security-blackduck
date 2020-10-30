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

### Frequency of scan

It is possible to run a scan on every pull request

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

### Configuring to run in Azure

### Generating NOTICES file

### Failing build on policy failure

## Running Locally
