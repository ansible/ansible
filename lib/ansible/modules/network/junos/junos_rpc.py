#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: junos_rpc
version_added: "2.3"
author: "Peter Sprygada (@privateip)"
short_description: Runs an arbitrary RPC over NetConf on an Juniper JUNOS device
description:
  - Sends a request to the remote device running JUNOS to execute the
    specified RPC using the NetConf transport.  The reply is then
    returned to the playbook in the C(xml) key.  If an alternate output
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
  attrs:
    description:
      - The C(attrs) arguments defines a list of attributes and their values
        to set for the RPC call. This accepts a dictionary of key-values.
    version_added: "2.5"
  output:
    description:
      - The C(output) argument specifies the desired output of the
        return data.  This argument accepts one of C(xml), C(text),
        or C(json).  For C(json), the JUNOS device must be running a
        version of software that supports native JSON output.
    default: xml
requirements:
  - ncclient (>=v0.5.2)
notes:
  - This module requires the netconf system service be enabled on
    the remote device being managed.
  - Tested against vSRX JUNOS version 15.1X49-D15.4, vqfx-10000 JUNOS Version 15.1X53-D60.4.
  - Recommended connection is C(netconf). See L(the Junos OS Platform Options,../network/user_guide/platform_junos.html).
  - This module also works with C(local) connections for legacy playbooks.
"""

EXAMPLES = """
- name: collect interface information using rpc
  junos_rpc:
    rpc: get-interface-information
    args:
      interface-name: em0
      media: True

- name: get system information
  junos_rpc:
    rpc: get-system-information

- name: load configuration
  junos_rpc:
    rpc: load-configuration
    attrs:
      action: override
      url: /tmp/config.conf
"""

RETURN = """
xml:
  description: The xml return string from the rpc request.
  returned: always
  type: str
output:
  description: The rpc rely converted to the output format.
  returned: always
  type: str
output_lines:
  description: The text output split into lines for readability.
  returned: always
  type: list
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.netconf import exec_rpc
from ansible.module_utils.network.junos.junos import junos_argument_spec, tostring
from ansible.module_utils.six import iteritems

USE_PERSISTENT_CONNECTION = True

try:
    from lxml.etree import Element, SubElement
except ImportError:
    from xml.etree.ElementTree import Element, SubElement


def main():
    """main entry point for Ansible module
    """
    argument_spec = dict(
        rpc=dict(required=True),
        args=dict(type='dict'),
        attrs=dict(type='dict'),
        output=dict(default='xml', choices=['xml', 'json', 'text']),
    )

    argument_spec.update(junos_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)

    warnings = list()
    result = {'changed': False, 'warnings': warnings}

    rpc = str(module.params['rpc']).replace('_', '-')

    if all((module.check_mode, not rpc.startswith('get'))):
        module.fail_json(msg='invalid rpc for running in check_mode')

    args = module.params['args'] or {}
    attrs = module.params['attrs'] or {}

    xattrs = {'format': module.params['output']}

    for key, value in iteritems(attrs):
        xattrs.update({key: value})

    element = Element(module.params['rpc'], xattrs)

    for key, value in iteritems(args):
        key = str(key).replace('_', '-')
        if isinstance(value, list):
            for item in value:
                child = SubElement(element, key)
                if item is not True:
                    child.text = item
        else:
            child = SubElement(element, key)
            if value is not True:
                child.text = value

    reply = exec_rpc(module, tostring(element), ignore_warning=False)

    result['xml'] = tostring(reply)

    if module.params['output'] == 'text':
        data = reply.find('.//output')
        result['output'] = data.text.strip()
        result['output_lines'] = result['output'].split('\n')

    elif module.params['output'] == 'json':
        result['output'] = module.from_json(reply.text.strip())

    else:
        result['output'] = tostring(reply).split('\n')

    module.exit_json(**result)


if __name__ == '__main__':
    main()
