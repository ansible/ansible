#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Google
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# ----------------------------------------------------------------------------
#
#     ***     AUTO GENERATED CODE    ***    AUTO GENERATED CODE     ***
#
# ----------------------------------------------------------------------------
#
#     This file is automatically generated by Magic Modules and manual
#     changes will be clobbered when the file is regenerated.
#
#     Please read more about how to change this file at
#     https://www.github.com/GoogleCloudPlatform/magic-modules
#
# ----------------------------------------------------------------------------

from __future__ import absolute_import, division, print_function
__metaclass__ = type

################################################################################
# Documentation
################################################################################

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ["preview"],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: gcp_sql_user
description:
    - The Users resource represents a database user in a Cloud SQL instance.
short_description: Creates a GCP User
version_added: 2.6
author: Google Inc. (@googlecloudplatform)
requirements:
    - python >= 2.6
    - requests >= 2.18.4
    - google-auth >= 1.3.0
options:
    state:
        description:
            - Whether the given object should exist in GCP
        choices: ['present', 'absent']
        default: 'present'
    host:
        description:
            - The host name from which the user can connect. For insert operations, host defaults
              to an empty string. For update operations, host is specified as part of the request
              URL. The host name cannot be updated after insertion.
        required: true
    name:
        description:
            - The name of the user in the Cloud SQL instance.
        required: true
    instance:
        description:
            - The name of the Cloud SQL instance. This does not include the project ID.
        required: true
    password:
        description:
            - The password for the user.
        required: false
extends_documentation_fragment: gcp
'''

EXAMPLES = '''
- name: create a instance
  gcp_sql_instance:
      name: 'instance-user'
      settings:
        ip_configuration:
          authorized_networks:
            - name: 'google dns server'
              value: '8.8.8.8/32'
        tier: db-n1-standard-1
      region: us-central1
      project: "{{ gcp_project }}"
      auth_kind: "{{ gcp_cred_kind }}"
      service_account_file: "{{ gcp_cred_file }}"
      scopes:
        - https://www.googleapis.com/auth/sqlservice.admin
      state: present
  register: instance
- name: create a user
  gcp_sql_user:
      # Can't use Ansible random name because it's too long
      name: 'test-user'
      host: '10.1.2.3'
      password: 'secret-password'
      instance: "{{ instance }}"
      project: testProject
      auth_kind: service_account
      service_account_file: /tmp/auth.pem
      scopes:
        - https://www.googleapis.com/auth/sqlservice.admin
      state: present
'''

RETURN = '''
    host:
        description:
            - The host name from which the user can connect. For insert operations, host defaults
              to an empty string. For update operations, host is specified as part of the request
              URL. The host name cannot be updated after insertion.
        returned: success
        type: str
    name:
        description:
            - The name of the user in the Cloud SQL instance.
        returned: success
        type: str
    instance:
        description:
            - The name of the Cloud SQL instance. This does not include the project ID.
        returned: success
        type: dict
    password:
        description:
            - The password for the user.
        returned: success
        type: str
