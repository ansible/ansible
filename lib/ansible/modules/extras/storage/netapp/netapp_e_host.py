#!/usr/bin/python

# (c) 2016, NetApp, Inc
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
DOCUMENTATION = """
---
module: netapp_e_host
short_description: manage eseries hosts
description:
    - Create, update, remove hosts on NetApp E-series storage arrays
version_added: '2.2'
author: Kevin Hulquest (@hulquest)
options:
    api_username:
        required: true
        description:
        - The username to authenticate with the SANtricity WebServices Proxy or embedded REST API.
    api_password:
        required: true
        description:
        - The password to authenticate with the SANtricity WebServices Proxy or embedded REST API.
    api_url:
        required: true
        description:
        - The url to the SANtricity WebServices Proxy or embedded REST API.
        example:
        - https://prod-1.wahoo.acme.com/devmgr/v2
    validate_certs:
        required: false
        default: true
        description:
        - Should https certificates be validated?
    ssid:
        description:
            - the id of the storage array you wish to act against
        required: True
    name:
        description:
            - If the host doesnt yet exist, the label to assign at creation time.
            - If the hosts already exists, this is what is used to identify the host to apply any desired changes
        required: True
    host_type_index:
        description:
            - The index that maps to host type you wish to create. It is recommended to use the M(netapp_e_facts) module to gather this information. Alternatively you can use the WSP portal to retrieve the information.
        required: True
    ports:
        description:
            - a list of of dictionaries of host ports you wish to associate with the newly created host
        required: False
    group:
        description:
            - the group you want the host to be a member of
        required: False

"""

EXAMPLES = """
    - name: Set Host Info
      netapp_e_host:
        ssid: "{{ ssid }}"
        api_url: "{{ netapp_api_url }}"
        api_username: "{{ netapp_api_username }}"
        api_password: "{{ netapp_api_password }}"
        name: "{{ host_name }}"
        host_type_index: "{{ host_type_index }}"
"""

RETURN = """
msg:
    description: Success message
    returned: success
    type: string
    sample: The host has been created.
"""
import json

from ansible.module_utils.api import basic_auth_argument_spec
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.urls import open_url
from ansible.module_utils.six.moves.urllib.error import HTTPError

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def request(url, data=None, headers=None, method='GET', use_proxy=True,
            force=False, last_mod_time=None, timeout=10, validate_certs=True,
            url_username=None, url_password=None, http_agent=None, force_basic_auth=True, ignore_errors=False):
    try:
        r = open_url(url=url, data=data, headers=headers, method=method, use_proxy=use_proxy,
                     force=force, last_mod_time=last_mod_time, timeout=timeout, validate_certs=validate_certs,
                     url_username=url_username, url_password=url_password, http_agent=http_agent,
                     force_basic_auth=force_basic_auth)
    except HTTPError:
        err = get_exception()
        r = err.fp

    try:
        raw_data = r.read()
        if raw_data:
            data = json.loads(raw_data)
        else:
            raw_data is None
    except:
        if ignore_errors:
            pass
        else:
            raise Exception(raw_data)

    resp_code = r.getcode()

    if resp_code >= 400 and not ignore_errors:
        raise Exception(resp_code, data)
    else:
        return resp_code, data


