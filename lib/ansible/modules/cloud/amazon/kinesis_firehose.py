#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: kinesis_stream
short_description: Manage a Kinesis Stream.
description:
    - Create or Delete a Kinesis Stream.
    - Update the retention period of a Kinesis Stream.
    - Update Tags on a Kinesis Stream.
version_added: "2.2"
author: Allen Sanabria (@linuxdynasty)
options:
  name:
    description:
      - "The name of the Kinesis Stream you are managing."
    default: None
    required: true
  shards:
    description:
      - "The number of shards you want to have with this stream."
      - "This is required when state == present"
    required: false
    default: None
  retention_period:
    description:
      - "The default retention period is 24 hours and can not be less than 24
      hours."
      - "The retention period can be modified during any point in time."
    required: false
    default: None
  state:
    description:
      - "Create or Delete the Kinesis Stream."
    required: false
    default: present
    choices: [ 'present', 'absent' ]
  wait:
    description:
      - Wait for operation to complete before returning.
    required: false
    default: true
  wait_timeout:
    description:
      - How many seconds to wait for an operation to complete before timing out.
    required: false
    default: 300
  tags:
    description:
      - "A dictionary of resource tags of the form: { tag1: value1, tag2: value2 }."
    required: false
    default: null
    aliases: [ "resource_tags" ]
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Basic creation example:
- name: Set up Kinesis Stream with 10 shards and wait for the stream to become ACTIVE
  kinesis_stream:
    name: test-stream
    shards: 10
    wait: yes
    wait_timeout: 600
  register: test_stream

# Basic creation example with tags:
- name: Set up Kinesis Stream with 10 shards, tag the environment, and wait for the stream to become ACTIVE
  kinesis_stream:
    name: test-stream
    shards: 10
    tags:
      Env: development
    wait: yes
    wait_timeout: 600
  register: test_stream

# Basic creation example with tags and increase the retention period from the default 24 hours to 48 hours:
- name: Set up Kinesis Stream with 10 shards, tag the environment, increase the retention period and wait for the stream to become ACTIVE
  kinesis_stream:
    name: test-stream
    retention_period: 48
    shards: 10
    tags:
      Env: development
    wait: yes
    wait_timeout: 600
  register: test_stream

# Basic delete example:
- name: Delete Kinesis Stream test-stream and wait for it to finish deleting.
  kinesis_stream:
    name: test-stream
    state: absent
    wait: yes
    wait_timeout: 600
  register: test_stream
'''

RETURN = '''
stream_name:
  description: The name of the Kinesis Stream.
  returned: when state == present.
  type: string
  sample: "test-stream"
stream_arn:
  description: The amazon resource identifier
  returned: when state == present.
  type: string
  sample: "arn:aws:kinesis:east-side:123456789:stream/test-stream"
stream_status:
  description: The current state of the Kinesis Stream.
  returned: when state == present.
  type: string
  sample: "ACTIVE"
retention_period_hours:
  description: Number of hours messages will be kept for a Kinesis Stream.
  returned: when state == present.
  type: int
  sample: 24
tags:
  description: Dictionary containing all the tags associated with the Kinesis stream.
  returned: when state == present.
  type: dict
  sample: {
      "Name": "Splunk",
      "Env": "development"
  }
