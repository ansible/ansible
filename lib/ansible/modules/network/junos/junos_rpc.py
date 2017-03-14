#!/usr/bin/python
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'core'}


DOCUMENTATION = """
---
module: junos_rpc
version_added: "2.3"
author: "Peter Sprygada (@privateip)"
short_description: Runs an arbitrary RPC on the remote device over NetConf
description:
  - Sends a request to the remote device running JUNOS to execute the
    specified RPC using the NetConf transport.  The reply is then
    returned to the playbook in the c(xml) key.  If an alternate output
    format is requested, the reply is transformed to the requested output.
extends_documentation_fragment: junos
options:
  rpc:
    description:
      - The C(rpc) argument specifies the RPC call to send to the
        remote devices to be executed.  The RPC Reply message is parsed
        and the contents are returned to the playbook.
    required: true
  args:
    description:
      - The C(args) argument provides a set of arguments for the RPC
        call and are encoded in the request message.  This argument
        accepts a set of key=value arguments.
    required: false
    default: null
  output:
    description:
      - The C(output) argument specifies the desired output of the
        return data.  This argument accepts one of C(xml), C(text),
        or C(json).  For C(json), the JUNOS device must be running a
        version of software that supports native JSON output.
    required: false
    default: xml
"""

EXAMPLES = """
- name: collect interface information using rpc
  junos_rpc:
    rpc: get-interface-information
    args:
      interface: em0
      media: True

- name: get system information
  junos_rpc:
    rpc: get-system-information
"""

RETURN = """
xml:
  description: The xml return string from the rpc request
  returned: always
output:
  description: The rpc rely converted to the output format
  returned: always
output_lines:
  description: The text output split into lines for readability
  returned: always
"""
from ncclient.xml_ import new_ele, sub_ele, to_xml, to_ele

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.netconf import send_request
from ansible.module_utils.six import iteritems



def main():
    """main entry point for Ansible module
    """
    argument_spec = dict(
        rpc=dict(required=True),
        args=dict(type='dict'),
        output=dict(default='xml', choices=['xml', 'json', 'text']),
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)

    result = {'changed': False}

    rpc = str(module.params['rpc']).replace('_', '-')

    if all((module.check_mode, not rpc.startswith('get'))):
        module.fail_json(msg='invalid rpc for running in check_mode')

    args = module.params['args'] or {}

    xattrs = {'format': module.params['output']}

    element = new_ele(module.params['rpc'], xattrs)

    for key, value in iteritems(args):
        key = str(key).replace('_', '-')
        if isinstance(value, list):
            for item in value:
                child = sub_ele(element, key)
                if item is not True:
                    child.text = item
        else:
            child = sub_ele(element, key)
            if value is not True:
                child.text = value

    reply = send_request(module, element)

    result['xml'] = str(to_xml(reply))

    if module.params['output'] == 'text':
        reply = to_ele(reply)
        data = reply.xpath('//output')
        result['output'] = data[0].text.strip()
        result['output_lines'] = result['output'].split('\n')

    elif module.params['output'] == 'json':
        reply = to_ele(reply)
        data = reply.xpath('//rpc-reply')
        result['output'] = module.from_json(data[0].text.strip())

    else:
        result['output'] = str(to_xml(reply)).split('\n')

    module.exit_json(**result)


if __name__ == '__main__':
    main()
