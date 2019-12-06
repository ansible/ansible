#!/usr/bin/python
'''
# (c) 2018, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
'''

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
short_description: NetApp ONTAP Run any cli command, the username provided needs to have console login permission.
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
    return_dict:
        description:
        - returns a parsesable dictionary instead of raw XML output
        type: bool
        default: false
        version_added: "2.9"
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
        return_dict: true
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
            privilege=dict(required=False, type='str', choices=['admin', 'advanced'], default='admin'),
            return_dict=dict(required=False, type='bool', default=False)
        ))
        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )
        parameters = self.module.params
        # set up state variables
        self.command = parameters['command']
        self.privilege = parameters['privilege']
        self.return_dict = parameters['return_dict']

        self.result_dict = dict()
        self.result_dict['status'] = ""
        self.result_dict['result_value'] = 0
        self.result_dict['invoked_command'] = " ".join(self.command)
        self.result_dict['stdout'] = ""
        self.result_dict['stdout_lines'] = []
        self.result_dict['xml_dict'] = dict()

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
        if self.return_dict:
            args_obj.add_new_child('arg', 'set')
            args_obj.add_new_child('arg', '-showseparator')
            args_obj.add_new_child('arg', '"###"')
            args_obj.add_new_child('arg', ';')
        for arg in self.command:
            args_obj.add_new_child('arg', arg)
        command_obj.add_child_elem(args_obj)
        command_obj.add_new_child('priv', self.privilege)

        try:
            output = self.server.invoke_successfully(command_obj, True)
            if self.return_dict:
                # Parseable dict output
                retval = self.parse_xml_to_dict(output.to_string())
            else:
                # Raw XML output
                retval = output.to_string()

            return retval
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error running command %s: %s' %
                                  (self.command, to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        ''' calls the command and returns raw output '''
        changed = True
        output = self.run_command()
        self.module.exit_json(changed=changed, msg=output)

    def parse_xml_to_dict(self, xmldata):
        '''Parse raw XML from system-cli and create an Ansible parseable dictionary'''
        xml_import_ok = True
        xml_parse_ok = True

        try:
            import xml.parsers.expat
        except ImportError:
            self.result_dict['status'] = "XML parsing failed. Cannot import xml.parsers.expat!"
            self.result_dict['stdout'] = str(xmldata)
            xml_import_ok = False

        if xml_import_ok:
            xml_str = xmldata.decode('utf-8').replace('\n', '---')
            xml_parser = xml.parsers.expat.ParserCreate()
            xml_parser.StartElementHandler = self._start_element
            xml_parser.CharacterDataHandler = self._char_data
            xml_parser.EndElementHandler = self._end_element

            try:
                xml_parser.Parse(xml_str)
            except xml.parsers.expat.ExpatError as errcode:
                self.result_dict['status'] = "XML parsing failed: " + str(errcode)
                self.result_dict['stdout'] = str(xmldata)
                xml_parse_ok = False

            if xml_parse_ok:
                self.result_dict['status'] = self.result_dict['xml_dict']['results']['attrs']['status']
                stdout_string = self._format_escaped_data(self.result_dict['xml_dict']['cli-output']['data'])
                self.result_dict['stdout'] = stdout_string
                for line in stdout_string.split('\n'):
                    stripped_line = line.strip()
                    if len(stripped_line) > 1:
                        self.result_dict['stdout_lines'].append(stripped_line)
                self.result_dict['xml_dict']['cli-output']['data'] = stdout_string
                self.result_dict['result_value'] = int(str(self.result_dict['xml_dict']['cli-result-value']['data']).replace("'", ""))

        return self.result_dict

    def _start_element(self, name, attrs):
        ''' Start XML element '''
        self.result_dict['xml_dict'][name] = dict()
        self.result_dict['xml_dict'][name]['attrs'] = attrs
        self.result_dict['xml_dict'][name]['data'] = ""
        self.result_dict['xml_dict']['active_element'] = name
        self.result_dict['xml_dict']['last_element'] = ""

    def _char_data(self, data):
        ''' Dump XML element data '''
        self.result_dict['xml_dict'][str(self.result_dict['xml_dict']['active_element'])]['data'] = repr(data)

    def _end_element(self, name):
        self.result_dict['xml_dict']['last_element'] = name
        self.result_dict['xml_dict']['active_element'] = ""

    @classmethod
    def _format_escaped_data(cls, datastring):
        ''' replace helper escape sequences '''
        formatted_string = datastring.replace('------', '---').replace('---', '\n').replace("###", "    ").strip()
        retval_string = ""
        for line in formatted_string.split('\n'):
            stripped_line = line.strip()
            if len(stripped_line) > 1:
                retval_string += stripped_line + "\n"
        return retval_string


def main():
    """
    Execute action from playbook
    """
    command = NetAppONTAPCommand()
    command.apply()


if __name__ == '__main__':
    main()
