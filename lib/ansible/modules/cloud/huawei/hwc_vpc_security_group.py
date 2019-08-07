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
module: hwc_vpc_security_group
description:
    - vpc security group management.
short_description: Creates a resource of Vpc/SecurityGroup in Huawei Cloud
version_added: '2.9'
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
    filters:
        description:
            - A list of filters to apply when deciding whether existing
              resources match and should be altered. The item of filters
              is the name of input options.
        type: list
        required: true
    name:
        description:
            - Specifies the security group name. The value is a string of 1 to
              64 characters that can contain letters, digits, underscores C(_),
              hyphens (-), and periods (.).
        type: str
        required: true
    enterprise_project_id:
        description:
            - Specifies the enterprise project ID. When creating a security
              group, associate the enterprise project ID with the security
              group.
        type: str
        required: false
    vpc_id:
        description:
            - Specifies the resource ID of the VPC to which the security group
              belongs.
        type: str
        required: false
extends_documentation_fragment: hwc
'''

EXAMPLES = '''
# create a security group
- name: create a security group
  hwc_vpc_security_group:
    name: "ansible_network_security_group_test"
    filters:
      - "name"
'''

RETURN = '''
    name:
        description:
            - Specifies the security group name. The value is a string of 1 to
              64 characters that can contain letters, digits, underscores C(_),
              hyphens (-), and periods (.).
        type: str
        returned: success
    enterprise_project_id:
        description:
            - Specifies the enterprise project ID. When creating a security
              group, associate the enterprise project ID with the security
              group.
        type: str
        returned: success
    vpc_id:
        description:
            - Specifies the resource ID of the VPC to which the security group
              belongs.
        type: str
        returned: success
    description:
        description:
            - Specifies supplementary information about the security group.
        type: str
        returned: success
    rules:
        description:
            - Specifies the security group rule, which ensures that resources
              in the security group can communicate with one another.
        type: complex
        returned: success
        contains:
            description:
                description:
                    - Provides supplementary information about the security
                      group rule.
                type: str
                returned: success
            direction:
                description:
                    - Specifies the direction of access control. The value can
                      be egress or ingress.
                type: str
                returned: success
            ethertype:
                description:
                    - Specifies the IP protocol version. The value can be IPv4
                      or IPv6.
                type: str
                returned: success
            id:
                description:
                    - Specifies the security group rule ID.
                type: str
                returned: success
            port_range_max:
                description:
                    - Specifies the end port number. The value ranges from 1 to
                      65535. If the protocol is not icmp, the value cannot be
                      smaller than the port_range_min value. An empty value
                      indicates all ports.
                type: int
                returned: success
            port_range_min:
                description:
                    - Specifies the start port number. The value ranges from 1
                      to 65535. The value cannot be greater than the
                      port_range_max value. An empty value indicates all ports.
                type: int
                returned: success
            protocol:
                description:
                    - Specifies the protocol type. The value can be icmp, tcp,
                      udp, or others. If the parameter is left blank, the
                      security group supports all protocols.
                type: str
                returned: success
            remote_address_group_id:
                description:
                    - Specifies the ID of remote IP address group.
                type: str
                returned: success
            remote_group_id:
                description:
                    - Specifies the ID of the peer security group.
                type: str
                returned: success
            remote_ip_prefix:
                description:
                    - Specifies the remote IP address. If the access control
                      direction is set to egress, the parameter specifies the
                      source IP address. If the access control direction is set
                      to ingress, the parameter specifies the destination IP
                      address.
                type: str
                returned: success
