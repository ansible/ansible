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
module: kinesis_firehose
short_description: Manage a Kinesis Firehose Delivery Stream.
description:
    - Create or Delete a Kinesis Firehose Delivery Stream.
version_added: "2.5"
author: Stephen Clark (clarkst)
options:
  delivery_stream_name:
    description:
      - "The name of the Kinesis Firhose Delivery Stream you are managing."
    default: None
    required: true
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
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

  # Basic creation example:
  - name: Set up Kinesis Firehose Delivery Stream with a Kinesis Stream input and S3 destination , wait for the stream to become ACTIVE
    kinesis_firehose:
      delivery_stream_name: clarky-test-stream
      delivery_stream_type: KinesisStreamAsSource
      kinesis_stream_source_configuration:
        kinesis_stream_a_r_n: arn:aws:kinesis:eu-west-1:XXXXXXXXXXXX:stream/playground-sclark-eu-west-1-Stream
        role_a_r_n: arn:aws:iam::XXXXXXXXXXXX:role/firehose_delivery_role
      s3_destination_configuration:
        role_a_r_n: arn:aws:iam::XXXXXXXXXXXX:role/firehose_delivery_role
        bucket_a_r_n: arn:aws:s3:::clarky.play.metadev.io
      wait: yes
      wait_timeout: 600
      state: present
    register: testout

  # Transformation Lambda creation example:
  # Basic creation example:
  - name: Set up Kinesis Firehose Stream , wait for the stream to become ACTIVE
    kinesis_firehose:
      delivery_stream_name: clarky-test-stream
      delivery_stream_type: KinesisStreamAsSource
      kinesis_stream_source_configuration:
        kinesis_stream_a_r_n: arn:aws:kinesis:eu-west-1:XXXXXXXXXXXX:stream/playground-sclark-eu-west-1-Stream
        role_a_r_n: arn:aws:iam::XXXXXXXXXXXX:role/firehose_delivery_role
      extended_s3_destination_configuration:
        role_a_r_n: arn:aws:iam::XXXXXXXXXXXX:role/firehose_delivery_role
        bucket_a_r_n: arn:aws:s3:::clarky.play.metadev.io
        compression_format: GZIP
        processing_configuration:
          enabled: true
          processors:
            -
              type: Lambda
              parameters:
                -
                  parameter_name: LambdaArn
                  parameter_value: "arn:aws:lambda:eu-west-1:XXXXXXXXXXXX:function:RecordDelimiter"
      wait: yes
      wait_timeout: 600
      state: present
    register: testout

  # Basic delete example:
  - name: Delete Kinesis Firehose Stream
    kinesis_firehose:
      delivery_stream_name: clarky-test-stream
      delivery_stream_type: KinesisStreamAsSource
      kinesis_stream_source_configuration:
      s3_destination_configuration:
      wait: yes
      wait_timeout: 300
      state: absent
    register: testout
'''

RETURN = '''
delivery_stream_name:
  description: The name of the Kinesis Firehose Delivery Stream.
  returned: when state == present.
  type: string
  sample: "test-stream"
delivery_stream_arn:
  description: The amazon resource identifier
  returned: when state == present.
  type: string
  sample: "arn:aws:kinesis:east-side:123456789:stream/test-stream"
delivery_stream_status:
  description: The current state of the Kinesis Firehose Delivery Stream.
  returned: when state == present.
  type: string
  sample: "ACTIVE"
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
from ansible.module_utils._text import to_native


