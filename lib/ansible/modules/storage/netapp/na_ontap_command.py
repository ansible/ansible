#!/usr/bin/python

# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
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
        required: true
    privilege:
        description:
        - privilege level at which to run the command.
        choices: ['admin', 'advanced']
        default: admin
        version_added: "2.8"
'''

EXAMPLES = """
    - name: run ontap cli command
      na_ontap_command:
        hostname: "{{ hostname }}"
        username: "{{ admin username }}"
        password: "{{ admin password }}"
        command: ['version']

    - name: run ontap cli command
      na_ontap_command:
        hostname: "{{ hostname }}"
        username: "{{ admin username }}"
        password: "{{ admin password }}"
        command: ['network', 'interface', 'show']
        privilege: 'admin'
"""

RETURN = """
"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPCommand(object):
    ''' calls a CLI command '''

    def __init__(self):
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            command=dict(required=True, type='list'),
            privilege=dict(required=False, type='str', choices=['admin', 'advanced'],
                           default='admin')
        ))
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )
        parameters = self.module.params
        # set up state variables
        self.command = parameters['command']
        self.privilege = parameters['privilege']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    def asup_log_for_cserver(self, event_name):
        """
        Fetch admin vserver for the given cluster
        Create and Autosupport log event with the given module name
        :param event_name: Name of the event log
        :return: None
        """
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event(event_name, cserver)

    def run_command(self):
        ''' calls the ZAPI '''
        self.asup_log_for_cserver("na_ontap_command: " + str(self.command))
        command_obj = netapp_utils.zapi.NaElement("system-cli")
        args_obj = netapp_utils.zapi.NaElement("args")
        for arg in self.command:
            args_obj.add_new_child('arg', arg)
        command_obj.add_child_elem(args_obj)
        command_obj.add_new_child('priv', self.privilege)

        try:
            output = self.server.invoke_successfully(command_obj, True)
            return output.to_string()
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error running command %s: %s' %
                                  (self.command, to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        ''' calls the command and returns raw output '''
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