'''

try:
    import botocore
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

import logging
import re
import datetime
import time
from functools import reduce
from ansible.module_utils._text import to_native


def convert_to_lower(data):
    """Convert all uppercase keys in dict with lowercase_
    Args:
        data (dict): Dictionary with keys that have upper cases in them
            Example.. FooBar == foo_bar
            if a val is of type datetime.datetime, it will be converted to
            the ISO 8601

    Basic Usage:
        >>> test = {'FooBar': []}
        >>> test = convert_to_lower(test)
        {
            'foo_bar': []
        }

    Returns:
        Dictionary
    """
    results = dict()
    if isinstance(data, dict):
        for key, val in data.items():
            key = re.sub(r'(([A-Z]{1,3}){1})', r'_\1', key).lower()
            if key[0] == '_':
                key = key[1:]
            if isinstance(val, datetime.datetime):
                results[key] = val.isoformat()
            elif isinstance(val, dict):
                results[key] = convert_to_lower(val)
            elif isinstance(val, list):
                converted = list()
                for item in val:
                    converted.append(convert_to_lower(item))
                results[key] = converted
            else:
                results[key] = val
    return results


def find_stream(client, stream_name, check_mode=False):
    """Retrieve a Kinesis Stream.
    Args:
        client (botocore.client.EC2): Boto3 client.
        stream_name (str): Name of the Kinesis stream.

    Kwargs:
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('kinesis')
        >>> stream_name = 'test-stream'

    Returns:
        Tuple (bool, str, dict)
    """
    err_msg = ''
    success = False
    params = {
        'DeliveryStreamName': stream_name,
    }
    results = dict()
    has_more_shards = True
    shards = list()
    try:
        if not check_mode:
            # while has_more_shards:
                results = (
                    client.describe_delivery_stream(**params)['DeliveryStreamDescription']
                )
                # shards.extend(results.pop('Shards'))
                # has_more_shards = results['HasMoreShards']
            # results['Shards'] = shards
            # num_closed_shards = len([s for s in shards if 'EndingSequenceNumber' in s['SequenceNumberRange']])
            # results['OpenShardsCount'] = len(shards) - num_closed_shards
            # results['ClosedShardsCount'] = num_closed_shards
            # results['ShardsCount'] = len(shards)
        else:
            results = {
                'OpenShardsCount': 5,
                'ClosedShardsCount': 0,
                'ShardsCount': 5,
                'HasMoreShards': True,
                'RetentionPeriodHours': 24,
                'StreamName': stream_name,
                'StreamARN': 'arn:aws:kinesis:east-side:123456789:stream/{0}'.format(stream_name),
                'DeliveryStreamStatus': 'ACTIVE'
            }
        success = True
    except botocore.exceptions.ClientError as e:
        err_msg = to_native(e)

    return success, err_msg, results


def wait_for_status(client, stream_name, status, wait_timeout=300,
                    check_mode=False):
    """Wait for the status to change for a Kinesis Stream.
    Args:
        client (botocore.client.EC2): Boto3 client
        stream_name (str): The name of the kinesis stream.
        status (str): The status to wait for.
            examples. status=available, status=deleted

    Kwargs:
        wait_timeout (int): Number of seconds to wait, until this timeout is reached.
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('kinesis')
        >>> stream_name = 'test-stream'
        >>> wait_for_status(client, stream_name, 'ACTIVE', 300)

    Returns:
        Tuple (bool, str, dict)
    """
    polling_increment_secs = 5
    wait_timeout = time.time() + wait_timeout
    status_achieved = False
    stream = dict()
    err_msg = ""

    while wait_timeout > time.time():
        try:
            logging.info('STREAM surrent status is {0} : Waiting for status : {1}'.format(stream.get('DeliveryStreamStatus'), status))
            find_success, find_msg, stream = (
                find_stream(client, stream_name, check_mode=check_mode)
            )
            if check_mode:
                status_achieved = True
                break

            elif status != 'DELETING':
                if find_success and stream:
                    if stream.get('DeliveryStreamStatus') == status:
                        status_achieved = True
                        break

            elif status == 'DELETING' and not check_mode:
                if not find_success:
                    status_achieved = True
                    break

            time.sleep(polling_increment_secs)

        except botocore.exceptions.ClientError as e:
            logging.info(' EXCEPTION '+to_native(e))
            err_msg = to_native(e)

    if not status_achieved:
        err_msg = "Wait time out reached, while waiting for results"
    else:
        err_msg = "Status {0} achieved successfully".format(status)

    logging.info(' EXITING  err_msg='+str(err_msg))
    return status_achieved, err_msg, stream


def stream_action(client, stream_name, s3_destination='NA', stream_type='NA', KinesisStreamSourceConfiguration='NA', action='create',
                  timeout=300, check_mode=False):
    """Create or Delete an Amazon Kinesis Stream.
    Args:
        client (botocore.client.EC2): Boto3 client.
        stream_name (str): The name of the kinesis stream.

    Kwargs:
        shard_count (int): Number of shards this stream will use.
        action (str): The action to perform.
            valid actions == create and delete
            default=create
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('kinesis')
        >>> stream_name = 'test-stream'
        >>> shard_count = 20
        >>> stream_action(client, stream_name, shard_count, action='create')

    Returns:
        List (bool, str)
    """
    success = False
    err_msg = ''
    params = {
        'DeliveryStreamName': stream_name
    }
    try:
        if not check_mode:
            if action == 'create':
                # params['ShardCount'] = shard_count
                params['S3DestinationConfiguration'] = s3_destination
                params['DeliveryStreamType'] = stream_type
                params['KinesisStreamSourceConfiguration'] = KinesisStreamSourceConfiguration
                logging.info('params '+str(params))
                client.create_delivery_stream(**params)
                success = True
            elif action == 'delete':
                client.delete_delivery_stream(**params)
                success = True
            else:
                err_msg = 'Invalid action {0}'.format(action)
        else:
            if action == 'create':
                success = True
            elif action == 'delete':
                success = True
            else:
                err_msg = 'Invalid action {0}'.format(action)

    except botocore.exceptions.ClientError as e:
        err_msg = to_native(e)

    return success, err_msg


def create_stream(client, stream_name, s3_destination, stream_type,
                  KinesisStreamSourceConfiguration, wait=False, wait_timeout=300, check_mode=False):
    """Create an Amazon Kinesis Stream.
    Args:
        client (botocore.client.EC2): Boto3 client.
        stream_name (str): The name of the kinesis stream.

    Kwargs:
        number_of_shards (int): Number of shards this stream will use.
            default=1
        retention_period (int): Can not be less than 24 hours
            default=None
        tags (dict): The tags you want applied.
            default=None
        wait (bool): Wait until Stream is ACTIVE.
            default=False
        wait_timeout (int): How long to wait until this operation is considered failed.
            default=300
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('kinesis')
        >>> stream_name = 'test-stream'
        >>> number_of_shards = 10
        >>> tags = {'env': 'test'}
        >>> create_stream(client, stream_name, number_of_shards, tags=tags)

    Returns:
        Tuple (bool, bool, str, dict)
    """
    success = False
    changed = False
    err_msg = ''
    results = dict()

    stream_found, stream_msg, current_stream = (
        find_stream(client, stream_name, check_mode=check_mode)
    )

    if stream_found and current_stream.get('DeliveryStreamStatus') == 'DELETING' and wait:
        wait_success, wait_msg, current_stream = (
            wait_for_status(
                client, stream_name, 'ACTIVE', wait_timeout,
                check_mode=check_mode
            )
        )

    # if stream_found and not check_mode:
    #     if current_stream['ShardsCount'] != number_of_shards:
    #         err_msg = 'Can not change the number of shards in a Kinesis Stream'
    #         return success, changed, err_msg, results

    if stream_found and current_stream.get('DeliveryStreamStatus') != 'DELETING':
        return False, True, 'Error creating Stream: Stream already exists', {}
    else:
        create_success, create_msg = (
            stream_action(
                client, stream_name, s3_destination, stream_type, KinesisStreamSourceConfiguration, action='create',
                check_mode=check_mode
            )
        )
        if not create_success:
            changed = False
            err_msg = 'Failed to create Kinesis stream: {0}'.format(create_msg)
            return create_success, changed, err_msg, {}
        else:
            changed = True
            if wait:
                wait_success, wait_msg, results = (
                    wait_for_status(
                        client, stream_name, 'ACTIVE', wait_timeout,
                        check_mode=check_mode
                    )
                )
                if wait_success:
                    success = wait_success
                    err_msg = wait_msg
                else:
                    err_msg = (
                        'Kinesis Stream {0} is in the process of being created'
                            .format(stream_name)
                    )
                    return wait_success, changed, wait_msg, results
            else:
                err_msg = (
                    'Kinesis Stream {0} is in the process of being created.'
                    .format(stream_name)
                )


    if success:
        _, _, results = (
            find_stream(client, stream_name, check_mode=check_mode)
        )
        results = convert_to_lower(results)

    return success, changed, err_msg, results


def delete_stream(client, stream_name, wait=False, wait_timeout=300,
                  check_mode=False):
    """Delete an Amazon Kinesis Stream.
    Args:
        client (botocore.client.EC2): Boto3 client.
        stream_name (str): The name of the kinesis stream.

    Kwargs:
        wait (bool): Wait until Stream is ACTIVE.
            default=False
        wait_timeout (int): How long to wait until this operation is considered failed.
            default=300
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('kinesis')
        >>> stream_name = 'test-stream'
        >>> delete_stream(client, stream_name)

    Returns:
        Tuple (bool, bool, str, dict)
    """
    success = False
    changed = False
    err_msg = ''
    results = dict()
    stream_found, stream_msg, current_stream = (
        find_stream(client, stream_name, check_mode=check_mode)
    )
    if stream_found:
        success, err_msg = (
            stream_action(
                client, stream_name, action='delete', check_mode=check_mode
            )
        )
        if success:
            changed = True
            if wait:
                success, err_msg, results = (
                    wait_for_status(
                        client, stream_name, 'DELETING', wait_timeout,
                        check_mode=check_mode
                    )
                )
                err_msg = 'Stream {0} deleted successfully'.format(stream_name)
                if not success:
                    return success, True, err_msg, results
            else:
                err_msg = (
                    'Stream {0} is in the process of being deleted'
                        .format(stream_name)
                )
    else:
        success = True
        changed = False
        err_msg = 'Stream {0} does not exist'.format(stream_name)

    return success, changed, err_msg, results


def main():
    logging.basicConfig(filename='/tmp/python.log',level=logging.INFO)
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(default=None, required=True),
            s3_destination=dict(required=True, type='dict'),
            stream_type=dict(required=True, type='str',choices=['KinesisStreamAsSource']),
            KinesisStreamSourceConfiguration=dict(required=True, type='dict'),
            wait=dict(default=True, required=False, type='bool'),
            wait_timeout=dict(default=300, required=False, type='int'),
            state=dict(default='present', choices=['present', 'absent']),
        )
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    stream_name = module.params.get('name')
    s3_destination = module.params.get('s3_destination')
    stream_type = module.params.get('stream_type')
    state = module.params.get('state')
    KinesisStreamSourceConfiguration = module.params.get('KinesisStreamSourceConfiguration')
    wait = module.params.get('wait')
    wait_timeout = module.params.get('wait_timeout')

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required.')

    check_mode = module.check_mode
    try:
        region, ec2_url, aws_connect_kwargs = (
            get_aws_connection_info(module, boto3=True)
        )
        client = (
            boto3_conn(
                module, conn_type='client', resource='firehose',
                region=region, endpoint=ec2_url, **aws_connect_kwargs
            )
        )
    except botocore.exceptions.ClientError as e:
        err_msg = 'Boto3 Client Error - {0}'.format(to_native(e.msg))
        module.fail_json(
            success=False, changed=False, result={}, msg=err_msg
        )

    if state == 'present':
        success, changed, err_msg, results = (
            create_stream(
                client, stream_name, s3_destination, stream_type, KinesisStreamSourceConfiguration,
                wait, wait_timeout, check_mode
            )
        )
    elif state == 'absent':
        success, changed, err_msg, results = (
            delete_stream(client, stream_name, wait, wait_timeout, check_mode)
        )

    if success:
        module.exit_json(
            success=success, changed=changed, msg=err_msg, **results
        )
    else:
        module.fail_json(
            success=success, changed=changed, msg=err_msg, result=results
        )

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
