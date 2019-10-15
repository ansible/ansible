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
module: hwc_vpc_port
description:
    - vpc port management.
short_description: Creates a resource of Vpc/Port in Huawei Cloud
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
    subnet_id:
        description:
            - Specifies the ID of the subnet to which the port belongs.
        type: str
        required: true
    admin_state_up:
        description:
            - Specifies the administrative state of the port.
        type: bool
        required: false
    allowed_address_pairs:
        description:
            - Specifies a set of zero or more allowed address pairs.
        required: false
        type: list
        suboptions:
            ip_address:
                description:
                    - Specifies the IP address. It cannot set it to 0.0.0.0.
                      Configure an independent security group for the port if a
                      large CIDR block (subnet mask less than 24) is configured
                      for parameter allowed_address_pairs.
                type: str
                required: false
            mac_address:
                description:
                    - Specifies the MAC address.
                type: str
                required: false
    extra_dhcp_opts:
        description:
            - Specifies the extended option of DHCP.
        type: list
        required: false
        suboptions:
            name:
                description:
                    - Specifies the option name.
                type: str
                required: false
            value:
                description:
                    - Specifies the option value.
                type: str
                required: false
    ip_address:
        description:
            - Specifies the port IP address.
        type: str
        required: false
    name:
        description:
            - Specifies the port name. The value can contain no more than 255
              characters.
        type: str
        required: false
    security_groups:
        description:
            - Specifies the ID of the security group.
        type: list
        required: false
extends_documentation_fragment: hwc
'''

EXAMPLES = '''
# create a port
- name: create vpc
  hwc_network_vpc:
    cidr: "192.168.100.0/24"
    name: "ansible_network_vpc_test"
  register: vpc
- name: create subnet
  hwc_vpc_subnet:
    gateway_ip: "192.168.100.32"
    name: "ansible_network_subnet_test"
    dhcp_enable: True
    vpc_id: "{{ vpc.id }}"
    cidr: "192.168.100.0/26"
  register: subnet
- name: create a port
  hwc_vpc_port:
    subnet_id: "{{ subnet.id }}"
    ip_address: "192.168.100.33"
'''

RETURN = '''
    subnet_id:
        description:
            - Specifies the ID of the subnet to which the port belongs.
        type: str
        returned: success
    admin_state_up:
        description:
            - Specifies the administrative state of the port.
        type: bool
        returned: success
    allowed_address_pairs:
        description:
            - Specifies a set of zero or more allowed address pairs.
        type: list
        returned: success
        contains:
            ip_address:
                description:
                    - Specifies the IP address. It cannot set it to 0.0.0.0.
                      Configure an independent security group for the port if a
                      large CIDR block (subnet mask less than 24) is configured
                      for parameter allowed_address_pairs.
                type: str
                returned: success
            mac_address:
                description:
                    - Specifies the MAC address.
                type: str
                returned: success
    extra_dhcp_opts:
        description:
            - Specifies the extended option of DHCP.
        type: list
        returned: success
        contains:
            name:
                description:
                    - Specifies the option name.
                type: str
                returned: success
            value:
                description:
                    - Specifies the option value.
                type: str
                returned: success
    ip_address:
        description:
            - Specifies the port IP address.
        type: str
        returned: success
    name:
        description:
            - Specifies the port name. The value can contain no more than 255
              characters.
        type: str
        returned: success
    security_groups:
        description:
            - Specifies the ID of the security group.
        type: list
        returned: success
    mac_address:
        description:
            - Specifies the port MAC address.
        type: str
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
            ), default=dict()),
            subnet_id=dict(type='str', required=True),
            admin_state_up=dict(type='bool'),
            allowed_address_pairs=dict(
                type='list', elements='dict',
                options=dict(
                    ip_address=dict(type='str'),
                    mac_address=dict(type='str')
                ),
            ),
            extra_dhcp_opts=dict(type='list', elements='dict', options=dict(
                name=dict(type='str'),
                value=dict(type='str')
            )),
            ip_address=dict(type='str'),
            name=dict(type='str'),
            security_groups=dict(type='list', elements='str')
        ),
        supports_check_mode=True,
    )


def main():
    """Main function"""

    module = build_module()
    config = Config(module, "vpc")

    try:
        resource = None
        if module.params['id']:
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
        "admin_state_up": module.params.get("admin_state_up"),
        "allowed_address_pairs": module.params.get("allowed_address_pairs"),
        "extra_dhcp_opts": module.params.get("extra_dhcp_opts"),
        "ip_address": module.params.get("ip_address"),
        "name": module.params.get("name"),
        "security_groups": module.params.get("security_groups"),
        "subnet_id": module.params.get("subnet_id"),
    }


