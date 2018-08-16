#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: aws_direct_connect_connection
short_description: Creates, deletes, modifies a DirectConnect connection
description:
  - Create, update, or delete a Direct Connect connection between a network and a specific AWS Direct Connect location.
    Upon creation the connection may be added to a link aggregation group or established as a standalone connection.
    The connection may later be associated or disassociated with a link aggregation group.
version_added: "2.4"
author: "Sloane Hertel (@s-hertel)"
extends_documentation_fragment:
    - aws
    - ec2
requirements:
  - boto3
  - botocore
options:
  state:
    description:
      - The state of the Direct Connect connection.
    choices:
      - present
      - absent
  name:
    description:
      - The name of the Direct Connect connection. This is required to create a
        new connection. To recreate or delete a connection I(name) or I(connection_id)
        is required.
  connection_id:
    description:
      - The ID of the Direct Connect connection. I(name) or I(connection_id) is
        required to recreate or delete a connection. Modifying attributes of a
        connection with I(forced_update) will result in a new Direct Connect connection ID.
  location:
    description:
      -  Where the Direct Connect connection is located. Required when I(state=present).
  bandwidth:
    description:
      - The bandwidth of the Direct Connect connection. Required when I(state=present).
    choices:
      - 1Gbps
      - 10Gbps
  link_aggregation_group:
    description:
      - The ID of the link aggregation group you want to associate with the connection.
        This is optional in case a stand-alone connection is desired.
  forced_update:
    description:
      - To modify bandwidth or location the connection will need to be deleted and recreated.
        By default this will not happen - this option must be set to True.
    type: bool
"""

EXAMPLES = """

# create a Direct Connect connection
- aws_direct_connect_connection:
    name: ansible-test-connection
    state: present
    location: EqDC2
    link_aggregation_group: dxlag-xxxxxxxx
    bandwidth: 1Gbps
  register: dc

# disassociate the LAG from the connection
- aws_direct_connect_connection:
    state: present
    connection_id: dc.connection.connection_id
    location: EqDC2
    bandwidth: 1Gbps

# replace the connection with one with more bandwidth
- aws_direct_connect_connection:
    state: present
    name: ansible-test-connection
    location: EqDC2
    bandwidth: 10Gbps
    forced_update: True

# delete the connection
- aws_direct_connect_connection:
    state: absent
    name: ansible-test-connection
"""

RETURN = """
connection:
  description: The attributes of the direct connect connection.
  type: complex
  returned: I(state=present)
  contains:
    aws_device:
      description: The endpoint which the physical connection terminates on.
      returned: when the requested state is no longer 'requested'
      type: string
      sample: EqDC2-12pmo7hemtz1z
    bandwidth:
      description: The bandwidth of the connection.
      returned: always
      type: string
      sample: 1Gbps
    connection_id:
      description: The ID of the connection.
      returned: always
      type: string
      sample: dxcon-ffy9ywed
    connection_name:
      description: The name of the connection.
      returned: always
      type: string
      sample: ansible-test-connection
    connection_state:
      description: The state of the connection.
      returned: always
      type: string
      sample: pending
    loa_issue_time:
      description: The issue time of the connection's Letter of Authorization - Connecting Facility Assignment.
      returned: when the LOA-CFA has been issued (the connection state will no longer be 'requested')
      type: string
      sample: '2018-03-20T17:36:26-04:00'
    location:
      description: The location of the connection.
      returned: always
      type: string
      sample: EqDC2
    owner_account:
      description: The account that owns the direct connect connection.
      returned: always
      type: string
      sample: '123456789012'
    region:
      description: The region in which the connection exists.
      returned: always
      type: string
      sample: us-east-1
