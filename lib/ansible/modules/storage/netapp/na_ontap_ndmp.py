#!/usr/bin/python
""" this is ndmp module

 (c) 2019, NetApp, Inc
 # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: na_ontap_ndmp
short_description: NetApp ONTAP NDMP services configuration
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.9'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
    - Modify NDMP Services.

options:

  vserver:
    description:
    - Name of the vserver.
    required: true
    type: str

  abort_on_disk_error:
    description:
    - Enable abort on disk error.
    type: bool

  authtype:
    description:
    - Authentication type.
    type: list

  backup_log_enable:
    description:
    - Enable backup log.
    type: bool

  data_port_range:
    description:
    - Data port range.
    type: str

  debug_enable:
    description:
    - Enable debug.
    type: bool

  debug_filter:
    description:
    - Debug filter.
    type: str

  dump_detailed_stats:
    description:
    - Enable logging of VM stats for dump.
    type: bool

  dump_logical_find:
    description:
    - Enable logical find for dump.
    type: str

  enable:
    description:
    - Enable NDMP on vserver.
    type: bool

  fh_dir_retry_interval:
    description:
    - FH throttle value for dir.
    type: int

  fh_node_retry_interval:
    description:
    - FH throttle value for node.
    type: int

  ignore_ctime_enabled:
    description:
    - Ignore ctime.
    type: bool

  is_secure_control_connection_enabled:
    description:
    - Is secure control connection enabled.
    type: bool

  offset_map_enable:
    description:
    - Enable offset map.
    type: bool

  per_qtree_exclude_enable:
    description:
    - Enable per qtree exclusion.
    type: bool

  preferred_interface_role:
    description:
    - Preferred interface role.
    type: list

  restore_vm_cache_size:
    description:
    - Restore VM file cache size.
    type: int

  secondary_debug_filter:
    description:
    - Secondary debug filter.
    type: str

  tcpnodelay:
    description:
    - Enable TCP nodelay.
    type: bool

  tcpwinsize:
    description:
    - TCP window size.
    type: int
'''

EXAMPLES = '''
    - name: modify ndmp
      na_ontap_ndmp:
        vserver: ansible
        hostname: "{{ hostname }}"
        abort_on_disk_error: true
        authtype: plaintext,challenge
        backup_log_enable: true
        data_port_range: 8000-9000
        debug_enable: true
        debug_filter: filter
        dump_detailed_stats: true
        dump_logical_find: default
        enable: true
        fh_dir_retry_interval: 100
        fh_node_retry_interval: 100
        ignore_ctime_enabled: true
        is_secure_control_connection_enabled: true
        offset_map_enable: true
        per_qtree_exclude_enable: true
        preferred_interface_role: node_mgmt,intercluster
        restore_vm_cache_size: 1000
        secondary_debug_filter: filter
        tcpnodelay: true
        tcpwinsize: 10000
        username: user
        password: pass
        https: False
'''

RETURN = '''
'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils
from ansible.module_utils.netapp_module import NetAppModule

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPNdmp(object):
    '''
    modify vserver cifs security
    '''
    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.modifiable_options = dict(
            abort_on_disk_error=dict(required=False, type='bool'),
            authtype=dict(required=False, type='list'),
            backup_log_enable=dict(required=False, type='bool'),
            data_port_range=dict(required=False, type='str'),
            debug_enable=dict(required=False, type='bool'),
            debug_filter=dict(required=False, type='str'),
            dump_detailed_stats=dict(required=False, type='bool'),
            dump_logical_find=dict(required=False, type='str'),
            enable=dict(required=False, type='bool'),
            fh_dir_retry_interval=dict(required=False, type='int'),
            fh_node_retry_interval=dict(required=False, type='int'),
            ignore_ctime_enabled=dict(required=False, type='bool'),
            is_secure_control_connection_enabled=dict(required=False, type='bool'),
            offset_map_enable=dict(required=False, type='bool'),
            per_qtree_exclude_enable=dict(required=False, type='bool'),
            preferred_interface_role=dict(required=False, type='list'),
            restore_vm_cache_size=dict(required=False, type='int'),
            secondary_debug_filter=dict(required=False, type='str'),
            tcpnodelay=dict(required=False, type='bool'),
            tcpwinsize=dict(required=False, type='int')
        )
        self.argument_spec.update(dict(
            vserver=dict(required=True, type='str')
        ))

        self.argument_spec.update(self.modifiable_options)

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.parameters['vserver'])

    def ndmp_get_iter(self):
        """
        get current vserver ndmp attributes.
        :return: a dict of ndmp attributes.
        """
        ndmp_get = netapp_utils.zapi.NaElement('ndmp-vserver-attributes-get-iter')
        query = netapp_utils.zapi.NaElement('query')
        ndmp_info = netapp_utils.zapi.NaElement('ndmp-vserver-attributes-info')
        ndmp_info.add_new_child('vserver', self.parameters['vserver'])
        query.add_child_elem(ndmp_info)
        ndmp_get.add_child_elem(query)
        ndmp_details = dict()
        try:
            result = self.server.invoke_successfully(ndmp_get, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error fetching ndmp from %s: %s'
                                      % (self.parameters['vserver'], to_native(error)),
                                  exception=traceback.format_exc())

        if result.get_child_by_name('num-records') and int(result.get_child_content('num-records')) > 0:
            ndmp_attributes = result.get_child_by_name('attributes-list').get_child_by_name('ndmp-vserver-attributes-info')
            self.get_ndmp_details(ndmp_details, ndmp_attributes)
        return ndmp_details

    def get_ndmp_details(self, ndmp_details, ndmp_attributes):
        """
        :param ndmp_details: a dict of current ndmp.
        :param ndmp_attributes: ndmp returned from api call in xml format.
        :return: None
        """
        for option in self.modifiable_options.keys():
            option_type = self.modifiable_options[option]['type']
            if option_type == 'bool':
                ndmp_details[option] = self.str_to_bool(ndmp_attributes.get_child_content(self.attribute_to_name(option)))
            elif option_type == 'int':
                ndmp_details[option] = int(ndmp_attributes.get_child_content(self.attribute_to_name(option)))
            elif option_type == 'list':
                child_list = ndmp_attributes.get_child_by_name(self.attribute_to_name(option))
                values = [child.get_content() for child in child_list.get_children()]
                ndmp_details[option] = values
            else:
                ndmp_details[option] = ndmp_attributes.get_child_content(self.attribute_to_name(option))

    def modify_ndmp(self, modify):
        """
        :param modify: A list of attributes to modify
        :return: None
        """
        ndmp_modify = netapp_utils.zapi.NaElement('ndmp-vserver-attributes-modify')
        for attribute in modify:
            if attribute == 'authtype':
                authtypes = netapp_utils.zapi.NaElement('authtype')
                types = self.parameters['authtype']
                for authtype in types:
                    authtypes.add_new_child('ndmpd-authtypes', authtype)
                ndmp_modify.add_child_elem(authtypes)
            elif attribute == 'preferred_interface_role':
                preferred_interface_roles = netapp_utils.zapi.NaElement('preferred-interface-role')
                roles = self.parameters['preferred_interface_role']
                for role in roles:
                    preferred_interface_roles.add_new_child('netport-role', role)
                ndmp_modify.add_child_elem(preferred_interface_roles)
            else:
                ndmp_modify.add_new_child(self.attribute_to_name(attribute), str(self.parameters[attribute]))
        try:
            self.server.invoke_successfully(ndmp_modify, enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error modifying ndmp on %s: %s'
                                  % (self.parameters['vserver'], to_native(e)),
                                  exception=traceback.format_exc())

    @staticmethod
    def attribute_to_name(attribute):
        return str.replace(attribute, '_', '-')

    @staticmethod
    def str_to_bool(s):
        if s == 'true':
            return True
        else:
            return False

    def apply(self):
        """Call modify operations."""
        self.asup_log_for_cserver("na_ontap_ndmp")
        current = self.ndmp_get_iter()
        modify = self.na_helper.get_modified_attributes(current, self.parameters)
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if modify:
                    self.modify_ndmp(modify)
        self.module.exit_json(changed=self.na_helper.changed)

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


def main():
    obj = NetAppONTAPNdmp()
    obj.apply()


if __name__ == '__main__':
    main()