def create(config):
    module = config.module
    client = config.client(get_region(module), "vpc", "project")
    timeout = 60 * int(module.params['timeouts']['create'].rstrip('m'))
    opts = user_input_parameters(module)

    params = build_create_parameters(opts)
    r = send_create_request(module, params, client)
    obj = async_wait_create(config, r, client, timeout)
    module.params['id'] = navigate_value(obj, ["port", "id"])


def update(config):
    module = config.module
    client = config.client(get_region(module), "vpc", "project")
    opts = user_input_parameters(module)

    params = build_update_parameters(opts)
    if params:
        send_update_request(module, params, client)


def delete(config):
    module = config.module
    client = config.client(get_region(module), "vpc", "project")

    send_delete_request(module, None, client)

    url = build_path(module, "ports/{id}")

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
        module.fail_json(msg="module(hwc_vpc_port): error "
                             "waiting for api(delete) to "
                             "be done, error= %s" % str(ex))


def read_resource(config, exclude_output=False):
    module = config.module
    client = config.client(get_region(module), "vpc", "project")

    res = {}

    r = send_read_request(module, client)
    res["read"] = fill_read_resp_body(r)

    array_index = {
        "read.fixed_ips": 0,
    }

    return update_properties(module, res, array_index, exclude_output)


def _build_query_link(opts):
    query_params = []

    v = navigate_value(opts, ["subnet_id"])
    if v:
        query_params.append("network_id=" + str(v))

    v = navigate_value(opts, ["name"])
    if v:
        query_params.append("name=" + str(v))

    v = navigate_value(opts, ["admin_state_up"])
    if v:
        query_params.append("admin_state_up=" + str(v))

    query_link = "?marker={marker}&limit=10"
    if query_params:
        query_link += "&" + "&".join(query_params)

    return query_link


def search_resource(config):
    module = config.module
    client = config.client(get_region(module), "vpc", "project")
    opts = user_input_parameters(module)
    identity_obj = _build_identity_object(opts)
    query_link = _build_query_link(opts)
    link = "ports" + query_link

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

    v = navigate_value(opts, ["admin_state_up"], None)
    if not is_empty_value(v):
        params["admin_state_up"] = v

    v = expand_create_allowed_address_pairs(opts, None)
    if not is_empty_value(v):
        params["allowed_address_pairs"] = v

    v = expand_create_extra_dhcp_opts(opts, None)
    if not is_empty_value(v):
        params["extra_dhcp_opts"] = v

    v = expand_create_fixed_ips(opts, None)
    if not is_empty_value(v):
        params["fixed_ips"] = v

    v = navigate_value(opts, ["name"], None)
    if not is_empty_value(v):
        params["name"] = v

    v = navigate_value(opts, ["subnet_id"], None)
    if not is_empty_value(v):
        params["network_id"] = v

    v = navigate_value(opts, ["security_groups"], None)
    if not is_empty_value(v):
        params["security_groups"] = v

    if not params:
        return params

    params = {"port": params}

    return params


def expand_create_allowed_address_pairs(d, array_index):
    new_array_index = dict()
    if array_index:
        new_array_index.update(array_index)

    req = []

    v = navigate_value(d, ["allowed_address_pairs"],
                       new_array_index)
    if not v:
        return req
    n = len(v)
    for i in range(n):
        new_array_index["allowed_address_pairs"] = i
        transformed = dict()

        v = navigate_value(d, ["allowed_address_pairs", "ip_address"],
                           new_array_index)
        if not is_empty_value(v):
            transformed["ip_address"] = v

        v = navigate_value(d, ["allowed_address_pairs", "mac_address"],
                           new_array_index)
        if not is_empty_value(v):
            transformed["mac_address"] = v

        if transformed:
            req.append(transformed)

    return req


def expand_create_extra_dhcp_opts(d, array_index):
    new_array_index = dict()
    if array_index:
        new_array_index.update(array_index)

    req = []

    v = navigate_value(d, ["extra_dhcp_opts"],
                       new_array_index)
    if not v:
        return req
    n = len(v)
    for i in range(n):
        new_array_index["extra_dhcp_opts"] = i
        transformed = dict()

        v = navigate_value(d, ["extra_dhcp_opts", "name"], new_array_index)
        if not is_empty_value(v):
            transformed["opt_name"] = v

        v = navigate_value(d, ["extra_dhcp_opts", "value"], new_array_index)
        if not is_empty_value(v):
            transformed["opt_value"] = v

        if transformed:
            req.append(transformed)

    return req


