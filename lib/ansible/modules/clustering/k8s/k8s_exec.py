#!/usr/bin/python
# Copyright 2019 Red Hat | Ansible
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: k8s_exec
short_description: Execute command in Pod
version_added: "2.10"
author: "Tristan de Cacqueray (@tristanC)"
description:
  - Use the Kubernetes Python client to execute command on K8s pods.
extends_documentation_fragment:
  - k8s_auth_options
requirements:
  - "python >= 2.7"
  - "openshift == 0.4.3"
  - "PyYAML >= 3.11"
options:
  proxy:
    description:
    - The URL of an HTTP proxy to use for the connection. Can also be specified via K8S_AUTH_PROXY environment variable.
    - Please note that this module does not pick up typical proxy settings from the environment (e.g. HTTP_PROXY).
    type: str
  namespace:
    description:
    - The pod namespace name
    type: str
    required: yes
  pod:
    description:
    - The pod name
    type: str
    required: yes
  command:
    description:
    - The command to execute
    type: str
    required: yes
'''

EXAMPLES = '''
- name: Execute a command
  k8s_exec:
    namespace: myproject
    pod: zuul-scheduler
    command: zuul-scheduler full-reconfigure
'''

RETURN = '''
result:
  description:
  - The command object
  returned: success
  type: complex
  contains:
     stdout:
       description: The command stdout
       type: str
     stdout_lines:
       description: The command stdout
       type: str
     stderr:
       description: The command stderr
       type: str
     stderr_lines:
       description: The command stderr
       type: str
'''

import copy
import shlex
from ansible.module_utils.k8s.common import KubernetesAnsibleModule
from ansible.module_utils.k8s.common import AUTH_ARG_SPEC

try:
    from kubernetes.client.apis import core_v1_api
    from kubernetes.stream import stream
except ImportError:
    # ImportError are managed by the common module already.
    pass


class KubernetesExecCommand(KubernetesAnsibleModule):
    @property
    def argspec(self):
        spec = copy.deepcopy(AUTH_ARG_SPEC)
        spec['namespace'] = {'type': 'str'}
        spec['pod'] = {'type': 'str'}
        spec['command'] = {'type': 'str'}
        return spec


def main():
    module = KubernetesExecCommand()
    # Load kubernetes.client.Configuration
    module.get_api_client()
    api = core_v1_api.CoreV1Api()
    resp = stream(
        api.connect_get_namespaced_pod_exec,
        module.params["pod"],
        module.params["namespace"],
        command=shlex.split(module.params["command"]),
        stdout=True,
        stderr=True,
        stdin=False,
        tty=False,
        _preload_content=False)
    stdout, stderr = [], []
    while resp.is_open():
        resp.update(timeout=1)
        if resp.peek_stdout():
            stdout.append(resp.read_stdout())
        if resp.peek_stderr():
            stderr.append(resp.read_stderr())
    module.exit_json(
        changed=True, stdout="".join(stdout), stderr="".join(stderr))


if __name__ == '__main__':
    main()
