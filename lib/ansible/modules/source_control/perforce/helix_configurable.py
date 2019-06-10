#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Asif Shaikh (@ripclawffb) <ripclaw_ffb@hotmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: helix_configurable

short_description: This module will allow you to set config options on Perforce Helix Core

version_added: "2.9"

description:
    - "Configurables allow you to customize a Perforce service. Configurable settings might affect the server, the client, or a proxy."
    - "This module supports check mode."

requirements:
    - "P4Python pip module is required. Tested with 2018.2.1743033"

seealso:
    - name: Helix Core Configurables
      description: "List of supported configurables"
      link: https://www.perforce.com/manuals/cmdref/Content/CmdRef/appendix.configurables.html
    - name: P4Python Pip Module
      description: "Python module to interact with Helix Core"
      link: https://pypi.org/project/p4python/


options:
    state:
        choices:
            - present
            - absent
        default: present
        description:
            - Determines if the configurable is set or removed
    name:
        description:
            - The name of the configurable that needs to be set
        required: true
        type: str
    value:
        description:
            - The value of named configurable
        required: true
        type: str
    p4port:
        description:
            - The hostname/ip and port of the server (perforce:1666)
        required: true
        type: str
    p4user:
        description:
            - A user with super user access
        required: true
        type: str
    p4passwd:
        description:
            - The super user password
        required: true
        type: str
    serverid:
        default: any
        description:
            - The server ID of the helix server
        required: false
        type: str

author:
    - Asif Shaikh (@ripclawffb)
'''

EXAMPLES = '''
# Set auth.id configurable for any server
- name: Set auth.id
  helix_configurable:
    state: present
    name: auth.id
    value: master.1
    p4port: '1666'
    p4user: bruno
    p4passwd: ''

# Unset auth.id configurable for specific server
- name: Unset auth.id
  helix_configurable:
    state: absent
    name: auth.id
    value: master.1
    serverid: master.1
    p4port: '1666'
    p4user: bruno
    p4passwd: ''
'''

RETURN = r''' # '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import string_types

try:
    from P4 import P4, P4Exception
    HAS_P4 = True
except ImportError:
    HAS_P4 = False


def helix_connect(p4_user, p4_port, p4_password, script_name):
    """
    Pass this function a user, p4port, password and client to connect to
    the server
    """
    try:
        p4 = P4()
        p4.prog = script_name
        p4.port = p4_port
        p4.user = p4_user
        p4.password = p4_password
        p4.connect()
        p4.run_login()
        if p4.connected() is not True:
            raise RuntimeError
        return p4
    except Exception as e:
        return "There was a problem in connecting to Helix: {0}".format(e)


def helix_disconnect(connection):
    """
    Pass this function a connection object to disconnect the Helix Core
    session
    """

    connection.disconnect()


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        state=dict(type='str', default='present', choices=['present', 'absent']),
        name=dict(type='str', required=True),
        value=dict(type='str', required=True),
        p4port=dict(type='str', required=True),
        p4user=dict(type='str', required=True),
        p4passwd=dict(type='str', required=True, no_log=True),
        serverid=dict(type='str', default='any')
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if not HAS_P4:
        module.fail_json(msg="Missing required lib 'p4python'")

    # connect to helix
    p4 = helix_connect(module.params['p4user'], module.params['p4port'], module.params['p4passwd'], 'ansible')

    # check to see if connection to helix server was successful
    if isinstance(p4, string_types) and 'problem' in p4:
        module.fail_json(msg="Error: {0}".format(p4), **result)

    try:
        # get existing config values
        p4_current_configs = p4.run('configure', 'show', 'allservers')

        p4_current_values = []

        # search for all config values specific to this server id and add to list
        for config in p4_current_configs:
            if config["ServerName"] == module.params['serverid']:
                p4_current_values.append(config)

        # get the current value of our specific configurable
        p4_current_value = next((item for item in p4_current_values if item["Name"] == module.params['name']), None)

        if module.params['state'] == 'present':
            if p4_current_value is None or module.params['value'] != p4_current_value['Value']:
                if not module.check_mode:
                    p4.run('configure', 'set', "{0}#{1}={2}".format(
                        module.params['serverid'], module.params['name'], module.params['value'])
                    )
                result['changed'] = True
        elif module.params['state'] == 'absent':
            if p4_current_value is not None:
                if not module.check_mode:
                    p4.run('configure', 'unset', "{0}#{1}".format(
                        module.params['serverid'], module.params['name'])
                    )
                result['changed'] = True
    except Exception as e:
        module.fail_json(msg="Error: {0}".format(e), **result)

    helix_disconnect(p4)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