def expand_create_fixed_ips(d, array_index):
    new_array_index = dict()
    if array_index:
        new_array_index.update(array_index)

    req = []

    n = 1
    for i in range(n):
        transformed = dict()

        v = navigate_value(d, ["ip_address"], new_array_index)
        if not is_empty_value(v):
            transformed["ip_address"] = v

        if transformed:
            req.append(transformed)

    return req


def send_create_request(module, params, client):
    url = "ports"
    try:
        r = client.post(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_port): error running "
               "api(create), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def async_wait_create(config, result, client, timeout):
    module = config.module

    path_parameters = {
        "port_id": ["port", "id"],
    }
    data = dict((key, navigate_value(result, path))
                for key, path in path_parameters.items())

    url = build_path(module, "ports/{port_id}", data)

    def _query_status():
        r = None
        try:
            r = client.get(url, timeout=timeout)
        except HwcClientException:
            return None, ""

        try:
            s = navigate_value(r, ["port", "status"])
            return r, s
        except Exception:
            return None, ""

    try:
        return wait_to_finish(
            ["ACTIVE", "DOWN"],
            ["BUILD"],
            _query_status, timeout)
    except Exception as ex:
        module.fail_json(msg="module(hwc_vpc_port): error "
                             "waiting for api(create) to "
                             "be done, error= %s" % str(ex))


def build_update_parameters(opts):
    params = dict()

    v = expand_update_allowed_address_pairs(opts, None)
    if v is not None:
        params["allowed_address_pairs"] = v

    v = expand_update_extra_dhcp_opts(opts, None)
    if v is not None:
        params["extra_dhcp_opts"] = v

    v = navigate_value(opts, ["name"], None)
    if not is_empty_value(v):
        params["name"] = v

    v = navigate_value(opts, ["security_groups"], None)
    if not is_empty_value(v):
        params["security_groups"] = v

    if not params:
        return params

    params = {"port": params}

    return params


def expand_update_allowed_address_pairs(d, array_index):
    new_array_index = dict()
    if array_index:
        new_array_index.update(array_index)

    req = []

    v = navigate_value(d, ["allowed_address_pairs"],
                       new_array_index)
    if not v:
        return req
    n = len(v)
    for i in range(n):
        new_array_index["allowed_address_pairs"] = i
        transformed = dict()

        v = navigate_value(d, ["allowed_address_pairs", "ip_address"],
                           new_array_index)
        if not is_empty_value(v):
            transformed["ip_address"] = v

        v = navigate_value(d, ["allowed_address_pairs", "mac_address"],
                           new_array_index)
        if not is_empty_value(v):
            transformed["mac_address"] = v

        if transformed:
            req.append(transformed)

    return req


def expand_update_extra_dhcp_opts(d, array_index):
    new_array_index = dict()
    if array_index:
        new_array_index.update(array_index)

    req = []

    v = navigate_value(d, ["extra_dhcp_opts"],
                       new_array_index)
    if not v:
        return req
    n = len(v)
    for i in range(n):
        new_array_index["extra_dhcp_opts"] = i
        transformed = dict()

        v = navigate_value(d, ["extra_dhcp_opts", "name"], new_array_index)
        if not is_empty_value(v):
            transformed["opt_name"] = v

        v = navigate_value(d, ["extra_dhcp_opts", "value"], new_array_index)
        if not is_empty_value(v):
            transformed["opt_value"] = v

        if transformed:
            req.append(transformed)

    return req


def send_update_request(module, params, client):
    url = build_path(module, "ports/{id}")

    try:
        r = client.put(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_port): error running "
               "api(update), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def send_delete_request(module, params, client):
    url = build_path(module, "ports/{id}")

    try:
        r = client.delete(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_port): error running "
               "api(delete), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def send_read_request(module, client):
    url = build_path(module, "ports/{id}")

    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_port): error running "
               "api(read), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return navigate_value(r, ["port"], None)


def fill_read_resp_body(body):
    result = dict()

    result["admin_state_up"] = body.get("admin_state_up")

    v = fill_read_resp_allowed_address_pairs(body.get("allowed_address_pairs"))
    result["allowed_address_pairs"] = v

    result["binding_host_id"] = body.get("binding_host_id")

    result["binding_vnic_type"] = body.get("binding_vnic_type")

    result["device_id"] = body.get("device_id")

    result["device_owner"] = body.get("device_owner")

    result["dns_name"] = body.get("dns_name")

    v = fill_read_resp_extra_dhcp_opts(body.get("extra_dhcp_opts"))
    result["extra_dhcp_opts"] = v

    v = fill_read_resp_fixed_ips(body.get("fixed_ips"))
    result["fixed_ips"] = v

    result["id"] = body.get("id")

    result["mac_address"] = body.get("mac_address")

    result["name"] = body.get("name")

    result["network_id"] = body.get("network_id")

    result["security_groups"] = body.get("security_groups")

    result["status"] = body.get("status")

    result["tenant_id"] = body.get("tenant_id")

    return result


