#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013-2014, Epic Games, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: phpipam_next_ip
short_description: Get next free IP from phpIPAM
version_added: "2.9"
description:
    - "This module allows you to create or remove ip address assignment in phpIPAM, U(https://phpipam.net)."
author:
    - Hampus Lundqvist (@HampusLundqvist)
requirements:
    - "python >= 2.6"
    - "phpipam-client >= 0.2"
options:
    hostname:
        description:
            - hostname to get ip for
        required: true
        aliases: ['name']
    description:
        description:
            - description field in phpipam
        required: false
        default: "API created"
    state:
        description:
            - Ensure ip and hostname is present or not in subnet
        default: present
        choices: ['present', 'absent']
    subnet_cidr:
        description:
            - A subnet, needs to be unique so get help from vlan_name and, or vrf_name to find it
        required: true
        aliases: ['cidr','subnet']
    vlan_name:
        description:
            - Name of the vlan the subnet is created in
        required: false
    vrf_name:
        description:
            - Name of vrf the subnet is created in
        required: false
    server_url:
        description:
            - Server URL to phpIPAM
        required: true
        aliases: ['url']
    username:
        description:
            - username for authentication in phpIPAM
        required: true
    password:
        description:
            - password for authentication in phpIPAM
        required: true
    app_id:
        description:
            - Application ID created in phpIPAM
        required: true
        aliases: ['appid']
'''

EXAMPLES = '''
- name: Create/Get ip address assignment in a subnet
  phpipam_next_ip:
    name: "test.domain"
    state: present
    username: user
    password: pw
    app_id: ansible
    server_url: https://ipam.domain
    subnet_cidr: 192.168.0.0/24
  register: ipam

- name: Remove ip assignment for hostname
  phpipam_next_ip:
    name: "test.domain"
    state: absent
    username: user
    password: pw
    app_id: ansible
    server_url: https://ipam.domain
    subnet_cidr: 192.168.0.0/24

'''

RETURN = '''
result:
    description: Information about the address entry in phpIPAM.
    type: dict
    returned: always
    subnet:
        description: information about the subnet settings in ipam.
        type: dict
        returned: present
    vlan:
        description: information from ipam any connected vlan.
        type: dict
        returned: present
    vrf:
        description: information from ipam about any confgured vrf.
        type: dict
        returned: present

