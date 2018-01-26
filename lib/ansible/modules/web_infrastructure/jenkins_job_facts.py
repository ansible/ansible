#!/usr/bin/python
#
# Copyright: (c) Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: jenkins_job_facts
short_description: Get facts about Jenkins jobs
version_added: "2.5"
description:
  - "Query facts about which Jenkins jobs exist"
requirements:
  - "python-jenkins >= 0.4.12"
options:
  name:
    description:
      - Exact name of the Jenkins job to fetch facts about.
    required: false
  glob:
    description:
      - A shell glob of Jenkins job names to fetch facts about.
  password:
    description:
      - Password to authenticate with the Jenkins server.
    required: false
  token:
    description:
      - API token used to authenticate alternatively to C(password).
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

author:
  - "Chris St. Pierre (@stpierre)"
'''

EXAMPLES = '''
# Get all Jenkins jobs using basic auth
- jenkins_job_facts:
    user: admin
    password: hunter2
  register: my_jenkins_job_facts

# Get all Jenkins jobs using the token
- jenkins_job_facts:
    user: admin
    token: abcdefghijklmnop
  register: my_jenkins_job_facts

# Get facts about a single job using basic auth
- jenkins_job_facts:
    name: some-job-name
    user: admin
    password: hunter2
  register: my_jenkins_job_facts

# Get facts about a single job in a folder using basic auth
- jenkins_job_facts:
    name: some-folder-name/some-job-name
    user: admin
    password: hunter2
  register: my_jenkins_job_facts

# Get facts about jobs matching a shell glob using basic auth
- jenkins_job_facts:
    glob: some-job-*
    user: admin
    password: hunter2
  register: my_jenkins_job_facts
'''

RETURN = '''
---
jobs:
  description: All jobs found matching the specified criteria
  returned: success
  type: list
  sample: [{"name": "test-job", "fullname": "test-folder/test-job", "url": "http://localhost:8080/job/test-job/", "color": "blue"}, ...]
'''

import fnmatch
import traceback

try:
    import jenkins
    python_jenkins_installed = True
except ImportError:
    python_jenkins_installed = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def get_jenkins_connection(url, username, password=None, token=None):
    if username and (password or token):
        return jenkins.Jenkins(url, username, password or token)
    elif username:
        return jenkins.Jenkins(url, username)
    else:
        return jenkins.Jenkins(url)


def test_dependencies(module):
    if not python_jenkins_installed:
        module.fail_json(
            msg="python-jenkins required for this module. "
            "see http://python-jenkins.readthedocs.io/en/latest/install.html")


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=False),
            glob=dict(type='str', required=False),
            password=dict(required=False, no_log=True),
            token=dict(required=False, no_log=True),
            url=dict(required=False, default="http://localhost:8080"),
            user=dict(required=False)),
        mutually_exclusive=[
            ['password', 'token'],
            ['name', 'glob'],
        ],
        supports_check_mode=True)

    test_dependencies(module)

    try:
        jenkins_conn = get_jenkins_connection(
            module.params["url"],
            module.params.get("user"),
            password=module.params.get("password"),
            token=module.params.get("token"))
    except Exception as err:
        module.fail_json(
            msg='Unable to connect to Jenkins server, %s' % to_native(err),
            exception=traceback.format_exc())

    jobs = []
    if module.params.get("name"):
        try:
            job_info = jenkins_conn.get_job_info(module.params.get("name"))
            jobs.append({
                "name": job_info["name"],
                "fullname": job_info["fullName"],
                "url": job_info["url"],
                "color": job_info["color"]
            })
        except jenkins.NotFoundException:
            pass
    else:
        all_jobs = jenkins_conn.get_all_jobs()
        if module.params.get("glob"):
            jobs.extend([
                j for j in all_jobs
                if fnmatch.fnmatch(j["fullname"], module.params.get("glob"))
            ])
        else:
            jobs = all_jobs
        for job in jobs:
            if "_class" in job:
                del job["_class"]

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(changed=False, jobs=jobs)


def main():
    run_module()


if __name__ == '__main__':
    main()
