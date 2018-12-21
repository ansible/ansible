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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ce_reboot
version_added: 2.4
short_description: Reboot a HUAWEI CloudEngine switches.
description:
    - Reboot a HUAWEI CloudEngine switches.
author: Gong Jianjun (@QijunPan)
requirements: ["ncclient"]
options:
    confirm:
        description:
            - Safeguard boolean. Set to true if you're sure you want to reboot.
        type: bool
        default: false
    save_config:
        description:
            - Flag indicating whether to save the configuration.
        required: false
        type: bool
        default: false
'''

EXAMPLES = '''
- name: reboot module test
  hosts: cloudengine
  connection: local
  gather_facts: no
  vars:
    cli:
      host: "{{ inventory_hostname }}"
      port: "{{ ansible_ssh_port }}"
      username: "{{ username }}"
      password: "{{ password }}"
      transport: cli

  tasks:
  - name: Reboot the device
    ce_reboot:
      confirm: true
      save_config: true
      provider: "{{ cli }}"
'''

RETURN = '''
rebooted:
    description: Whether the device was instructed to reboot.
    returned: success
    type: bool
    sample: true
'''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.cloudengine.ce import execute_nc_action, ce_argument_spec

try:
    from ncclient.operations.errors import TimeoutExpiredError
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False

CE_NC_XML_EXECUTE_REBOOT = """
    <action>
      <devm xmlns="http://www.huawei.com/netconf/vrp" content-version="1.0" format-version="1.0">
        <reboot>
            <saveConfig>%s</saveConfig>
        </reboot>
      </devm>
    </action>
"""


class Reboot(object):
    """ Reboot a network device """

    def __init__(self, **kwargs):
        """ __init___ """

        self.network_module = None
        self.netconf = None
        self.init_network_module(**kwargs)

        self.confirm = self.network_module.params['confirm']
        self.save_config = self.network_module.params['save_config']

    def init_network_module(self, **kwargs):
        """ init network module """

        self.network_module = AnsibleModule(**kwargs)

    def netconf_set_action(self, xml_str):
        """ netconf execute action """

        try:
            execute_nc_action(self.network_module, xml_str)
        except TimeoutExpiredError:
            pass

    def work(self):
        """ start to work """

        if not self.confirm:
            self.network_module.fail_json(
                msg='Error: Confirm must be set to true for this module to work.')

        xml_str = CE_NC_XML_EXECUTE_REBOOT % str(self.save_config).lower()
        self.netconf_set_action(xml_str)


def main():
    """ main """

    argument_spec = dict(
        confirm=dict(required=True, type='bool', default='false'),
        save_config=dict(required=False, type='bool', default='false')
    )

    argument_spec.update(ce_argument_spec)
    module = Reboot(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_NCCLIENT:
        module.network_module.fail_json(msg='Error: The ncclient library is required.')

    changed = False
    rebooted = False

    module.work()

    changed = True
    rebooted = True

    results = dict()
    results['changed'] = changed
    results['rebooted'] = rebooted

    module.network_module.exit_json(**results)


if __name__ == '__main__':
    main()
