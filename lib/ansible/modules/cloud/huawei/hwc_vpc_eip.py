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
module: hwc_vpc_eip
description:
    - elastic ip management.
short_description: Creates a resource of Vpc/EIP in Huawei Cloud
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
                default: '5m'
            update:
                description:
                    - The timeouts for update operation.
                type: str
                default: '5m'
    type:
        description:
            - Specifies the EIP type.
        type: str
        required: true
    dedicated_bandwidth:
        description:
            - Specifies the dedicated bandwidth object.
        type: dict
        required: false
        suboptions:
            charge_mode:
                description:
                    - Specifies whether the bandwidth is billed by traffic or
                      by bandwidth size. The value can be bandwidth or traffic.
                      If this parameter is left blank or is null character
                      string, default value bandwidth is used. For IPv6
                      addresses, the default parameter value is bandwidth
                      outside China and is traffic in China.
                type: str
                required: true
            name:
                description:
                    - Specifies the bandwidth name. The value is a string of 1
                      to 64 characters that can contain letters, digits,
                      underscores C(_), hyphens (-), and periods (.).
                type: str
                required: true
            size:
                description:
                    - Specifies the bandwidth size. The value ranges from 1
                      Mbit/s to 2000 Mbit/s by default. (The specific range may
                      vary depending on the configuration in each region. You
                      can see the bandwidth range of each region on the
                      management console.) The minimum unit for bandwidth
                      adjustment varies depending on the bandwidth range. The
                      details are as follows.
                    - The minimum unit is 1 Mbit/s if the allowed bandwidth
                      size ranges from 0 to 300 Mbit/s (with 300 Mbit/s
                      included).
                    - The minimum unit is 50 Mbit/s if the allowed bandwidth
                      size ranges 300 Mbit/s to 1000 Mbit/s (with 1000 Mbit/s
                      included).
                    - The minimum unit is 500 Mbit/s if the allowed bandwidth
                      size is greater than 1000 Mbit/s.
                type: int
                required: true
    enterprise_project_id:
        description:
            - Specifies the enterprise project ID.
        type: str
        required: false
    ip_version:
        description:
            - The value can be 4 (IPv4 address) or 6 (IPv6 address). If this
              parameter is left blank, an IPv4 address will be assigned.
        type: int
        required: false
    ipv4_address:
        description:
            - Specifies the obtained IPv4 EIP. The system automatically assigns
              an EIP if you do not specify it.
        type: str
        required: false
    port_id:
        description:
            - Specifies the port ID. This parameter is returned only when a
              private IP address is bound with the EIP.
        type: str
        required: false
    shared_bandwidth_id:
        description:
            - Specifies the ID of shared bandwidth.
        type: str
        required: false
extends_documentation_fragment: hwc
'''

EXAMPLES = '''
# create an eip and bind it to a port
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
  register: port
- name: create an eip and bind it to a port
  hwc_vpc_eip:
    type: "5_bgp"
    dedicated_bandwidth:
      charge_mode: "traffic"
      name: "ansible_test_dedicated_bandwidth"
      size: 1
    port_id: "{{ port.id }}"