def fill_read_resp_allowed_address_pairs(value):
    if not value:
        return None

    result = []
    for item in value:
        val = dict()

        val["ip_address"] = item.get("ip_address")

        val["mac_address"] = item.get("mac_address")

        result.append(val)

    return result


def fill_read_resp_extra_dhcp_opts(value):
    if not value:
        return None

    result = []
    for item in value:
        val = dict()

        val["opt_name"] = item.get("opt_name")

        val["opt_value"] = item.get("opt_value")

        result.append(val)

    return result


def fill_read_resp_fixed_ips(value):
    if not value:
        return None

    result = []
    for item in value:
        val = dict()

        val["ip_address"] = item.get("ip_address")

        result.append(val)

    return result


def update_properties(module, response, array_index, exclude_output=False):
    r = user_input_parameters(module)

    v = navigate_value(response, ["read", "admin_state_up"], array_index)
    r["admin_state_up"] = v

    v = r.get("allowed_address_pairs")
    v = flatten_allowed_address_pairs(response, array_index, v, exclude_output)
    r["allowed_address_pairs"] = v

    v = r.get("extra_dhcp_opts")
    v = flatten_extra_dhcp_opts(response, array_index, v, exclude_output)
    r["extra_dhcp_opts"] = v

    v = navigate_value(response, ["read", "fixed_ips", "ip_address"],
                       array_index)
    r["ip_address"] = v

    if not exclude_output:
        v = navigate_value(response, ["read", "mac_address"], array_index)
        r["mac_address"] = v

    v = navigate_value(response, ["read", "name"], array_index)
    r["name"] = v

    v = navigate_value(response, ["read", "security_groups"], array_index)
    r["security_groups"] = v

    v = navigate_value(response, ["read", "network_id"], array_index)
    r["subnet_id"] = v

    return r


def flatten_allowed_address_pairs(d, array_index,
                                  current_value, exclude_output):
    n = 0
    result = current_value
    has_init_value = True
    if result:
        n = len(result)
    else:
        has_init_value = False
        result = []
        v = navigate_value(d, ["read", "allowed_address_pairs"],
                           array_index)
        if not v:
            return current_value
        n = len(v)

    new_array_index = dict()
    if array_index:
        new_array_index.update(array_index)

    for i in range(n):
        new_array_index["read.allowed_address_pairs"] = i

        val = dict()
        if len(result) >= (i + 1) and result[i]:
            val = result[i]

        v = navigate_value(d, ["read", "allowed_address_pairs", "ip_address"],
                           new_array_index)
        val["ip_address"] = v

        v = navigate_value(d, ["read", "allowed_address_pairs", "mac_address"],
                           new_array_index)
        val["mac_address"] = v

        if len(result) >= (i + 1):
            result[i] = val
        else:
            for v in val.values():
                if v is not None:
                    result.append(val)
                    break

    return result if (has_init_value or result) else current_value


def flatten_extra_dhcp_opts(d, array_index, current_value, exclude_output):
    n = 0
    result = current_value
    has_init_value = True
    if result:
        n = len(result)
    else:
        has_init_value = False
        result = []
        v = navigate_value(d, ["read", "extra_dhcp_opts"],
                           array_index)
        if not v:
            return current_value
        n = len(v)

    new_array_index = dict()
    if array_index:
        new_array_index.update(array_index)

    for i in range(n):
        new_array_index["read.extra_dhcp_opts"] = i

        val = dict()
        if len(result) >= (i + 1) and result[i]:
            val = result[i]

        v = navigate_value(d, ["read", "extra_dhcp_opts", "opt_name"],
                           new_array_index)
        val["name"] = v

        v = navigate_value(d, ["read", "extra_dhcp_opts", "opt_value"],
                           new_array_index)
        val["value"] = v

        if len(result) >= (i + 1):
            result[i] = val
        else:
            for v in val.values():
                if v is not None:
                    result.append(val)
                    break

    return result if (has_init_value or result) else current_value


def send_list_request(module, client, url):

    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_port): error running "
               "api(list), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return navigate_value(r, ["ports"], None)


