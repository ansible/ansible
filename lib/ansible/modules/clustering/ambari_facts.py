#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, Thomas Hamm <thms.hmm@gmail.com>
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
#

import urllib2
import base64
import json

from ansible.module_utils.basic import AnsibleModule


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: ambari_facts
short_description: Module to gather facts about Ambari components.
author: Thomas Hamm (thms.hmm@gmail.com)
version_added: "2.4"
options:
  ambari_host:
    description:
      - Host where Ambari is running on.
    required: false
    type: str
    default: localhost
  ambari_port:
    description:
      - Port to connect to Ambari.
    required: false
    type: str
    default: 8080
  ambari_protocol:
    description:
      - Enable or disable secure connections.
    required: false
    type: str
    default: http
    choices:
      - http -- Enable unsecured connection
      - https -- Enable secured connection
  ambari_user:
    description:
      - Username to connect to Ambari.
    required: false
    type: str
    default: admin
  ambari_password:
    description:
      - Password to connect to Ambari.
    required: false
    type: str
    default: admin
  cluster_name:
    description:
      - Name of the cluster to get the component versions from.
    required: true
    type: str
'''

EXAMPLES = '''
# Get component versions, only required parameters
- ambari_facts:
    cluster_name: "TEST-CLUSTER"

# Get component versions, secure connection
- ambari_facts:
    ambari_host: "{{ ansible_fqdn }}"
    ambari_protocol: "https"
    cluster_name: "TEST-CLUSTER"
'''

RETURN = '''
ambari_cluster_component_versions:
    description: Contains component versions of all components installed for the cluster.
    returned: success
    type: complex
    sample:
      HBASE:
        version: "1.2.5"
        major_version: "1"
        minor_version: "2"
'''


class AmbariAPI:
    def __init__(self, module, host, port, protocol, user, password):
        self._module = module
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._credentials = base64.b64encode('%s:%s' % (user, password))
        self._version = 'v1'
        self._protocol = protocol

    def get(self, url):
        request = urllib2.Request(url)
        request.add_header("Authorization", "Basic %s" % self._credentials)

        response = ""

        try:
            response = urllib2.urlopen(request)
        except Exception as err:
            self._module.fail_json(msg="An exception occurred: %s" % err)

        response_body = dict()

        try:
            response_body = json.loads(response.read())
        except Exception as err:
            self._module.fail_json(msg="An exception occured while parsing the json response: %s" % err)

        return response_body

    def __get_base_url(self):
        return str('%s://%s:%s/api/%s' % (self._protocol, self._host, self._port, self._version))

    def get_cluster_component_versions(self, cluster_name):
        stack_versions = self.get(self.__get_base_url() + '/clusters/%s/stack_versions' % cluster_name)

        stack_name = ''
        stack_version = ''

        for stack_version in stack_versions['items']:
            stack_version = self.get(stack_version['href'])

            if stack_version['ClusterStackVersions']['state'] == 'CURRENT':
                stack_name = stack_version['ClusterStackVersions']['stack']
                stack_version = stack_version['ClusterStackVersions']['version']
                break

        services = self.get(self.__get_base_url() + '/stacks/%s/versions/%s/services' % (stack_name, stack_version))

        svc_versions = dict()

        for svc_item in services['items']:
            svc = self.get(svc_item['href'])

            svc_name = svc['StackServices']['service_name']
            svc_version = svc['StackServices']['service_version']

            svc_version_fragments = svc_version.split('.')

            svc_versions[svc_name] = {}
            svc_versions[svc_name]['version'] = svc_version
            svc_versions[svc_name]['major_version'] = svc_version_fragments[0]
            svc_versions[svc_name]['minor_version'] = svc_version_fragments[1]

        return svc_versions


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ambari_host=dict(required=False, default='localhost', type='str', aliases=['host']),
            ambari_port=dict(required=False, default='8080', type='str', aliases=['port']),
            ambari_protocol=dict(required=False, default='http', type='str', aliases=['protocol'], choices=['http', 'https']),
            ambari_user=dict(required=False, default='admin', type='str', aliases=['user']),
            ambari_password=dict(required=False, default='admin', type='str', no_log=True, aliases=['password']),
            cluster_name=dict(required=True, type='str', aliases=['cluster'])
        ),
        supports_check_mode=True
    )

    ambari_host = module.params['ambari_host']
    ambari_port = module.params['ambari_port']
    ambari_protocol = module.params['ambari_protocol']
    ambari_user = module.params['ambari_user']
    ambari_password = module.params['ambari_password']
    cluster_name = module.params['cluster_name']

    api = AmbariAPI(module, ambari_host, ambari_port, ambari_protocol, ambari_user, ambari_password)

    module.exit_json(msg='Registered cluster component versions as fact "ambari_cluster_component_versions".', ansible_facts=dict(ambari_cluster_component_versions=api.get_cluster_component_versions(cluster_name)))


if __name__ == '__main__':
    main()