'''

RETURN = '''
    type:
        description:
            - Specifies the EIP type.
        type: str
        returned: success
    dedicated_bandwidth:
        description:
            - Specifies the dedicated bandwidth object.
        type: dict
        returned: success
        contains:
            charge_mode:
                description:
                    - Specifies whether the bandwidth is billed by traffic or
                      by bandwidth size. The value can be bandwidth or traffic.
                      If this parameter is left blank or is null character
                      string, default value bandwidth is used. For IPv6
                      addresses, the default parameter value is bandwidth
                      outside China and is traffic in China.
                type: str
                returned: success
            name:
                description:
                    - Specifies the bandwidth name. The value is a string of 1
                      to 64 characters that can contain letters, digits,
                      underscores C(_), hyphens (-), and periods (.).
                type: str
                returned: success
            size:
                description:
                    - Specifies the bandwidth size. The value ranges from 1
                      Mbit/s to 2000 Mbit/s by default. (The specific range may
                      vary depending on the configuration in each region. You
                      can see the bandwidth range of each region on the
                      management console.) The minimum unit for bandwidth
                      adjustment varies depending on the bandwidth range. The
                      details are as follows:.
                    - The minimum unit is 1 Mbit/s if the allowed bandwidth
                      size ranges from 0 to 300 Mbit/s (with 300 Mbit/s
                      included).
                    - The minimum unit is 50 Mbit/s if the allowed bandwidth
                      size ranges 300 Mbit/s to 1000 Mbit/s (with 1000 Mbit/s
                      included).
                    - The minimum unit is 500 Mbit/s if the allowed bandwidth
                      size is greater than 1000 Mbit/s.
                type: int
                returned: success
            id:
                description:
                    - Specifies the ID of dedicated bandwidth.
                type: str
                returned: success
    enterprise_project_id:
        description:
            - Specifies the enterprise project ID.
        type: str
        returned: success
    ip_version:
        description:
            - The value can be 4 (IPv4 address) or 6 (IPv6 address). If this
              parameter is left blank, an IPv4 address will be assigned.
        type: int
        returned: success
    ipv4_address:
        description:
            - Specifies the obtained IPv4 EIP. The system automatically assigns
              an EIP if you do not specify it.
        type: str
        returned: success
    port_id:
        description:
            - Specifies the port ID. This parameter is returned only when a
              private IP address is bound with the EIP.
        type: str
        returned: success
    shared_bandwidth_id:
        description:
            - Specifies the ID of shared bandwidth.
        type: str
        returned: success
    create_time:
        description:
            - Specifies the time (UTC time) when the EIP was assigned.
        type: str
        returned: success
    ipv6_address:
        description:
            - Specifies the obtained IPv6 EIP.
        type: str
        returned: success
    private_ip_address:
        description:
            - Specifies the private IP address bound with the EIP. This
              parameter is returned only when a private IP address is bound
              with the EIP.
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
                create=dict(default='5m', type='str'),
                update=dict(default='5m', type='str'),
            ), default=dict()),
            type=dict(type='str', required=True),
            dedicated_bandwidth=dict(type='dict', options=dict(
                charge_mode=dict(type='str', required=True),
                name=dict(type='str', required=True),
                size=dict(type='int', required=True)
            )),
            enterprise_project_id=dict(type='str'),
            ip_version=dict(type='int'),
            ipv4_address=dict(type='str'),
            port_id=dict(type='str'),
            shared_bandwidth_id=dict(type='str')
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
        "dedicated_bandwidth": module.params.get("dedicated_bandwidth"),
        "enterprise_project_id": module.params.get("enterprise_project_id"),
        "ip_version": module.params.get("ip_version"),
        "ipv4_address": module.params.get("ipv4_address"),
        "port_id": module.params.get("port_id"),
        "shared_bandwidth_id": module.params.get("shared_bandwidth_id"),
        "type": module.params.get("type"),
    }


