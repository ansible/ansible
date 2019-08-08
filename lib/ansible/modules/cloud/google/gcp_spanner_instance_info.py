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

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ["preview"], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: gcp_spanner_instance_info
description:
- Gather info for GCP Instance
- This module was called C(gcp_spanner_instance_facts) before Ansible 2.9. The usage
  has not changed.
short_description: Gather info for GCP Instance
version_added: 2.8
author: Google Inc. (@googlecloudplatform)
requirements:
- python >= 2.6
- requests >= 2.18.4
- google-auth >= 1.3.0
options: {}
extends_documentation_fragment: gcp
'''

EXAMPLES = '''
- name: get info on a instance
  gcp_spanner_instance_info:
    project: test_project
    auth_kind: serviceaccount
    service_account_file: "/tmp/auth.pem"
'''

RETURN = '''
resources:
  description: List of resources
  returned: always
  type: complex
  contains:
    name:
      description:
      - A unique identifier for the instance, which cannot be changed after the instance
        is created. The name must be between 6 and 30 characters in length.
      returned: success
      type: str
    config:
      description:
      - The name of the instance's configuration (similar but not quite the same as
        a region) which defines defines the geographic placement and replication of
        your databases in this instance. It determines where your data is stored.
        Values are typically of the form `regional-europe-west1` , `us-central` etc.
      - In order to obtain a valid list please consult the [Configuration section
        of the docs](U(https://cloud.google.com/spanner/docs/instances)).
      returned: success
      type: str
    displayName:
      description:
      - The descriptive name for this instance as it appears in UIs. Must be unique
        per project and between 4 and 30 characters in length.
      returned: success
      type: str
    nodeCount:
      description:
      - The number of nodes allocated to this instance.
      returned: success
      type: int
    labels:
      description:
      - 'An object containing a list of "key": value pairs.'
      - 'Example: { "name": "wrench", "mass": "1.3kg", "count": "3" }.'
      returned: success
      type: dict
'''

################################################################################
# Imports
################################################################################
from ansible.module_utils.gcp_utils import navigate_hash, GcpSession, GcpModule, GcpRequest
import json

################################################################################
# Main
################################################################################


def main():
    module = GcpModule(argument_spec=dict())

    if module._name == 'gcp_spanner_instance_facts':
        module.deprecate("The 'gcp_spanner_instance_facts' module has been renamed to 'gcp_spanner_instance_info'", version='2.13')

    if not module.params['scopes']:
        module.params['scopes'] = ['https://www.googleapis.com/auth/spanner.admin']

    items = fetch_list(module, collection(module))
    if items.get('instances'):
        items = items.get('instances')
    else:
        items = []
    return_value = {'resources': items}
    module.exit_json(**return_value)


def collection(module):
    return "https://spanner.googleapis.com/v1/projects/{project}/instances".format(**module.params)


def fetch_list(module, link):
    auth = GcpSession(module, 'spanner')
    response = auth.get(link)
    return return_if_object(module, response)


def return_if_object(module, response):
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

    return result


if __name__ == "__main__":
    main()
