#!/usr/bin/python
#
# Copyright: (c) Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: jenkins_build
short_description: Build jenkins jobs
version_added: "2.8"
description:
  - "Build Jenkins jobs by using Jenkins REST API."
requirements:
  - "python-jenkins >= 1.4.0"
options:
  name:
    description:
      - Name of the Jenkins job.
    required: true
  params:
    description:
      - Dictionary with job parameters.
    required: false
  password:
    description:
      - Password to authenticate with the Jenkins server.
    required: false
  token:
    description:
      - API token used to authenticate alternatively to password.
    required: false
  url:
    description:
      - Url where the Jenkins server is accessible.
    required: false
    default: http://localhost:8080
  user:
    description:
       - User to authenticate with the Jenkins server.
    required: false
  wait_build:
    description:
      - Wait until build is finished
    type: bool
    required: false
    default: 'yes'
  wait_build_timeout:
    description:
      - Wait until build is finished timeout, sec
    required: false
    default: 600
  build_token:
    description:
      - Token for building job
    required: false
  console_output:
    description:
      - Include build console output in result
    type: bool
    required: false
    default: 'no'
  timeout:
    description:
      - The request timeout in seconds
    required: false
    default: 10
  fail:
    description:
      - Fail job if result != 'SUCCESS'
    required: false
    default: false
author: "Vladislav Gorbunov (@vadikso), Sergio Millan Rodriguez (@sermilrod)"
notes:
    - Since the build can do anything this does not report on changes.
      Knowing the build is being run it's important to set changed_when
      for the build_info.console_output to be clear on any alterations made.
'''

EXAMPLES = '''
# Build a parameterized job using basic authentication
- jenkins_build:
    params:
        'param1': 'test value 1'
        'param2': 'test value 2'
    name: test
    password: admin
    url: http://localhost:8080
    user: admin

# Build a parameterized job using the token
- jenkins_build:
    params:
        'param1': 'test value 1'
        'param2': 'test value 2'
    name: test
    token: asdfasfasfasdfasdfadfasfasdfasdfc
    url: http://localhost:8080
    user: admin

# Build a jenkins job using basic authentication
- jenkins_build:
    name: test
    password: admin
    url: http://localhost:8080
    user: admin

# Build a jenkins job using basic authentication, don't wait job end
- jenkins_build:
    name: test
    password: admin
    url: http://localhost:8080
    user: admin
    wait_build: false

# Build a jenkins job anonymously with job token
- jenkins_build:
    name: test
    url: http://localhost:8080
    build_token: token_eDahX3ve
'''

RETURN = '''
---
build_info:
  description: Jenkins job build info.
  returned: success
  type: dict
  sample: >
    {u'building': False, u'queueId': 3, u'displayName': u'#2', u'description': None, u'changeSets': [],
    u'artifacts': [], u'timestamp': 1520431274718,
    u'previousBuild': {u'url': u'http://localhost:8080/job/test/1/', u'number': 1},
    u'number': 2, u'id': u'2', u'keepLog': False, u'url': u'http://localhost:8080/job/test/2/',
    u'result': u'SUCCESS', u'executor': None, u'duration': 172,
    u'_class': u'org.jenkinsci.plugins.workflow.job.WorkflowRun', u'nextBuild': None,
    u'fullDisplayName': u'test #2', u'estimatedDuration': 905}
