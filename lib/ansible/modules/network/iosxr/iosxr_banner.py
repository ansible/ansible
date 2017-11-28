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
module: iosxr_banner
version_added: "2.4"
author:
    - Trishna Guha (@trishnaguha)
    - Kedar Kekan (@kedarX)
short_description: Manage multiline banners on Cisco IOS XR devices
description:
  - This will configure both exec and motd banners on remote devices
    running Cisco IOS XR. It allows playbooks to add or remote
    banner text from the active running configuration.
notes:
  - Tested against IOS XR 6.1.2
options:
  banner:
    description:
      - Specifies which banner that should be
        configured on the remote device.
    required: true
    default: null
    choices: ['login', 'motd']
  text:
    description:
      - The banner text that should be
        present in the remote device running configuration. This argument
        accepts a multiline string, with no empty lines. Requires I(state=present).
    default: null
  state:
    description:
      - Specifies whether or not the configuration is present in the current
        devices active running configuration.
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
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - banner login
    - this is my login banner
    - that contains a multiline
    - string
"""

import re
import collections
from lxml import etree

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.iosxr.iosxr import get_config, load_config
from ansible.module_utils.network.iosxr.iosxr import get_config_diff, commit_config, discard_config
from ansible.module_utils.network.iosxr.iosxr import iosxr_argument_spec, check_args
from ansible.module_utils.network.iosxr.iosxr import get_device_capabilities, build_xml


class ConfigBase(object):
    def __init__(self, module, warnings):
        self._module = module
        self._result = {'changed': False, 'warnings': warnings}
        self._want = {}
        self._have = {}

    def map_params_to_obj(self):
        text = self._module.params['text']
        if text:
            text = "{!r}".format(str(text).strip())
        self._want.update({
            'banner': self._module.params['banner'],
            'text': text,
            'state': self._module.params['state']
        })


class CliConfiguration(ConfigBase):
    def __init__(self, module, warnings):
        super(CliConfiguration, self).__init__(module, warnings)

    def map_obj_to_commands(self):
        commands = list()
        state = self._module.params['state']
        if state == 'absent':
            if self._have.get('state') != 'absent' and ('text' in self._have.keys() and self._have['text']):
                commands.append('no banner {!s}'.format(self._module.params['banner']))
        elif state == 'present':
            if (self._want['text'] and
                    self._want['text'].encode().decode('unicode_escape').strip("'") != self._have.get('text')):
                banner_cmd = 'banner {!s} '.format(self._module.params['banner'])
                banner_cmd += self._want['text'].strip()
                commands.append(banner_cmd)
        self._result['commands'] = commands
        if commands:
            if not self._module.check_mode:
                load_config(self._module, commands, self._result['warnings'], commit=True)
            self._result['changed'] = True

    def map_config_to_obj(self):
        cli_filter = 'banner {!s}'.format(self._module.params['banner'])
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
    def __init__(self, module, warnings):
        super(NCConfiguration, self).__init__(module, warnings)
        self._banners_meta = collections.OrderedDict()
        self._banners_meta.update([
            ('banner', {'xpath': 'banners/banner', 'tag': True, 'attrib': "operation"}),
            ('a:banner', {'xpath': 'banner/banner-name'}),
            ('a:text', {'xpath': 'banner/banner-text', 'operation': 'edit'})
        ])

    def map_obj_to_commands(self):
        state = self._module.params['state']
        _get_filter = build_xml('banners', xmap=self._banners_meta, params=self._module.params, opcode="filter")
        running = get_config(self._module, source='running', config_filter=etree.tostring(_get_filter))

        opcode = None
        banner_name = None
        banner_text = None
        running_utf8 = running.encode('utf8')
        if etree.fromstring(running_utf8).find('.//banner-text') is not None:
            banner_name = etree.fromstring(running_utf8).find('.//banner-name').text
            banner_text = etree.fromstring(running_utf8).find('.//banner-text').text

        if state == 'absent' and banner_name == self._module.params['banner'] and len(banner_text):
            opcode = "delete"
        elif state == 'present':
            opcode = 'merge'

        self._result['commands'] = []
        if opcode:
            _edit_filter = build_xml('banners', xmap=self._banners_meta, params=self._module.params, opcode=opcode)
            if _edit_filter is not None:
                if not self._module.check_mode:
                    load_config(self._module, etree.tostring(_edit_filter), self._result['warnings'])
                    candidate = get_config(self._module, source='candidate', config_filter=etree.tostring(_get_filter))

                    rc, diff = get_config_diff(self._module, running, candidate)
                    if rc:
                        commit_config(self._module)
                        self._result['changed'] = True
                        self._result['commands'] = etree.tostring(_edit_filter)
                        if self._module._diff:
                            self._result['diff'] = {'prepared': diff}
                    else:
                        discard_config(self._module)

    def run(self):
        self.map_params_to_obj()
        self.map_obj_to_commands()

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

    warnings = list()
    check_args(module, warnings)

    device_capabilities = get_device_capabilities(module)
    network_api = device_capabilities.get('network_api')

    if network_api == 'cliconf':
        warnings.append('cli support for \'iosxr_banner\' is deprecated and will be removed 4 releases from 2.5. Use \'netconf\' instead')
        config_object = CliConfiguration(module, warnings)
    elif network_api == 'netconf':
        config_object = NCConfiguration(module, warnings)
    else:
        module.fail_json(msg=('unsupported network_api: {!s}'.format(network_api)))

    result = config_object.run()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
