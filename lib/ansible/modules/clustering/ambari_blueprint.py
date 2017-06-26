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


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
module: ambari_blueprint
short_description: Module to manage Ambari Blueprints
description: The module provides the functionallity to register, update, get or delete Ambari Blueprints within an Ambari managed cluster
author: Thomas Hamm (thms.hmm@gmail.com)
version_added: "2.4"
options:
  ambari_server:
    description:
      - Ambari Server host name/address
    required: false
    default: localhost
    aliases: ['server']
  ambari_port:
    description:
      - Ambari Server port
    required: false
    default: 8080
    aliases: ['port']
  ambari_protocol:
    description:
      - Enable or disable secure connections
    required: false
    default: 'http'
    choices: ['http', 'https']
    aliases: ['protocol']
  ambari_user:
    description:
      - Username to connect to Ambari
    required: false
    default: 'admin'
    aliases: ['user']
  ambari_password:
    description:
      - Password to connect to Ambari
    required: false
    default: 'admin'
    aliases: ['password']
  blueprint_name:
    description:
      - Name of the Ambari Blueprint
    required: true
    aliases: ['name']
  blueprint:
    description:
      - The Ambari Blueprint structure (dict)
    required: false
  validate_topology:
    description:
      - Enable/disable the topology validation within Ambari
    required: false
    default: true
    aliases: ['validate']
  state:
    description:
      - Whether to register, delete or get the Ambari Blueprint
    required: false
    default: 'present'
    choices: ['present', 'absent', 'get']
'''

EXAMPLES = '''
# Blueprint definition
- set_fact:
    cluster_blueprint:
      Blueprints:
        stack_name: <STACK_NAME>
        stack_version: <STACK_VERSION>
        security:
          type: "NONE"
      host_groups:
        - name: "master"
          components:
            - { name: "NAMENODE" }
            - { name: "SECONDARY_NAMENODE" }
            - { name: "RESOURCEMANAGER" }
            - { name: "HISTORYSERVER" }
            - { name: "ZOOKEEPER_SERVER" }
            - { name: "APP_TIMELINE_SERVER" }
            - { name: "HDFS_CLIENT" }
          configurations: [ ]
          cardinality: "NOT SPECIFIED"
        - name: "slaves"
          components:
            - { name: "DATANODE" }
            - { name: "HDFS_CLIENT" }
            - { name: "NODEMANAGER" }
            - { name: "YARN_CLIENT" }
            - { name: "MAPREDUCE2_CLIENT" }
            - { name: "ZOOKEEPER_CLIENT" }
          configurations: [ ]
          cardinality: "NOT SPECIFIED"
      configurations: [ ]
      settings: [ ]

# Register blueprint
- ambari_blueprint:
    name: "multi-node"
    blueprint: "{{ cluster_blueprint }}"

# Remove blueprint
- ambari_blueprint:
    name: "multi-node"
    state: absent

# Set blueprint 'multi-node' as fact 'ambari_blueprint'
- ambari_blueprint:
    name: "multi-node"
    state: get
'''

RETURN = '''
ambari_blueprint:
  description: currently registered blueprint under given name
  returned: when state argument equals get
  type: complex
  contains:
    Blueprints:
      stack_name: "<STACK_NAME>"
      stack_version: "<STACK_VERSION>"
      security: {...}
    host_groups: [...]
    configurations: [...]
    settings: [...]
  sample: '{"Blueprints": {...}, "host_groups": {...}, "configurations": [...], ...}'
