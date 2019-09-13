#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
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
module: ovirt_storage_domain
short_description: Module to manage storage domains in oVirt/RHV
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage storage domains in oVirt/RHV"
options:
    id:
        description:
            - "Id of the storage domain to be imported."
        version_added: "2.4"
    name:
        description:
            - "Name of the storage domain to manage. (Not required when state is I(imported))"
    state:
        description:
            - "Should the storage domain be present/absent/maintenance/unattached/imported/update_ovf_store"
            - "I(imported) is supported since version 2.4."
            - "I(update_ovf_store) is supported since version 2.5, currently if C(wait) is (true), we don't wait for update."
        choices: ['present', 'absent', 'maintenance', 'unattached', 'imported', 'update_ovf_store']
        default: present
    description:
        description:
            - "Description of the storage domain."
    comment:
        description:
            - "Comment of the storage domain."
    data_center:
        description:
            - "Data center name where storage domain should be attached."
            - "This parameter isn't idempotent, it's not possible to change data center of storage domain."
    domain_function:
        description:
            - "Function of the storage domain."
            - "This parameter isn't idempotent, it's not possible to change domain function of storage domain."
        choices: ['data', 'iso', 'export']
        default: 'data'
        aliases:  ['type']
    host:
        description:
            - "Host to be used to mount storage."
    localfs:
        description:
            - "Dictionary with values for localfs storage type:"
            - "Note that these parameters are not idempotent."
        suboptions:
            path:
                description:
                    - "Path of the mount point. E.g.: /path/to/my/data"
        version_added: "2.4"
    nfs:
        description:
            - "Dictionary with values for NFS storage type:"
            - "Note that these parameters are not idempotent."
        suboptions:
            address:
                description:
                    - "Address of the NFS server. E.g.: myserver.mydomain.com"
            path:
                description:
                    - "Path of the mount point. E.g.: /path/to/my/data"
            version:
                description:
                    - "NFS version. One of: I(auto), I(v3), I(v4) or I(v4_1)."
            timeout:
                description:
                    - "The time in tenths of a second to wait for a response before retrying NFS requests. Range 0 to 65535."
            retrans:
                description:
                    - "The number of times to retry a request before attempting further recovery actions. Range 0 to 65535."
            mount_options:
                description:
                    - "Option which will be passed when mounting storage."
    iscsi:
        description:
            - "Dictionary with values for iSCSI storage type:"
            - "Note that these parameters are not idempotent."
        suboptions:
            address:
                description:
                    - Address of the iSCSI storage server.
            port:
                description:
                    - Port of the iSCSI storage server.
            target:
                description:
                    - The target IQN for the storage device.
            lun_id:
                description:
                    - LUN id(s).
            username:
                description:
                    - A CHAP user name for logging into a target.
            password:
                description:
                    - A CHAP password for logging into a target.
            override_luns:
                description:
                    - If I(True) ISCSI storage domain luns will be overridden before adding.
                type: bool
            target_lun_map:
                description:
                    - List of dictionary containing targets and LUNs.
                version_added: 2.5
    posixfs:
        description:
            - "Dictionary with values for PosixFS storage type:"
            - "Note that these parameters are not idempotent."
        suboptions:
            path:
                description:
                    - "Path of the mount point. E.g.: /path/to/my/data"
            vfs_type:
                description:
                    - Virtual File System type.
            mount_options:
                description:
                    - Option which will be passed when mounting storage.
    glusterfs:
        description:
            - "Dictionary with values for GlusterFS storage type:"
            - "Note that these parameters are not idempotent."
        suboptions:
            address:
                description:
                    - "Address of the Gluster server. E.g.: myserver.mydomain.com"
            path:
                description:
                    - "Path of the mount point. E.g.: /path/to/my/data"
            mount_options:
                description:
                    - Option which will be passed when mounting storage.
    fcp:
        description:
            - "Dictionary with values for fibre channel storage type:"
            - "Note that these parameters are not idempotent."
        suboptions:
            lun_id:
                description:
                    - LUN id.
            override_luns:
                description:
                    - If I(True) FCP storage domain LUNs will be overridden before adding.
                type: bool
    wipe_after_delete:
        description:
            - "Boolean flag which indicates whether the storage domain should wipe the data after delete."
        type: bool
        version_added: "2.5"
    backup:
        description:
            - "Boolean flag which indicates whether the storage domain is configured as backup or not."
        type: bool
        version_added: "2.5"
    critical_space_action_blocker:
        description:
            - "Indicates the minimal free space the storage domain should contain in percentages."
        version_added: "2.5"
    warning_low_space:
        description:
            - "Indicates the minimum percentage of a free space in a storage domain to present a warning."
        version_added: "2.5"
    destroy:
        description:
            - "Logical remove of the storage domain. If I(true) retains the storage domain's data for import."
            - "This parameter is relevant only when C(state) is I(absent)."
        type: bool
    format:
        description:
            - "If I(True) storage domain will be formatted after removing it from oVirt/RHV."
            - "This parameter is relevant only when C(state) is I(absent)."
        type: bool
    discard_after_delete:
        description:
            - "If I(True) storage domain blocks will be discarded upon deletion. Enabled by default."
            - "This parameter is relevant only for block based storage domains."
        type: bool
        version_added: 2.5
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Add data NFS storage domain
- ovirt_storage_domain:
    name: data_nfs
    host: myhost
    data_center: mydatacenter
    nfs:
      address: 10.34.63.199
      path: /path/data

