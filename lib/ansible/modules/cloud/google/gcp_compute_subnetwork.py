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
module: gcp_compute_subnetwork
description:
    - A VPC network is a virtual version of the traditional physical networks that exist
      within and between physical data centers. A VPC network provides connectivity for
      your Compute Engine virtual machine (VM) instances, Container Engine containers,
      App Engine Flex services, and other network-related resources.
    - Each GCP project contains one or more VPC networks. Each VPC network is a global
      entity spanning all GCP regions. This global VPC network allows VM instances and
      other resources to communicate with each other via internal, private IP addresses.
    - Each VPC network is subdivided into subnets, and each subnet is contained within
      a single region. You can have more than one subnet in a region for a given VPC network.
      Each subnet has a contiguous private RFC1918 IP space. You create instances, containers,
      and the like in these subnets.
    - When you create an instance, you must create it in a subnet, and the instance draws
      its internal IP address from that subnet.
    - Virtual machine (VM) instances in a VPC network can communicate with instances in
      all other subnets of the same VPC network, regardless of region, using their RFC1918
      private IP addresses. You can isolate portions of the network, even entire subnets,
      using firewall rules.
short_description: Creates a GCP Subnetwork
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
    description:
        description:
            - An optional description of this resource. Provide this property when you create
              the resource. This field can be set only at resource creation time.
        required: false
    ip_cidr_range:
        description:
            - The range of internal addresses that are owned by this subnetwork.
            - Provide this property when you create the subnetwork. For example, 10.0.0.0/8 or
              192.168.0.0/16. Ranges must be unique and non-overlapping within a network. Only
              IPv4 is supported.
        required: true
    name:
        description:
            - The name of the resource, provided by the client when initially creating the resource.
              The name must be 1-63 characters long, and comply with RFC1035. Specifically, the
              name must be 1-63 characters long and match the regular expression `[a-z]([-a-z0-9]*[a-z0-9])?`
              which means the first character must be a lowercase letter, and all following characters
              must be a dash, lowercase letter, or digit, except the last character, which cannot
              be a dash.
        required: true
    network:
        description:
            - The network this subnet belongs to.
            - Only networks that are in the distributed mode can have subnetworks.
        required: true
    private_ip_google_access:
        description:
            - Whether the VMs in this subnet can access Google services without assigned external
              IP addresses.
        required: false
        type: bool
    region:
        description:
            - URL of the GCP region for this subnetwork.
        required: true
extends_documentation_fragment: gcp
notes:
    - "API Reference: U(https://cloud.google.com/compute/docs/reference/rest/beta/subnetworks)"
    - "Private Google Access: U(https://cloud.google.com/vpc/docs/configure-private-google-access)"
    - "Cloud Networking: U(https://cloud.google.com/vpc/docs/using-vpc)"
'''

EXAMPLES = '''
- name: create a network
  gcp_compute_network:
      name: 'network-subnetwork'
      auto_create_subnetworks: true
      project: "{{ gcp_project }}"
      auth_kind: "{{ gcp_cred_kind }}"
      service_account_file: "{{ gcp_cred_file }}"
      scopes:
        - https://www.googleapis.com/auth/compute
      state: present
  register: network
- name: create a subnetwork
  gcp_compute_subnetwork:
      name: 'ansiblenet'
      region: 'us-west1'
      network: "{{ network }}"
      ip_cidr_range: '172.16.0.0/16'
      project: testProject
      auth_kind: service_account
      service_account_file: /tmp/auth.pem
      scopes:
        - https://www.googleapis.com/auth/compute
      state: present
