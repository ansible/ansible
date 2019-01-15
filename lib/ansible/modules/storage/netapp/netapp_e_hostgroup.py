#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {"metadata_version": "1.1",
                    "status": ["preview"],
                    "supported_by": "community"}


DOCUMENTATION = """
---
module: netapp_e_hostgroup
version_added: "2.2"
short_description: NetApp E-Series manage array host groups
author:
    - Kevin Hulquest (@hulquest)
    - Nathan Swartz (@ndswartz)
description: Create, update or destroy host groups on a NetApp E-Series storage array.
extends_documentation_fragment:
    - netapp.eseries
options:
    state:
        required: true
        description:
            - Whether the specified host group should exist or not.
        choices: ["present", "absent"]
    name:
        required: false
        description:
            - Name of the host group to manage
            - This option is mutually exclusive with I(id).
    new_name:
        required: false
        description:
            - Specify this when you need to update the name of a host group
    id:
        required: false
        description:
            - Host reference identifier for the host group to manage.
            - This option is mutually exclusive with I(name).
    hosts:
        required: false
        description:
            - List of host names/labels to add to the group
"""
EXAMPLES = """
    - name: Configure Hostgroup
      netapp_e_hostgroup:
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        validate_certs: "{{ netapp_api_validate_certs }}"
        state: present
"""
RETURN = """
clusterRef:
    description: The unique identification value for this object. Other objects may use this reference value to refer to the cluster.
    returned: always except when state is absent
    type: str
    sample: "3233343536373839303132333100000000000000"
confirmLUNMappingCreation:
    description: If true, indicates that creation of LUN-to-volume mappings should require careful confirmation from the end-user, since such a mapping
                 will alter the volume access rights of other clusters, in addition to this one.
    returned: always
    type: bool
    sample: false
hosts:
    description: A list of the hosts that are part of the host group after all operations.
    returned: always except when state is absent
    type: list
    sample: ["HostA","HostB"]
id:
    description: The id number of the hostgroup
    returned: always except when state is absent
    type: str
    sample: "3233343536373839303132333100000000000000"
isSAControlled:
    description: If true, indicates that I/O accesses from this cluster are subject to the storage array's default LUN-to-volume mappings. If false,
                 indicates that I/O accesses from the cluster are subject to cluster-specific LUN-to-volume mappings.
    returned: always except when state is absent
    type: bool
    sample: false
label:
    description: The user-assigned, descriptive label string for the cluster.
    returned: always
    type: str
    sample: "MyHostGroup"
name:
    description: same as label
    returned: always except when state is absent
    type: str
    sample: "MyHostGroup"
protectionInformationCapableAccessMethod:
    description: This field is true if the host has a PI capable access method.
    returned: always except when state is absent
    type: bool
    sample: true
"""

from ansible.module_utils.netapp import NetAppESeriesModule
from ansible.module_utils._text import to_native