'''


import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url
from urllib2 import URLError, HTTPError


class AmbariAPI:
    def __init__(self, module, host, port, protocol, user, password):
        self._module = module
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._version = 'v1'
        self._protocol = protocol
        self._headers = {'X-Requested-By': 'ambari'}

    def query(self, url, data=None, method='GET'):
        response = None
        response_json = None

        if data is not None:
            data = json.dumps(data)

        try:
            response = open_url(self.__get_base_url() + url, url_username=self._user, url_password=self._password,
                                force_basic_auth=True, headers=self._headers, data=data, method=method)
            response_json = {'status': response.code, 'message': response.msg}

            try:
                response_json['data'] = json.loads(response.read())
            except Exception as errRead:
                pass
        except URLError as urlErr:
            if not isinstance(urlErr, HTTPError):
                self._module.fail_json(msg='error connecting to ambari server, verify host and port')
            else:
                response = urlErr.read()

                try:
                    response_json = json.loads(response)

                    # http error handling
                    if response_json['status'] == 403:
                        self._module.fail_json(msg='{}'.format(response_json['message']))

                except Exception as errJson:
                    self._module.fail_json(msg='failed to parse json response: {}'.format(errJson))

        return response_json

    def __get_base_url(self):
        return str('%s://%s:%s/api/%s' % (self._protocol, self._host, self._port, self._version))

    def cmp_blueprints(self, obj1, obj2):
        if obj1 is None or obj2 is None:
            return False

        if isinstance(obj1, unicode):
            obj1 = obj1.encode('utf-8')

        if isinstance(obj2, unicode):
            obj2 = obj2.encode('utf-8')

        if obj1.__class__ != obj2.__class__:
            return False

        if isinstance(obj1, dict):
            if len(obj1) != len(obj2):
                return False

            if len(set(obj1.keys()).symmetric_difference(set(obj2.keys()))) > 0:
                return False

            for key1 in obj1.keys():
                if not self.cmp_blueprints(obj1.get(key1), obj2.get(key1)):
                    return False

            return True

        elif isinstance(obj1, list):
            if len(obj1) != len(obj2):
                return False

            for item1 in obj1:
                match = False

                for item2 in obj2:
                    if item1.__class__ == item2.__class__:
                        match = self.cmp_blueprints(item1, item2)
                        if match:
                            break

                if not match:
                    return False

            return True

        else:
            return obj1 == obj2

    def register_blueprint(self, name, blueprint, validate=True):
        return self.query('/blueprints/' + name + '?validate_topology=' + str(validate), blueprint, 'POST')

    def get_blueprint(self, name):
        response = self.query('/blueprints/' + name)

        try:
            response['data'].pop('href', None)
            response['data']['Blueprints'].pop('blueprint_name', None)
        except KeyError:
            pass

        return response

    def get_blueprints(self):
        return self.query('/blueprints')

    def delete_blueprint(self, name):
        return self.query('/blueprints/' + name, method='DELETE')


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ambari_server=dict(required=False, default='localhost', aliases=['server']),
            ambari_port=dict(required=False, default='8080', aliases=['port']),
            ambari_protocol=dict(required=False, default='http', aliases=['protocol'], choices=['http', 'https']),
            ambari_user=dict(required=False, default='admin', aliases=['user']),
            ambari_password=dict(required=False, default='admin', no_log=True, aliases=['password']),
            blueprint_name=dict(required=True, aliases=['name']),
            blueprint=dict(required=False, type='dict'),
            validate_topology=dict(required=False, default=True, type='bool', aliases=['validate']),
            state=dict(required=False, default='present', choices=['present', 'absent', 'get'])
        ),
        supports_check_mode=False
    )

    ambari_server = module.params['ambari_server']
    ambari_port = module.params['ambari_port']
    ambari_protocol = module.params['ambari_protocol']
    ambari_user = module.params['ambari_user']
    ambari_password = module.params['ambari_password']
    blueprint_name = module.params['blueprint_name']
    blueprint = module.params['blueprint']
    validate_topology = module.params['validate_topology']
    state = module.params['state']

    api = AmbariAPI(module, ambari_server, ambari_port, ambari_protocol, ambari_user, ambari_password)

    if state == 'present':
        if blueprint is None:
            module.fail_json(msg='missing required argument \'blueprint\' for state \'present\'')

        # check if blueprint exists
        response_get_bp = api.get_blueprint(blueprint_name)

        # blueprint already exists
        if response_get_bp['status'] == 200:
            bp_compare = api.cmp_blueprints(blueprint, response_get_bp['data'])

            if bp_compare is True:
                module.exit_json(changed=False)
            else:
                # delete registered blueprint
                response_delete_bp = api.delete_blueprint(blueprint_name)

                # register new blueprint version
                if response_delete_bp['status'] == 200:
                    response_register_bp = api.register_blueprint(blueprint_name, blueprint, validate_topology)

                    if response_register_bp['status'] == 201:
                        module.exit_json(changed=True)
                    else:
                        # try to re-register previous blueprint, because registering the new blueprint failed
                        response_register_bp_prev = api.register_blueprint(blueprint_name, response_get_bp['data'], validate_topology)

                        if response_register_bp_prev['status'] != 201:
                            module.fail_json(msg='failed to update blueprint and to re-register previous, '
                                             'validate your current blueprint')

                        # succeeded re-registering blueprint, failed to update anyway
                        module.fail_json(msg='failed to update blueprint with message: {}'.format(response_register_bp['message']))
                else:
                    module.fail_json(msg='failed to update blueprint')
        else:
            response_register_bp = api.register_blueprint(blueprint_name, blueprint, validate_topology)

            if response_register_bp['status'] == 201:
                module.exit_json(changed=True)
            else:
                module.fail_json(msg='failed to register blueprint with message: {}'.format(response_register_bp['message']))
    elif state == 'absent':
        response_get_bp = api.get_blueprint(blueprint_name)

        if response_get_bp['status'] == 200:
            response_delete_bp = api.delete_blueprint(blueprint_name)

            if response_delete_bp['status'] == 200:
                module.exit_json(changed=True)
            else:
                module.fail_json(msg=response_delete_bp['message'])
        else:
            module.exit_json(changed=False)
    elif state == 'get':
        response_get_bp = api.get_blueprint(blueprint_name)

        if response_get_bp['status'] == 200:
            module.exit_json(msg='registered current ambari blueprint as fact \'ambari_blueprint\'',
                             ansible_facts=dict(ambari_blueprint=response_get_bp['data']))
        elif response_get_bp['status'] == 404:
            module.fail_json(msg='blueprint \'{}\' not found'.format(blueprint_name))
        else:
            module.fail_json(msg='unknown error fetching blueprint \'{}\''.format(blueprint_name))

    module.fail_json(msg="no action detected, this should never happen")


if __name__ == '__main__':
    main()
