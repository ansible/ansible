#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}
DOCUMENTATION = """
---
module: spotinst_event_subscription
version_added: 2.8
short_description: Create, update or delete Spotinst Ocean
author: Spotinst (@jeffnoehren)
description:
  - Can create, update, or delete Spotinst Ocean
    You will have to have a credentials file in this location - <home>/.spotinst/credentials
    The credentials file must contain a row that looks like this
    token = <YOUR TOKEN>
    Full documentation available at U(https://help.spotinst.com/hc/en-us/articles/115003530285-Ansible-)
requirements:
  - python >= 2.7
  - spotinst_sdk >= 1.0.44
options:

  id:
    description:
      - Parameters used for Updating or Deleting subscription.
    type: str

  credentials_path:
    default: "~/.spotinst/credentials"
    description:
      - Optional parameter that allows to set a non-default credentials path.
    type: str

  account_id:
    description:
      - Optional parameter that allows to set an account-id inside the module configuration. By default this is retrieved from the credentials path
    type: str

  token:
    description:
      - Optional parameter that allows to set an token inside the module configuration. By default this is retrieved from the credentials path
    type: str

  state:
    type: str
    choices:
      - present
      - absent
    default: present
    description:
      - create update or delete

  resource_id:
    description:
      - Resource that the subscription will be on
    type: str

  protocol:
    description:
      - (String) Type of desired protocol

  endpoint:
    description:
      - Endpoint for Subscription to hit
    type: str

  event_type:
    description:
      - Type of desired event
    type: str

  event_format:
    description:
      - Event body to be sent to endpoint
    type: str
"""
EXAMPLES = """
#In this basic example, we create an event subscription

- hosts: localhost
  tasks:
    - name: create ocean
      spotinst_event_subscription:
        account_id:
        token:
        state: present
        id: sis-e62dfd0f
        resource_id: sig-992a78db
        protocol: web
        endpoint: https://webhook.com
        event_type: GROUP_UPDATED
        event_format: { "subject" : "%s", "message" : "%s" }
      register: result
    - debug: var=result
"""
RETURN = """
---
result:
    type: str
    sample: sis-e62dfd0f
    returned: success
    description: Created Subscription successfully
"""

HAS_SPOTINST_SDK = False
__metaclass__ = type

import os
import time
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    import spotinst_sdk as spotinst
    from spotinst_sdk import SpotinstClientException

    HAS_SPOTINST_SDK = True

except ImportError:
    pass


# region Request Builder Funcitons
def expand_subscription_request(module):
    event_subscription = spotinst.spotinst_event_subscription.Subscription()

    resource_id = module.params.get('resource_id')
    protocol = module.params.get('protocol')
    endpoint = module.params.get('endpoint')
    event_type = module.params.get('event_type')
    event_format = module.params.get('event_format')

    if resource_id is not None:
        event_subscription.resource_id = resource_id

    if protocol is not None:
        event_subscription.protocol = protocol

    if endpoint is not None:
        event_subscription.endpoint = endpoint

    if event_type is not None:
        event_subscription.event_type = event_type

    if event_format is not None:
        event_subscription.event_format = event_format

    return event_subscription
# endregion


# region Util Functions
def handle_subscription(client, module):
    subscription_id = None
    message = None
    has_changed = False

    request_type, subscription_id = get_request_type_and_id(client=client, module=module)

    if request_type == "create":
        subscription_id, message, has_changed = handle_create(client=client, module=module)
    elif request_type == "update":
        subscription_id, message, has_changed = handle_update(client=client, module=module, subscription_id=subscription_id)
    elif request_type == "delete":
        subscription_id, message, has_changed = handle_delete(client=client, module=module, subscription_id=subscription_id)
    else:
        module.fail_json(msg="Action Not Allowed")

    return subscription_id, message, has_changed


def get_request_type_and_id(client, module):
    request_type = None
    subscription_id = module.params.get('id')
    state = module.params.get('state')

    if state == 'present':
        if subscription_id is None:
            request_type = "create"

        else:
            request_type = "update"

    elif state == 'absent':
        request_type = "delete"

    return request_type, subscription_id


def get_client(module):
    # Retrieve creds file variables
    creds_file_loaded_vars = dict()

    credentials_path = module.params.get('credentials_path')

    if credentials_path is not None:
        try:
            with open(credentials_path, "r") as creds:
                for line in creds:
                    eq_index = line.find('=')
                    var_name = line[:eq_index].strip()
                    string_value = line[eq_index + 1:].strip()
                    creds_file_loaded_vars[var_name] = string_value
        except IOError:
            pass
    # End of creds file retrieval

    token = module.params.get('token')
    if not token:
        token = creds_file_loaded_vars.get("token")

    account = module.params.get('account_id')
    if not account:
        account = creds_file_loaded_vars.get("account")

    client = spotinst.SpotinstClient(auth_token=token, print_output=False)

    if account is not None:
        client = spotinst.SpotinstClient(auth_token=token, account_id=account, print_output=False)

    return client
# endregion


# region Request Functions
def handle_create(client, module):
    subscription_request = expand_subscription_request(module=module)
    subscription = client.create_event_subscription(subscription=subscription_request)

    subscription_id = subscription['id']
    message = 'Created subscription successfully'
    has_changed = True

    return subscription_id, message, has_changed


def handle_update(client, module, subscription_id):
    subscription_request = expand_subscription_request(module=module)
    client.update_event_subscription(subscription_id=subscription_id, subscription=subscription_request)

    message = 'Updated subscription successfully'
    has_changed = True

    return subscription_id, message, has_changed


def handle_delete(client, module, subscription_id):
    client.delete_event_subscription(subscription_id=subscription_id)

    message = 'Deleted subscription successfully'
    has_changed = True

    return subscription_id, message, has_changed
# endregion


def main():
    fields = dict(
        account_id=dict(type='str', fallback=(env_fallback, ['SPOTINST_ACCOUNT_ID', 'ACCOUNT'])),
        token=dict(type='str', fallback=(env_fallback, ['SPOTINST_TOKEN'])),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        id=dict(type='str'),
        credentials_path=dict(type='path', default="~/.spotinst/credentials"),

        resource_id=dict(type='str'),
        protocol=dict(type='str'),
        endpoint=dict(type='str'),
        event_type=dict(type='str'),
        event_format=dict(type='dict'))

    module = AnsibleModule(argument_spec=fields)

    if not HAS_SPOTINST_SDK:
        module.fail_json(msg="the Spotinst SDK library is required. (pip install spotinst_sdk)")

    client = get_client(module=module)

    subscription_id, message, has_changed = handle_subscription(client=client, module=module)

    module.exit_json(changed=has_changed, subscription_id=subscription_id, message=message)


if __name__ == '__main__':
    main()
