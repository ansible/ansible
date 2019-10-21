#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Huawei
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

###############################################################################
# Documentation
###############################################################################

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ["preview"],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: hwc_vpc_subnet
description:
    - subnet management.
short_description: Creates a resource of Vpc/Subnet in Huawei Cloud
version_added: '2.10'
author: Huawei Inc. (@huaweicloud)
requirements:
    - keystoneauth1 >= 3.6.0
options:
    state:
        description:
            - Whether the given object should exist in Huawei Cloud.
        type: str
        choices: ['present', 'absent']
        default: 'present'
    timeouts:
        description:
            - The timeouts for each operations.
        type: dict
        suboptions:
            create:
                description:
                    - The timeouts for create operation.
                type: str
                default: '15m'
            update:
                description:
                    - The timeouts for update operation.
                type: str
                default: '15m'
    cidr:
        description:
            - Specifies the subnet CIDR block. The value must be within the VPC
              CIDR block and be in CIDR format. The subnet mask cannot be
              greater than 28. Cannot be changed after creating the subnet.
        type: str
        required: true
    gateway_ip:
        description:
            - Specifies the gateway of the subnet. The value must be an IP
              address in the subnet. Cannot be changed after creating the subnet.
        type: str
        required: true
    name:
        description:
            - Specifies the subnet name. The value is a string of 1 to 64
              characters that can contain letters, digits, underscores C(_),
              hyphens (-), and periods (.).
        type: str
        required: true
    vpc_id:
        description:
            - Specifies the ID of the VPC to which the subnet belongs. Cannot
              be changed after creating the subnet.
        type: str
        required: true
    availability_zone:
        description:
            - Specifies the AZ to which the subnet belongs. Cannot be changed
              after creating the subnet.
        type: str
        required: false
    dhcp_enable:
        description:
            - Specifies whether DHCP is enabled for the subnet. The value can
              be true (enabled) or false(disabled), and default value is true.
              If this parameter is set to false, newly created ECSs cannot
              obtain IP addresses, and usernames and passwords cannot be
              injected using Cloud-init.
        type: bool
        required: false
    dns_address:
        description:
            - Specifies the DNS server addresses for subnet. The address
              in the head will be used first.
        type: list
        required: false
extends_documentation_fragment: hwc
'''

EXAMPLES = '''
# create subnet
- name: create vpc
  hwc_network_vpc:
    cidr: "192.168.100.0/24"
    name: "ansible_network_vpc_test"
  register: vpc
- name: create subnet
  hwc_vpc_subnet:
    vpc_id: "{{ vpc.id }}"
    cidr: "192.168.100.0/26"
    gateway_ip: "192.168.100.32"
    name: "ansible_network_subnet_test"
    dhcp_enable: True
'''

RETURN = '''
    cidr:
        description:
            - Specifies the subnet CIDR block. The value must be within the VPC
              CIDR block and be in CIDR format. The subnet mask cannot be
              greater than 28.
        type: str
        returned: success
    gateway_ip:
        description:
            - Specifies the gateway of the subnet. The value must be an IP
              address in the subnet.
        type: str
        returned: success
    name:
        description:
            - Specifies the subnet name. The value is a string of 1 to 64
              characters that can contain letters, digits, underscores C(_),
              hyphens (-), and periods (.).
        type: str
        returned: success
    vpc_id:
        description:
            - Specifies the ID of the VPC to which the subnet belongs.
        type: str
        returned: success
    availability_zone:
        description:
            - Specifies the AZ to which the subnet belongs.
        type: str
        returned: success
    dhcp_enable:
        description:
            - Specifies whether DHCP is enabled for the subnet. The value can
              be true (enabled) or false(disabled), and default value is true.
              If this parameter is set to false, newly created ECSs cannot
              obtain IP addresses, and usernames and passwords cannot be
              injected using Cloud-init.
        type: bool
        returned: success
    dns_address:
        description:
            - Specifies the DNS server addresses for subnet. The address
              in the head will be used first.
        type: list
        returned: success