# Add data NFS storage domain with id for data center
- ovirt_storage_domain:
    name: data_nfs
    host: myhost
    data_center: 11111
    nfs:
      address: 10.34.63.199
      path: /path/data
      mount_options: noexec,nosuid

# Add data localfs storage domain
- ovirt_storage_domain:
    name: data_localfs
    host: myhost
    data_center: mydatacenter
    localfs:
      path: /path/to/data

# Add data iSCSI storage domain:
- ovirt_storage_domain:
    name: data_iscsi
    host: myhost
    data_center: mydatacenter
    iscsi:
      target: iqn.2016-08-09.domain-01:nickname
      lun_id:
       - 1IET_000d0001
       - 1IET_000d0002
      address: 10.34.63.204
    discard_after_delete: True
    backup: False
    critical_space_action_blocker: 5
    warning_low_space: 10

# Since Ansible 2.5 you can specify multiple targets for storage domain,
# Add data iSCSI storage domain with multiple targets:
- ovirt_storage_domain:
    name: data_iscsi
    host: myhost
    data_center: mydatacenter
    iscsi:
      target_lun_map:
        - target: iqn.2016-08-09.domain-01:nickname
          lun_id: 1IET_000d0001
        - target: iqn.2016-08-09.domain-02:nickname
          lun_id: 1IET_000d0002
      address: 10.34.63.204
    discard_after_delete: True

# Add data glusterfs storage domain
-  ovirt_storage_domain:
    name: glusterfs_1
    host: myhost
    data_center: mydatacenter
    glusterfs:
      address: 10.10.10.10
      path: /path/data

# Create export NFS storage domain:
- ovirt_storage_domain:
    name: myexportdomain
    domain_function: export
    host: myhost
    data_center: mydatacenter
    nfs:
      address: 10.34.63.199
      path: /path/export
    wipe_after_delete: False
    backup: True
    critical_space_action_blocker: 2
    warning_low_space: 5

# Import export NFS storage domain:
- ovirt_storage_domain:
    state: imported
    domain_function: export
    host: myhost
    data_center: mydatacenter
    nfs:
      address: 10.34.63.199
      path: /path/export

# Import FCP storage domain:
- ovirt_storage_domain:
    state: imported
    name: data_fcp
    host: myhost
    data_center: mydatacenter
    fcp: {}

# Update OVF_STORE:
- ovirt_storage_domain:
    state: update_ovf_store
    name: domain

# Create ISO NFS storage domain
- ovirt_storage_domain:
    name: myiso
    domain_function: iso
    host: myhost
    data_center: mydatacenter
    nfs:
      address: 10.34.63.199
      path: /path/iso

# Remove storage domain
- ovirt_storage_domain:
    state: absent
    name: mystorage_domain
    format: true
'''

RETURN = '''
id:
    description: ID of the storage domain which is managed
    returned: On success if storage domain is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
storage_domain:
    description: "Dictionary of all the storage domain attributes. Storage domain attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/storage_domain."
    returned: On success if storage domain is found.
    type: dict
