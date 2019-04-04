#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Huawei
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
module: hwc_network_vpc
description:
    - Represents an vpc resource.
short_description: Creates a Huawei Cloud VPC
version_added: '2.8'
author: Huawei Inc. (@huaweicloud)
requirements:
    - requests >= 2.18.4
    - keystoneauth1 >= 3.6.0
options:
    state:
        description:
            - Whether the given object should exist in vpc.
        type: str
        choices: ['present', 'absent']
        default: 'present'
    name:
        description:
            - the name of vpc.
        type: str
        required: true
    cidr:
        description:
            - the range of available subnets in the vpc.
        type: str
        required: true
extends_documentation_fragment: hwc
'''

EXAMPLES = '''
- name: create a vpc
  hwc_network_vpc:
      identity_endpoint: "{{ identity_endpoint }}"
      user: "{{ user }}"
      password: "{{ password }}"
      domain: "{{ domain }}"
      project: "{{ project }}"
      region: "{{ region }}"
      name: "vpc_1"
      cidr: "192.168.100.0/24"
      state: present
'''

RETURN = '''
    id:
        description:
            - the id of vpc.
        type: str
        returned: success
    name:
        description:
            - the name of vpc.
        type: str
        returned: success
    cidr:
        description:
            - the range of available subnets in the vpc.
        type: str
        returned: success
    status:
        description:
            - the status of vpc.
        type: str
        returned: success
    routes:
        description:
            - the route information.
        type: complex
        returned: success
        contains:
            destination:
                description:
                    - the destination network segment of a route.
                type: str
                returned: success
            next_hop:
                description:
                    - the next hop of a route.
                type: str
                returned: success
    enable_shared_snat:
        description:
            - show whether the shared snat is enabled.
        type: bool
        returned: success
