#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage PaloAltoNetworks Firewall
# (c) 2016, techbizdev <techbizdev@paloaltonetworks.com>
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

DOCUMENTATION = '''
---
module: panos_dag
short_description: create a dynamic address group
description:
    - Create a dynamic address group object in the firewall used for policy rules
author: "Luigi Mori (@jtschichold), Ivan Bojer (@ivanbojer)"
version_added: "2.3"
requirements:
    - pan-python
options:
    dag_name:
        description:
            - name of the dynamic address group
        required: true
    dag_filter:
        description:
            - dynamic filter user by the dynamic address group
        required: true
    commit:
        description:
            - commit if changed
        type: bool
        default: 'yes'
extends_documentation_fragment: panos
'''

EXAMPLES = '''
- name: dag
  panos_dag:
    ip_address: "192.168.1.1"
    password: "admin"
    dag_name: "dag-1"
    dag_filter: "'aws-tag.aws:cloudformation:logical-id.ServerInstance' and 'instanceState.running'"
'''

RETURN = '''
# Default return values
'''

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


from ansible.module_utils.basic import AnsibleModule

try:
    import pan.xapi
    HAS_LIB = True
except ImportError:
    HAS_LIB = False

_ADDRGROUP_XPATH = "/config/devices/entry[@name='localhost.localdomain']" +\
                   "/vsys/entry[@name='vsys1']/address-group/entry[@name='%s']"


def addressgroup_exists(xapi, group_name):
    xapi.get(_ADDRGROUP_XPATH % group_name)
    e = xapi.element_root.find('.//entry')
    if e is None:
        return False
    return True


def add_dag(xapi, dag_name, dag_filter):
    if addressgroup_exists(xapi, dag_name):
        return False

    # setup the non encrypted part of the monitor
    exml = []

    exml.append('<dynamic>')
    exml.append('<filter>%s</filter>' % dag_filter)
    exml.append('</dynamic>')

    exml = ''.join(exml)
    xapi.set(xpath=_ADDRGROUP_XPATH % dag_name, element=exml)

    return True


def main():
    argument_spec = dict(
        ip_address=dict(required=True),
        password=dict(required=True, no_log=True),
        username=dict(default='admin'),
        dag_name=dict(required=True),
        dag_filter=dict(required=True),
        commit=dict(type='bool', default=True)
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=False)
    if not HAS_LIB:
        module.fail_json(msg='pan-python is required for this module')

    ip_address = module.params["ip_address"]
    password = module.params["password"]
    username = module.params['username']

    xapi = pan.xapi.PanXapi(
        hostname=ip_address,
        api_username=username,
        api_password=password
    )

    dag_name = module.params['dag_name']
    dag_filter = module.params['dag_filter']
    commit = module.params['commit']

    changed = add_dag(xapi, dag_name, dag_filter)

    if changed and commit:
        xapi.commit(cmd="<commit></commit>", sync=True, interval=1)

    module.exit_json(changed=changed, msg="okey dokey")

if __name__ == '__main__':
    main()
