#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = """
module: na_ontap_nfs
short_description: NetApp ONTAP NFS status
extends_documentation_fragment:
    - netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
description:
- Enable or disable NFS on ONTAP
options:
  state:
    description:
    - Whether NFS should exist or not.
    choices: ['present', 'absent']
    default: present
  service_state:
    description:
    - Whether the specified NFS should be enabled or disabled. Creates NFS service if does not exist.
    choices: ['started', 'stopped']
  vserver:
    description:
    - Name of the vserver to use.
    required: true
  nfsv3:
    description:
    - status of NFSv3.
    choices: ['enabled', 'disabled']
  nfsv3_fsid_change:
    description:
    - status of if NFSv3 clients see change in FSID as they traverse filesystems.
    choices: ['enabled', 'disabled']
    version_added: '2.7'
  nfsv4:
    description:
    - status of NFSv4.
    choices: ['enabled', 'disabled']
  nfsv41:
    description:
    - status of NFSv41.
    aliases: ['nfsv4.1']
    choices: ['enabled', 'disabled']
  vstorage_state:
    description:
    - status of vstorage_state.
    choices: ['enabled', 'disabled']
  nfsv4_id_domain:
    description:
    - Name of the nfsv4_id_domain to use.
  nfsv40_acl:
    description:
    - status of NFS v4.0 ACL feature
    choices: ['enabled', 'disabled']
    version_added: '2.7'
  nfsv40_read_delegation:
    description:
    - status for NFS v4.0 read delegation feature.
    choices: ['enabled', 'disabled']
    version_added: '2.7'
  nfsv40_write_delegation:
    description:
    - status for NFS v4.0 write delegation feature.
    choices: ['enabled', 'disabled']
    version_added: '2.7'
  nfsv41_acl:
    description:
    - status of NFS v4.1 ACL feature
    choices: ['enabled', 'disabled']
    version_added: '2.7'
  nfsv41_read_delegation:
    description:
    - status for NFS v4.1 read delegation feature.
    choices: ['enabled', 'disabled']
    version_added: '2.7'
  nfsv41_write_delegation:
    description:
    - status for NFS v4.1 write delegation feature.
    choices: ['enabled', 'disabled']
    version_added: '2.7'
  tcp:
    description:
    - Enable TCP (support from ONTAP 9.3 onward).
    choices: ['enabled', 'disabled']
  udp:
    description:
    - Enable UDP (support from ONTAP 9.3 onward).
    choices: ['enabled', 'disabled']
  showmount:
    description:
    - Whether SVM allows showmount
    choices: ['enabled', 'disabled']
    version_added: '2.7'
  tcp_max_xfer_size:
    description:
    - TCP Maximum Transfer Size (bytes). The default value is 65536.
    version_added: '2.8'
    type: int

