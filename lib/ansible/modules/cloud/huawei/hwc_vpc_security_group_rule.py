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
module: hwc_vpc_security_group_rule
description:
    - vpc security group management.
short_description: Creates a resource of Vpc/SecurityGroupRule in Huawei Cloud
notes:
  - If I(id) option is provided, it takes precedence over
    I(enterprise_project_id) for security group rule selection.
  - I(security_group_id) is used for security group rule selection. If more
    than one security group rule with this options exists, execution is
    aborted.
  - No parameter support updating. If one of option is changed, the module
    will create a new resource.
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
    direction:
        description:
            - Specifies the direction of access control. The value can be
              egress or ingress.
        type: str
        required: true
    security_group_id:
        description:
            - Specifies the security group rule ID, which uniquely identifies
              the security group rule.
        type: str
        required: true
    description:
        description:
            - Provides supplementary information about the security group rule.
              The value is a string of no more than 255 characters that can
              contain letters and digits.
        type: str
        required: false
    ethertype:
        description:
            - Specifies the IP protocol version. The value can be IPv4 or IPv6.
              If you do not set this parameter, IPv4 is used by default.
        type: str
        required: false
    port_range_max:
        description:
            - Specifies the end port number. The value ranges from 1 to 65535.
              If the protocol is not icmp, the value cannot be smaller than the
              port_range_min value. An empty value indicates all ports.
        type: int
        required: false
    port_range_min:
        description:
            - Specifies the start port number. The value ranges from 1 to
              65535. The value cannot be greater than the port_range_max value.
              An empty value indicates all ports.
        type: int
        required: false
    protocol:
        description:
            - Specifies the protocol type. The value can be icmp, tcp, or udp.
              If the parameter is left blank, the security group supports all
              protocols.
        type: str
        required: false
    remote_group_id:
        description:
            - Specifies the ID of the peer security group. The value is
              exclusive with parameter remote_ip_prefix.
        type: str
        required: false
    remote_ip_prefix:
        description:
            - Specifies the remote IP address. If the access control direction
              is set to egress, the parameter specifies the source IP address.
              If the access control direction is set to ingress, the parameter
              specifies the destination IP address. The value can be in the
              CIDR format or IP addresses. The parameter is exclusive with
              parameter remote_group_id.
        type: str
        required: false
extends_documentation_fragment: hwc
'''

EXAMPLES = '''
# create a security group rule
- name: create a security group
  hwc_vpc_security_group:
    name: "ansible_network_security_group_test"
  register: sg
- name: create a security group rule
  hwc_vpc_security_group_rule:
    direction: "ingress"
    protocol: "tcp"
    ethertype: "IPv4"
    port_range_max: 22
    security_group_id: "{{ sg.id }}"
    port_range_min: 22
    remote_ip_prefix: "0.0.0.0/0"
'''

RETURN = '''
    direction:
        description:
            - Specifies the direction of access control. The value can be
              egress or ingress.
        type: str
        returned: success
    security_group_id:
        description:
            - Specifies the security group rule ID, which uniquely identifies
              the security group rule.
        type: str
        returned: success
    description:
        description:
            - Provides supplementary information about the security group rule.
              The value is a string of no more than 255 characters that can
              contain letters and digits.
        type: str
        returned: success
    ethertype:
        description:
            - Specifies the IP protocol version. The value can be IPv4 or IPv6.
              If you do not set this parameter, IPv4 is used by default.
        type: str
        returned: success
    port_range_max:
        description:
            - Specifies the end port number. The value ranges from 1 to 65535.
              If the protocol is not icmp, the value cannot be smaller than the
              port_range_min value. An empty value indicates all ports.
        type: int
        returned: success
    port_range_min:
        description:
            - Specifies the start port number. The value ranges from 1 to
              65535. The value cannot be greater than the port_range_max value.
              An empty value indicates all ports.
        type: int
        returned: success
    protocol:
        description:
            - Specifies the protocol type. The value can be icmp, tcp, or udp.
              If the parameter is left blank, the security group supports all
              protocols.
        type: str
        returned: success
    remote_group_id:
        description:
            - Specifies the ID of the peer security group. The value is
              exclusive with parameter remote_ip_prefix.
        type: str
        returned: success
    remote_ip_prefix:
        description:
            - Specifies the remote IP address. If the access control direction
              is set to egress, the parameter specifies the source IP address.
              If the access control direction is set to ingress, the parameter
              specifies the destination IP address. The value can be in the
              CIDR format or IP addresses. The parameter is exclusive with
              parameter remote_group_id.
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
            direction=dict(type='str', required=True),
            security_group_id=dict(type='str', required=True),
            description=dict(type='str'),
            ethertype=dict(type='str'),
            port_range_max=dict(type='int'),
            port_range_min=dict(type='int'),
            protocol=dict(type='str'),
            remote_group_id=dict(type='str'),
            remote_ip_prefix=dict(type='str')
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
                raise Exception(
                    "Cannot change option from (%s) to (%s) for an"
                    " existing security group(%s)." % (current, expect, module.params.get('id')))
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
        "description": module.params.get("description"),
        "direction": module.params.get("direction"),
        "ethertype": module.params.get("ethertype"),
        "port_range_max": module.params.get("port_range_max"),
        "port_range_min": module.params.get("port_range_min"),
        "protocol": module.params.get("protocol"),
        "remote_group_id": module.params.get("remote_group_id"),
        "remote_ip_prefix": module.params.get("remote_ip_prefix"),
        "security_group_id": module.params.get("security_group_id"),
    }