'''

from ansible.module_utils.hwc_utils import (
    Config, HwcClientException, HwcClientException404, HwcModule,
    are_different_dicts, build_path, get_region, is_empty_value,
    navigate_value, wait_to_finish)


def build_module():
    return HwcModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'],
                       type='str'),
            timeouts=dict(type='dict', options=dict(
                create=dict(default='15m', type='str'),
                update=dict(default='15m', type='str'),
            ), default=dict()),
            cidr=dict(type='str', required=True),
            gateway_ip=dict(type='str', required=True),
            name=dict(type='str', required=True),
            vpc_id=dict(type='str', required=True),
            availability_zone=dict(type='str'),
            dhcp_enable=dict(type='bool'),
            dns_address=dict(type='list', elements='str')
        ),
        supports_check_mode=True,
    )


def main():
    """Main function"""

    module = build_module()
    config = Config(module, "vpc")

    try:
        resource = None
        if module.params.get('id'):
            resource = True
        else:
            v = search_resource(config)
            if len(v) > 1:
                raise Exception("Found more than one resource(%s)" % ", ".join([
                                navigate_value(i, ["id"]) for i in v]))

            if len(v) == 1:
                resource = v[0]
                module.params['id'] = navigate_value(resource, ["id"])

        result = {}
        changed = False
        if module.params['state'] == 'present':
            if resource is None:
                if not module.check_mode:
                    create(config)
                changed = True

            current = read_resource(config, exclude_output=True)
            expect = user_input_parameters(module)
            if are_different_dicts(expect, current):
                if not module.check_mode:
                    update(config)
                changed = True

            result = read_resource(config)
            result['id'] = module.params.get('id')
        else:
            if resource:
                if not module.check_mode:
                    delete(config)
                changed = True

    except Exception as ex:
        module.fail_json(msg=str(ex))

    else:
        result['changed'] = changed
        module.exit_json(**result)


def user_input_parameters(module):
    return {
        "availability_zone": module.params.get("availability_zone"),
        "cidr": module.params.get("cidr"),
        "dhcp_enable": module.params.get("dhcp_enable"),
        "dns_address": module.params.get("dns_address"),
        "gateway_ip": module.params.get("gateway_ip"),
        "name": module.params.get("name"),
        "vpc_id": module.params.get("vpc_id"),
    }


def create(config):
    module = config.module
    client = config.client(get_region(module), "vpc", "project")
    timeout = 60 * int(module.params['timeouts']['create'].rstrip('m'))
    opts = user_input_parameters(module)

    params = build_create_parameters(opts)
    r = send_create_request(module, params, client)
    obj = async_wait_create(config, r, client, timeout)
    module.params['id'] = navigate_value(obj, ["subnet", "id"])


def update(config):
    module = config.module
    client = config.client(get_region(module), "vpc", "project")
    timeout = 60 * int(module.params['timeouts']['update'].rstrip('m'))
    opts = user_input_parameters(module)

    params = build_update_parameters(opts)
    if params:
        r = send_update_request(module, params, client)
        async_wait_update(config, r, client, timeout)


def delete(config):
    module = config.module
    client = config.client(get_region(module), "vpc", "project")

    send_delete_request(module, None, client)

    url = build_path(module, "subnets/{id}")

    def _refresh_status():
        try:
            client.get(url)
        except HwcClientException404:
            return True, "Done"

        except Exception:
            return None, ""

        return True, "Pending"

    timeout = 60 * int(module.params['timeouts']['create'].rstrip('m'))
    try:
        wait_to_finish(["Done"], ["Pending"], _refresh_status, timeout)
    except Exception as ex:
        module.fail_json(msg="module(hwc_vpc_subnet): error "
                             "waiting for api(delete) to "
                             "be done, error= %s" % str(ex))


def read_resource(config, exclude_output=False):
    module = config.module
    client = config.client(get_region(module), "vpc", "project")

    res = {}

    r = send_read_request(module, client)
    res["read"] = fill_read_resp_body(r)

    return update_properties(module, res, None, exclude_output)


def _build_query_link(opts):
    query_link = "?marker={marker}&limit=10"
    v = navigate_value(opts, ["vpc_id"])
    if v:
        query_link += "&vpc_id=" + str(v)

    return query_link


def search_resource(config):
    module = config.module
    client = config.client(get_region(module), "vpc", "project")
    opts = user_input_parameters(module)
    identity_obj = _build_identity_object(opts)
    query_link = _build_query_link(opts)
    link = "subnets" + query_link

    result = []
    p = {'marker': ''}
    while True:
        url = link.format(**p)
        r = send_list_request(module, client, url)
        if not r:
            break

        for item in r:
            item = fill_list_resp_body(item)
            if not are_different_dicts(identity_obj, item):
                result.append(item)

        if len(result) > 1:
            break

        p['marker'] = r[-1].get('id')

    return result


def build_create_parameters(opts):
    params = dict()

    v = navigate_value(opts, ["availability_zone"], None)
    if not is_empty_value(v):
        params["availability_zone"] = v

    v = navigate_value(opts, ["cidr"], None)
    if not is_empty_value(v):
        params["cidr"] = v

    v = navigate_value(opts, ["dhcp_enable"], None)
    if v is not None:
        params["dhcp_enable"] = v

    v = expand_create_dns_list(opts, None)
    if not is_empty_value(v):
        params["dnsList"] = v

    v = navigate_value(opts, ["gateway_ip"], None)
    if not is_empty_value(v):
        params["gateway_ip"] = v

    v = navigate_value(opts, ["name"], None)
    if not is_empty_value(v):
        params["name"] = v

    v = expand_create_primary_dns(opts, None)
    if not is_empty_value(v):
        params["primary_dns"] = v

    v = expand_create_secondary_dns(opts, None)
    if not is_empty_value(v):
        params["secondary_dns"] = v

    v = navigate_value(opts, ["vpc_id"], None)
    if not is_empty_value(v):
        params["vpc_id"] = v

    if not params:
        return params

    params = {"subnet": params}

    return params


def expand_create_dns_list(d, array_index):
    v = navigate_value(d, ["dns_address"], array_index)
    return v if (v and len(v) > 2) else []


def expand_create_primary_dns(d, array_index):
    v = navigate_value(d, ["dns_address"], array_index)
    return v[0] if v else ""


def expand_create_secondary_dns(d, array_index):
    v = navigate_value(d, ["dns_address"], array_index)
    return v[1] if (v and len(v) > 1) else ""


def send_create_request(module, params, client):
    url = "subnets"
    try:
        r = client.post(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_subnet): error running "
               "api(create), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def async_wait_create(config, result, client, timeout):
    module = config.module

    path_parameters = {
        "subnet_id": ["subnet", "id"],
    }
    data = dict((key, navigate_value(result, path))
                for key, path in path_parameters.items())

    url = build_path(module, "subnets/{subnet_id}", data)

    def _query_status():
        r = None
        try:
            r = client.get(url, timeout=timeout)
        except HwcClientException:
            return None, ""

        try:
            s = navigate_value(r, ["subnet", "status"])
            return r, s
        except Exception:
            return None, ""

    try:
        return wait_to_finish(
            ["ACTIVE"],
            ["UNKNOWN"],
            _query_status, timeout)
    except Exception as ex:
        module.fail_json(msg="module(hwc_vpc_subnet): error "
                             "waiting for api(create) to "
                             "be done, error= %s" % str(ex))


def build_update_parameters(opts):
    params = dict()

    v = navigate_value(opts, ["dhcp_enable"], None)
    if v is not None:
        params["dhcp_enable"] = v

    v = expand_update_dns_list(opts, None)
    if v is not None:
        params["dnsList"] = v

    v = navigate_value(opts, ["name"], None)
    if not is_empty_value(v):
        params["name"] = v

    v = expand_update_primary_dns(opts, None)
    if v is not None:
        params["primary_dns"] = v

    v = expand_update_secondary_dns(opts, None)
    if v is not None:
        params["secondary_dns"] = v

    if not params:
        return params

    params = {"subnet": params}

    return params


def expand_update_dns_list(d, array_index):
    v = navigate_value(d, ["dns_address"], array_index)
    if v:
        if len(v) > 2:
            return v
        return None
    return []


def expand_update_primary_dns(d, array_index):
    v = navigate_value(d, ["dns_address"], array_index)
    return v[0] if v else ""


def expand_update_secondary_dns(d, array_index):
    v = navigate_value(d, ["dns_address"], array_index)
    return v[1] if (v and len(v) > 1) else ""


def send_update_request(module, params, client):
    url = build_path(module, "vpcs/{vpc_id}/subnets/{id}")

    try:
        r = client.put(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_subnet): error running "
               "api(update), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def async_wait_update(config, result, client, timeout):
    module = config.module

    path_parameters = {
        "subnet_id": ["subnet", "id"],
    }
    data = dict((key, navigate_value(result, path))
                for key, path in path_parameters.items())

    url = build_path(module, "subnets/{subnet_id}", data)

    def _query_status():
        r = None
        try:
            r = client.get(url, timeout=timeout)
        except HwcClientException:
            return None, ""

        try:
            s = navigate_value(r, ["subnet", "status"])
            return r, s
        except Exception:
            return None, ""

    try:
        return wait_to_finish(
            ["ACTIVE"],
            ["UNKNOWN"],
            _query_status, timeout)
    except Exception as ex:
        module.fail_json(msg="module(hwc_vpc_subnet): error "
                             "waiting for api(update) to "
                             "be done, error= %s" % str(ex))


def send_delete_request(module, params, client):
    url = build_path(module, "vpcs/{vpc_id}/subnets/{id}")

    try:
        r = client.delete(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_subnet): error running "
               "api(delete), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def send_read_request(module, client):
    url = build_path(module, "subnets/{id}")

    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_subnet): error running "
               "api(read), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return navigate_value(r, ["subnet"], None)


def fill_read_resp_body(body):
    result = dict()

    result["availability_zone"] = body.get("availability_zone")

    result["cidr"] = body.get("cidr")

    result["dhcp_enable"] = body.get("dhcp_enable")

    result["dnsList"] = body.get("dnsList")

    result["gateway_ip"] = body.get("gateway_ip")

    result["id"] = body.get("id")

    result["name"] = body.get("name")

    result["neutron_network_id"] = body.get("neutron_network_id")

    result["neutron_subnet_id"] = body.get("neutron_subnet_id")

    result["primary_dns"] = body.get("primary_dns")

    result["secondary_dns"] = body.get("secondary_dns")

    result["status"] = body.get("status")

    result["vpc_id"] = body.get("vpc_id")

    return result


def update_properties(module, response, array_index, exclude_output=False):
    r = user_input_parameters(module)

    v = navigate_value(response, ["read", "availability_zone"], array_index)
    r["availability_zone"] = v

    v = navigate_value(response, ["read", "cidr"], array_index)
    r["cidr"] = v

    v = navigate_value(response, ["read", "dhcp_enable"], array_index)
    r["dhcp_enable"] = v

    v = navigate_value(response, ["read", "dnsList"], array_index)
    r["dns_address"] = v

    v = navigate_value(response, ["read", "gateway_ip"], array_index)
    r["gateway_ip"] = v

    v = navigate_value(response, ["read", "name"], array_index)
    r["name"] = v

    v = navigate_value(response, ["read", "vpc_id"], array_index)
    r["vpc_id"] = v

    return r


def send_list_request(module, client, url):

    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_subnet): error running "
               "api(list), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return navigate_value(r, ["subnets"], None)


def _build_identity_object(all_opts):
    result = dict()

    v = navigate_value(all_opts, ["availability_zone"], None)
    result["availability_zone"] = v

    v = navigate_value(all_opts, ["cidr"], None)
    result["cidr"] = v

    v = navigate_value(all_opts, ["dhcp_enable"], None)
    result["dhcp_enable"] = v

    v = navigate_value(all_opts, ["dns_address"], None)
    result["dnsList"] = v

    v = navigate_value(all_opts, ["gateway_ip"], None)
    result["gateway_ip"] = v

    result["id"] = None

    v = navigate_value(all_opts, ["name"], None)
    result["name"] = v

    result["neutron_network_id"] = None

    result["neutron_subnet_id"] = None

    result["primary_dns"] = None

    result["secondary_dns"] = None

    result["status"] = None

    v = navigate_value(all_opts, ["vpc_id"], None)
    result["vpc_id"] = v

    return result


def fill_list_resp_body(body):
    result = dict()

    result["availability_zone"] = body.get("availability_zone")

    result["cidr"] = body.get("cidr")

    result["dhcp_enable"] = body.get("dhcp_enable")

    result["dnsList"] = body.get("dnsList")

    result["gateway_ip"] = body.get("gateway_ip")

    result["id"] = body.get("id")

    result["name"] = body.get("name")

    result["neutron_network_id"] = body.get("neutron_network_id")

    result["neutron_subnet_id"] = body.get("neutron_subnet_id")

    result["primary_dns"] = body.get("primary_dns")

    result["secondary_dns"] = body.get("secondary_dns")

    result["status"] = body.get("status")

    result["vpc_id"] = body.get("vpc_id")

    return result


if __name__ == '__main__':
    main()