"""

import traceback
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (camel_dict_to_snake_dict, AWSRetry)
from ansible.module_utils.aws.direct_connect import (DirectConnectError, delete_connection,
                                                     associate_connection_and_lag, disassociate_connection_and_lag)

try:
    from botocore.exceptions import BotoCoreError, ClientError
except:
    pass
    # handled by imported AnsibleAWSModule

retry_params = {"tries": 10, "delay": 5, "backoff": 1.2, "catch_extra_error_codes": ["DirectConnectClientException"]}


def connection_status(client, connection_id):
    return connection_exists(client, connection_id=connection_id, connection_name=None, verify=False)


def connection_exists(client, connection_id=None, connection_name=None, verify=True):
    params = {}
    if connection_id:
        params['connectionId'] = connection_id
    try:
        response = AWSRetry.backoff(**retry_params)(client.describe_connections)(**params)
    except (BotoCoreError, ClientError) as e:
        if connection_id:
            msg = "Failed to describe DirectConnect ID {0}".format(connection_id)
        else:
            msg = "Failed to describe DirectConnect connections"
        raise DirectConnectError(msg=msg,
                                 last_traceback=traceback.format_exc(),
                                 exception=e)

    match = []
    connection = []

    # look for matching connections

    if len(response.get('connections', [])) == 1 and connection_id:
        if response['connections'][0]['connectionState'] != 'deleted':
            match.append(response['connections'][0]['connectionId'])
            connection.extend(response['connections'])

    for conn in response.get('connections', []):
        if connection_name == conn['connectionName'] and conn['connectionState'] != 'deleted':
            match.append(conn['connectionId'])
            connection.append(conn)

    # verifying if the connections exists; if true, return connection identifier, otherwise return False
    if verify and len(match) == 1:
        return match[0]
    elif verify:
        return False
    # not verifying if the connection exists; just return current connection info
    elif len(connection) == 1:
        return {'connection': connection[0]}
    return {'connection': {}}


def create_connection(client, location, bandwidth, name, lag_id):
    if not name:
        raise DirectConnectError(msg="Failed to create a Direct Connect connection: name required.")
    params = {
        'location': location,
        'bandwidth': bandwidth,
        'connectionName': name,
    }
    if lag_id:
        params['lagId'] = lag_id

    try:
        connection = AWSRetry.backoff(**retry_params)(client.create_connection)(**params)
    except (BotoCoreError, ClientError) as e:
        raise DirectConnectError(msg="Failed to create DirectConnect connection {0}".format(name),
                                 last_traceback=traceback.format_exc(),
                                 exception=e)
    return connection['connectionId']


def changed_properties(current_status, location, bandwidth):
    current_bandwidth = current_status['bandwidth']
    current_location = current_status['location']

    return current_bandwidth != bandwidth or current_location != location


@AWSRetry.backoff(**retry_params)
def update_associations(client, latest_state, connection_id, lag_id):
    changed = False
    if 'lagId' in latest_state and lag_id != latest_state['lagId']:
        disassociate_connection_and_lag(client, connection_id, lag_id=latest_state['lagId'])
        changed = True
    if (changed and lag_id) or (lag_id and 'lagId' not in latest_state):
        associate_connection_and_lag(client, connection_id, lag_id)
        changed = True
    return changed


def ensure_present(client, connection_id, connection_name, location, bandwidth, lag_id, forced_update):
    # the connection is found; get the latest state and see if it needs to be updated
    if connection_id:
        latest_state = connection_status(client, connection_id=connection_id)['connection']
        if changed_properties(latest_state, location, bandwidth) and forced_update:
            ensure_absent(client, connection_id)
            return ensure_present(client=client,
                                  connection_id=None,
                                  connection_name=connection_name,
                                  location=location,
                                  bandwidth=bandwidth,
                                  lag_id=lag_id,
                                  forced_update=forced_update)
        elif update_associations(client, latest_state, connection_id, lag_id):
            return True, connection_id

    # no connection found; create a new one
    else:
        return True, create_connection(client, location, bandwidth, connection_name, lag_id)

    return False, connection_id


@AWSRetry.backoff(**retry_params)
def ensure_absent(client, connection_id):
    changed = False
    if connection_id:
        delete_connection(client, connection_id)
        changed = True

    return changed


def main():
    argument_spec = dict(
        state=dict(required=True, choices=['present', 'absent']),
        name=dict(),
        location=dict(),
        bandwidth=dict(choices=['1Gbps', '10Gbps']),
        link_aggregation_group=dict(),
        connection_id=dict(),
        forced_update=dict(type='bool', default=False)
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_one_of=[('connection_id', 'name')],
        required_if=[('state', 'present', ('location', 'bandwidth'))]
    )

    connection = module.client('directconnect')

    state = module.params.get('state')
    try:
        connection_id = connection_exists(
            connection,
            connection_id=module.params.get('connection_id'),
            connection_name=module.params.get('name')
        )
        if not connection_id and module.params.get('connection_id'):
            module.fail_json(msg="The Direct Connect connection {0} does not exist.".format(module.params.get('connection_id')))

        if state == 'present':
            changed, connection_id = ensure_present(connection,
                                                    connection_id=connection_id,
                                                    connection_name=module.params.get('name'),
                                                    location=module.params.get('location'),
                                                    bandwidth=module.params.get('bandwidth'),
                                                    lag_id=module.params.get('link_aggregation_group'),
                                                    forced_update=module.params.get('forced_update'))
            response = connection_status(connection, connection_id)
        elif state == 'absent':
            changed = ensure_absent(connection, connection_id)
            response = {}
    except DirectConnectError as e:
        if e.last_traceback:
            module.fail_json(msg=e.msg, exception=e.last_traceback, **camel_dict_to_snake_dict(e.exception.response))
        else:
            module.fail_json(msg=e.msg)

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(response))


if __name__ == '__main__':
    main()