def create(config):
    module = config.module
    client = config.client(get_region(module), "vpc", "project")
    timeout = 60 * int(module.params['timeouts']['create'].rstrip('m'))
    opts = user_input_parameters(module)

    params = build_create_parameters(opts)
    r = send_create_request(module, params, client)
    obj = async_wait_create(config, r, client, timeout)
    module.params['id'] = navigate_value(obj, ["publicip", "id"])


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

    if module.params["port_id"]:
        module.params["port_id"] = ""
        update(config)

    send_delete_request(module, None, client)

    url = build_path(module, "publicips/{id}")

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
        module.fail_json(msg="module(hwc_vpc_eip): error "
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
    query_params = []

    v = navigate_value(opts, ["ip_version"])
    if v:
        query_params.append("ip_version=" + str(v))

    v = navigate_value(opts, ["enterprise_project_id"])
    if v:
        query_params.append("enterprise_project_id=" + str(v))

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
    link = "publicips" + query_link

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

    v = expand_create_bandwidth(opts, None)
    if not is_empty_value(v):
        params["bandwidth"] = v

    v = navigate_value(opts, ["enterprise_project_id"], None)
    if not is_empty_value(v):
        params["enterprise_project_id"] = v

    v = expand_create_publicip(opts, None)
    if not is_empty_value(v):
        params["publicip"] = v

    return params


def expand_create_bandwidth(d, array_index):
    v = navigate_value(d, ["dedicated_bandwidth"], array_index)
    sbwid = navigate_value(d, ["shared_bandwidth_id"], array_index)
    if v and sbwid:
        raise Exception("don't input shared_bandwidth_id and "
                        "dedicated_bandwidth at same time")

    if not (v or sbwid):
        raise Exception("must input shared_bandwidth_id or "
                        "dedicated_bandwidth")

    if sbwid:
        return {
            "id": sbwid,
            "share_type": "WHOLE"}

    return {
        "charge_mode": v["charge_mode"],
        "name": v["name"],
        "share_type": "PER",
        "size": v["size"]}


def expand_create_publicip(d, array_index):
    r = dict()

    v = navigate_value(d, ["ipv4_address"], array_index)
    if not is_empty_value(v):
        r["ip_address"] = v

    v = navigate_value(d, ["ip_version"], array_index)
    if not is_empty_value(v):
        r["ip_version"] = v

    v = navigate_value(d, ["type"], array_index)
    if not is_empty_value(v):
        r["type"] = v

    return r


def send_create_request(module, params, client):
    url = "publicips"
    try:
        r = client.post(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_eip): error running "
               "api(create), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def async_wait_create(config, result, client, timeout):
    module = config.module

    path_parameters = {
        "publicip_id": ["publicip", "id"],
    }
    data = dict((key, navigate_value(result, path))
                for key, path in path_parameters.items())

    url = build_path(module, "publicips/{publicip_id}", data)

    def _query_status():
        r = None
        try:
            r = client.get(url, timeout=timeout)
        except HwcClientException:
            return None, ""

        try:
            s = navigate_value(r, ["publicip", "status"])
            return r, s
        except Exception:
            return None, ""

    try:
        return wait_to_finish(
            ["ACTIVE", "DOWN"],
            None,
            _query_status, timeout)
    except Exception as ex:
        module.fail_json(msg="module(hwc_vpc_eip): error "
                             "waiting for api(create) to "
                             "be done, error= %s" % str(ex))


def build_update_parameters(opts):
    params = dict()

    v = navigate_value(opts, ["ip_version"], None)
    if not is_empty_value(v):
        params["ip_version"] = v

    v = navigate_value(opts, ["port_id"], None)
    if v is not None:
        params["port_id"] = v

    if not params:
        return params

    params = {"publicip": params}

    return params


def send_update_request(module, params, client):
    url = build_path(module, "publicips/{id}")

    try:
        r = client.put(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_eip): error running "
               "api(update), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def async_wait_update(config, result, client, timeout):
    module = config.module

    url = build_path(module, "publicips/{id}")

    def _query_status():
        r = None
        try:
            r = client.get(url, timeout=timeout)
        except HwcClientException:
            return None, ""

        try:
            s = navigate_value(r, ["publicip", "status"])
            return r, s
        except Exception:
            return None, ""

    try:
        return wait_to_finish(
            ["ACTIVE", "DOWN"],
            None,
            _query_status, timeout)
    except Exception as ex:
        module.fail_json(msg="module(hwc_vpc_eip): error "
                             "waiting for api(update) to "
                             "be done, error= %s" % str(ex))


def send_delete_request(module, params, client):
    url = build_path(module, "publicips/{id}")

    try:
        r = client.delete(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_eip): error running "
               "api(delete), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def send_read_request(module, client):
    url = build_path(module, "publicips/{id}")

    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_eip): error running "
               "api(read), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return navigate_value(r, ["publicip"], None)


def fill_read_resp_body(body):
    result = dict()

    result["bandwidth_id"] = body.get("bandwidth_id")

    result["bandwidth_name"] = body.get("bandwidth_name")

    result["bandwidth_share_type"] = body.get("bandwidth_share_type")

    result["bandwidth_size"] = body.get("bandwidth_size")

    result["create_time"] = body.get("create_time")

    result["enterprise_project_id"] = body.get("enterprise_project_id")

    result["id"] = body.get("id")

    result["ip_version"] = body.get("ip_version")

    result["port_id"] = body.get("port_id")

    result["private_ip_address"] = body.get("private_ip_address")

    result["public_ip_address"] = body.get("public_ip_address")

    result["public_ipv6_address"] = body.get("public_ipv6_address")

    result["status"] = body.get("status")

    result["tenant_id"] = body.get("tenant_id")

    result["type"] = body.get("type")

    return result


