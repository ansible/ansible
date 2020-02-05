#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Francois Lallart (@fraff)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = '''
---
module: ovh_monthly_billing
author: Francois Lallart (@fraff)
version_added: "2.10"
short_description: Manage OVH monthly billing
description:
    - Enable monthly billing on OVH cloud intances (be aware OVH does not allow to disable it).
requirements: [ "ovh" ]
options:
    project_id:
        required: true
        type: str
        description:
            - ID of the project, get it with U(https://api.ovh.com/console/#/cloud/project#GET)
    instance_id:
        required: true
        type: str
        description:
            - ID of the instance, get it with U(https://api.ovh.com/console/#/cloud/project/%7BserviceName%7D/instance#GET)
    endpoint:
        type: str
        description:
            - The endpoint to use (for instance ovh-eu)
    application_key:
        type: str
        description:
            - The applicationKey to use
    application_secret:
        type: str
        description:
            - The application secret to use
    consumer_key:
        type: str
        description:
            - The consumer key to use
'''

EXAMPLES = '''
# basic usage, using auth from /etc/ovh.conf
  - ovh_monthly_billing:
       project_id: 0c727a20aa144485b70c44dee9123b46
       instance_id: 8fa89ad2-8f08-4220-9fa4-9695ea23e948

# a bit more more complex
  # get openstack cloud ID and instance ID, OVH use them in its API
  - os_server_info:
      cloud: myProjectName
      region_name: myRegionName
      server: myServerName
    # force run even in check_mode
    check_mode: no

  # use theses IDs
  - ovh_monthly_billing:
      project_id: "{{ openstack_servers.0.tenant_id }}"
      instance_id: "{{ openstack_servers.0.id }}"
      application_key: yourkey
      application_secret: yoursecret
      consumer_key: yourconsumerkey
'''

RETURN = '''
'''

import os
import sys
import traceback

try:
    import ovh
    import ovh.exceptions
    from ovh.exceptions import APIError
    HAS_OVH = True
except ImportError:
    HAS_OVH = False
    OVH_IMPORT_ERROR = traceback.format_exc()

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            project_id=dict(required=True),
            instance_id=dict(required=True),
            endpoint=dict(required=False),
            application_key=dict(required=False, no_log=True),
            application_secret=dict(required=False, no_log=True),
            consumer_key=dict(required=False, no_log=True),
        ),
        supports_check_mode=True
    )

    # Get parameters
    project_id = module.params.get('project_id')
    instance_id = module.params.get('instance_id')
    endpoint = module.params.get('endpoint')
    application_key = module.params.get('application_key')
    application_secret = module.params.get('application_secret')
    consumer_key = module.params.get('consumer_key')
    project = ""
    instance = ""
    ovh_billing_status = ""

    if not HAS_OVH:
        module.fail_json(msg='python-ovh is required to run this module, see https://github.com/ovh/python-ovh')

    # Connect to OVH API
    client = ovh.Client(
        endpoint=endpoint,
        application_key=application_key,
        application_secret=application_secret,
        consumer_key=consumer_key
    )

    # Check that the instance exists
    try:
        project = client.get('/cloud/project/{0}'.format(project_id))
    except ovh.exceptions.ResourceNotFoundError:
        module.fail_json(msg='project {0} does not exist'.format(project_id))

    # Check that the instance exists
    try:
        instance = client.get('/cloud/project/{0}/instance/{1}'.format(project_id, instance_id))
    except ovh.exceptions.ResourceNotFoundError:
        module.fail_json(msg='instance {0} does not exist in project {1}'.format(instance_id, project_id))

    # Is monthlyBilling already enabled or pending ?
    if instance['monthlyBilling'] is not None:
        if instance['monthlyBilling']['status'] in ['ok', 'activationPending']:
            module.exit_json(changed=False, ovh_billing_status=instance['monthlyBilling'])

    if module.check_mode:
        module.exit_json(changed=True, msg="Dry Run!")

    try:
        ovh_billing_status = client.post('/cloud/project/{0}/instance/{1}/activeMonthlyBilling'.format(project_id, instance_id))
        module.exit_json(changed=True, ovh_billing_status=ovh_billing_status['monthlyBilling'])
    except APIError as apiError:
        module.fail_json(changed=False, msg="Failed to call OVH API: {0}".format(apiError))

    # We should never reach here
    module.fail_json(msg='Internal ovh_monthly_billing module error')


if __name__ == "__main__":
    main()