'''

################################################################################
# Imports
################################################################################

from ansible.module_utils.gcp_utils import navigate_hash, GcpSession, GcpModule, GcpRequest, replace_resource_dict
import json
import time

################################################################################
# Main
################################################################################


def main():
    """Main function"""

    module = GcpModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            host=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            instance=dict(required=True, type='dict'),
            password=dict(type='str')
        )
    )

    if not module.params['scopes']:
        module.params['scopes'] = ['https://www.googleapis.com/auth/sqlservice.admin']

    state = module.params['state']
    kind = 'sql#user'

    fetch = fetch_wrapped_resource(module, 'sql#user',
                                   'sql#usersList',
                                   'items')
    changed = False

    if fetch:
        if state == 'present':
            if is_different(module, fetch):
                fetch = update(module, self_link(module), kind)
                changed = True
        else:
            delete(module, self_link(module), kind)
            fetch = {}
            changed = True
    else:
        if state == 'present':
            fetch = create(module, collection(module), kind)
            changed = True
        else:
            fetch = {}

    fetch.update({'changed': changed})

    module.exit_json(**fetch)


def create(module, link, kind):
    auth = GcpSession(module, 'sql')
    return wait_for_operation(module, auth.post(link, resource_to_request(module)))


def update(module, link, kind):
    auth = GcpSession(module, 'sql')
    return wait_for_operation(module, auth.put(link, resource_to_request(module)))


def delete(module, link, kind):
    auth = GcpSession(module, 'sql')
    return wait_for_operation(module, auth.delete(link))


def resource_to_request(module):
    request = {
        u'kind': 'sql#user',
        u'password': module.params.get('password'),
        u'host': module.params.get('host'),
        u'name': module.params.get('name')
    }
    return_vals = {}
    for k, v in request.items():
        if v:
            return_vals[k] = v

    return return_vals


def unwrap_resource_filter(module):
    return {
        'host': module.params['host'],
        'name': module.params['name']
    }


def unwrap_resource(result, module):
    query_predicate = unwrap_resource_filter(module)
    matched_items = []
    for item in result:
        if all(item[k] == query_predicate[k] for k in query_predicate.keys()):
            matched_items.append(item)
    if len(matched_items) > 1:
        module.fail_json(msg="More than 1 result found: %s" % matched_items)

    if matched_items:
        return matched_items[0]
    else:
        return None


def fetch_resource(module, link, kind):
    auth = GcpSession(module, 'sql')
    return return_if_object(module, auth.get(link), kind)


def fetch_wrapped_resource(module, kind, wrap_kind, wrap_path):
    result = fetch_resource(module, self_link(module), wrap_kind)
    if result is None or wrap_path not in result:
        return None

    result = unwrap_resource(result[wrap_path], module)

    if result is None:
        return None

    if result['kind'] != kind:
        module.fail_json(msg="Incorrect result: {kind}".format(**result))

    return result


def self_link(module):
    res = {
        'project': module.params['project'],
        'instance': replace_resource_dict(module.params['instance'], 'name'),
        'name': module.params['name'],
        'host': module.params['host']
    }
    return "https://www.googleapis.com/sql/v1beta4/projects/{project}/instances/{instance}/users?name={name}&host={host}".format(**res)


def collection(module):
    res = {
        'project': module.params['project'],
        'instance': replace_resource_dict(module.params['instance'], 'name')
    }
    return "https://www.googleapis.com/sql/v1beta4/projects/{project}/instances/{instance}/users".format(**res)


def return_if_object(module, response, kind):
    # If not found, return nothing.
    if response.status_code == 404:
        return None

    # If no content, return nothing.
    if response.status_code == 204:
        return None

    # SQL only: return on 403 if not exist
    if response.status_code == 403:
        return None

    try:
        result = response.json()
    except getattr(json.decoder, 'JSONDecodeError', ValueError) as inst:
        module.fail_json(msg="Invalid JSON response with error: %s" % inst)

    if navigate_hash(result, ['error', 'errors']):
        module.fail_json(msg=navigate_hash(result, ['error', 'errors']))
    if result['kind'] != kind:
        module.fail_json(msg="Incorrect result: {kind}".format(**result))

    return result


def is_different(module, response):
    request = resource_to_request(module)
    response = response_to_hash(module, response)

    # Remove all output-only from response.
    response_vals = {}
    for k, v in response.items():
        if k in request:
            response_vals[k] = v

    request_vals = {}
    for k, v in request.items():
        if k in response:
            request_vals[k] = v

    return GcpRequest(request_vals) != GcpRequest(response_vals)


# Remove unnecessary properties from the response.
# This is for doing comparisons with Ansible's current parameters.
def response_to_hash(module, response):
    return {
        u'host': response.get(u'host'),
        u'name': response.get(u'name')
    }


def async_op_url(module, extra_data=None):
    if extra_data is None:
        extra_data = {}
    url = "https://www.googleapis.com/sql/v1beta4/projects/{project}/operations/{op_id}"
    combined = extra_data.copy()
    combined.update(module.params)
    return url.format(**combined)


def wait_for_operation(module, response):
    op_result = return_if_object(module, response, 'sql#operation')
    if op_result is None:
        return {}
    status = navigate_hash(op_result, ['status'])
    wait_for_completion(status, op_result, module)
    return fetch_wrapped_resource(module, 'sql#user', 'sql#usersList', 'items')


def wait_for_completion(status, op_result, module):
    op_id = navigate_hash(op_result, ['name'])
    op_uri = async_op_url(module, {'op_id': op_id})
    while status != 'DONE':
        raise_if_errors(op_result, ['error', 'errors'], 'message')
        time.sleep(1.0)
        if status not in ['PENDING', 'RUNNING', 'DONE']:
            module.fail_json(msg="Invalid result %s" % status)
        op_result = fetch_resource(module, op_uri, 'sql#operation')
        status = navigate_hash(op_result, ['status'])
    return op_result


def raise_if_errors(response, err_path, module):
    errors = navigate_hash(response, err_path)
    if errors is not None:
        module.fail_json(msg=errors)

if __name__ == '__main__':
    main()
