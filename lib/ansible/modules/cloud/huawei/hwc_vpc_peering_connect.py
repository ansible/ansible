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
module: hwc_vpc_peering_connect
description:
    - vpc peering management.
short_description: Creates a resource of Vpc/PeeringConnect in Huawei Cloud
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
    local_vpc_id:
        description:
            - Specifies the ID of local VPC.
        type: str
        required: true
    name:
        description:
            - Specifies the name of the VPC peering connection. The value can
              contain 1 to 64 characters.
        type: str
        required: true
    peering_vpc:
        description:
            - Specifies information about the peering VPC.
        type: dict
        required: true
        suboptions:
            vpc_id:
                description:
                    - Specifies the ID of peering VPC.
                type: str
                required: true
            project_id:
                description:
                    - Specifies the ID of the project which the peering vpc
                      belongs to.
                type: str
                required: false
    description:
        description:
            - The description of vpc peering connection.
        type: str
        required: false
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
    peering_vpc:
      vpc_id: "{{ vpc2.id }}"
'''

RETURN = '''
    local_vpc_id:
        description:
            - Specifies the ID of local VPC.
        type: str
        returned: success
    name:
        description:
            - Specifies the name of the VPC peering connection. The value can
              contain 1 to 64 characters.
        type: str
        returned: success
    peering_vpc:
        description:
            - Specifies information about the peering VPC.
        type: dict
        returned: success
        contains:
            vpc_id:
                description:
                    - Specifies the ID of peering VPC.
                type: str
                returned: success
            project_id:
                description:
                    - Specifies the ID of the project which the peering vpc
                      belongs to.
                type: str
                returned: success
    description:
        description:
            - The description of vpc peering connection.
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
            local_vpc_id=dict(type='str', required=True),
            name=dict(type='str', required=True),
            peering_vpc=dict(type='dict', required=True, options=dict(
                vpc_id=dict(type='str', required=True),
                project_id=dict(type='str')
            )),
            description=dict(type='str')
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
        "description": module.params.get("description"),
        "local_vpc_id": module.params.get("local_vpc_id"),
        "name": module.params.get("name"),
        "peering_vpc": module.params.get("peering_vpc"),
    }


def create(config):
    module = config.module
    client = config.client(get_region(module), "network", "project")
    timeout = 60 * int(module.params['timeouts']['create'].rstrip('m'))
    opts = user_input_parameters(module)

    params = build_create_parameters(opts)
    r = send_create_request(module, params, client)
    obj = async_wait_create(config, r, client, timeout)
    module.params['id'] = navigate_value(obj, ["peering", "id"])


def update(config):
    module = config.module
    client = config.client(get_region(module), "network", "project")
    opts = user_input_parameters(module)

    params = build_update_parameters(opts)
    if params:
        send_update_request(module, params, client)


def delete(config):
    module = config.module
    client = config.client(get_region(module), "network", "project")

    send_delete_request(module, None, client)

    url = build_path(module, "v2.0/vpc/peerings/{id}")

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
        module.fail_json(msg="module(hwc_vpc_peering_connect): error "
                             "waiting for api(delete) to "
                             "be done, error= %s" % str(ex))


def read_resource(config, exclude_output=False):
    module = config.module
    client = config.client(get_region(module), "network", "project")

    res = {}

    r = send_read_request(module, client)
    res["read"] = fill_read_resp_body(r)

    return update_properties(module, res, None, exclude_output)


def _build_query_link(opts):
    query_params = []

    v = navigate_value(opts, ["local_vpc_id"])
    if v:
        query_params.append("vpc_id=" + str(v))

    v = navigate_value(opts, ["name"])
    if v:
        query_params.append("name=" + str(v))

    query_link = "?marker={marker}&limit=10"
    if query_params:
        query_link += "&" + "&".join(query_params)

    return query_link


def search_resource(config):
    module = config.module
    client = config.client(get_region(module), "network", "project")
    opts = user_input_parameters(module)
    identity_obj = _build_identity_object(opts)
    query_link = _build_query_link(opts)
    link = "v2.0/vpc/peerings" + query_link

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

    v = expand_create_accept_vpc_info(opts, None)
    if not is_empty_value(v):
        params["accept_vpc_info"] = v

    v = navigate_value(opts, ["description"], None)
    if not is_empty_value(v):
        params["description"] = v

    v = navigate_value(opts, ["name"], None)
    if not is_empty_value(v):
        params["name"] = v

    v = expand_create_request_vpc_info(opts, None)
    if not is_empty_value(v):
        params["request_vpc_info"] = v

    if not params:
        return params

    params = {"peering": params}

    return params


def expand_create_accept_vpc_info(d, array_index):
    r = dict()

    v = navigate_value(d, ["peering_vpc", "project_id"], array_index)
    if not is_empty_value(v):
        r["tenant_id"] = v

    v = navigate_value(d, ["peering_vpc", "vpc_id"], array_index)
    if not is_empty_value(v):
        r["vpc_id"] = v

    return r


def expand_create_request_vpc_info(d, array_index):
    r = dict()

    r["tenant_id"] = ""

    v = navigate_value(d, ["local_vpc_id"], array_index)
    if not is_empty_value(v):
        r["vpc_id"] = v

    return r