"""

EXAMPLES = """
    - name: change nfs status
      na_ontap_nfs:
        state: present
        service_state: stopped
        vserver: vs_hack
        nfsv3: disabled
        nfsv4: disabled
        nfsv41: enabled
        tcp: disabled
        udp: disabled
        vstorage_state: disabled
        nfsv4_id_domain: example.com
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"
"""

RETURN = """
"""
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils


HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppONTAPNFS(object):
    """ object initialize and class methods """
    def __init__(self):

        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, type='str', choices=['present', 'absent'], default='present'),
            service_state=dict(required=False, choices=['started', 'stopped']),
            vserver=dict(required=True, type='str'),
            nfsv3=dict(required=False, default=None, choices=['enabled', 'disabled']),
            nfsv3_fsid_change=dict(required=False, default=None, choices=['enabled', 'disabled']),
            nfsv4=dict(required=False, default=None, choices=['enabled', 'disabled']),
            nfsv41=dict(required=False, default=None, choices=['enabled', 'disabled'], aliases=['nfsv4.1']),
            vstorage_state=dict(required=False, default=None, choices=['enabled', 'disabled']),
            tcp=dict(required=False, default=None, choices=['enabled', 'disabled']),
            udp=dict(required=False, default=None, choices=['enabled', 'disabled']),
            nfsv4_id_domain=dict(required=False, type='str', default=None),
            nfsv40_acl=dict(required=False, default=None, choices=['enabled', 'disabled']),
            nfsv40_read_delegation=dict(required=False, default=None, choices=['enabled', 'disabled']),
            nfsv40_write_delegation=dict(required=False, default=None, choices=['enabled', 'disabled']),
            nfsv41_acl=dict(required=False, default=None, choices=['enabled', 'disabled']),
            nfsv41_read_delegation=dict(required=False, default=None, choices=['enabled', 'disabled']),
            nfsv41_write_delegation=dict(required=False, default=None, choices=['enabled', 'disabled']),
            showmount=dict(required=False, default=None, choices=['enabled', 'disabled']),
            tcp_max_xfer_size=dict(required=False, default=None, type='int')
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        parameters = self.module.params

        # set up service_state variables
        self.state = parameters['state']
        self.service_state = parameters['service_state']
        self.vserver = parameters['vserver']
        self.nfsv3 = parameters['nfsv3']
        self.nfsv3_fsid_change = parameters['nfsv3_fsid_change']
        self.nfsv4 = parameters['nfsv4']
        self.nfsv41 = parameters['nfsv41']
        self.vstorage_state = parameters['vstorage_state']
        self.nfsv4_id_domain = parameters['nfsv4_id_domain']
        self.udp = parameters['udp']
        self.tcp = parameters['tcp']
        self.nfsv40_acl = parameters['nfsv40_acl']
        self.nfsv40_read_delegation = parameters['nfsv40_read_delegation']
        self.nfsv40_write_delegation = parameters['nfsv40_write_delegation']
        self.nfsv41_acl = parameters['nfsv41_acl']
        self.nfsv41_read_delegation = parameters['nfsv41_read_delegation']
        self.nfsv41_write_delegation = parameters['nfsv41_write_delegation']
        self.showmount = parameters['showmount']
        self.tcp_max_xfer_size = parameters['tcp_max_xfer_size']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=self.vserver)

    def get_nfs_service(self):
        """
        Return details about nfs
        :param:
            name : name of the vserver
        :return: Details about nfs. None if not found.
        :rtype: dict
        """
        nfs_get_iter = netapp_utils.zapi.NaElement('nfs-service-get-iter')
        nfs_info = netapp_utils.zapi.NaElement('nfs-info')
        nfs_info.add_new_child('vserver', self.vserver)
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(nfs_info)
        nfs_get_iter.add_child_elem(query)
        result = self.server.invoke_successfully(nfs_get_iter, True)
        nfs_details = None
        # check if job exists
        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) >= 1:
            attributes_list = result.get_child_by_name('attributes-list').get_child_by_name('nfs-info')
            is_nfsv3_enabled = attributes_list.get_child_content('is-nfsv3-enabled')
            is_nfsv3_fsid_change_enabled = attributes_list.get_child_content('is-nfsv3-fsid-change-enabled')
            is_nfsv40_enabled = attributes_list.get_child_content('is-nfsv40-enabled')
            is_nfsv41_enabled = attributes_list.get_child_content('is-nfsv41-enabled')
            is_vstorage_enabled = attributes_list.get_child_content('is-vstorage-enabled')
            nfsv4_id_domain_value = attributes_list.get_child_content('nfsv4-id-domain')
            is_tcp_enabled = attributes_list.get_child_content('is-tcp-enabled')
            is_udp_enabled = attributes_list.get_child_content('is-udp-enabled')
            is_nfsv40_acl_enabled = attributes_list.get_child_content('is-nfsv40-acl-enabled')
            is_nfsv40_write_delegation_enabled = attributes_list.get_child_content('is-nfsv40-write-delegation-enabled')
            is_nfsv40_read_delegation_enabled = attributes_list.get_child_content('is-nfsv40-read-delegation-enabled')
            is_nfsv41_acl_enabled = attributes_list.get_child_content('is-nfsv41-acl-enabled')
            is_nfsv41_write_delegation_enabled = attributes_list.get_child_content('is-nfsv41-write-delegation-enabled')
            is_nfsv41_read_delegation_enabled = attributes_list.get_child_content('is-nfsv41-read-delegation-enabled')
            is_showmount_enabled = attributes_list.get_child_content('showmount')
            tcp_max_xfer_size = attributes_list.get_child_content('tcp-max-xfer-size')
            nfs_details = {
                'is_nfsv3_enabled': is_nfsv3_enabled,
                'is_nfsv3_fsid_change_enabled': is_nfsv3_fsid_change_enabled,
                'is_nfsv40_enabled': is_nfsv40_enabled,
                'is_nfsv41_enabled': is_nfsv41_enabled,
                'is_vstorage_enabled': is_vstorage_enabled,
                'nfsv4_id_domain': nfsv4_id_domain_value,
                'is_tcp_enabled': is_tcp_enabled,
                'is_udp_enabled': is_udp_enabled,
                'is_nfsv40_acl_enabled': is_nfsv40_acl_enabled,
                'is_nfsv40_write_delegation_enabled': is_nfsv40_write_delegation_enabled,
                'is_nfsv40_read_delegation_enabled': is_nfsv40_read_delegation_enabled,
                'is_nfsv41_acl_enabled': is_nfsv41_acl_enabled,
                'is_nfsv41_write_delegation_enabled': is_nfsv41_write_delegation_enabled,
                'is_nfsv41_read_delegation_enabled': is_nfsv41_read_delegation_enabled,
                'is_showmount_enabled': is_showmount_enabled,
                'tcp_max_xfer_size': tcp_max_xfer_size
            }
        return nfs_details

    def get_nfs_status(self):
        """
        Return status of nfs
        :param:
            name : Name of the vserver
        :return: status of nfs. None if not found.
        :rtype: bool
        """
        nfs_status = netapp_utils.zapi.NaElement('nfs-status')
        result = self.server.invoke_successfully(nfs_status, True)
        return_value = result.get_child_content('is-enabled')

        return return_value

    def enable_nfs(self):
        """
        enable nfs (online). If the NFS service was not explicitly created,
        this API will create one with default options.
        """
        nfs_enable = netapp_utils.zapi.NaElement.create_node_with_children('nfs-enable')
        try:
            self.server.invoke_successfully(nfs_enable,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error changing the service_state of nfs %s to %s: %s' %
                                  (self.vserver, self.service_state, to_native(error)),
                                  exception=traceback.format_exc())

    def disable_nfs(self):
        """
        disable nfs (offline).
        """
        nfs_disable = netapp_utils.zapi.NaElement.create_node_with_children('nfs-disable')
        try:
            self.server.invoke_successfully(nfs_disable,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error changing the service_state of nfs %s to %s: %s' %
                                  (self.vserver, self.service_state, to_native(error)),
                                  exception=traceback.format_exc())

    def modify_nfs(self):
        """
        modify nfs service
        """
        nfs_modify = netapp_utils.zapi.NaElement('nfs-service-modify')
        if self.nfsv3 == 'enabled':
            nfs_modify.add_new_child('is-nfsv3-enabled', 'true')
        elif self.nfsv3 == 'disabled':
            nfs_modify.add_new_child('is-nfsv3-enabled', 'false')
        if self.nfsv3_fsid_change == 'enabled':
            nfs_modify.add_new_child('is-nfsv3-fsid-change-enabled', 'true')
        elif self.nfsv3_fsid_change == 'disabled':
            nfs_modify.add_new_child('is-nfsv3-fsid-change-enabled', 'false')
        if self.nfsv4 == 'enabled':
            nfs_modify.add_new_child('is-nfsv40-enabled', 'true')
        elif self.nfsv4 == 'disabled':
            nfs_modify.add_new_child('is-nfsv40-enabled', 'false')
        if self.nfsv41 == 'enabled':
            nfs_modify.add_new_child('is-nfsv41-enabled', 'true')
        elif self.nfsv41 == 'disabled':
            nfs_modify.add_new_child('is-nfsv41-enabled', 'false')
        if self.vstorage_state == 'enabled':
            nfs_modify.add_new_child('is-vstorage-enabled', 'true')
        elif self.vstorage_state == 'disabled':
            nfs_modify.add_new_child('is-vstorage-enabled', 'false')
        if self.tcp == 'enabled':
            nfs_modify.add_new_child('is-tcp-enabled', 'true')
        elif self.tcp == 'disabled':
            nfs_modify.add_new_child('is-tcp-enabled', 'false')
        if self.udp == 'enabled':
            nfs_modify.add_new_child('is-udp-enabled', 'true')
        elif self.udp == 'disabled':
            nfs_modify.add_new_child('is-udp-enabled', 'false')
        if self.nfsv40_acl == 'enabled':
            nfs_modify.add_new_child('is-nfsv40-acl-enabled', 'true')
        elif self.nfsv40_acl == 'disabled':
            nfs_modify.add_new_child('is-nfsv40-acl-enabled', 'false')
        if self.nfsv40_read_delegation == 'enabled':
            nfs_modify.add_new_child('is-nfsv40-read-delegation-enabled', 'true')
        elif self.nfsv40_read_delegation == 'disabled':
            nfs_modify.add_new_child('is-nfsv40-read-delegation-enabled', 'false')
        if self.nfsv40_write_delegation == 'enabled':
            nfs_modify.add_new_child('is-nfsv40-write-delegation-enabled', 'true')
        elif self.nfsv40_write_delegation == 'disabled':
            nfs_modify.add_new_child('is-nfsv40-write-delegation-enabled', 'false')
        if self.nfsv41_acl == 'enabled':
            nfs_modify.add_new_child('is-nfsv41-acl-enabled', 'true')
        elif self.nfsv41_acl == 'disabled':
            nfs_modify.add_new_child('is-nfsv41-acl-enabled', 'false')
        if self.nfsv41_read_delegation == 'enabled':
            nfs_modify.add_new_child('is-nfsv41-read-delegation-enabled', 'true')
        elif self.nfsv41_read_delegation == 'disabled':
            nfs_modify.add_new_child('is-nfsv41-read-delegation-enabled', 'false')
        if self.nfsv41_write_delegation == 'enabled':
            nfs_modify.add_new_child('is-nfsv41-write-delegation-enabled', 'true')
        elif self.nfsv41_write_delegation == 'disabled':
            nfs_modify.add_new_child('is-nfsv41-write-delegation-enabled', 'false')
        if self.showmount == 'enabled':
            nfs_modify.add_new_child('showmount', 'true')
        elif self.showmount == 'disabled':
            nfs_modify.add_new_child('showmount', 'false')
        if self.tcp_max_xfer_size is not None:
            nfs_modify.add_new_child('tcp-max-xfer-size', str(self.tcp_max_xfer_size))
        try:
            self.server.invoke_successfully(nfs_modify,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error modifying nfs: %s'
                                  % (to_native(error)),
                                  exception=traceback.format_exc())

    def modify_nfsv4_id_domain(self):
        """
        modify nfs service
        """
        nfsv4_id_domain_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'nfs-service-modify', **{'nfsv4-id-domain': self.nfsv4_id_domain})
        if nfsv4_id_domain_modify is not None:
            try:
                self.server.invoke_successfully(nfsv4_id_domain_modify,
                                                enable_tunneling=True)
            except netapp_utils.zapi.NaApiError as error:
                self.module.fail_json(msg='Error modifying nfs: %s'
                                      % (to_native(error)),
                                      exception=traceback.format_exc())

    def delete_nfs(self):
        """
        delete nfs service.
        """
        nfs_delete = netapp_utils.zapi.NaElement.create_node_with_children('nfs-service-destroy')
        try:
            self.server.invoke_successfully(nfs_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as error:
            self.module.fail_json(msg='Error deleting nfs: %s' %
                                  (to_native(error)),
                                  exception=traceback.format_exc())

    def apply(self):
        """Apply action to nfs"""
        changed = False
        nfs_exists = False
        modify_nfs = False
        enable_nfs = False
        disable_nfs = False
        netapp_utils.ems_log_event("na_ontap_nfs", self.server)
        nfs_enabled = self.get_nfs_status()
        nfs_service_details = self.get_nfs_service()
        is_nfsv4_id_domain_changed = False

        def state_changed(expected, current):
            if expected == "enabled" and current == "true":
                return False
            if expected == "disabled" and current == "false":
                return False
            return True

        def is_modify_needed():
            if (((self.nfsv3 is not None) and state_changed(self.nfsv3, nfs_service_details['is_nfsv3_enabled'])) or
                ((self.nfsv3_fsid_change is not None) and state_changed(self.nfsv3_fsid_change, nfs_service_details['is_nfsv3_fsid_change_enabled'])) or
                ((self.nfsv4 is not None) and state_changed(self.nfsv4, nfs_service_details['is_nfsv40_enabled'])) or
                ((self.nfsv41 is not None) and state_changed(self.nfsv41, nfs_service_details['is_nfsv41_enabled'])) or
                ((self.tcp is not None) and state_changed(self.tcp, nfs_service_details['is_tcp_enabled'])) or
                ((self.udp is not None) and state_changed(self.udp, nfs_service_details['is_udp_enabled'])) or
                ((self.nfsv40_acl is not None) and state_changed(self.nfsv40_acl, nfs_service_details['is_nfsv40_acl_enabled'])) or
                ((self.nfsv40_write_delegation is not None) and state_changed(self.nfsv40_write_delegation,
                                                                              nfs_service_details['is_nfsv40_write_delegation_enabled'])) or
                ((self.nfsv40_write_delegation is not None) and state_changed(self.nfsv40_write_delegation,
                                                                              nfs_service_details['is_nfsv40_write_delegation_enabled'])) or
                ((self.showmount is not None) and state_changed(self.showmount, nfs_service_details['is_showmount_enabled'])) or
                    ((self.vstorage_state is not None) and state_changed(self.vstorage_state, nfs_service_details['is_vstorage_enabled'])) or
                    ((self.tcp_max_xfer_size is not None) and int(self.tcp_max_xfer_size) != int(nfs_service_details['tcp_max_xfer_size']))):
                return True
            return False

        def is_domain_changed():
            if (self.nfsv4_id_domain is not None) and (self.nfsv4_id_domain != nfs_service_details['nfsv4_id_domain']):
                return True
            return False

        if nfs_service_details:
            nfs_exists = True
            if self.state == 'absent':  # delete
                changed = True
            elif self.state == 'present':  # modify
                if self.service_state == 'started' and nfs_enabled == 'false':
                    enable_nfs = True
                    changed = True
                elif self.service_state == 'stopped' and nfs_enabled == 'true':
                    disable_nfs = True
                    changed = True
                if is_modify_needed():
                    modify_nfs = True
                    changed = True
                if is_domain_changed():
                    is_nfsv4_id_domain_changed = True
                    changed = True
        else:
            if self.state == 'present':  # create
                changed = True
        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':  # execute create
                    if not nfs_exists:
                        self.enable_nfs()
                        nfs_service_details = self.get_nfs_service()
                        if self.service_state == 'stopped':
                            self.disable_nfs()
                        if is_modify_needed():
                            self.modify_nfs()
                        if is_domain_changed():
                            self.modify_nfsv4_id_domain()
                    else:
                        if enable_nfs:
                            self.enable_nfs()
                        elif disable_nfs:
                            self.disable_nfs()
                        if modify_nfs:
                            self.modify_nfs()
                        if is_nfsv4_id_domain_changed:
                            self.modify_nfsv4_id_domain()
                elif self.state == 'absent':  # execute delete
                    self.delete_nfs()

        self.module.exit_json(changed=changed)


def main():
    """ Create object and call apply """
    obj = NetAppONTAPNFS()
    obj.apply()


if __name__ == '__main__':
    main()