class NetAppESeriesHostGroup(NetAppESeriesModule):
    EXPANSION_TIMEOUT_SEC = 10
    DEFAULT_DISK_POOL_MINIMUM_DISK_COUNT = 11

    def __init__(self):
        version = "02.00.0000.0000"
        ansible_options = dict(
            state=dict(required=True, choices=["present", "absent"], type="str"),
            name=dict(required=False, type="str"),
            new_name=dict(required=False, type="str"),
            id=dict(required=False, type="str"),
            hosts=dict(required=False, type="list"))
        mutually_exclusive = [["name", "id"]]
        super(NetAppESeriesHostGroup, self).__init__(ansible_options=ansible_options,
                                                     web_services_version=version,
                                                     supports_check_mode=True,
                                                     mutually_exclusive=mutually_exclusive)

        args = self.module.params
        self.state = args["state"]
        self.name = args["name"]
        self.new_name = args["new_name"]
        self.id = args["id"]
        self.hosts_list = args["hosts"]

        self.current_host_group = None

    @property
    def hosts(self):
        """Retrieve a list of host reference identifiers should be associated with the host group."""
        host_list = []
        existing_hosts = []

        if self.hosts_list:
            try:
                rc, existing_hosts = self.request("storage-systems/%s/hosts" % self.ssid)
            except Exception as error:
                self.module.fail_json(msg="Failed to retrieve hosts information. Array id [%s].  Error[%s]."
                                          % (self.ssid, to_native(error)))

            for host in self.hosts_list:
                for existing_host in existing_hosts:
                    if host in existing_host["id"] or host in existing_host["name"]:
                        host_list.append(existing_host["id"])
                        break
                else:
                    self.module.fail_json(msg="Expected host does not exist. Array id [%s].  Host [%s]."
                                              % (self.ssid, host))

        return host_list

    @property
    def host_groups(self):
        """Retrieve a list of existing host groups."""
        host_groups = []
        hosts = []
        try:
            rc, host_groups = self.request("storage-systems/%s/host-groups" % self.ssid)
            rc, hosts = self.request("storage-systems/%s/hosts" % self.ssid)
        except Exception as error:
            self.module.fail_json(msg="Failed to retrieve host group information. Array id [%s].  Error[%s]."
                                      % (self.ssid, to_native(error)))

        host_groups = [{"id": group["clusterRef"], "name": group["name"]} for group in host_groups]
        for group in host_groups:
            hosts_ids = []
            for host in hosts:
                if group["id"] == host["clusterRef"]:
                    hosts_ids.append(host["hostRef"])
            group.update({"hosts": hosts_ids})

        return host_groups

    @property
    def current_hosts_in_host_group(self):
        """Retrieve the current hosts associated with the current hostgroup."""
        current_hosts = []
        for group in self.host_groups:
            if (self.name and group["name"] == self.name) or (self.id and group["id"] == self.id):
                current_hosts = group["hosts"]

        return current_hosts

    def unassign_hosts(self, host_list=None):
        """Unassign hosts from host group."""
        if host_list is None:
            host_list = self.current_host_group["hosts"]

        for host_id in host_list:
            try:
                rc, resp = self.request("storage-systems/%s/hosts/%s/move" % (self.ssid, host_id),
                                        method="POST", data={"group": "0000000000000000000000000000000000000000"})
            except Exception as error:
                self.module.fail_json(msg="Failed to unassign hosts from host group. Array id [%s].  Host id [%s]."
                                          "  Error[%s]." % (self.ssid, host_id, to_native(error)))

    def delete_host_group(self, unassign_hosts=True):
        """Delete host group"""
        if unassign_hosts:
            self.unassign_hosts()

        try:
            rc, resp = self.request("storage-systems/%s/host-groups/%s" % (self.ssid, self.current_host_group["id"]),
                                    method="DELETE")
        except Exception as error:
            self.module.fail_json(msg="Failed to delete host group. Array id [%s].  Error[%s]."
                                      % (self.ssid, to_native(error)))

    def create_host_group(self):
        """Create host group."""
        data = {"name": self.name, "hosts": self.hosts}

        response = None
        try:
            rc, response = self.request("storage-systems/%s/host-groups" % self.ssid, method="POST", data=data)
        except Exception as error:
            self.module.fail_json(msg="Failed to create host group. Array id [%s].  Error[%s]."
                                      % (self.ssid, to_native(error)))

        return response

    def update_host_group(self):
        """Update host group."""
        data = {"name": self.new_name if self.new_name else self.name,
                "hosts": self.hosts}

        # unassign hosts that should not be part of the hostgroup
        desired_host_ids = self.hosts
        for host in self.current_hosts_in_host_group:
            if host not in desired_host_ids:
                self.unassign_hosts([host])

        update_response = None
        try:
            rc, update_response = self.request("storage-systems/%s/host-groups/%s"
                                               % (self.ssid, self.current_host_group["id"]), method="POST", data=data)
        except Exception as error:
            self.module.fail_json(msg="Failed to create host group. Array id [%s].  Error[%s]."
                                      % (self.ssid, to_native(error)))

        return update_response

    def apply(self):
        """Apply desired host group state to the storage array."""
        changes_required = False

        # Search for existing host group match
        for group in self.host_groups:
            if (self.id and group["id"] == self.id) or (self.name and group["name"] == self.name):
                self.current_host_group = group

        # Determine whether changes are required
        if self.state == "present":
            if self.current_host_group:
                if (self.new_name and self.new_name != self.name) or self.hosts != self.current_host_group["hosts"]:
                    changes_required = True
            else:
                if not self.name:
                    self.module.fail_json(msg="The option name must be supplied when creating a new host group."
                                              " Array id [%s]." % self.ssid)
                changes_required = True

        elif self.current_host_group:
            changes_required = True

        # Apply any necessary changes
        msg = ""
        if changes_required and not self.module.check_mode:
            msg = "No changes required."
            if self.state == "present":
                if self.current_host_group:
                    if ((self.new_name and self.new_name != self.name) or
                            (self.hosts != self.current_host_group["hosts"])):
                        msg = self.update_host_group()
                else:
                    msg = self.create_host_group()

            elif self.current_host_group:
                self.delete_host_group()
                msg = "Host group deleted. Array Id [%s].  Host Name [%s].  Host Id [%s]."\
                      % (self.ssid, self.current_host_group["name"], self.current_host_group["id"])

        self.module.exit_json(msg=msg, changed=changes_required)


def main():
    hostgroup = NetAppESeriesHostGroup()
    hostgroup.apply()


if __name__ == "__main__":
    main()
