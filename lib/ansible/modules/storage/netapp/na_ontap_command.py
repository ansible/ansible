#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
author: NetApp Ansible Team (ng-ansibleteam@netapp.com)
description:
  - "Run system-cli commands on ONTAP"
extends_documentation_fragment:
  - netapp.na_ontap
module: na_ontap_command
short_description: "NetApp ONTAP Run any cli command"
version_added: "2.7"
options:
    command:
        description:
        - a comma separated list containing the command and arguments.
'''

EXAMPLES = """
    - name: run ontap cli command
      na_ontap_command:
        hostname: "{{ hostname }} "
        username: "{{ admin username }}"
        password: "{{ admin password }}"
        command: ['version']

    - name: run ontap cli command
      na_ontap_command:
        hostname: "{{ hostname }} "
        username: "{{ admin username }}"
        password: "{{ admin password }}"
        command: ['network', 'interface', 'show']
"""

RETURN = """
"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPCommand(object):
    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            command=dict(required=True, type='list')
        ))
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )
        parameters = self.module.params
        # set up state variables
        self.command = parameters['command']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def run_command(self):

        command_obj = netapp_utils.zapi.NaElement("system-cli")
        args_obj = netapp_utils.zapi.NaElement("args")
        for arg in self.command:
            args_obj.add_new_child('arg', arg)
        command_obj.add_child_elem(args_obj)

        try:
            output = self.server.invoke_successfully(command_obj, True)
            return output.to_string()
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error running command %s: %s' %
                                  (self.command, to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        changed = True
        output = self.run_command()
        self.module.exit_json(changed=changed, msg=output)


def main():
        """
        Execute action from playbook
        """
        command = NetAppONTAPCommand()
        command.apply()


if __name__ == '__main__':
        main()