def create(config):
    module = config.module
    client = config.client(get_region(module), "vpc", "project")
    opts = user_input_parameters(module)

    params = build_create_parameters(opts)
    r = send_create_request(module, params, client)
    module.params['id'] = navigate_value(r, ["security_group_rule", "id"])


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
    query_link = "?marker={marker}&limit=10"
    v = navigate_value(opts, ["security_group_id"])
    if v:
        query_link += "&security_group_id=" + str(v)

    return query_link


def search_resource(config):
    module = config.module
    client = config.client(get_region(module), "vpc", "project")
    opts = user_input_parameters(module)
    identity_obj = _build_identity_object(opts)
    query_link = _build_query_link(opts)
    link = "security-group-rules" + query_link

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

    v = navigate_value(opts, ["description"], None)
    if not is_empty_value(v):
        params["description"] = v

    v = navigate_value(opts, ["direction"], None)
    if not is_empty_value(v):
        params["direction"] = v

    v = navigate_value(opts, ["ethertype"], None)
    if not is_empty_value(v):
        params["ethertype"] = v

    v = navigate_value(opts, ["port_range_max"], None)
    if not is_empty_value(v):
        params["port_range_max"] = v

    v = navigate_value(opts, ["port_range_min"], None)
    if not is_empty_value(v):
        params["port_range_min"] = v

    v = navigate_value(opts, ["protocol"], None)
    if not is_empty_value(v):
        params["protocol"] = v

    v = navigate_value(opts, ["remote_group_id"], None)
    if not is_empty_value(v):
        params["remote_group_id"] = v

    v = navigate_value(opts, ["remote_ip_prefix"], None)
    if not is_empty_value(v):
        params["remote_ip_prefix"] = v

    v = navigate_value(opts, ["security_group_id"], None)
    if not is_empty_value(v):
        params["security_group_id"] = v

    if not params:
        return params

    params = {"security_group_rule": params}

    return params


def send_create_request(module, params, client):
    url = "security-group-rules"
    try:
        r = client.post(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_security_group_rule): error running "
               "api(create), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def send_delete_request(module, params, client):
    url = build_path(module, "security-group-rules/{id}")

    try:
        r = client.delete(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_security_group_rule): error running "
               "api(delete), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def send_read_request(module, client):
    url = build_path(module, "security-group-rules/{id}")

    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_security_group_rule): error running "
               "api(read), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return navigate_value(r, ["security_group_rule"], None)


def fill_read_resp_body(body):
    result = dict()

    result["description"] = body.get("description")

    result["direction"] = body.get("direction")

    result["ethertype"] = body.get("ethertype")

    result["id"] = body.get("id")

    result["port_range_max"] = body.get("port_range_max")

    result["port_range_min"] = body.get("port_range_min")

    result["protocol"] = body.get("protocol")

    result["remote_address_group_id"] = body.get("remote_address_group_id")

    result["remote_group_id"] = body.get("remote_group_id")

    result["remote_ip_prefix"] = body.get("remote_ip_prefix")

    result["security_group_id"] = body.get("security_group_id")

    return result


def update_properties(module, response, array_index, exclude_output=False):
    r = user_input_parameters(module)

    v = navigate_value(response, ["read", "description"], array_index)
    r["description"] = v

    v = navigate_value(response, ["read", "direction"], array_index)
    r["direction"] = v

    v = navigate_value(response, ["read", "ethertype"], array_index)
    r["ethertype"] = v

    v = navigate_value(response, ["read", "port_range_max"], array_index)
    r["port_range_max"] = v

    v = navigate_value(response, ["read", "port_range_min"], array_index)
    r["port_range_min"] = v

    v = navigate_value(response, ["read", "protocol"], array_index)
    r["protocol"] = v

    v = navigate_value(response, ["read", "remote_group_id"], array_index)
    r["remote_group_id"] = v

    v = navigate_value(response, ["read", "remote_ip_prefix"], array_index)
    r["remote_ip_prefix"] = v

    v = navigate_value(response, ["read", "security_group_id"], array_index)
    r["security_group_id"] = v

    return r


def send_list_request(module, client, url):

    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_security_group_rule): error running "
               "api(list), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return navigate_value(r, ["security_group_rules"], None)


def _build_identity_object(all_opts):
    result = dict()

    v = navigate_value(all_opts, ["description"], None)
    result["description"] = v

    v = navigate_value(all_opts, ["direction"], None)
    result["direction"] = v

    v = navigate_value(all_opts, ["ethertype"], None)
    result["ethertype"] = v

    result["id"] = None

    v = navigate_value(all_opts, ["port_range_max"], None)
    result["port_range_max"] = v

    v = navigate_value(all_opts, ["port_range_min"], None)
    result["port_range_min"] = v

    v = navigate_value(all_opts, ["protocol"], None)
    result["protocol"] = v

    result["remote_address_group_id"] = None

    v = navigate_value(all_opts, ["remote_group_id"], None)
    result["remote_group_id"] = v

    v = navigate_value(all_opts, ["remote_ip_prefix"], None)
    result["remote_ip_prefix"] = v

    v = navigate_value(all_opts, ["security_group_id"], None)
    result["security_group_id"] = v

    return result


def fill_list_resp_body(body):
    result = dict()

    result["description"] = body.get("description")

    result["direction"] = body.get("direction")

    result["ethertype"] = body.get("ethertype")

    result["id"] = body.get("id")

    result["port_range_max"] = body.get("port_range_max")

    result["port_range_min"] = body.get("port_range_min")

    result["protocol"] = body.get("protocol")

    result["remote_address_group_id"] = body.get("remote_address_group_id")

    result["remote_group_id"] = body.get("remote_group_id")

    result["remote_ip_prefix"] = body.get("remote_ip_prefix")

    result["security_group_id"] = body.get("security_group_id")

    return result


if __name__ == '__main__':
    main()
