#!/usr/bin/python
#
# Copyright: (c) Ansible Project
#
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
module: jenkins_build_artifacts
short_description: Get artifact urls from Jenkins
version_added: "2.7"
description:
  - This module can be used to obtain download URLs for build artifacts stored in Jenkins
requirements:
  - "python-jenkins >= 0.4.12"
options:
  job_name:
    description:
      - Exact name of the Jenkins build in which artifacts should be discovered
  build_number:
    description:
      - Build number for which artifacts should be returned
  glob:
    description:
      - A shell glob to which returned artifacts must match.
  password:
    description:
      - Password to authenticate with the Jenkins server.
      - This is a required parameter, if C(token) is not provided.
  token:
    description:
      - API token used to authenticate with the Jenkins server.
      - This is a required parameter, if C(password) is not provided.
  url:
    description:
      - URL where the Jenkins server is accessible.
    default: http://localhost:8080
  user:
    description:
       - User to authenticate with the Jenkins server.
  validate_certs:
    description:
       - If set to C(False), the SSL certificates will not be validated.
       - This should only set to C(False) used on personally controlled sites using self-signed certificates.
    default: true
    type: bool
    version_added: "2.6"
author:
  - "Charles Crossan (@crossan007)"
'''

EXAMPLES = '''
# Get all Jenkins build artifacts from a known job/build number
- jenkins_job_facts:
    user: admin
    password: hunter2
    job_name: "{{JenkinsFullJobName}}"
    build_number: "{{build}}"
    glob: "*XML*"
  register: my_jenkins_job_facts

# Get artifacts matching a glob pattern from a known job/build number 
- jenkins_job_facts:
    user: admin
    password: hunter2
    job_name: "master"
    build_number: "1"
    glob: "*XML*"
  register: my_jenkins_job_facts
'''

RETURN = '''
---
artifacts:
  description: All artifacts found for the selected job / glob criteria
  returned: success
  type: list
  sample:
    [
        {
            "displayPath": "master-18675309.zip", 
            "downloadURL": "https://jenkins.mydomain.com/job/master/1/artifact/master-18675309.zip.zip", 
            "fileName": "master-18675309.zip.zip", 
            "relativePath": "master-18675309.zip.zip"
        }
    ], 
'''

import ssl
import fnmatch
import traceback
import urllib

try:
    import jenkins
    HAS_JENKINS = True
except ImportError:
    HAS_JENKINS = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def get_jenkins_connection(module):
    url = module.params["url"]
    username = module.params.get("user")
    password = module.params.get("password")
    token = module.params.get("token")

    validate_certs = module.params.get('validate_certs')
    if not validate_certs and hasattr(ssl, 'SSLContext'):
        ssl._create_default_https_context = ssl._create_unverified_context
    if validate_certs and not hasattr(ssl, 'SSLContext'):
        module.fail_json(msg="Module does not support changing verification mode with python < 2.7.9."
                             " Either update Python or use validate_certs=false.")

    if username and (password or token):
        return jenkins.Jenkins(url, username, password or token)
    elif username:
        return jenkins.Jenkins(url, username)
    else:
        return jenkins.Jenkins(url)


def test_dependencies(module):
    if not HAS_JENKINS:
        module.fail_json(
            msg="python-jenkins required for this module. "
            "see http://python-jenkins.readthedocs.io/en/latest/install.html")

def format_artifact(build_info, artifact):
  return {
    "displayPath": artifact['displayPath'],
    "fileName": artifact['fileName'],
    "relativePath": artifact['displayPath'],
    "downloadURL": build_info['url']+"artifact/"+urllib.quote(artifact['fileName'])
  }

def artifact_passes_glob(artifact,glob):
  return fnmatch.fnmatch(artifact["fileName"], glob)

def get_artifacts(module):
    jenkins_conn = get_jenkins_connection(module)
    artifacts = []
    job_name = module.params.get("job_name")
    build_number = module.params.get("build_number")
    glob = module.params.get("glob")

    if job_name and build_number:
        try:
            build_info = jenkins_conn.get_build_info(job_name,build_number,1)
        except jenkins.NotFoundException:
            pass
        else:
          for artifact in build_info['artifacts']:
            if not glob or artifact_passes_glob(artifact,glob):
              artifacts.append(format_artifact(build_info,artifact))

    return artifacts

def main():
    module = AnsibleModule(
        argument_spec=dict(
            job_name=dict(),
            glob=dict(),
            password=dict(no_log=True),
            token=dict(no_log=True),
            url=dict(default="http://localhost:8080"),
            user=dict(),
            validate_certs=dict(type='bool', default=True),
            build_number=dict(type='int')
        ),
        mutually_exclusive=[
            ['password', 'token'],
            ['name', 'glob'],
        ],
        required_one_of=[
            ['password', 'token'],
        ],
        supports_check_mode=True,
    )

    test_dependencies(module)
    artifacts = list()
    try:
        artifacts = get_artifacts(module)
    except jenkins.JenkinsException as err:
        module.fail_json(
            msg='Unable to connect to Jenkins server, %s' % to_native(err),
            exception=traceback.format_exc())

    module.exit_json(changed=False, artifacts=artifacts)

if __name__ == '__main__':
    main()
