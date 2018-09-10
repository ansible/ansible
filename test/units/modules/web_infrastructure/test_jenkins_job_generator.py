import pytest
import os
import sys
import xml.etree.ElementTree as ET

from mock import patch

from nose.plugins.skip import SkipTest
if sys.version_info < (2, 7):
    raise SkipTest("F5 Ansible modules require Python >= 2.7")

from ansible.modules.web_infrastructure.jenkins_job_generator import get_job_builder, ActionRunner
import jenkins


class TestJobBuilder(object):
    scm_yaml = """
- scm:
      name: main-scm
      scm:
        - git:
           url: ssh://git@stash.net/build_authomation.git
           clean: true
           branches:
            - '*/master'
           credentials-id: cred-id
    """
    test_job_yaml = """
- job:
    name: 'test'
    project-type: pipeline
    pipeline-scm:
      scm:
        - main-scm
      script-path: jenkins/build_and_test.gdsl
    parameters:
      - string:
          name: EASYCONFIG
          default: f/foss/foss-2017a.eb
          description: Path to easyconfig file
      - string:
          name: BRANCH
          default: master
          description:
      - string:
          name: TEST_CONTAINER_SIZE
          default: "4000"
          description:
      - choice:
          name: TEST_CONTAINER_TYPE
          choices:
            - minimal
            - GUI-compatible
          description: "On which project to run?"
    """
    build_job_yaml = """
- job:
    name: 'build'
    project-type: pipeline
    pipeline-scm:
      scm:
        - main-scm
      script-path: jenkins/build.gdsl
    sandbox: true
    parameters:
      - string:
          name: EASYCONFIG
          default: f/foss/foss-2017a.eb
          description: Path to easyconfig file
      - string:
          name: BRANCH
          default: master
          description:
      - bool:
          name: UPDATE_CONFLUENCE
          default: true
          description:
      - bool:
          name: KEEP_CONTAINER
          default: false
          description:
    """

    test_job_xml = """<?xml version='1.0' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.14.1">
    <actions/>
    <description>&lt;!-- Managed by Jenkins Job Builder --&gt;</description>
    <keepDependencies>false</keepDependencies>
    <properties>
        <hudson.model.ParametersDefinitionProperty>
            <parameterDefinitions>
                <hudson.model.StringParameterDefinition>
                    <name>EASYCONFIG</name>
                    <description>Path to easyconfig file</description>
                    <defaultValue>f/foss/foss-2017a.eb</defaultValue>
                </hudson.model.StringParameterDefinition>
                <hudson.model.StringParameterDefinition>
                    <name>BRANCH</name>
                    <description></description>
                    <defaultValue>master</defaultValue>
                </hudson.model.StringParameterDefinition>
                <hudson.model.StringParameterDefinition>
                    <name>TEST_CONTAINER_SIZE</name>
                    <description></description>
                    <defaultValue>4000</defaultValue>
                </hudson.model.StringParameterDefinition>
                <hudson.model.ChoiceParameterDefinition>
                    <name>TEST_CONTAINER_TYPE</name>
                    <description>On which project to run?</description>
                    <choices class="java.util.Arrays$ArrayList">
                        <a class="string-array">
                            <string>minimal</string>
                            <string>GUI-compatible</string>
                        </a>
                    </choices>
                </hudson.model.ChoiceParameterDefinition>
            </parameterDefinitions>
        </hudson.model.ParametersDefinitionProperty>
        <org.jenkinsci.plugins.workflow.job.properties.DisableConcurrentBuildsJobProperty/>
    </properties>
    <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition" plugin="workflow-cps@2.43">
        <scm class="hudson.plugins.git.GitSCM" plugin="git@3.5.1">
            <configVersion>2</configVersion>
            <userRemoteConfigs>
                <hudson.plugins.git.UserRemoteConfig>
                    <name>origin</name>
                    <refspec>+refs/heads/*:refs/remotes/origin/*</refspec>
                    <url>ssh://git@stash.net/build_authomation.git</url>
                    <credentialsId>cred-id</credentialsId>
                </hudson.plugins.git.UserRemoteConfig>
            </userRemoteConfigs>
            <branches>
                <hudson.plugins.git.BranchSpec>
                    <name>*/master</name>
                </hudson.plugins.git.BranchSpec>
            </branches>
            <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
            <gitTool>Default</gitTool>
            <submoduleCfg class="list"/>
            <extensions>
                <hudson.plugins.git.extensions.impl.CleanCheckout/>
                <hudson.plugins.git.extensions.impl.WipeWorkspace/>
            </extensions>
        </scm>
        <scriptPath>jenkins/build_and_test.gdsl</scriptPath>
        <lightweight>false</lightweight>
    </definition>
    <disabled>false</disabled>
</flow-definition>
    """
    build_job_xml = """<?xml version="1.0" encoding="utf-8"?>
<flow-definition plugin="workflow-job">
    <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition" plugin="workflow-cps">
        <sandbox>true</sandbox>
        <scm class="hudson.plugins.git.GitSCM">
            <configVersion>2</configVersion>
            <userRemoteConfigs>
                <hudson.plugins.git.UserRemoteConfig>
                    <name>origin</name>
                    <refspec>+refs/heads/*:refs/remotes/origin/*</refspec>
                    <url>ssh://git@stash.net/build_authomation.git</url>
                    <credentialsId>cred-id</credentialsId>
                </hudson.plugins.git.UserRemoteConfig>
            </userRemoteConfigs>
            <branches>
                <hudson.plugins.git.BranchSpec>
                    <name>*/master</name>
                </hudson.plugins.git.BranchSpec>
            </branches>
            <disableSubmodules>false</disableSubmodules>
            <recursiveSubmodules>false</recursiveSubmodules>
            <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
            <remotePoll>false</remotePoll>
            <gitTool>Default</gitTool>
            <submoduleCfg class="list"/>
            <reference/>
            <gitConfigName/>
            <gitConfigEmail/>
            <extensions>
                <hudson.plugins.git.extensions.impl.CleanCheckout/>
                <hudson.plugins.git.extensions.impl.WipeWorkspace/>
            </extensions>
        </scm>
        <scriptPath>jenkins/build.gdsl</scriptPath>
    </definition>
    <actions/>
    <description>&lt;!-- Managed by Jenkins Job Builder --&gt;</description>
    <keepDependencies>false</keepDependencies>
    <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
    <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
    <concurrentBuild>false</concurrentBuild>
    <canRoam>true</canRoam>
    <properties>
        <hudson.model.ParametersDefinitionProperty>
            <parameterDefinitions>
                <hudson.model.StringParameterDefinition>
                    <name>EASYCONFIG</name>
                    <description>Path to easyconfig file</description>
                    <defaultValue>f/foss/foss-2017a.eb</defaultValue>
                </hudson.model.StringParameterDefinition>
                <hudson.model.StringParameterDefinition>
                    <name>BRANCH</name>
                    <description/>
                    <defaultValue>master</defaultValue>
                </hudson.model.StringParameterDefinition>
                <hudson.model.BooleanParameterDefinition>
                    <name>UPDATE_CONFLUENCE</name>
                    <description/>
                    <defaultValue>true</defaultValue>
                </hudson.model.BooleanParameterDefinition>
                <hudson.model.BooleanParameterDefinition>
                    <name>KEEP_CONTAINER</name>
                    <description/>
                    <defaultValue>false</defaultValue>
                </hudson.model.BooleanParameterDefinition>
            </parameterDefinitions>
        </hudson.model.ParametersDefinitionProperty>
    </properties>
    <scm class="hudson.scm.NullSCM"/>
    <publishers/>
    <buildWrappers/>
</flow-definition>
        """
    test_job_xml2 = test_job_xml
    empty_xml = """<?xml version="1.0" encoding="UTF-8"?><com.cloudbees.hudson.plugins.folder.Folder
plugin="cloudbees-folder"> <actions/>  <icon
class="com.cloudbees.hudson.plugins.folder.icons.StockFolderIcon"/> <views/>  <viewsTabBar
class="hudson.views.DefaultViewsTabBar"/>  <primaryView>All</primaryView>  <healthMetrics/>  <actions/>
<description>&lt;!-- Managed by Jenkins Job Builder --&gt;</description>
<keepDependencies>false</keepDependencies>
<blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
<blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
<concurrentBuild>false</concurrentBuild>  <canRoam>true</canRoam>  <properties/>  <scm
class="hudson.scm.NullSCM"/>  <publishers/>  <buildWrappers/></com.cloudbees.hudson.plugins.folder.Folder>
    """

    def setup(self):
        def stub(self):
            pass

        job_builder = get_job_builder()
        old_init = job_builder.__init__
        job_builder.__init__ = stub
        self.job_builder = job_builder()
        job_builder.__init__ = old_init
        self.job_files_path = 'jobs'

    def test_xml_cchange_true(self):
        xml1 = ET.fromstring(self.test_job_xml)
        xml2 = ET.fromstring(self.test_job_xml2)
        print(self.job_builder.xml_compare(xml1, xml2))
        assert self.job_builder.xml_compare(xml1, xml2)

    def test_xml_cchange_false(self):
        xml1 = ET.fromstring(self.test_job_xml)
        xml2 = ET.fromstring(self.build_job_xml)

        assert not self.job_builder.xml_compare(xml1, xml2)

    def test_get_action_method(self):
        result = dict(
            changed=False,
            status=''
        )
        params = {
            'jenkins_server': 'http://127.0.0.1',
            'user': 'jenkins',
            'password': 'jenkins',
            'state': 'present'
        }
        action = ActionRunner(result=result, **params)

        assert action.__getattribute__(params['state']) is not None

    # Mock tests

    @patch('jenkins.Jenkins.get_job_config')
    def test_jobs_not_update(self, mock, tmpdir):
        dir = tmpdir.mkdir(self.job_files_path)
        result = dict(
            changed=False,
            status=''
        )
        params = {
            'jenkins_server': 'http://127.0.0.1:8080',
            'user': '',
            'password': '',
            'jobs': ['build'],
            'path': str(dir.realpath()),
            'file': '',
            'workers': '1',
            'delete_old': False,
            'state': 'present'
        }
        f = dir.join("job.yml")
        f.write('\n'.join([self.scm_yaml, self.build_job_yaml, self.test_job_yaml]))

        mock.return_value = self.build_job_xml

        action = ActionRunner(result=result, **params)

        result = action.__getattribute__(params['state'])(**params)

        assert not result['changed']

    @patch('jenkins.Jenkins.get_job_config')
    @patch('jenkins_jobs.builder.JenkinsManager.update_job')
    def test_jobs_update(self, update_job_mock, get_job_config_mock, tmpdir):
        dir = tmpdir.mkdir(self.job_files_path)
        result = dict(
            changed=False,
            status=''
        )
        params = {
            'jenkins_server': 'http://127.0.0.1:8080',
            'user': '',
            'password': '',
            'jobs': ['test', 'build'],
            'path': str(dir.realpath()),
            'file': '',
            'workers': '1',
            'delete_old': False,
            'state': 'present'
        }
        f = dir.join("job.yaml")
        f.write('\n'.join([self.scm_yaml, self.build_job_yaml]))

        get_job_config_mock.return_value = self.test_job_xml
        update_job_mock.return_value = None

        action = ActionRunner(result=result, **params)

        result = action.__getattribute__(params['state'])(**params)

        assert result['changed']

    @patch('jenkins.Jenkins.get_job_config')
    @patch('jenkins_jobs.builder.JenkinsManager.update_job')
    def test_jobs_create(self, update_job_mock, get_job_config_mock, tmpdir):
        dir = tmpdir.mkdir(self.job_files_path)
        result = dict(
            changed=False,
            status=''
        )
        params = {
            'jenkins_server': 'http://127.0.0.1:8080',
            'user': '',
            'password': '',
            'jobs': ['test', 'build'],
            'path': str(dir.realpath()),
            'file': '',
            'workers': '1',
            'delete_old': False,
            'state': 'present'
        }
        f = dir.join("job.yml")
        f.write('\n'.join([self.scm_yaml, self.build_job_yaml, self.test_job_yaml]))

        get_job_config_mock.return_value = self.empty_xml
        update_job_mock.return_value = None

        action = ActionRunner(result=result, **params)

        result = action.__getattribute__(params['state'])(**params)

        assert result['changed']
