#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: iosxr_banner
version_added: "2.4"
author:
    - Trishna Guha (@trishnaguha)
    - Kedar Kekan (@kedarX)
short_description: Manage multiline banners on Cisco IOS XR devices
description:
  - This module will configure both exec and motd banners on remote device
    running Cisco IOS XR. It allows playbooks to add or remove
    banner text from the running configuration.
requirements:
    - ncclient >= 0.5.3 when using netconf
    - lxml >= 4.1.1 when using netconf
extends_documentation_fragment: iosxr
notes:
  - Tested against IOS XRv 6.1.3.
  - This module works with connection C(network_cli) and C(netconf). See L(the IOS-XR Platform Options,../network/user_guide/platform_iosxr.html).
options:
  banner:
    description:
      - Specifies the type of banner to configure on remote device.
    required: true
    choices: ['login', 'motd']
  text:
    description:
      - Banner text to be configured. Accepts multiline string,
        without empty lines. Requires I(state=present).
  state:
    description:
      - Existential state of the configuration on the device.
    default: present
    choices: ['present', 'absent']
"""

EXAMPLES = """
- name: configure the login banner
  iosxr_banner:
    banner: login
    text: |
      this is my login banner
      that contains a multiline
      string
    state: present
- name: remove the motd banner
  iosxr_banner:
    banner: motd
    state: absent
- name: Configure banner from file
  iosxr_banner:
    banner:  motd
    text: "{{ lookup('file', './config_partial/raw_banner.cfg') }}"
    state: present
"""

RETURN = """
commands:
  description: The list of configuration mode commands sent to device with transport C(cli)
  returned: always (empty list when no commands to send)
  type: list
  sample:
    - banner login
    - this is my login banner
    - that contains a multiline
    - string

xml:
  description: NetConf rpc xml sent to device with transport C(netconf)
  returned: always (empty list when no xml rpc to send)
  type: list
  version_added: 2.5
  sample:
    - '<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <banners xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-infra-infra-cfg">
                <banner xc:operation="merge">
                  <banner-name>motd</banner-name>
                  <banner-text>Ansible banner example</banner-text>
                </banner>
            </banners>
        </config>'
"""

import re
import collections

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.iosxr.iosxr import get_config, load_config
from ansible.module_utils.network.iosxr.iosxr import iosxr_argument_spec
from ansible.module_utils.network.iosxr.iosxr import build_xml, is_cliconf
from ansible.module_utils.network.iosxr.iosxr import etree_find, is_netconf


class ConfigBase(object):
    def __init__(self, module):
        self._module = module
        self._result = {'changed': False, 'warnings': []}
        self._want = {}
        self._have = {}

    def map_params_to_obj(self):
        text = self._module.params['text']
        if text:
            text = "{0!r}".format(str(text).strip())
        self._want.update({
            'banner': self._module.params['banner'],
            'text': text,
            'state': self._module.params['state']
        })


class CliConfiguration(ConfigBase):
    def __init__(self, module):
        super(CliConfiguration, self).__init__(module)

    def map_obj_to_commands(self):
        commands = list()
        state = self._module.params['state']
        if state == 'absent':
            if self._have.get('state') != 'absent' and ('text' in self._have.keys() and self._have['text']):
                commands.append('no banner {0!s}'.format(self._module.params['banner']))
        elif state == 'present':
            if (self._want['text'] and
                    self._want['text'].encode().decode('unicode_escape').strip("'") != self._have.get('text')):
                banner_cmd = 'banner {0!s} '.format(self._module.params['banner'])
                banner_cmd += self._want['text'].strip()
                commands.append(banner_cmd)
        self._result['commands'] = commands
        if commands:
            commit = not self._module.check_mode
            diff = load_config(self._module, commands, commit=commit)
            if diff:
                self._result['diff'] = dict(prepared=diff)
            self._result['changed'] = True

    def map_config_to_obj(self):
        cli_filter = 'banner {0!s}'.format(self._module.params['banner'])
        output = get_config(self._module, config_filter=cli_filter)
        match = re.search(r'banner (\S+) (.*)', output, re.DOTALL)
        if match:
            text = match.group(2).strip("'")
        else:
            text = None
        obj = {'banner': self._module.params['banner'], 'state': 'absent'}
        if output:
            obj['text'] = text
            obj['state'] = 'present'
        self._have.update(obj)

    def run(self):
        self.map_params_to_obj()
        self.map_config_to_obj()
        self.map_obj_to_commands()

        return self._result


class NCConfiguration(ConfigBase):
    def __init__(self, module):
        super(NCConfiguration, self).__init__(module)
        self._banners_meta = collections.OrderedDict()
        self._banners_meta.update([
            ('banner', {'xpath': 'banners/banner', 'tag': True, 'attrib': "operation"}),
            ('a:banner', {'xpath': 'banner/banner-name'}),
            ('a:text', {'xpath': 'banner/banner-text', 'operation': 'edit'})
        ])

    def map_obj_to_xml_rpc(self):
        state = self._module.params['state']
        _get_filter = build_xml('banners', xmap=self._banners_meta, params=self._module.params, opcode="filter")

        running = get_config(self._module, source='running', config_filter=_get_filter)

        banner_name = None
        banner_text = None
        if etree_find(running, 'banner-text') is not None:
            banner_name = etree_find(running, 'banner-name').text
            banner_text = etree_find(running, 'banner-text').text

        opcode = None
        if state == 'absent' and banner_name == self._module.params['banner'] and len(banner_text):
            opcode = "delete"
        elif state == 'present':
            opcode = 'merge'

        self._result['xml'] = []
        if opcode:
            _edit_filter = build_xml('banners', xmap=self._banners_meta, params=self._module.params, opcode=opcode)

            if _edit_filter is not None:
                commit = not self._module.check_mode
                diff = load_config(self._module, _edit_filter, commit=commit, running=running, nc_get_filter=_get_filter)

                if diff:
                    self._result['xml'] = _edit_filter
                    if self._module._diff:
                        self._result['diff'] = dict(prepared=diff)

                    self._result['changed'] = True

    def run(self):
        self.map_params_to_obj()
        self.map_obj_to_xml_rpc()

        return self._result


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        banner=dict(required=True, choices=['login', 'motd']),
        text=dict(),
        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(iosxr_argument_spec)

    required_if = [('state', 'present', ('text',))]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    config_object = None
    if is_cliconf(module):
        # Commenting the below cliconf deprecation support call for Ansible 2.9 as it'll be continued to be supported
        # module.deprecate("cli support for 'iosxr_interface' is deprecated. Use transport netconf instead",
        #                  version='2.9')
        config_object = CliConfiguration(module)
    elif is_netconf(module):
        config_object = NCConfiguration(module)

    result = None
    if config_object is not None:
        result = config_object.run()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