'''

try:
    import ovirtsdk4.types as otypes

    from ovirtsdk4.types import StorageDomainStatus as sdstate
    from ovirtsdk4.types import HostStatus as hoststate
    from ovirtsdk4.types import DataCenterStatus as dcstatus
except ImportError:
    pass

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    BaseModule,
    check_sdk,
    create_connection,
    equal,
    get_entity,
    get_id_by_name,
    OvirtRetry,
    ovirt_full_argument_spec,
    search_by_name,
    search_by_attributes,
    wait,
)


class StorageDomainModule(BaseModule):

    def _get_storage_type(self):
        for sd_type in ['nfs', 'iscsi', 'posixfs', 'glusterfs', 'fcp', 'localfs']:
            if self.param(sd_type) is not None:
                return sd_type

    def _get_storage(self):
        for sd_type in ['nfs', 'iscsi', 'posixfs', 'glusterfs', 'fcp', 'localfs']:
            if self.param(sd_type) is not None:
                return self.param(sd_type)

    def _login(self, storage_type, storage):
        if storage_type == 'iscsi':
            hosts_service = self._connection.system_service().hosts_service()
            host_id = get_id_by_name(hosts_service, self.param('host'))
            if storage.get('target'):
                hosts_service.host_service(host_id).iscsi_login(
                    iscsi=otypes.IscsiDetails(
                        username=storage.get('username'),
                        password=storage.get('password'),
                        address=storage.get('address'),
                        target=storage.get('target'),
                    ),
                )
            elif storage.get('target_lun_map'):
                for target in [m['target'] for m in storage.get('target_lun_map')]:
                    hosts_service.host_service(host_id).iscsi_login(
                        iscsi=otypes.IscsiDetails(
                            username=storage.get('username'),
                            password=storage.get('password'),
                            address=storage.get('address'),
                            target=target,
                        ),
                    )

    def __target_lun_map(self, storage):
        if storage.get('target'):
            lun_ids = storage.get('lun_id') if isinstance(storage.get('lun_id'), list) else [(storage.get('lun_id'))]
            return [(lun_id, storage.get('target')) for lun_id in lun_ids]
        elif storage.get('target_lun_map'):
            return [(target_map.get('lun_id'), target_map.get('target')) for target_map in storage.get('target_lun_map')]
        else:
            lun_ids = storage.get('lun_id') if isinstance(storage.get('lun_id'), list) else [(storage.get('lun_id'))]
            return [(lun_id, None) for lun_id in lun_ids]

    def build_entity(self):
        storage_type = self._get_storage_type()
        storage = self._get_storage()
        self._login(storage_type, storage)

        return otypes.StorageDomain(
            name=self.param('name'),
            description=self.param('description'),
            comment=self.param('comment'),
            wipe_after_delete=self.param('wipe_after_delete'),
            backup=self.param('backup'),
            critical_space_action_blocker=self.param('critical_space_action_blocker'),
            warning_low_space_indicator=self.param('warning_low_space'),
            import_=True if self.param('state') == 'imported' else None,
            id=self.param('id') if self.param('state') == 'imported' else None,
            type=otypes.StorageDomainType(self.param('domain_function')),
            host=otypes.Host(name=self.param('host')),
            discard_after_delete=self.param('discard_after_delete'),
            storage=otypes.HostStorage(
                type=otypes.StorageType(storage_type),
                logical_units=[
                    otypes.LogicalUnit(
                        id=lun_id,
                        address=storage.get('address'),
                        port=int(storage.get('port', 3260)),
                        target=target,
                        username=storage.get('username'),
                        password=storage.get('password'),
                    ) for lun_id, target in self.__target_lun_map(storage)
                ] if storage_type in ['iscsi', 'fcp'] else None,
                override_luns=storage.get('override_luns'),
                mount_options=storage.get('mount_options'),
                vfs_type=(
                    'glusterfs'
                    if storage_type in ['glusterfs'] else storage.get('vfs_type')
                ),
                address=storage.get('address'),
                path=storage.get('path'),
                nfs_retrans=storage.get('retrans'),
                nfs_timeo=storage.get('timeout'),
                nfs_version=otypes.NfsVersion(
                    storage.get('version')
                ) if storage.get('version') else None,
            ) if storage_type is not None else None
        )

    def _find_attached_datacenter_name(self, sd_name):
        """
        Finds the name of the datacenter that a given
        storage domain is attached to.

        Args:
            sd_name (str): Storage Domain name

        Returns:
            str: Data Center name

        Raises:
            Exception: In case storage domain in not attached to
                an active Datacenter
        """
        dcs_service = self._connection.system_service().data_centers_service()
        dc = search_by_attributes(dcs_service, storage=sd_name)
        if dc is None:
            raise Exception(
                "Can't bring storage to state `%s`, because it seems that"
                "it is not attached to any datacenter"
                % self.param('state')
            )
        else:
            if dc.status == dcstatus.UP:
                return dc.name
            else:
                raise Exception(
                    "Can't bring storage to state `%s`, because Datacenter "
                    "%s is not UP" % (self.param('state'), dc.name)
                )

    def _attached_sds_service(self, dc_name):
        # Get data center object of the storage domain:
        dcs_service = self._connection.system_service().data_centers_service()

        # Search the data_center name, if it does not exist, try to search by guid.
        dc = search_by_name(dcs_service, dc_name)
        if dc is None:
            dc = get_entity(dcs_service.service(dc_name))
            if dc is None:
                return None

        dc_service = dcs_service.data_center_service(dc.id)
        return dc_service.storage_domains_service()

    def _attached_sd_service(self, storage_domain):
        dc_name = self.param('data_center')
        if not dc_name:
            # Find the DC, where the storage resides:
            dc_name = self._find_attached_datacenter_name(storage_domain.name)
        attached_sds_service = self._attached_sds_service(dc_name)
        attached_sd_service = attached_sds_service.storage_domain_service(storage_domain.id)
        return attached_sd_service

    def _maintenance(self, storage_domain):
        attached_sd_service = self._attached_sd_service(storage_domain)
        attached_sd = get_entity(attached_sd_service)

        if attached_sd and attached_sd.status != sdstate.MAINTENANCE:
            if not self._module.check_mode:
                attached_sd_service.deactivate()
            self.changed = True

            wait(
                service=attached_sd_service,
                condition=lambda sd: sd.status == sdstate.MAINTENANCE,
                wait=self.param('wait'),
                timeout=self.param('timeout'),
            )

    def _unattach(self, storage_domain):
        attached_sd_service = self._attached_sd_service(storage_domain)
        attached_sd = get_entity(attached_sd_service)

        if attached_sd and attached_sd.status == sdstate.MAINTENANCE:
            if not self._module.check_mode:
                # Detach the storage domain:
                attached_sd_service.remove()
            self.changed = True
            # Wait until storage domain is detached:
            wait(
                service=attached_sd_service,
                condition=lambda sd: sd is None,
                wait=self.param('wait'),
                timeout=self.param('timeout'),
            )

    def pre_remove(self, storage_domain):
        # In case the user chose to destroy the storage domain there is no need to
        # move it to maintenance or detach it, it should simply be removed from the DB.
        # Also if storage domain in already unattached skip this step.
        if storage_domain.status == sdstate.UNATTACHED or self.param('destroy'):
            return
        # Before removing storage domain we need to put it into maintenance state:
        self._maintenance(storage_domain)

        # Before removing storage domain we need to detach it from data center:
        self._unattach(storage_domain)

    def post_create_check(self, sd_id):
        storage_domain = self._service.service(sd_id).get()
        dc_name = self.param('data_center')
        if not dc_name:
            # Find the DC, where the storage resides:
            dc_name = self._find_attached_datacenter_name(storage_domain.name)
        self._service = self._attached_sds_service(dc_name)

        # If storage domain isn't attached, attach it:
        attached_sd_service = self._service.service(storage_domain.id)
        if get_entity(attached_sd_service) is None:
            self._service.add(
                otypes.StorageDomain(
                    id=storage_domain.id,
                ),
            )
            self.changed = True
            # Wait until storage domain is in maintenance:
            wait(
                service=attached_sd_service,
                condition=lambda sd: sd.status == sdstate.ACTIVE,
                wait=self.param('wait'),
                timeout=self.param('timeout'),
            )

    def unattached_pre_action(self, storage_domain):
        dc_name = self.param('data_center')
        if not dc_name:
            # Find the DC, where the storage resides:
            dc_name = self._find_attached_datacenter_name(storage_domain.name)
        self._service = self._attached_sds_service(storage_domain, dc_name)
        self._maintenance(self._service, storage_domain)

    def update_check(self, entity):
        return (
            equal(self.param('comment'), entity.comment) and
            equal(self.param('description'), entity.description) and
            equal(self.param('backup'), entity.backup) and
            equal(self.param('critical_space_action_blocker'), entity.critical_space_action_blocker) and
            equal(self.param('discard_after_delete'), entity.discard_after_delete) and
            equal(self.param('wipe_after_delete'), entity.wipe_after_delete) and
            equal(self.param('warning_low_space_indicator'), entity.warning_low_space_indicator)
        )


def failed_state(sd):
    return sd.status in [sdstate.UNKNOWN, sdstate.INACTIVE]


def control_state(sd_module):
    sd = sd_module.search_entity()
    if sd is None:
        return

    sd_service = sd_module._service.service(sd.id)

    # In the case of no status returned, it's an attached storage domain.
    # Redetermine the corresponding service and entity:
    if sd.status is None:
        sd_service = sd_module._attached_sd_service(sd)
        sd = get_entity(sd_service)

    if sd.status == sdstate.LOCKED:
        wait(
            service=sd_service,
            condition=lambda sd: sd.status != sdstate.LOCKED,
            fail_condition=failed_state,
        )

    if failed_state(sd):
        raise Exception("Not possible to manage storage domain '%s'." % sd.name)
    elif sd.status == sdstate.ACTIVATING:
        wait(
            service=sd_service,
            condition=lambda sd: sd.status == sdstate.ACTIVE,
            fail_condition=failed_state,
        )
    elif sd.status == sdstate.DETACHING:
        wait(
            service=sd_service,
            condition=lambda sd: sd.status == sdstate.UNATTACHED,
            fail_condition=failed_state,
        )
    elif sd.status == sdstate.PREPARING_FOR_MAINTENANCE:
        wait(
            service=sd_service,
            condition=lambda sd: sd.status == sdstate.MAINTENANCE,
            fail_condition=failed_state,
        )


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent', 'maintenance', 'unattached', 'imported', 'update_ovf_store'],
            default='present',
        ),
        id=dict(default=None),
        name=dict(default=None),
        description=dict(default=None),
        comment=dict(default=None),
        data_center=dict(default=None),
        domain_function=dict(choices=['data', 'iso', 'export'], default='data', aliases=['type']),
        host=dict(default=None),
        localfs=dict(default=None, type='dict'),
        nfs=dict(default=None, type='dict'),
        iscsi=dict(default=None, type='dict'),
        posixfs=dict(default=None, type='dict'),
        glusterfs=dict(default=None, type='dict'),
        fcp=dict(default=None, type='dict'),
        wipe_after_delete=dict(type='bool', default=None),
        backup=dict(type='bool', default=None),
        critical_space_action_blocker=dict(type='int', default=None),
        warning_low_space=dict(type='int', default=None),
        destroy=dict(type='bool', default=None),
        format=dict(type='bool', default=None),
        discard_after_delete=dict(type='bool', default=None)
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        storage_domains_service = connection.system_service().storage_domains_service()
        storage_domains_module = StorageDomainModule(
            connection=connection,
            module=module,
            service=storage_domains_service,
        )

        state = module.params['state']
        control_state(storage_domains_module)
        if state == 'absent':
            # Pick random available host when host parameter is missing
            host_param = module.params['host']
            if not host_param:
                host = search_by_attributes(connection.system_service().hosts_service(), status='up')
                if host is None:
                    raise Exception(
                        "Not possible to remove storage domain '%s' "
                        "because no host found with status `up`." % module.params['name']
                    )
                host_param = host.name
            ret = storage_domains_module.remove(
                destroy=module.params['destroy'],
                format=module.params['format'],
                host=host_param,
            )
        elif state == 'present' or state == 'imported':
            sd_id = storage_domains_module.create()['id']
            storage_domains_module.post_create_check(sd_id)
            ret = storage_domains_module.action(
                action='activate',
                action_condition=lambda s: s.status == sdstate.MAINTENANCE,
                wait_condition=lambda s: s.status == sdstate.ACTIVE,
                fail_condition=failed_state,
                search_params={'id': sd_id} if state == 'imported' else None
            )
        elif state == 'maintenance':
            sd_id = storage_domains_module.create()['id']
            storage_domains_module.post_create_check(sd_id)

            ret = OvirtRetry.backoff(tries=5, delay=1, backoff=2)(
                storage_domains_module.action
            )(
                action='deactivate',
                action_condition=lambda s: s.status == sdstate.ACTIVE,
                wait_condition=lambda s: s.status == sdstate.MAINTENANCE,
                fail_condition=failed_state,
            )
        elif state == 'unattached':
            ret = storage_domains_module.create()
            storage_domains_module.pre_remove(
                storage_domain=storage_domains_service.service(ret['id']).get()
            )
            ret['changed'] = storage_domains_module.changed
        elif state == 'update_ovf_store':
            ret = storage_domains_module.action(
                action='update_ovf_store'
            )
        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