def convert_to_snake_case(data):
    """Convert all uppercase keys in dict with lowercase_
    Args:
        data (dict): Dictionary with keys that have upper cases in them
            Example.. FooBar == foo_bar
            if a val is of type datetime.datetime, it will be converted to
            the ISO 8601

    Basic Usage:
        >>> test = {'FooBar': []}
        >>> test = convert_to_snake_case(test)
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
                results[key] = convert_to_snake_case(val)
            elif isinstance(val, list):
                converted = list()
                for item in val:
                    converted.append(convert_to_snake_case(item))
                results[key] = converted
            else:
                results[key] = val
    return results


def convert_to_title_case(data):
    """Convert all snake_case keys in dict with TitleCase
    Args:
        data (dict): Dictionary with keys that have snake_case in them
            Example.. foo_bar == FooBar
            if a val is of type datetime.datetime, it will be converted to
            the ISO 8601

    Basic Usage:
        >>> test = {'foo_bar': []}
        >>> test = convert_to_title_case(test)
        {
            'FooBar': []
        }

    Returns:
        Dictionary
    """
    results = dict()
    if isinstance(data, dict):
        for key, val in data.items():
            key = to_title(key)
            if key[0] == '_':
                key = key[1:]
            if isinstance(val, datetime.datetime):
                results[key] = val.isoformat()
            elif isinstance(val, dict):
                results[key] = convert_to_title_case(val)
            elif isinstance(val, list):
                converted = list()
                for item in val:
                    converted.append(convert_to_title_case(item))
                results[key] = converted
            else:
                results[key] = val
    return results


def find_stream(client, delivery_stream_name, check_mode=False):
    """Retrieve a Kinesis Firehose Delivery Stream.
    Args:
        client (botocore.client.EC2): Boto3 client.
        stream_name (str): Name of the Kinesis Firehose Delivery stream.

    Kwargs:
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('firehose')
        >>> stream_name = 'test-stream'

    Returns:
        Tuple (bool, str, dict)
    """
    err_msg = ''
    success = False
    params = {
        'DeliveryStreamName': delivery_stream_name,
    }
    results = dict()
    try:
        if not check_mode:
            results = (
                client.describe_delivery_stream(**params)['DeliveryStreamDescription']
            )
        else:
            results = {
                'StreamName': delivery_stream_name,
                'StreamARN': 'arn:aws:kinesis:east-side:123456789:stream/{0}'.format(delivery_stream_name),
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
        >>> client = boto3.client('firehose')
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


def stream_action(client, delivery_stream_name, s3_destination_configuration='NA', delivery_stream_type='NA', kinesis_stream_source_configuration='NA',
                  extended_s3_destination_configuration='NA', action='create', timeout=300, check_mode=False):
    """Create or Delete an Amazon Kinesis Stream.
    Args:
        client (botocore.client.EC2): Boto3 client.
        stream_name (str): The name of the kinesis stream.

    Kwargs:
        action (str): The action to perform.
            valid actions == create and delete
            default=create
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('firehose')
        >>> delivery_stream_name = 'test-stream'
        >>> stream_action(client, delivery_stream_name, shard_count, action='create')

    Returns:
        List (bool, str)
    """
    success = False
    err_msg = ''
    params = {
        'DeliveryStreamName': delivery_stream_name
    }
    try:
        if not check_mode:
            if action == 'create':
                if s3_destination_configuration:
                    params['S3DestinationConfiguration'] = s3_destination_configuration
                params['DeliveryStreamType'] = delivery_stream_type
                if kinesis_stream_source_configuration:
                    params['KinesisStreamSourceConfiguration'] = kinesis_stream_source_configuration
                if extended_s3_destination_configuration:
                    params['ExtendedS3DestinationConfiguration'] = extended_s3_destination_configuration
                # logging.info('params '+str(params))
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


def create_delivery_stream(client, delivery_stream_name, s3_destination_configuration, stream_type,
                  KinesisStreamSourceConfiguration, ExtendedS3DestinationConfiguration, wait=False, wait_timeout=300, check_mode=False):
    """Create an Amazon Kinesis Firehose Delivery Stream.
    Args:
        client (botocore.client.EC2): Boto3 client.
        stream_name (str): The name of the kinesis firehose delivery stream.

    Kwargs:
        wait (bool): Wait until Firehose Delivery Stream is ACTIVE.
            default=False
        wait_timeout (int): How long to wait until this operation is considered failed.
            default=300
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('firehose')
        >>> stream_name = 'test-stream'
        >>> create_delivery_stream(client, stream_name)

    Returns:
        Tuple (bool, bool, str, dict)
    """
    success = False
    changed = False
    err_msg = ''
    results = dict()

    stream_found, stream_msg, current_stream = (
        find_stream(client, delivery_stream_name, check_mode=check_mode)
    )

    if stream_found and current_stream.get('DeliveryStreamStatus') == 'DELETING' and wait:
        wait_success, wait_msg, current_stream = (
            wait_for_status(
                client, delivery_stream_name, 'ACTIVE', wait_timeout,
                check_mode=check_mode
            )
        )

    if stream_found and current_stream.get('DeliveryStreamStatus') != 'DELETING':
        return False, True, 'Error creating Stream: Stream already exists', {}
    else:
        create_success, create_msg = (
            stream_action(
                client, delivery_stream_name, s3_destination_configuration, stream_type, KinesisStreamSourceConfiguration,
                ExtendedS3DestinationConfiguration, action='create', check_mode=check_mode
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
                        client, delivery_stream_name, 'ACTIVE', wait_timeout,
                        check_mode=check_mode
                    )
                )
                if wait_success:
                    success = wait_success
                    err_msg = wait_msg
                else:
                    err_msg = (
                        'Kinesis Stream {0} is in the process of being created'.format(delivery_stream_name)
                    )
                    return wait_success, changed, wait_msg, results
            else:
                err_msg = (
                    'Kinesis Stream {0} is in the process of being created.'
                    .format(delivery_stream_name)
                )

    if success:
        _, _, results = (
            find_stream(client, delivery_stream_name, check_mode=check_mode)
        )
        results = convert_to_snake_case(results)

    return success, changed, err_msg, results


def delete_stream(client, delivery_stream_name, wait=False, wait_timeout=300,
                  check_mode=False):
    """Delete an Amazon Firehose Delivery Kinesis Stream.
    Args:
        client (botocore.client.EC2): Boto3 client.
        delivery_stream_name (str): The name of the kinesis firehose delivery stream.

    Kwargs:
        wait (bool): Wait until Delivery Stream is ACTIVE.
            default=False
        wait_timeout (int): How long to wait until this operation is considered failed.
            default=300
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('firehose')
        >>> delivery_stream_name = 'test-stream'
        >>> delete_stream(client, delivery_stream_name)

    Returns:
        Tuple (bool, bool, str, dict)
    """
    success = False
    changed = False
    err_msg = ''
    results = dict()
    stream_found, stream_msg, current_stream = (
        find_stream(client, delivery_stream_name, check_mode=check_mode)
    )
    if stream_found:
        success, err_msg = (
            stream_action(
                client, delivery_stream_name, action='delete', check_mode=check_mode
            )
        )
        if success:
            changed = True
            if wait:
                success, err_msg, results = (
                    wait_for_status(
                        client, delivery_stream_name, 'DELETING', wait_timeout,
                        check_mode=check_mode
                    )
                )
                err_msg = 'Stream {0} deleted successfully'.format(delivery_stream_name)
                if not success:
                    return success, True, err_msg, results
            else:
                err_msg = (
                    'Stream {0} is in the process of being deleted'.format(delivery_stream_name)
                )
    else:
        success = True
        changed = False
        err_msg = 'Stream {0} does not exist'.format(delivery_stream_name)

    return success, changed, err_msg, results


def to_title(word):
    return ''.join([si.title() if not (str.isdigit(si[0])) else si for si in word.split('_')])


def main():
    logging.basicConfig(filename='/tmp/kinesis_firehose.log', level=logging.INFO)
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            delivery_stream_name=dict(default=None, required=True),
            s3_destination_configuration=dict(type='dict'),
            delivery_stream_type=dict(required=True, type='str', choices=['DirectPut', 'KinesisStreamAsSource']),
            kinesis_stream_source_configuration=dict(required=True, type='dict'),
            extended_s3_destination_configuration=dict(type='dict'),
            wait=dict(default=True, required=False, type='bool'),
            wait_timeout=dict(default=300, required=False, type='int'),
            state=dict(default='present', choices=['present', 'absent']),
        )
    )
    mutually_exclusive = [['s3_destination_configuration', 'extended_s3_destination_configuration']]

    required_one_of = [
        ['s3_destination_configuration', 'extended_s3_destination_configuration']
    ]

    required_if = [
        ['state', 'present', ['delivery_stream_type']],
        ['delivery_stream_type', 'DirectPut', ['s3_destination_configuration']],
        ['delivery_stream_type', 'KinesisStreamAsSource', ['kinesis_stream_source_configuration']]
    ]

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=mutually_exclusive,
        required_if=required_if,
        required_one_of=required_one_of
    )

    delivery_stream_name = module.params.get('delivery_stream_name')
    s3_destination_configuration = module.params.get('s3_destination_configuration')
    delivery_stream_type = module.params.get('delivery_stream_type')
    state = module.params.get('state')
    kinesis_stream_source_configuration = convert_to_title_case(module.params.get('kinesis_stream_source_configuration'))
    extended_s3_destination_configuration = convert_to_title_case(module.params.get('extended_s3_destination_configuration'))
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
            create_delivery_stream(
                client, delivery_stream_name, s3_destination_configuration, delivery_stream_type, kinesis_stream_source_configuration,
                extended_s3_destination_configuration, wait, wait_timeout, check_mode
            )
        )
    elif state == 'absent':
        success, changed, err_msg, results = (
            delete_stream(client, delivery_stream_name, wait, wait_timeout, check_mode)
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
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, camel_dict_to_snake_dict, ec2_argument_spec, get_aws_connection_info

if __name__ == '__main__':
    main()