'''

from ansible.module_utils.hwc_utils import (
    Config, HwcClientException, HwcModule, are_different_dicts, build_path,
    get_region, is_empty_value, navigate_value)


def build_module():
    return HwcModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'],
                       type='str'),
            filters=dict(required=True, type='list', elements='str'),
            name=dict(type='str', required=True),
            enterprise_project_id=dict(type='str'),
            vpc_id=dict(type='str')
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
                raise Exception("find more than one resources(%s)" % ", ".join([
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
        "enterprise_project_id": module.params.get("enterprise_project_id"),
        "name": module.params.get("name"),
        "vpc_id": module.params.get("vpc_id"),
    }


def create(config):
    module = config.module
    client = config.client(get_region(module), "vpc", "project")
    opts = user_input_parameters(module)

    params = build_create_parameters(opts)
    r = send_create_request(module, params, client)
    module.params['id'] = navigate_value(r, ["security_group", "id"])


def delete(config):
    module = config.module
    client = config.client(get_region(module), "vpc", "project")

    send_delete_request(module, None, client)


def read_resource(config, exclude_output=False):
    module = config.module
    client = config.client(get_region(module), "vpc", "project")

    res = {}

    r = send_read_request(module, client)
    res["read"] = fill_read_resp_body(r)

    return update_properties(module, res, None, exclude_output)


def _build_query_link(opts):
    query_params = []

    v = navigate_value(opts, ["enterprise_project_id"])
    if v:
        query_params.append("enterprise_project_id=" + str(v))

    v = navigate_value(opts, ["vpc_id"])
    if v:
        query_params.append("vpc_id=" + str(v))

    query_link = "?marker={marker}&limit=10"
    if query_params:
        query_link += "&" + "&".join(query_params)

    return query_link


def search_resource(config):
    module = config.module
    client = config.client(get_region(module), "vpc", "project")
    opts = user_input_parameters(module)
    identity_obj = _build_identity_object(module, opts)
    query_link = _build_query_link(opts)
    link = "security-groups" + query_link

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

    v = navigate_value(opts, ["enterprise_project_id"], None)
    if not is_empty_value(v):
        params["enterprise_project_id"] = v

    v = navigate_value(opts, ["name"], None)
    if not is_empty_value(v):
        params["name"] = v

    v = navigate_value(opts, ["vpc_id"], None)
    if not is_empty_value(v):
        params["vpc_id"] = v

    if not params:
        return params

    params = {"security_group": params}

    return params


def send_create_request(module, params, client):
    url = "security-groups"
    try:
        r = client.post(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_security_group): error running "
               "api(create), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def send_delete_request(module, params, client):
    url = build_path(module, "security-groups/{id}")

    try:
        r = client.delete(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_security_group): error running "
               "api(delete), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def send_read_request(module, client):
    url = build_path(module, "security-groups/{id}")

    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_security_group): error running "
               "api(read), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return navigate_value(r, ["security_group"], None)


def fill_read_resp_body(body):
    result = dict()

    result["description"] = body.get("description")

    result["enterprise_project_id"] = body.get("enterprise_project_id")

    result["id"] = body.get("id")

    result["name"] = body.get("name")

    v = fill_read_resp_security_group_rules(body.get("security_group_rules"))
    result["security_group_rules"] = v

    result["vpc_id"] = body.get("vpc_id")

    return result


def fill_read_resp_security_group_rules(value):
    if not value:
        return None

    result = []
    for item in value:
        val = dict()

        val["description"] = item.get("description")

        val["direction"] = item.get("direction")

        val["ethertype"] = item.get("ethertype")

        val["id"] = item.get("id")

        val["port_range_max"] = item.get("port_range_max")

        val["port_range_min"] = item.get("port_range_min")

        val["protocol"] = item.get("protocol")

        val["remote_address_group_id"] = item.get("remote_address_group_id")

        val["remote_group_id"] = item.get("remote_group_id")

        val["remote_ip_prefix"] = item.get("remote_ip_prefix")

        val["security_group_id"] = item.get("security_group_id")

        result.append(val)

    return result


def update_properties(module, response, array_index, exclude_output=False):
    r = user_input_parameters(module)

    if not exclude_output:
        v = navigate_value(response, ["read", "description"], array_index)
        r["description"] = v

    v = navigate_value(response, ["read", "enterprise_project_id"],
                       array_index)
    r["enterprise_project_id"] = v

    v = navigate_value(response, ["read", "name"], array_index)
    r["name"] = v

    if not exclude_output:
        v = r.get("rules")
        v = flatten_rules(response, array_index, v, exclude_output)
        r["rules"] = v

    v = navigate_value(response, ["read", "vpc_id"], array_index)
    r["vpc_id"] = v

    return r


def flatten_rules(d, array_index, current_value, exclude_output):
    n = 0
    result = current_value
    has_init_value = True
    if result:
        n = len(result)
    else:
        has_init_value = False
        result = []
        v = navigate_value(d, ["read", "security_group_rules"],
                           array_index)
        if not v:
            return current_value
        n = len(v)

    new_array_index = dict()
    if array_index:
        new_array_index.update(array_index)

    for i in range(n):
        new_array_index["read.security_group_rules"] = i

        val = dict()
        if len(result) >= (i + 1) and result[i]:
            val = result[i]

        if not exclude_output:
            v = navigate_value(d, ["read", "security_group_rules", "description"],
                               new_array_index)
            val["description"] = v

        if not exclude_output:
            v = navigate_value(d, ["read", "security_group_rules", "direction"],
                               new_array_index)
            val["direction"] = v

        if not exclude_output:
            v = navigate_value(d, ["read", "security_group_rules", "ethertype"],
                               new_array_index)
            val["ethertype"] = v

        if not exclude_output:
            v = navigate_value(d, ["read", "security_group_rules", "id"],
                               new_array_index)
            val["id"] = v

        if not exclude_output:
            v = navigate_value(d, ["read", "security_group_rules", "port_range_max"],
                               new_array_index)
            val["port_range_max"] = v

        if not exclude_output:
            v = navigate_value(d, ["read", "security_group_rules", "port_range_min"],
                               new_array_index)
            val["port_range_min"] = v

        if not exclude_output:
            v = navigate_value(d, ["read", "security_group_rules", "protocol"],
                               new_array_index)
            val["protocol"] = v

        if not exclude_output:
            v = navigate_value(d, ["read", "security_group_rules", "remote_address_group_id"],
                               new_array_index)
            val["remote_address_group_id"] = v

        if not exclude_output:
            v = navigate_value(d, ["read", "security_group_rules", "remote_group_id"],
                               new_array_index)
            val["remote_group_id"] = v

        if not exclude_output:
            v = navigate_value(d, ["read", "security_group_rules", "remote_ip_prefix"],
                               new_array_index)
            val["remote_ip_prefix"] = v

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
        msg = ("module(hwc_vpc_security_group): error running "
               "api(list), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return navigate_value(r, ["security_groups"], None)


def _build_identity_object(module, all_opts):
    filters = module.params.get("filters")
    opts = dict()
    for k, v in all_opts.items():
        opts[k] = v if k in filters else None

    result = dict()

    result["description"] = None

    v = navigate_value(opts, ["enterprise_project_id"], None)
    result["enterprise_project_id"] = v

    result["id"] = None

    v = navigate_value(opts, ["name"], None)
    result["name"] = v

    result["security_group_rules"] = None

    v = navigate_value(opts, ["vpc_id"], None)
    result["vpc_id"] = v

    return result


def fill_list_resp_body(body):
    result = dict()

    result["description"] = body.get("description")

    result["enterprise_project_id"] = body.get("enterprise_project_id")

    result["id"] = body.get("id")

    result["name"] = body.get("name")

    v = fill_list_resp_security_group_rules(body.get("security_group_rules"))
    result["security_group_rules"] = v

    result["vpc_id"] = body.get("vpc_id")

    return result


def fill_list_resp_security_group_rules(value):
    if not value:
        return None

    result = []
    for item in value:
        val = dict()

        val["description"] = item.get("description")

        val["direction"] = item.get("direction")

        val["ethertype"] = item.get("ethertype")

        val["id"] = item.get("id")

        val["port_range_max"] = item.get("port_range_max")

        val["port_range_min"] = item.get("port_range_min")

        val["protocol"] = item.get("protocol")

        val["remote_address_group_id"] = item.get("remote_address_group_id")

        val["remote_group_id"] = item.get("remote_group_id")

        val["remote_ip_prefix"] = item.get("remote_ip_prefix")

        val["security_group_id"] = item.get("security_group_id")

        result.append(val)

    return result


if __name__ == '__main__':
    main()
