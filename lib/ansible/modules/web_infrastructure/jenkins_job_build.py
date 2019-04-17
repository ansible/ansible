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
module: jenkins_job_build
short_description: Trigger Jenkins jobs builds
description:
  - Trigger jobs using Jenkins REST API, optionally poll the API for the build completion and return result
requirements: []
version_added: "2.8"
author:
  - Tomas Mazak (@tomas-mazak)
  - Venkateswarlu Annangi (@venkatannangi)
options:
  name:
    description:
      - Name of the Jenkins job to build.
    required: true
  build_params:
    description:
      - Parameters to build a parametrized Jenkins job with.
    type: dict
  wait_for_building:
    description:
      - Whether to wait for the job to start building.
        The build number is only returned if this or I(wait_for_completion) is enabled.
    type: bool
    default: false
  wait_for_completion:
    description:
      - Whether to wait for the job to complete. Result is only checked for success if this is enabled.
    type: bool
    default: false
  timeout:
    description:
      - Number of seconds to wait for the job to start building, if I(wait_for_building) is set, and to complete,
        if I(wait_for_completion) is set
    type: int
    default: 600
  url:
    description:
      - URL where the Jenkins server is accessible.
        If not specified, JENKINS_URL environment variable is used
  user:
    description:
       - User to authenticate with the Jenkins server.
        If not specified, JENKINS_USERNAME environment variable is used
  password:
    description:
      - Password to authenticate with the Jenkins server.
        If not specified, JENKINS_PASSWORD environment variable is used
'''

EXAMPLES = '''
# Build a jenkins job
- jenkins_job_build:
    name: my_simple_job

# Build a jenkins job with parameters
- jenkins_job_build:
    name: my_parametrized_job
    build_params:
      foo: val1
      bar: val2

# Build a jenkins job and wait for it to start building to get build number and URL
- jenkins_job_build:
    name: my_simple_job
    wait_for_building: true
  register: build

- debug:
    msg: "Build number {{ build.build_number }}, URL: {{ build.build_url }}"

# Build a jenkins job and wait for completion, fail if not successful
- name: run tests using new module
  jenkins_job_build:
    name: my_simple_job
    wait_for_completion: true
  register: build
  failed_when: build.result|default('') != 'SUCCESS'
'''

RETURN = '''
---
queue_url:
  description:
    - URL to the Jenkins job queue item. Only returned if I(wait_for_building) and I(wait_for_completion) are false
  returned: success
  type: str
  sample: http://localhost:8080/queue/item/1337/
build_number:
  description:
    - Build number of the build triggered. Only returned if I(wait_for_building) or I(wait_for_completion) is true
  returned: success
  type: int
  sample: 42
build_url:
  description:
    - URL to the build triggered. Only returned if I(wait_for_building) or I(wait_for_completion) is true
  returned: success
  type: str
  sample: http://localhost:8080/job/my_simple_job/42/
result:
  description:
    - The build result. Only returned if I(wait_for_completion) is true
  type: str
  sample: SUCCESS
'''

import os
import requests
import time
from ast import literal_eval
from ansible.module_utils.basic import AnsibleModule


class JenkinsJobBuilder(object):
    POLL_INTERVAL = 5  # seconds

    class TimeoutError(Exception):
        pass

    def __init__(self, url, username, password, timeout=600):
        self.url = url
        self.auth = (username, password)
        self.timeout = timeout

    def _get_api_url(self, url):
        if url.startswith('http://') and self.url.startswith('https://'):
            url = 'https://' + url[len('http://'):]
        return url.rstrip('/') + '/api/python'

    def trigger_job(self, job_name, params):
        url = '{jenkins_url}/job/{job_name}/buildWithParameters'.format(jenkins_url=self.url, job_name=job_name)
        r = requests.post(url, auth=self.auth, params=params)
        r.raise_for_status()
        return r.headers['Location']

    def wait_for_build(self, queue_url):
        for _ in range(self.timeout // self.POLL_INTERVAL):
            r = requests.get(self._get_api_url(queue_url), auth=self.auth)
            r.raise_for_status()
            data = literal_eval(r.content)
            if 'executable' in data:
                return data['executable']['number'], data['executable']['url']
            time.sleep(self.POLL_INTERVAL)
        raise self.TimeoutError('Timed out waiting for the job to start building')

    def wait_for_completion(self, build_url):
        for _ in range(self.timeout // self.POLL_INTERVAL):
            r = requests.get(self._get_api_url(build_url), auth=self.auth, params=dict(depth=1, tree='building,result'))
            r.raise_for_status()
            data = literal_eval(r.content)
            if not data['building']:
                return data['result']
            time.sleep(self.POLL_INTERVAL)
        raise self.TimeoutError('Timed out waiting for the job to complete')

    def build_with_params(self, job_name, params={}, wait_for_building=False, wait_for_completion=False):
        queue_url = self.trigger_job(job_name, params)

        if not wait_for_building and not wait_for_completion:
            return {'queue_url': queue_url}

        build_number, build_url = self.wait_for_build(queue_url)

        if not wait_for_completion:
            return {'build_number': build_number, 'build_url': build_url}

        result = self.wait_for_completion(build_url)
        return {'build_number': build_number, 'build_url': build_url, 'result': result}


def main():
    module_args = dict(
        name=dict(required=True, type='str', aliases=['job']),
        build_params=dict(default={}, type='dict'),
        wait_for_building=dict(default=False, type='bool'),
        wait_for_completion=dict(default=False, type='bool'),
        timeout=dict(default=600, type='int'),
        url=dict(default=None, type='str'),
        user=dict(default=None, type='str'),
        password=dict(default=None, type='str', no_log=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    url = module.params.get('url') or os.getenv("JENKINS_URL")
    user = module.params.get('user') or os.getenv("JENKINS_USERNAME")
    password = module.params.get('password') or os.getenv("JENKINS_PASSWORD")
    job_name = module.params.get('name')
    build_params = module.params.get('build_params')
    wait_for_building = module.params.get('wait_for_building')
    wait_for_completion = module.params.get('wait_for_completion')
    timeout = module.params.get('timeout')

    if not url:
        module.fail_json(msg='Either the "url" parameter must be provided or JENKINS_URL environment variable present')
    if not user:
        module.fail_json(msg='Either the "user" parameter must be provided '
                             'or JENKINS_USERNAME environment variable present')
    if not password:
        module.fail_json(msg='Either the "password" parameter must be provided '
                             'or JENKINS_PASSWORD environment variable present')

    builder = JenkinsJobBuilder(url, user, password, timeout)
    try:
        res = builder.build_with_params(job_name, build_params, wait_for_building, wait_for_completion)
        action = 'completed with result {}'.format(res['result']) if wait_for_completion \
                 else 'started successfully' if wait_for_building \
                 else 'queued successfully'
        module.exit_json(changed=True, msg="The build was {}".format(action), **res)
    except JenkinsJobBuilder.TimeoutError as ex:
        module.fail_json(msg=str(ex))
    except requests.HTTPError as ex:
        module.fail_json(msg="Jenkins API call failed: {}".format(str(ex)))


if __name__ == '__main__':
    main()