def update_properties(module, response, array_index, exclude_output=False):
    r = user_input_parameters(module)

    if not exclude_output:
        v = navigate_value(response, ["read", "create_time"], array_index)
        r["create_time"] = v

    v = r.get("dedicated_bandwidth")
    v = flatten_dedicated_bandwidth(response, array_index, v, exclude_output)
    r["dedicated_bandwidth"] = v

    v = navigate_value(response, ["read", "enterprise_project_id"],
                       array_index)
    r["enterprise_project_id"] = v

    v = navigate_value(response, ["read", "ip_version"], array_index)
    r["ip_version"] = v

    v = navigate_value(response, ["read", "public_ip_address"], array_index)
    r["ipv4_address"] = v

    if not exclude_output:
        v = navigate_value(response, ["read", "public_ipv6_address"],
                           array_index)
        r["ipv6_address"] = v

    v = navigate_value(response, ["read", "port_id"], array_index)
    r["port_id"] = v

    if not exclude_output:
        v = navigate_value(response, ["read", "private_ip_address"],
                           array_index)
        r["private_ip_address"] = v

    v = r.get("shared_bandwidth_id")
    v = flatten_shared_bandwidth_id(response, array_index, v, exclude_output)
    r["shared_bandwidth_id"] = v

    v = navigate_value(response, ["read", "type"], array_index)
    r["type"] = v

    return r


def flatten_dedicated_bandwidth(d, array_index, current_value, exclude_output):
    v = navigate_value(d, ["read", "bandwidth_share_type"], array_index)
    if not (v and v == "PER"):
        return current_value

    result = current_value
    if not result:
        result = dict()

    if not exclude_output:
        v = navigate_value(d, ["read", "bandwidth_id"], array_index)
        if v is not None:
            result["id"] = v

    v = navigate_value(d, ["read", "bandwidth_name"], array_index)
    if v is not None:
        result["name"] = v

    v = navigate_value(d, ["read", "bandwidth_size"], array_index)
    if v is not None:
        result["size"] = v

    return result if result else current_value


def flatten_shared_bandwidth_id(d, array_index, current_value, exclude_output):
    v = navigate_value(d, ["read", "bandwidth_id"], array_index)

    v1 = navigate_value(d, ["read", "bandwidth_share_type"], array_index)

    return v if (v1 and v1 == "WHOLE") else current_value


def send_list_request(module, client, url):

    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_eip): error running "
               "api(list), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return navigate_value(r, ["publicips"], None)


def _build_identity_object(all_opts):
    result = dict()

    v = expand_list_bandwidth_id(all_opts, None)
    result["bandwidth_id"] = v

    v = navigate_value(all_opts, ["dedicated_bandwidth", "name"], None)
    result["bandwidth_name"] = v

    result["bandwidth_share_type"] = None

    v = navigate_value(all_opts, ["dedicated_bandwidth", "size"], None)
    result["bandwidth_size"] = v

    result["create_time"] = None

    v = navigate_value(all_opts, ["enterprise_project_id"], None)
    result["enterprise_project_id"] = v

    result["id"] = None

    v = navigate_value(all_opts, ["ip_version"], None)
    result["ip_version"] = v

    v = navigate_value(all_opts, ["port_id"], None)
    result["port_id"] = v

    result["private_ip_address"] = None

    v = navigate_value(all_opts, ["ipv4_address"], None)
    result["public_ip_address"] = v

    result["public_ipv6_address"] = None

    result["status"] = None

    result["tenant_id"] = None

    v = navigate_value(all_opts, ["type"], None)
    result["type"] = v

    return result


def expand_list_bandwidth_id(d, array_index):
    v = navigate_value(d, ["dedicated_bandwidth"], array_index)
    sbwid = navigate_value(d, ["shared_bandwidth_id"], array_index)
    if v and sbwid:
        raise Exception("don't input shared_bandwidth_id and "
                        "dedicated_bandwidth at same time")

    return sbwid


def fill_list_resp_body(body):
    result = dict()

    result["bandwidth_id"] = body.get("bandwidth_id")

    result["bandwidth_name"] = body.get("bandwidth_name")

    result["bandwidth_share_type"] = body.get("bandwidth_share_type")

    result["bandwidth_size"] = body.get("bandwidth_size")

    result["create_time"] = body.get("create_time")

    result["enterprise_project_id"] = body.get("enterprise_project_id")

    result["id"] = body.get("id")

    result["ip_version"] = body.get("ip_version")

    result["port_id"] = body.get("port_id")

    result["private_ip_address"] = body.get("private_ip_address")

    result["public_ip_address"] = body.get("public_ip_address")

    result["public_ipv6_address"] = body.get("public_ipv6_address")

    result["status"] = body.get("status")

    result["tenant_id"] = body.get("tenant_id")

    result["type"] = body.get("type")

    return result


if __name__ == '__main__':
    main()
