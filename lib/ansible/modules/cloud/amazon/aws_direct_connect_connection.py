#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
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
        is required. Modifying attributes of a connection with I(force_update) will
        result in a new Direct Connect connection.
  connection_id:
    description:
      - The ID of the Direct Connect connection. I(name) or I(connection_id) is
        required to recreate or delete a connection. Modifying attributes of a
        connection with I(force_update) will result in a new Direct Connect connection.
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
  force_update:
    description:
      - To modify bandwidth or location the connection will need to be deleted and recreated.
        By default this will not happen - this option must be set to True.
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
  force_update: True

# delete the connection
- aws_direct_connect_connection:
  state: absent
  name: ansible-test-connection
"""

RETURN = """
connection:
  description:
    - The attributes of the Direct Connect connection
  type: complex
  returned: I(state=present)
  contains:
    aws_device:
      description: The endpoint which the physical connection terminates on.
    bandwidth:
      description: The bandwidth of the connection.
    connection_id:
      description: ID of the Direct Connect connection.
    connection_state:
      description: The state of the connection.
    location:
      description: Where the connection is located.
    owner_account:
      description: The owner of the connection.
    region:
      description: The region in which the connection exists.
"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (camel_dict_to_snake_dict, ec2_argument_spec, HAS_BOTO3,
                                      get_aws_connection_info, boto3_conn, AWSRetry)
from ansible.module_utils.aws.direct_connect import (DirectConnectError, delete_connection,
                                                     associate_connection_and_lag, disassociate_connection_and_lag)

try:
    import botocore
except:
    pass
    # handled by imported HAS_BOTO3

retry_params = {"tries": 10, "delay": 5, "backoff": 1.2}


def connection_status(client, connection_id):
    return connection_exists(client, connection_id=connection_id, connection_name=None, verify=False)


@AWSRetry.backoff(**retry_params)
def connection_exists(client, connection_id=None, connection_name=None, verify=True):
    try:
        if connection_id:
            response = client.describe_connections(connectionId=connection_id)
        else:
            response = client.describe_connections()
    except botocore.exceptions.ClientError as e:
        raise DirectConnectError(msg="Failed to describe DirectConnect ID {0}".format(connection_id),
                                 last_traceback=traceback.format_exc(),
                                 response=e.response)

    match = []
    connection = []

    # look for matching connections

    if len(response.get('connections', [])) == 1 and connection_id:
        if response['connections'][0]['connectionState'] != 'deleted':
            match.append(response['connections'][0]['connectionId'])
            connection.append(response['connections'][0])

    for each in response.get('connections', []):
        if connection_name == each['connectionName'] and each['connectionState'] != 'deleted':
            match.append(each['connectionId'])
            connection.append(each)

    # verifying if the connections exists; if true, return connection identifier, otherwise return False
    if verify and len(match) == 1:
        return match[0]
    elif verify:
        return False

    # not verifying if the connection exists; just return current connection info
    else:
        if len(connection) == 1:
            return {'connection': connection[0]}
        else:
            return {'connection': {}}


@AWSRetry.backoff(**retry_params)
def create_connection(client, location, bandwidth, name, lag_id):
    if not name:
        raise DirectConnectError(msg="Failed to create a Direct Connect connection: name required.")
    try:
        if lag_id:
            connection = client.create_connection(location=location,
                                                  bandwidth=bandwidth,
                                                  connectionName=name,
                                                  lagId=lag_id)
        else:
            connection = client.create_connection(location=location,
                                                  bandwidth=bandwidth,
                                                  connectionName=name)
    except botocore.exceptions.ClientError as e:
        raise DirectConnectError(msg="Failed to create DirectConnect connection {0}".format(name),
                                 last_traceback=traceback.format_exc(),
                                 response=e.response)
    return connection['connectionId']


def changed_properties(current_status, location, bandwidth):
    changed = False

    current_bandwidth = current_status['bandwidth']
    current_location = current_status['location']

    if (current_bandwidth != bandwidth or current_location != location):
        changed = True

    return changed


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
    changed = False

    # the connection is found; get the latest state and see if it needs to be updated
    if connection_id:
        latest_state = connection_status(client, connection_id=connection_id)['connection']
        if changed_properties(latest_state, location, bandwidth) and forced_update:
            ensure_absent(client, connection_id)
            changed, connection_id = ensure_present(client=client,
                                                    connection_id=None,
                                                    connection_name=connection_name,
                                                    location=location,
                                                    bandwidth=bandwidth,
                                                    lag_id=lag_id,
                                                    forced_update=forced_update)
        elif update_associations(client, latest_state, connection_id, lag_id):
            changed = True
            latest_state = connection_status(client, connection_id=connection_id)['connection']

    # no connection found; create a new one
    else:
        connection_id = create_connection(client, location, bandwidth, connection_name, lag_id)
        changed = True

    return changed, connection_id


@AWSRetry.backoff(**retry_params)
def ensure_absent(client, connection_id):
    changed = False
    if connection_id:
        delete_connection(client, connection_id)
        changed = True

    return changed, {}


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(required=True, choices=['present', 'absent']),
        name=dict(),
        location=dict(),
        bandwidth=dict(choices=['1Gbps', '10Gbps']),
        link_aggregation_group=dict(),
        connection_id=dict(),
        forced_update=dict(type='bool', default=False)
    ))

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=[('connection_id', 'name')],
                           required_if=[('state', 'present', ('location', 'bandwidth'))])

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    if not region:
        module.fail_json(msg="Either region or AWS_REGION or EC2_REGION environment variable or boto config aws_region or ec2_region must be set.")

    connection = boto3_conn(module, conn_type='client',
                            resource='directconnect', region=region,
                            endpoint=ec2_url, **aws_connect_kwargs)

    connection_id = connection_exists(connection,
                                      connection_id=module.params.get('connection_id'),
                                      connection_name=module.params.get('name'))
    if not connection_id and module.params.get('connection_id'):
        module.fail_json(msg="The Direct Connect connection {0} does not exist.".format(module.params.get('connection_id')))

    state = module.params.get('state')
    try:
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
            changed, response = ensure_absent(connection, connection_id)
    except DirectConnectError as e:
        if e.response:
            module.fail_json(msg=e.msg, exception=e.last_traceback, **e.response)
        elif e.last_traceback:
            module.fail_json(msg=e.msg, exception=e.last_traceback)
        else:
            module.fail_json(msg=e.msg)

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(response))


if __name__ == '__main__':
    main()
