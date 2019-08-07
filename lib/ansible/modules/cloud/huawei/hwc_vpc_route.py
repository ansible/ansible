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
module: hwc_vpc_route
description:
    - vpc route management.
short_description: Creates a resource of Vpc/Route in Huawei Cloud
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
    destination:
        description:
            - Specifies the destination IP address or CIDR block.
        type: str
        required: true
    next_hop:
        description:
            - Specifies the next hop. The value is VPC peering connection ID.
        type: str
        required: true
    vpc_id:
        description:
            - Specifies the VPC ID to which route is added.
        type: str
        required: true
    type:
        description:
            - Specifies the type of route.
        type: str
        required: false
        default: 'peering'
extends_documentation_fragment: hwc
'''

EXAMPLES = '''
# create a peering connect
- name: create a local vpc
  hwc_network_vpc:
    cidr: "192.168.0.0/16"
    name: "ansible_network_vpc_test_local"
  register: vpc1
- name: create a peering vpc
  hwc_network_vpc:
    cidr: "192.168.0.0/16"
    name: "ansible_network_vpc_test_peering"
  register: vpc2
- name: create a peering connect
  hwc_vpc_peering_connect:
    local_vpc_id: "{{ vpc1.id }}"
    name: "ansible_network_peering_test"
    filters:
      - "name"
    peering_vpc:
      vpc_id: "{{ vpc2.id }}"
  register: connect
- name: create a route
  hwc_vpc_route:
    vpc_id: "{{ vpc1.id }}"
    destination: "192.168.0.0/16"
    next_hop: "{{ connect.id }}"
    filters:
      - "vpc_id"
      - "destination"
      - "type"
'''

RETURN = '''
    destination:
        description:
            - Specifies the destination IP address or CIDR block.
        type: str
        returned: success
    next_hop:
        description:
            - Specifies the next hop. The value is VPC peering connection ID.
        type: str
        returned: success
    vpc_id:
        description:
            - Specifies the VPC ID to which route is added.
        type: str
        returned: success
    type:
        description:
            - Specifies the type of route.
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
            destination=dict(type='str', required=True),
            next_hop=dict(type='str', required=True),
            vpc_id=dict(type='str', required=True),
            type=dict(type='str', default='peering')
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
        "destination": module.params.get("destination"),
        "next_hop": module.params.get("next_hop"),
        "type": module.params.get("type"),
        "vpc_id": module.params.get("vpc_id"),
    }


def create(config):
    module = config.module
    client = config.client(get_region(module), "network", "project")
    opts = user_input_parameters(module)

    params = build_create_parameters(opts)
    r = send_create_request(module, params, client)
    module.params['id'] = navigate_value(r, ["route", "id"])


def delete(config):
    module = config.module
    client = config.client(get_region(module), "network", "project")

    send_delete_request(module, None, client)


def read_resource(config, exclude_output=False):
    module = config.module
    client = config.client(get_region(module), "network", "project")

    res = {}

    r = send_read_request(module, client)
    res["read"] = fill_read_resp_body(r)

    return update_properties(module, res, None, exclude_output)


def _build_query_link(opts):
    query_params = []

    v = navigate_value(opts, ["type"])
    if v:
        query_params.append("type=" + str(v))

    v = navigate_value(opts, ["destination"])
    if v:
        query_params.append("destination=" + str(v))

    v = navigate_value(opts, ["vpc_id"])
    if v:
        query_params.append("vpc_id=" + str(v))

    query_link = "?marker={marker}&limit=10"
    if query_params:
        query_link += "&" + "&".join(query_params)

    return query_link


def search_resource(config):
    module = config.module
    client = config.client(get_region(module), "network", "project")
    opts = user_input_parameters(module)
    identity_obj = _build_identity_object(module, opts)
    query_link = _build_query_link(opts)
    link = "v2.0/vpc/routes" + query_link

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

    v = navigate_value(opts, ["destination"], None)
    if not is_empty_value(v):
        params["destination"] = v

    v = navigate_value(opts, ["next_hop"], None)
    if not is_empty_value(v):
        params["nexthop"] = v

    v = navigate_value(opts, ["type"], None)
    if not is_empty_value(v):
        params["type"] = v

    v = navigate_value(opts, ["vpc_id"], None)
    if not is_empty_value(v):
        params["vpc_id"] = v

    if not params:
        return params

    params = {"route": params}

    return params


def send_create_request(module, params, client):
    url = "v2.0/vpc/routes"
    try:
        r = client.post(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_route): error running "
               "api(create), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def send_delete_request(module, params, client):
    url = build_path(module, "v2.0/vpc/routes/{id}")

    try:
        r = client.delete(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_route): error running "
               "api(delete), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def send_read_request(module, client):
    url = build_path(module, "v2.0/vpc/routes/{id}")

    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_route): error running "
               "api(read), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return navigate_value(r, ["route"], None)


def fill_read_resp_body(body):
    result = dict()

    result["destination"] = body.get("destination")

    result["id"] = body.get("id")

    result["nexthop"] = body.get("nexthop")

    result["tenant_id"] = body.get("tenant_id")

    result["type"] = body.get("type")

    result["vpc_id"] = body.get("vpc_id")

    return result


def update_properties(module, response, array_index, exclude_output=False):
    r = user_input_parameters(module)

    v = navigate_value(response, ["read", "destination"], array_index)
    r["destination"] = v

    v = navigate_value(response, ["read", "nexthop"], array_index)
    r["next_hop"] = v

    v = navigate_value(response, ["read", "type"], array_index)
    r["type"] = v

    v = navigate_value(response, ["read", "vpc_id"], array_index)
    r["vpc_id"] = v

    return r


def send_list_request(module, client, url):

    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_route): error running "
               "api(list), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return navigate_value(r, ["routes"], None)


def _build_identity_object(module, all_opts):
    filters = module.params.get("filters")
    opts = dict()
    for k, v in all_opts.items():
        opts[k] = v if k in filters else None

    result = dict()

    v = navigate_value(opts, ["destination"], None)
    result["destination"] = v

    result["id"] = None

    v = navigate_value(opts, ["next_hop"], None)
    result["nexthop"] = v

    result["tenant_id"] = None

    v = navigate_value(opts, ["type"], None)
    result["type"] = v

    v = navigate_value(opts, ["vpc_id"], None)
    result["vpc_id"] = v

    return result


def fill_list_resp_body(body):
    result = dict()

    result["destination"] = body.get("destination")

    result["id"] = body.get("id")

    result["nexthop"] = body.get("nexthop")

    result["tenant_id"] = body.get("tenant_id")

    result["type"] = body.get("type")

    result["vpc_id"] = body.get("vpc_id")

    return result


if __name__ == '__main__':
    main()