class Host(object):
    def __init__(self):
        argument_spec = basic_auth_argument_spec()
        argument_spec.update(dict(
            api_username=dict(type='str', required=True),
            api_password=dict(type='str', required=True, no_log=True),
            api_url=dict(type='str', required=True),
            ssid=dict(type='str', required=True),
            state=dict(type='str', required=True, choices=['absent', 'present']),
            group=dict(type='str', required=False),
            ports=dict(type='list', required=False),
            force_port=dict(type='bool', default=False),
            name=dict(type='str', required=True),
            host_type_index=dict(type='int', required=True)
        ))

        self.module = AnsibleModule(argument_spec=argument_spec)
        args = self.module.params
        self.group = args['group']
        self.ports = args['ports']
        self.force_port = args['force_port']
        self.name = args['name']
        self.host_type_index = args['host_type_index']
        self.state = args['state']
        self.ssid = args['ssid']
        self.url = args['api_url']
        self.user = args['api_username']
        self.pwd = args['api_password']
        self.certs = args['validate_certs']
        self.ports = args['ports']
        self.post_body = dict()

        if not self.url.endswith('/'):
            self.url += '/'

    @property
    def valid_host_type(self):
        try:
            (rc, host_types) = request(self.url + 'storage-systems/%s/host-types' % self.ssid, url_password=self.pwd,
                                       url_username=self.user, validate_certs=self.certs, headers=HEADERS)
        except Exception:
            err = get_exception()
            self.module.fail_json(
                msg="Failed to get host types. Array Id [%s]. Error [%s]." % (self.ssid, str(err)))

        try:
            match = filter(lambda host_type: host_type['index'] == self.host_type_index, host_types)[0]
            return True
        except IndexError:
            self.module.fail_json(msg="There is no host type with index %s" % self.host_type_index)

    @property
    def hostports_available(self):
        used_ids = list()
        try:
            (rc, self.available_ports) = request(self.url + 'storage-systems/%s/unassociated-host-ports' % self.ssid,
                                                 url_password=self.pwd, url_username=self.user,
                                                 validate_certs=self.certs,
                                                 headers=HEADERS)
        except:
            err = get_exception()
            self.module.fail_json(
                msg="Failed to get unassociated host ports. Array Id [%s]. Error [%s]." % (self.ssid, str(err)))

        if len(self.available_ports) > 0 and len(self.ports) <= len(self.available_ports):
            for port in self.ports:
                for free_port in self.available_ports:
                    # Desired Type matches but also make sure we havent already used the ID
                    if not free_port['id'] in used_ids:
                        # update the port arg to have an id attribute
                        used_ids.append(free_port['id'])
                        break

            if len(used_ids) != len(self.ports) and not self.force_port:
                self.module.fail_json(
                    msg="There are not enough free host ports with the specified port types to proceed")
            else:
                return True

        else:
            self.module.fail_json(msg="There are no host ports available OR there are not enough unassigned host ports")

    @property
    def group_id(self):
        if self.group:
            try:
                (rc, all_groups) = request(self.url + 'storage-systems/%s/host-groups' % self.ssid,
                                           url_password=self.pwd,
                                           url_username=self.user, validate_certs=self.certs, headers=HEADERS)
            except:
                err = get_exception()
                self.module.fail_json(
                    msg="Failed to get host groups. Array Id [%s]. Error [%s]." % (self.ssid, str(err)))

            try:
                group_obj = filter(lambda group: group['name'] == self.group, all_groups)[0]
                return group_obj['id']
            except IndexError:
                self.module.fail_json(msg="No group with the name: %s exists" % self.group)
        else:
            # Return the value equivalent of no group
            return "0000000000000000000000000000000000000000"

    @property
    def host_exists(self):
        try:
            (rc, all_hosts) = request(self.url + 'storage-systems/%s/hosts' % self.ssid, url_password=self.pwd,
                                      url_username=self.user, validate_certs=self.certs, headers=HEADERS)
        except:
            err = get_exception()
            self.module.fail_json(
                msg="Failed to determine host existence. Array Id [%s]. Error [%s]." % (self.ssid, str(err)))

        self.all_hosts = all_hosts
        try:  # Try to grab the host object
            self.host_obj = filter(lambda host: host['label'] == self.name, all_hosts)[0]
            return True
        except IndexError:
            # Host with the name passed in does not exist
            return False

    @property
    def needs_update(self):
        needs_update = False
        self.force_port_update = False

        if self.host_obj['clusterRef'] != self.group_id or \
                self.host_obj['hostTypeIndex'] != self.host_type_index:
            needs_update = True

        if self.ports:
            if not self.host_obj['ports']:
                needs_update = True
            for arg_port in self.ports:
                # First a quick check to see if the port is mapped to a different host
                if not self.port_on_diff_host(arg_port):
                    for obj_port in self.host_obj['ports']:
                        if arg_port['label'] == obj_port['label']:
                            # Confirmed that port arg passed in exists on the host
                            # port_id = self.get_port_id(obj_port['label'])
                            if arg_port['type'] != obj_port['portId']['ioInterfaceType']:
                                needs_update = True
                            if 'iscsiChapSecret' in arg_port:
                                # No way to know the current secret attr, so always return True just in case
                                needs_update = True
                else:
                    # If the user wants the ports to be reassigned, do it
                    if self.force_port:
                        self.force_port_update = True
                        needs_update = True
                    else:
                        self.module.fail_json(
                            msg="The port you specified:\n%s\n is associated with a different host. Specify force_port as True or try a different port spec" % arg_port)

        return needs_update

    def port_on_diff_host(self, arg_port):
        """ Checks to see if a passed in port arg is present on a different host """
        for host in self.all_hosts:
            # Only check 'other' hosts
            if self.host_obj['name'] != self.name:
                for port in host['ports']:
                    # Check if the port label is found in the port dict list of each host
                    if arg_port['label'] == port['label']:
                        self.other_host = host
                        return True
        return False

    def reassign_ports(self, apply=True):
        if not self.post_body:
            self.post_body = dict(
                portsToUpdate=dict()
            )

        for port in self.ports:
            if self.port_on_diff_host(port):
                self.post_body['portsToUpdate'].update(dict(
                    portRef=self.other_host['hostPortRef'],
                    hostRef=self.host_obj['id'],
                    # Doesnt yet address port identifier or chap secret
                ))

        if apply:
            try:
                (rc, self.host_obj) = request(
                    self.url + 'storage-systems/%s/hosts/%s' % (self.ssid, self.host_obj['id']),
                    url_username=self.user, url_password=self.pwd, headers=HEADERS,
                    validate_certs=self.certs, method='POST', data=json.dumps(self.post_body))
            except:
                err = get_exception()
                self.module.fail_json(
                    msg="Failed to reassign host port. Host Id [%s]. Array Id [%s]. Error [%s]." % (
                        self.host_obj['id'], self.ssid, str(err)))

    def update_host(self):
        if self.ports:
            if self.hostports_available:
                if self.force_port_update is True:
                    self.reassign_ports(apply=False)
                    # Make sure that only ports that arent being reassigned are passed into the ports attr
                    self.ports = [port for port in self.ports if not self.port_on_diff_host(port)]

                self.post_body['ports'] = self.ports

        if self.group:
            self.post_body['groupId'] = self.group_id

        self.post_body['hostType'] = dict(index=self.host_type_index)

        try:
            (rc, self.host_obj) = request(self.url + 'storage-systems/%s/hosts/%s' % (self.ssid, self.host_obj['id']),
                                          url_username=self.user, url_password=self.pwd, headers=HEADERS,
                                          validate_certs=self.certs, method='POST', data=json.dumps(self.post_body))
        except:
            err = get_exception()
            self.module.fail_json(msg="Failed to update host. Array Id [%s]. Error [%s]." % (self.ssid, str(err)))

        self.module.exit_json(changed=True, **self.host_obj)

    def create_host(self):
        post_body = dict(
            name=self.name,
            host_type=dict(index=self.host_type_index),
            groupId=self.group_id,
            ports=self.ports
        )
        if self.ports:
            # Check that all supplied port args are valid
            if self.hostports_available:
                post_body.update(ports=self.ports)
            elif not self.force_port:
                self.module.fail_json(
                    msg="You supplied ports that are already in use. Supply force_port to True if you wish to reassign the ports")

        if not self.host_exists:
            try:
                (rc, create_resp) = request(self.url + "storage-systems/%s/hosts" % self.ssid, method='POST',
                                            url_username=self.user, url_password=self.pwd, validate_certs=self.certs,
                                            data=json.dumps(post_body), headers=HEADERS)
            except:
                err = get_exception()
                self.module.fail_json(
                    msg="Failed to create host. Array Id [%s]. Error [%s]." % (self.ssid, str(err)))
        else:
            self.module.exit_json(changed=False,
                                  msg="Host already exists. Id [%s]. Host [%s]." % (self.ssid, self.name))

        self.host_obj = create_resp

        if self.ports and self.force_port:
            self.reassign_ports()

        self.module.exit_json(changed=True, **self.host_obj)

    def remove_host(self):
        try:
            (rc, resp) = request(self.url + "storage-systems/%s/hosts/%s" % (self.ssid, self.host_obj['id']),
                                 method='DELETE',
                                 url_username=self.user, url_password=self.pwd, validate_certs=self.certs)
        except:
            err = get_exception()
            self.module.fail_json(
                msg="Failed to remote host.  Host[%s]. Array Id [%s]. Error [%s]." % (self.host_obj['id'],
                                                                                      self.ssid,
                                                                                      str(err)))

    def apply(self):
        if self.state == 'present':
            if self.host_exists:
                if self.needs_update and self.valid_host_type:
                    self.update_host()
                else:
                    self.module.exit_json(changed=False, msg="Host already present.", id=self.ssid, label=self.name)
            elif self.valid_host_type:
                self.create_host()
        else:
            if self.host_exists:
                self.remove_host()
                self.module.exit_json(changed=True, msg="Host removed.")
            else:
                self.module.exit_json(changed=False, msg="Host already absent.", id=self.ssid, label=self.name)


def main():
    host = Host()
    host.apply()


if __name__ == '__main__':
    main()