'''

###############################################################################
# Imports
###############################################################################

from ansible.module_utils.hwc_utils import (HwcSession, HwcModule,
                                            DictComparison, navigate_hash,
                                            remove_nones_from_dict,
                                            remove_empty_from_dict,
                                            are_dicts_different)
import json
import re
import time

###############################################################################
# Main
###############################################################################


def main():
    """Main function"""

    module = HwcModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            name=dict(required=True, type='str'),
            cidr=dict(required=True, type='str')
        ),
        supports_check_mode=True,
    )
    session = HwcSession(module, 'network')

    state = module.params['state']

    if (not module.params.get("id")) and module.params.get("name"):
        module.params['id'] = get_id_by_name(session)

    fetch = None
    link = self_link(session)
    # the link will include Nones if required format parameters are missed
    if not re.search('/None/|/None$', link):
        fetch = fetch_resource(session, link)
        if fetch:
            fetch = fetch.get('vpc')
    changed = False

    if fetch:
        if state == 'present':
            expect = _get_editable_properties(module)
            current_state = response_to_hash(module, fetch)
            if are_dicts_different(expect, current_state):
                if not module.check_mode:
                    fetch = update(session, self_link(session), [200])
                    fetch = response_to_hash(module, fetch.get('vpc'))
                changed = True
            else:
                fetch = current_state
        else:
            if not module.check_mode:
                delete(session, self_link(session))
                fetch = {}
            changed = True
    else:
        if state == 'present':
            if not module.check_mode:
                fetch = create(session, collection(session), [200])
                fetch = response_to_hash(module, fetch.get('vpc'))
            changed = True
        else:
            fetch = {}

    fetch.update({'changed': changed})

    module.exit_json(**fetch)


def create(session, link, success_codes=None):
    if not success_codes:
        success_codes = [201, 202]
    module = session.module
    r = return_if_object(module, session.post(link, resource_to_create(module)), success_codes)

    wait_done = wait_for_operation(session, 'create', r)

    url = resource_get_url(session, wait_done)
    return fetch_resource(session, url)


def update(session, link, success_codes=None):
    if not success_codes:
        success_codes = [201, 202]
    module = session.module
    r = return_if_object(module, session.put(link, resource_to_update(module)), success_codes)

    wait_done = wait_for_operation(session, 'update', r)

    url = resource_get_url(session, wait_done)
    return fetch_resource(session, url)


def delete(session, link, success_codes=None):
    if not success_codes:
        success_codes = [202, 204]
    return_if_object(session.module, session.delete(link), success_codes, False)

    wait_for_delete(session, link)


def fetch_resource(session, link, success_codes=None):
    if not success_codes:
        success_codes = [200]
    return return_if_object(session.module, session.get(link), success_codes)


def link_wrapper(f):
    def _wrapper(module, *args, **kwargs):
        try:
            return f(module, *args, **kwargs)
        except KeyError as ex:
            module.fail_json(
                msg="Mapping keys(%s) are not found in generating link." % ex)

    return _wrapper


def get_id_by_name(session):
    module = session.module
    name = module.params.get("name")
    link = list_link(session, {'limit': 10, 'marker': '{marker}'})
    not_format_keys = re.findall("={marker}", link)
    none_values = re.findall("=None", link)

    if not (not_format_keys or none_values):
        r = fetch_resource(session, link)
        if r is None:
            return ""
        r = r.get('vpcs', [])
        ids = [
            i.get('id') for i in r if i.get('name', '') == name
        ]
        if not ids:
            return ""
        elif len(ids) == 1:
            return ids[0]
        else:
            module.fail_json(msg="Multiple resources with same name are found.")
    elif none_values:
        module.fail_json(
            msg="Can not find id by name because url includes None.")
    else:
        p = {'marker': ''}
        ids = set()
        while True:
            r = fetch_resource(session, link.format(**p))
            if r is None:
                break
            r = r.get('vpcs', [])
            if r == []:
                break
            for i in r:
                if i.get('name') == name:
                    ids.add(i.get('id'))
            if len(ids) >= 2:
                module.fail_json(
                    msg="Multiple resources with same name are found.")

            p['marker'] = r[-1].get('id')

        return ids.pop() if ids else ""


@link_wrapper
def list_link(session, extra_data=None):
    url = "{endpoint}vpcs?limit={limit}&marker={marker}"

    combined = session.module.params.copy()
    if extra_data:
        combined.update(extra_data)

    combined['endpoint'] = session.get_service_endpoint('vpc')

    return url.format(**combined)


@link_wrapper
def self_link(session):
    url = "{endpoint}vpcs/{id}"

    combined = session.module.params.copy()
    combined['endpoint'] = session.get_service_endpoint('vpc')

    return url.format(**combined)


@link_wrapper
def collection(session):
    url = "{endpoint}vpcs"

    combined = session.module.params.copy()
    combined['endpoint'] = session.get_service_endpoint('vpc')

    return url.format(**combined)


def return_if_object(module, response, success_codes, has_content=True):
    code = response.status_code

    # If not found, return nothing.
    if code == 404:
        return None

    success_codes = [200, 201, 202, 203, 204, 205, 206, 207, 208, 226]
    # If no content, return nothing.
    if code in success_codes and not has_content:
        return None

    result = None
    try:
        result = response.json()
    except getattr(json.decoder, 'JSONDecodeError', ValueError) as inst:
        module.fail_json(msg="Invalid JSON response with error: %s" % inst)

    if code not in success_codes:
        msg = navigate_hash(result, ['message'])
        if msg:
            module.fail_json(msg=msg)
        else:
            module.fail_json(msg="operation failed, return code=%d" % code)

    return result


def resource_to_create(module):
    request = remove_empty_from_dict({
        u'name': module.params.get('name'),
        u'cidr': module.params.get('cidr')
    })
    return {'vpc': request}


def resource_to_update(module):
    request = remove_nones_from_dict({
        u'name': module.params.get('name'),
        u'cidr': module.params.get('cidr')
    })
    return {'vpc': request}


def _get_editable_properties(module):
    request = remove_nones_from_dict({
        "name": module.params.get("name"),
        "cidr": module.params.get("cidr"),
    })

    return request


def response_to_hash(module, response):
    """ Remove unnecessary properties from the response.
        This is for doing comparisons with Ansible's current parameters.
    """
    return {
        u'id': response.get(u'id'),
        u'name': response.get(u'name'),
        u'cidr': response.get(u'cidr'),
        u'status': response.get(u'status'),
        u'routes': VpcRoutesArray(response.get(u'routes', []), module).from_response(),
        u'enable_shared_snat': response.get(u'enable_shared_snat')
    }


@link_wrapper
def resource_get_url(session, wait_done):
    combined = session.module.params.copy()
    combined['op_id'] = navigate_hash(wait_done, ['vpc', 'id'])
    url = 'vpcs/{op_id}'.format(**combined)

    endpoint = session.get_service_endpoint('vpc')
    return endpoint + url


@link_wrapper
def async_op_url(session, extra_data=None):
    url = "{endpoint}vpcs/{op_id}"

    combined = session.module.params.copy()
    if extra_data:
        combined.update(extra_data)

    combined['endpoint'] = session.get_service_endpoint('vpc')

    return url.format(**combined)


def wait_for_operation(session, op_type, op_result):
    op_id = navigate_hash(op_result, ['vpc', 'id'])
    url = async_op_url(session, {'op_id': op_id})
    timeout = 60 * int(session.module.params['timeouts'][op_type].rstrip('m'))
    states = {
        'create': {
            'allowed': ['CREATING', 'DONW', 'OK'],
            'complete': ['OK'],
        },
        'update': {
            'allowed': ['PENDING_UPDATE', 'DONW', 'OK'],
            'complete': ['OK'],
        }
    }

    return wait_for_completion(url, timeout, states[op_type]['allowed'],
                               states[op_type]['complete'], session)


def wait_for_completion(op_uri, timeout, allowed_states,
                        complete_states, session):
    module = session.module
    end = time.time() + timeout
    while time.time() <= end:
        try:
            op_result = fetch_resource(session, op_uri)
        except Exception:
            time.sleep(1.0)
            continue

        raise_if_errors(op_result, module)

        status = navigate_hash(op_result, ['vpc', 'status'])
        if status not in allowed_states:
            module.fail_json(msg="Invalid async operation status %s" % status)
        if status in complete_states:
            return op_result

        time.sleep(1.0)

    module.fail_json(msg="Timeout to wait completion.")


def raise_if_errors(response, module):
    errors = navigate_hash(response, [])
    if errors:
        module.fail_json(msg=navigate_hash(response, []))


def wait_for_delete(session, link):
    end = time.time() + 60 * int(
        session.module.params['timeouts']['delete'].rstrip('m'))
    while time.time() <= end:
        try:
            resp = session.get(link)
            if resp.status_code == 404:
                return
        except Exception:
            pass

        time.sleep(1.0)

    session.module.fail_json(msg="Timeout to wait for deletion to be complete.")


class VpcRoutesArray(object):
    def __init__(self, request, module):
        self.module = module
        if request:
            self.request = request
        else:
            self.request = []

    def to_request(self):
        items = []
        for item in self.request:
            items.append(self._request_for_item(item))
        return items

    def from_response(self):
        items = []
        for item in self.request:
            items.append(self._response_from_item(item))
        return items

    def _request_for_item(self, item):
        return {
            u'destination': item.get('destination'),
            u'nexthop': item.get('next_hop')
        }

    def _response_from_item(self, item):
        return {
            u'destination': item.get(u'destination'),
            u'next_hop': item.get(u'nexthop')
        }


if __name__ == '__main__':
    main()
