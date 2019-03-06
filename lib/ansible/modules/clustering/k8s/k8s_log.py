#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Fabian von Feilitzsch <@fabianvf>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: k8s_log

short_description: Fetch logs from Kubernetes resources

version_added: "2.8"

author:
    - "Fabian von Feilitzsch (@fabianvf)"

description:
  - Use the OpenShift Python client to perform read operations on K8s log endpoints.
  - Authenticate using either a config file, certificates, password or token.
  - Supports check mode.
  - Analogous to `kubectl log` or `oc log`

options:
  api_version:
    description:
    - Use to specify the API version. in conjunction with I(kind), I(name), and I(namespace) to identify a
      specific object.
    default: v1
    aliases:
    - api
    - version
  kind:
    description:
    - Use to specify an object model. Use in conjunction with I(api_version), I(name), and I(namespace) to identify a
      specific object.
    required: no
    default: Pod
  name:
    description:
    - Use to specify an object name.  Use in conjunction with I(api_version), I(kind) and I(namespace) to identify a
      specific object.
  namespace:
    description:
    - Use to specify an object namespace. Use in conjunction with I(api_version), I(kind), and I(name)
      to identify a specfic object.
  container:
    description:
    - Use to specify the container within a pod to grab the log from
    required: no

extends_documentation_fragment:
  - k8s_auth_options

requirements:
  - "python >= 2.7"
  - "openshift >= 0.6"
  - "PyYAML >= 3.11"
'''

EXAMPLES = '''
- name: Get a log from a Pod
  k8s_log:
    api_version: v1
    kind: Pod
    name: web-1
    namespace: testing
  register: web_log
'''

RETURN = '''
log:
  description:
  - The text log of the object
  returned: success
'''


from ansible.module_utils.k8s.common import KubernetesAnsibleModule, AUTH_ARG_SPEC
import copy


class KubernetesFactsModule(KubernetesAnsibleModule):

    def __init__(self, *args, **kwargs):
        KubernetesAnsibleModule.__init__(self, *args,
                                         supports_check_mode=True,
                                         **kwargs)

    def execute_module(self):
        self.client = self.get_api_client()
        resource = self.find_resource(self.params['kind'], self.params['api_version'], fail=True)

        self.exit_json(changed=False, log=resource.log.get(
            name=self.params['name'],
            namespace=self.params['namespace'],
            query_params=dict(container=self.params.get('container'))
        ))

    @property
    def argspec(self):
        args = copy.deepcopy(AUTH_ARG_SPEC)
        args.update(
            dict(
                kind=dict(default='Pod'),
                api_version=dict(default='v1', aliases=['api', 'version']),
                name=dict(),
                namespace=dict(),
                container=dict(),
            )
        )
        return args


def main():
    KubernetesFactsModule().execute_module()


if __name__ == '__main__':
    main()