def _build_identity_object(all_opts):
    result = dict()

    v = navigate_value(all_opts, ["admin_state_up"], None)
    result["admin_state_up"] = v

    v = expand_list_allowed_address_pairs(all_opts, None)
    result["allowed_address_pairs"] = v

    result["binding_host_id"] = None

    result["binding_vnic_type"] = None

    result["device_id"] = None

    result["device_owner"] = None

    result["dns_name"] = None

    v = expand_list_extra_dhcp_opts(all_opts, None)
    result["extra_dhcp_opts"] = v

    v = expand_list_fixed_ips(all_opts, None)
    result["fixed_ips"] = v

    result["id"] = None

    result["mac_address"] = None

    v = navigate_value(all_opts, ["name"], None)
    result["name"] = v

    v = navigate_value(all_opts, ["subnet_id"], None)
    result["network_id"] = v

    v = navigate_value(all_opts, ["security_groups"], None)
    result["security_groups"] = v

    result["status"] = None

    result["tenant_id"] = None

    return result


def expand_list_allowed_address_pairs(d, array_index):
    new_array_index = dict()
    if array_index:
        new_array_index.update(array_index)

    req = []

    v = navigate_value(d, ["allowed_address_pairs"],
                       new_array_index)

    n = len(v) if v else 1
    for i in range(n):
        new_array_index["allowed_address_pairs"] = i
        transformed = dict()

        v = navigate_value(d, ["allowed_address_pairs", "ip_address"],
                           new_array_index)
        transformed["ip_address"] = v

        v = navigate_value(d, ["allowed_address_pairs", "mac_address"],
                           new_array_index)
        transformed["mac_address"] = v

        for v in transformed.values():
            if v is not None:
                req.append(transformed)
                break

    return req if req else None


def expand_list_extra_dhcp_opts(d, array_index):
    new_array_index = dict()
    if array_index:
        new_array_index.update(array_index)

    req = []

    v = navigate_value(d, ["extra_dhcp_opts"],
                       new_array_index)

    n = len(v) if v else 1
    for i in range(n):
        new_array_index["extra_dhcp_opts"] = i
        transformed = dict()

        v = navigate_value(d, ["extra_dhcp_opts", "name"], new_array_index)
        transformed["opt_name"] = v

        v = navigate_value(d, ["extra_dhcp_opts", "value"], new_array_index)
        transformed["opt_value"] = v

        for v in transformed.values():
            if v is not None:
                req.append(transformed)
                break

    return req if req else None


def expand_list_fixed_ips(d, array_index):
    new_array_index = dict()
    if array_index:
        new_array_index.update(array_index)

    req = []

    n = 1
    for i in range(n):
        transformed = dict()

        v = navigate_value(d, ["ip_address"], new_array_index)
        transformed["ip_address"] = v

        for v in transformed.values():
            if v is not None:
                req.append(transformed)
                break

    return req if req else None


def fill_list_resp_body(body):
    result = dict()

    result["admin_state_up"] = body.get("admin_state_up")

    v = fill_list_resp_allowed_address_pairs(body.get("allowed_address_pairs"))
    result["allowed_address_pairs"] = v

    result["binding_host_id"] = body.get("binding_host_id")

    result["binding_vnic_type"] = body.get("binding_vnic_type")

    result["device_id"] = body.get("device_id")

    result["device_owner"] = body.get("device_owner")

    result["dns_name"] = body.get("dns_name")

    v = fill_list_resp_extra_dhcp_opts(body.get("extra_dhcp_opts"))
    result["extra_dhcp_opts"] = v

    v = fill_list_resp_fixed_ips(body.get("fixed_ips"))
    result["fixed_ips"] = v

    result["id"] = body.get("id")

    result["mac_address"] = body.get("mac_address")

    result["name"] = body.get("name")

    result["network_id"] = body.get("network_id")

    result["security_groups"] = body.get("security_groups")

    result["status"] = body.get("status")

    result["tenant_id"] = body.get("tenant_id")

    return result


def fill_list_resp_allowed_address_pairs(value):
    if not value:
        return None

    result = []
    for item in value:
        val = dict()

        val["ip_address"] = item.get("ip_address")

        val["mac_address"] = item.get("mac_address")

        result.append(val)

    return result


def fill_list_resp_extra_dhcp_opts(value):
    if not value:
        return None

    result = []
    for item in value:
        val = dict()

        val["opt_name"] = item.get("opt_name")

        val["opt_value"] = item.get("opt_value")

        result.append(val)

    return result


def fill_list_resp_fixed_ips(value):
    if not value:
        return None

    result = []
    for item in value:
        val = dict()

        val["ip_address"] = item.get("ip_address")

        result.append(val)

    return result


if __name__ == '__main__':
    main()