def send_create_request(module, params, client):
    url = "v2.0/vpc/peerings"
    try:
        r = client.post(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_peering_connect): error running "
               "api(create), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def async_wait_create(config, result, client, timeout):
    module = config.module

    path_parameters = {
        "peering_id": ["peering", "id"],
    }
    data = dict((key, navigate_value(result, path))
                for key, path in path_parameters.items())

    url = build_path(module, "v2.0/vpc/peerings/{peering_id}", data)

    def _query_status():
        r = None
        try:
            r = client.get(url, timeout=timeout)
        except HwcClientException:
            return None, ""

        try:
            s = navigate_value(r, ["peering", "status"])
            return r, s
        except Exception:
            return None, ""

    try:
        return wait_to_finish(
            ["ACTIVE"],
            ["PENDING_ACCEPTANCE"],
            _query_status, timeout)
    except Exception as ex:
        module.fail_json(msg="module(hwc_vpc_peering_connect): error "
                             "waiting for api(create) to "
                             "be done, error= %s" % str(ex))


def build_update_parameters(opts):
    params = dict()

    v = navigate_value(opts, ["description"], None)
    if not is_empty_value(v):
        params["description"] = v

    v = navigate_value(opts, ["name"], None)
    if not is_empty_value(v):
        params["name"] = v

    if not params:
        return params

    params = {"peering": params}

    return params


def send_update_request(module, params, client):
    url = build_path(module, "v2.0/vpc/peerings/{id}")

    try:
        r = client.put(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_peering_connect): error running "
               "api(update), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def send_delete_request(module, params, client):
    url = build_path(module, "v2.0/vpc/peerings/{id}")

    try:
        r = client.delete(url, params)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_peering_connect): error running "
               "api(delete), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return r


def send_read_request(module, client):
    url = build_path(module, "v2.0/vpc/peerings/{id}")

    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_peering_connect): error running "
               "api(read), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return navigate_value(r, ["peering"], None)


def fill_read_resp_body(body):
    result = dict()

    v = fill_read_resp_accept_vpc_info(body.get("accept_vpc_info"))
    result["accept_vpc_info"] = v

    result["description"] = body.get("description")

    result["id"] = body.get("id")

    result["name"] = body.get("name")

    v = fill_read_resp_request_vpc_info(body.get("request_vpc_info"))
    result["request_vpc_info"] = v

    result["status"] = body.get("status")

    return result


def fill_read_resp_accept_vpc_info(value):
    if not value:
        return None

    result = dict()

    result["tenant_id"] = value.get("tenant_id")

    result["vpc_id"] = value.get("vpc_id")

    return result


def fill_read_resp_request_vpc_info(value):
    if not value:
        return None

    result = dict()

    result["tenant_id"] = value.get("tenant_id")

    result["vpc_id"] = value.get("vpc_id")

    return result


def update_properties(module, response, array_index, exclude_output=False):
    r = user_input_parameters(module)

    v = navigate_value(response, ["read", "description"], array_index)
    r["description"] = v

    v = navigate_value(response, ["read", "request_vpc_info", "vpc_id"],
                       array_index)
    r["local_vpc_id"] = v

    v = navigate_value(response, ["read", "name"], array_index)
    r["name"] = v

    v = r.get("peering_vpc")
    v = flatten_peering_vpc(response, array_index, v, exclude_output)
    r["peering_vpc"] = v

    return r


def flatten_peering_vpc(d, array_index, current_value, exclude_output):
    result = current_value
    has_init_value = True
    if not result:
        result = dict()
        has_init_value = False

    v = navigate_value(d, ["read", "accept_vpc_info", "tenant_id"],
                       array_index)
    result["project_id"] = v

    v = navigate_value(d, ["read", "accept_vpc_info", "vpc_id"], array_index)
    result["vpc_id"] = v

    if has_init_value:
        return result

    for v in result.values():
        if v is not None:
            return result
    return current_value


def send_list_request(module, client, url):

    r = None
    try:
        r = client.get(url)
    except HwcClientException as ex:
        msg = ("module(hwc_vpc_peering_connect): error running "
               "api(list), error: %s" % str(ex))
        module.fail_json(msg=msg)

    return navigate_value(r, ["peerings"], None)


def _build_identity_object(all_opts):
    result = dict()

    v = expand_list_accept_vpc_info(all_opts, None)
    result["accept_vpc_info"] = v

    v = navigate_value(all_opts, ["description"], None)
    result["description"] = v

    result["id"] = None

    v = navigate_value(all_opts, ["name"], None)
    result["name"] = v

    v = expand_list_request_vpc_info(all_opts, None)
    result["request_vpc_info"] = v

    result["status"] = None

    return result


def expand_list_accept_vpc_info(d, array_index):
    r = dict()

    v = navigate_value(d, ["peering_vpc", "project_id"], array_index)
    r["tenant_id"] = v

    v = navigate_value(d, ["peering_vpc", "vpc_id"], array_index)
    r["vpc_id"] = v

    for v in r.values():
        if v is not None:
            return r
    return None


def expand_list_request_vpc_info(d, array_index):
    r = dict()

    r["tenant_id"] = None

    v = navigate_value(d, ["local_vpc_id"], array_index)
    r["vpc_id"] = v

    for v in r.values():
        if v is not None:
            return r
    return None


def fill_list_resp_body(body):
    result = dict()

    v = fill_list_resp_accept_vpc_info(body.get("accept_vpc_info"))
    result["accept_vpc_info"] = v

    result["description"] = body.get("description")

    result["id"] = body.get("id")

    result["name"] = body.get("name")

    v = fill_list_resp_request_vpc_info(body.get("request_vpc_info"))
    result["request_vpc_info"] = v

    result["status"] = body.get("status")

    return result


def fill_list_resp_accept_vpc_info(value):
    if not value:
        return None

    result = dict()

    result["tenant_id"] = value.get("tenant_id")

    result["vpc_id"] = value.get("vpc_id")

    return result


def fill_list_resp_request_vpc_info(value):
    if not value:
        return None

    result = dict()

    result["tenant_id"] = value.get("tenant_id")

    result["vpc_id"] = value.get("vpc_id")

    return result


if __name__ == '__main__':
    main()