'''

RETURN = '''
    creation_timestamp:
        description:
            - Creation timestamp in RFC3339 text format.
        returned: success
        type: str
    description:
        description:
            - An optional description of this resource. Provide this property when you create
              the resource. This field can be set only at resource creation time.
        returned: success
        type: str
    gateway_address:
        description:
            - The gateway address for default routes to reach destination addresses outside this
              subnetwork.
        returned: success
        type: str
    id:
        description:
            - The unique identifier for the resource.
        returned: success
        type: int
    ip_cidr_range:
        description:
            - The range of internal addresses that are owned by this subnetwork.
            - Provide this property when you create the subnetwork. For example, 10.0.0.0/8 or
              192.168.0.0/16. Ranges must be unique and non-overlapping within a network. Only
              IPv4 is supported.
        returned: success
        type: str
    name:
        description:
            - The name of the resource, provided by the client when initially creating the resource.
              The name must be 1-63 characters long, and comply with RFC1035. Specifically, the
              name must be 1-63 characters long and match the regular expression `[a-z]([-a-z0-9]*[a-z0-9])?`
              which means the first character must be a lowercase letter, and all following characters
              must be a dash, lowercase letter, or digit, except the last character, which cannot
              be a dash.
        returned: success
        type: str
    network:
        description:
            - The network this subnet belongs to.
            - Only networks that are in the distributed mode can have subnetworks.
        returned: success
        type: dict
    private_ip_google_access:
        description:
            - Whether the VMs in this subnet can access Google services without assigned external
              IP addresses.
        returned: success
        type: bool
    region:
        description:
            - URL of the GCP region for this subnetwork.
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
            description=dict(type='str'),
            ip_cidr_range=dict(required=True, type='str'),
            name=dict(required=True, type='str'),
            network=dict(required=True, type='dict'),
            private_ip_google_access=dict(type='bool'),
            region=dict(required=True, type='str')
        )
    )

    if not module.params['scopes']:
        module.params['scopes'] = ['https://www.googleapis.com/auth/compute']

    state = module.params['state']
    kind = 'compute#subnetwork'

    fetch = fetch_resource(module, self_link(module), kind)
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
    auth = GcpSession(module, 'compute')
    return wait_for_operation(module, auth.post(link, resource_to_request(module)))


def update(module, link, kind):
    auth = GcpSession(module, 'compute')
    return wait_for_operation(module, auth.put(link, resource_to_request(module)))


def delete(module, link, kind):
    auth = GcpSession(module, 'compute')
    return wait_for_operation(module, auth.delete(link))


def resource_to_request(module):
    request = {
        u'kind': 'compute#subnetwork',
        u'description': module.params.get('description'),
        u'ipCidrRange': module.params.get('ip_cidr_range'),
        u'name': module.params.get('name'),
        u'network': replace_resource_dict(module.params.get(u'network', {}), 'selfLink'),
        u'privateIpGoogleAccess': module.params.get('private_ip_google_access'),
        u'region': module.params.get('region')
    }
    return_vals = {}
    for k, v in request.items():
        if v:
            return_vals[k] = v

    return return_vals


def fetch_resource(module, link, kind):
    auth = GcpSession(module, 'compute')
    return return_if_object(module, auth.get(link), kind)


def self_link(module):
    return "https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/subnetworks/{name}".format(**module.params)


def collection(module):
    return "https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/subnetworks".format(**module.params)


def return_if_object(module, response, kind):
    # If not found, return nothing.
    if response.status_code == 404:
        return None

    # If no content, return nothing.
    if response.status_code == 204:
        return None

    try:
        module.raise_for_status(response)
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
        u'creationTimestamp': response.get(u'creationTimestamp'),
        u'description': response.get(u'description'),
        u'gatewayAddress': response.get(u'gatewayAddress'),
        u'id': response.get(u'id'),
        u'ipCidrRange': response.get(u'ipCidrRange'),
        u'name': response.get(u'name'),
        u'network': replace_resource_dict(module.params.get(u'network', {}), 'selfLink'),
        u'privateIpGoogleAccess': response.get(u'privateIpGoogleAccess'),
        u'region': module.params.get('region')
    }


def async_op_url(module, extra_data=None):
    if extra_data is None:
        extra_data = {}
    url = "https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/operations/{op_id}"
    combined = extra_data.copy()
    combined.update(module.params)
    return url.format(**combined)


def wait_for_operation(module, response):
    op_result = return_if_object(module, response, 'compute#operation')
    if op_result is None:
        return {}
    status = navigate_hash(op_result, ['status'])
    wait_done = wait_for_completion(status, op_result, module)
    return fetch_resource(module, navigate_hash(wait_done, ['targetLink']), 'compute#subnetwork')


def wait_for_completion(status, op_result, module):
    op_id = navigate_hash(op_result, ['name'])
    op_uri = async_op_url(module, {'op_id': op_id})
    while status != 'DONE':
        raise_if_errors(op_result, ['error', 'errors'], 'message')
        time.sleep(1.0)
        if status not in ['PENDING', 'RUNNING', 'DONE']:
            module.fail_json(msg="Invalid result %s" % status)
        op_result = fetch_resource(module, op_uri, 'compute#operation')
        status = navigate_hash(op_result, ['status'])
    return op_result


def raise_if_errors(response, err_path, module):
    errors = navigate_hash(response, err_path)
    if errors is not None:
        module.fail_json(msg=errors)

if __name__ == '__main__':
    main()