'''

import traceback
import time
import uuid
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

try:
    import jenkins
    python_jenkins_installed = True
except ImportError:
    python_jenkins_installed = False


class JenkinsBuild:

    def __init__(self, module):
        self.module = module

        self.params = module.params.get('params')
        self.name = module.params.get('name')
        self.password = module.params.get('password')
        self.token = module.params.get('token')
        self.user = module.params.get('user')
        self.jenkins_url = module.params.get('url')
        self.wait_build = module.params.get('wait_build')
        self.wait_build_timeout = module.params.get('wait_build_timeout')
        self.build_token = module.params.get('build_token')
        self.build_number = 1
        self.timeout = module.params.get('timeout')
        self.console_output = module.params.get('console_output')
        self.fail = module.params.get('fail')

        self.server = self.get_jenkins_connection()

        self.result = {
            'build_info': {}
        }

    def is_fail(self):
        return self.fail

    def get_jenkins_connection(self):
        try:
            if (self.user and self.password):
                return jenkins.Jenkins(self.jenkins_url, self.user, self.password, self.timeout)
            elif (self.user and self.token):
                return jenkins.Jenkins(self.jenkins_url, self.user, self.token, self.timeout)
            elif (self.user and not (self.password or self.token)):
                return jenkins.Jenkins(self.jenkins_url, self.user, timeout=self.timeout)
            else:
                return jenkins.Jenkins(self.jenkins_url, timeout=self.timeout)
        except Exception as e:
            self.module.fail_json(msg='Unable to connect to Jenkins server, %s' % to_native(e),
                                  exception=traceback.format_exc())

    def job_exists(self):
        try:
            return bool(self.server.job_exists(self.name))
        except Exception as e:
            self.module.fail_json(msg='Unable to validate if job exists, %s for %s' % (to_native(e),
                                  self.jenkins_url), exception=traceback.format_exc())

    def wait_job_build(self):
        for _ in range(1, self.wait_build_timeout):
            if self.server.get_build_info(self.name, self.build_number)['building']:
                time.sleep(1)
            else:
                return
        self.module.fail_json(msg='Job build complete timeout exceed, %s for %s' % (self.name,
                              self.jenkins_url),
                              exception=traceback.format_exc())

    def build_job(self):
        result = self.result
        if not self.module.check_mode and self.job_exists():
            try:
                try:
                    self.build_number = self.server.get_job_info(self.name)['nextBuildNumber']
                except Exception as e:
                    self.module.fail_json(msg='Fail to get nextBuildNumber: %s' % str(e))
                queue_id = self.server.build_job(self.name, self.params, self.build_token)
                for _ in range(1, self.wait_build_timeout):
                    queue_item = self.server.get_queue_item(queue_id)
                    if (queue_item is not None) \
                       and ('executable' in queue_item) \
                       and (queue_item['executable'] is not None) \
                       and ('number' in queue_item['executable']):
                        self.build_number = queue_item['executable']['number']
                        break
                    time.sleep(1)
            except Exception as e:
                if str(e) == 'Error in request. Possibly authentication failed [500]: Server Error':
                    self.module.fail_json(msg="Error in request. Possibly call job that can't handle "
                                              "parameters. Server Error 500.")
                elif str(e) == 'HTTP Error 400: Nothing is submitted':
                    # pass random parameter if it not defined in params field
                    # Job is build with default parameters
                    self.params = {uuid.uuid4(): uuid.uuid4()}
                    self.build_job()
                else:
                    self.module.fail_json(msg='Runtime error in module jenkins_build: %s' % traceback.format_exc())
            if self.wait_build:
                self.wait_job_build()
            result['build_info'] = self.server.get_build_info(self.name, self.build_number)
            del result['build_info']['actions']
            if self.console_output:
                result['build_info']['console_output'] = self.server.get_build_console_output(
                    self.name, number=self.build_number)
        return result


def test_dependencies(module):
    if not python_jenkins_installed:
        module.fail_json(msg="python-jenkins >= 1.4.0 required for this module. "
                         "see http://python-jenkins.readthedocs.io/en/latest/install.html")


def main():
    module = AnsibleModule(
        argument_spec=dict(
            params=dict(required=False, default=None, type='dict'),
            name=dict(required=True),
            password=dict(required=False, no_log=True),
            token=dict(required=False, no_log=True),
            url=dict(required=False, default="http://localhost:8080"),
            user=dict(required=False),
            wait_build=dict(required=False, default=True, type='bool'),
            wait_build_timeout=dict(required=False, default=600, type='int'),
            build_token=dict(required=False, default=None, no_log=True),
            timeout=dict(required=False, type="int", default=10),
            console_output=dict(required=False, default=False, type='bool'),
            fail=dict(required=False, default=False, type='bool')
        ),
        mutually_exclusive=[
            ['password', 'token'],
        ],
        supports_check_mode=True,
    )

    test_dependencies(module)
    jenkins_build = JenkinsBuild(module)

    result = jenkins_build.build_job()
    if jenkins_build.is_fail() and result['build_info']['result'] != 'SUCCESS':
        result['msg'] = "Jenkins job build failed"
        module.fail_json(**result)
    else:
        module.exit_json(**result)


if __name__ == '__main__':
    main()