'''

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
import traceback

try:
    from phpipam_client import PhpIpamClient, POST, DELETE
    HAS_PHPIPAM_CLIENT = True

except ImportError:
    PHPIPAM_CLIENT_IMP_ERR = traceback.format_exc()
    HAS_PHPIPAM_CLIENT = False


class Ip(object):
    def __init__(self, module, ipam):
        self._module = module
        self._ipam = ipam

    def get_vlan_by_name(self, vlan_name):
        try:
            vlan_result = self._ipam.query('/vlan/?filter_by=name&filter_value={}'.format(vlan_name))
            if len(vlan_result) != 1:
                self._module.fail_json(msg="Failed when finding {} vlans with name: {}".format(len(vlan_result), vlan_name))
            return vlan_result[0]
        except Exception as e:
            self._module.fail_json(msg="Failed when finding vlan name {}: ".format(vlan_name, e))

    def get_vlan_by_id(self, vlanId):

        try:
            vlan_result = self._ipam.query('/vlan/{}/'.format(vlanId))

            return vlan_result

        except Exception as e:
            self._module.fail_json(msg="Could not find a vlan id {}: {}".format(vlanId, e))

    def get_vrf_by_name(self, vrf_name):
        try:
            vrf_result = self._ipam.query('/vrf/?filter_by=name&filter_value={}'.format(vrf_name))
            if len(vrf_result) != 1:
                self._module.fail_json(msg="Failed when finding {} vrf with name: {}".format(len(vrf_result), vrf_name))
            return vrf_result[0]

        except Exception as e:
            self._module.fail_json(msg="Could not find a vrf named {}: {}".format(vrf_name, e))

    def get_subnet(self, cidr, vrfId=None, vlanId=None):
        try:

            if vrfId is None and vlanId is None:
                query = "/subnets/cidr/{}".format(cidr)
            elif vrfId is None and vlanId is not None:
                query = "/subnets/cidr/{}/?filter_by=vlanId,filter_value={}".format(cidr, vlanId)
            elif vrfId is not None and vlanId is None:
                query = "/subnets/cidr/{}/?filter_by=vrfId&filter_value={}".format(cidr, vrfId)
            elif vrfId is not None and vlanId is not None:
                query = "/subnets/cidr/{}/?filter_by=vrfId&filter_value={}&filter_by=vlanId&filter_value={}".format(cidr, vrfId, vlanId)

            subnet_result = self._ipam.query(query)

            if len(subnet_result) != 1:
                self._module.fail_json(msg="Error found {} subnets with cidr {} using query: {}, \
                                       try using vlan_name and / or vrf_name".format(len(subnet_result), cidr, query))

            return subnet_result[0]

        except Exception as e:
            self._module.fail_jsoon(msg="Error in getting subnet: {}".format(e))

    def search_host_in_subnet(self, hostname, subnetId):
        try:
            query = "/subnets/{}/addresses/?filter_by=hostname&filter_value={}".format(subnetId, hostname)
            host_result = self._ipam.query(query)

            if len(host_result) != 1:
                self._module.fail_json(msg="Error found {} hosts within this subnet. hostname has to be unique in the subnet".format(len(host_result)))
            return host_result[0]

        except Exception:
            return None

    def get_first_gateway_from_subnet(self, subnetId):
        try:
            gw_query = "/subnets/{}/addresses/?filter_by=is_gateway&filter_value={}".format(subnetId, "1")
            gateway_result = self._ipam.query(gw_query)
            gateway = gateway_result[0]["ip"]
        except Exception:
            gateway = None

        return gateway

    def delete_host_ip(self, ip_id, subnetid, remove_dns):
        try:
            query = "/addresses/{}/{}".format(ip_id, subnetid)
            host_remove = self._ipam.query(query, method=delete, data={'remove_dns': remove_dns})

        except Exception as e:
            self._module.fail_json(msg="Error in removing ip assignment: {}".format(e))

        return host_remove

    def get_first_ip(self, hostname, description, subnetid):
        try:
            query = "/addresses/first_free/{}/".format(subnetid)
            new_host = self._ipam.query(query, method=POST, data={'hostname': hostname, 'description': description})

        except Exception as e:
            self._module.fail_json(msg="Error creating new ip assignment: {}".format(e))

        return new_host


def main():

    module = AnsibleModule(
        argument_spec=dict(
            hostname=dict(type='str', required=True, aliases=['name']),
            app_id=dict(type='str', required=True, aliases=['appid']),
            username=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
            server_url=dict(type='str', required=True, aliases=['url']),
            description=dict(type='str', required=False, default="API created"),
            subnet_cidr=dict(type='str', required=True, aliases=['cidr', 'subnet']),
            vlan_name=dict(type='str', required=False),
            vrf_name=dict(type='str', required=False),
            state=dict(default='present', choices=['present', 'absent']),
            remove_dns=dict(default='no', choices=['yes', 'no'])
        ),
        supports_check_mode=False
    )

    if not HAS_PHPIPAM_CLIENT:
        module.fail_json(msg=missing_required_lib('phpipam-client', url='https://pypi.org/project/phpipam-client/'), exception=PHPIPAM_CLIENT_IMP_ERR)

    remove_dns = 0 if status == "no" else 1

    hostname = module.params['hostname']
    app_id = module.params['app_id']
    username = module.params['username']
    password = module.params['password']
    server_url = module.params['server_url']
    description = module.params['description']
    subnet_cidr = module.params['subnet_cidr']
    vlan_name = module.params['vlan_name']
    vrf_name = module.params['vrf_name']
    state = module.params['state']

    # login to phpIPAM
    try:
        ipam = PhpIpamClient(url=server_url, app_id=app_id, username=username, password=password)

    except Exception as e:
        module.fail_json(msg='Failed to connect to phpIPAM server: {}'.format(e))

    hostip = Ip(module, ipam)

    vrf = {}
    vlan = {}
    vrf['vrfId'] = None
    vlan['vlanId'] = None

    if vrf_name:
        vrf = hostip.get_vrf_by_name(vrf_name)

    if vlan_name:
        vlan = hostip.get_vlan_by_name(vlan_name)

    subnet = hostip.get_subnet(subnet_cidr, vrf['vrfId'], vlan['vlanId'])

    host = hostip.search_host_in_subnet(hostname, subnet['id'])

    if state == "present":
        if not host:
            ip = hostip.get_first_ip(hostname, description, subnet['id'])
            host = hostip.search_host_in_subnet(hostname, subnet['id'])

        host['subnet'] = subnet

        if not vlan['vlanId'] and subnet['vlanId'] != 0:
            host['vlan'] = hostip.get_vlan_by_id(subnet['vlanId'])
        else:
            host['vlan'] = vlan
        if not vrf['vrfId'] and subnet['vrfId'] != 0:
            host['vrf'] = hostip.get_vrf_by_id(subnet['vrfId'])
        else:
            host['vrf'] = vrf

        host['gateway'] = hostip.get_first_gateway_from_subnet(subnet['id'])
        module.exit_json(changed=True, result=host)

    else:
        if not host:
            module.exit_json(changed=False, result="Host does not exist on this subnet")
        else:
            host_remove = hostip.delete_host_ip(host['id'], subnet['id'], remove_dns)
            module.exit_json(changed=True, result="removed")


if __name__ == '__main__':
    main()
