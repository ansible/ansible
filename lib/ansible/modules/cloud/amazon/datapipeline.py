#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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

DOCUMENTATION = '''
---
module: datapipeline
version_added: "2.2"
author: Raghu Udiyar <raghusiddarth@gmail.com>
requirements: [ "boto3" ]
short_description: Create and manage AWS Datapipelines
extends_documentation_fragment:
    - aws
    - ec2
description:
    - Create and manage AWS Datapipelines. Creation is not idempotent in AWS,
      so the version tag is used to acheive idempotency by embedding it in
      the uniqueId field.

      The pipeline definition must be in the format given here
      U(http://docs.aws.amazon.com/datapipeline/latest/APIReference/API_PutPipelineDefinition.html#API_PutPipelineDefinition_RequestSyntax)

      Also operations will wait for a configurable amount
      of time to ensure the pipeline is in the requested state.
options:
  name:
    description:
      - Name of the Datapipeline
    required: true
  description:
    description:
      - Optional pipeline description
    required: false
    default: ''
  version:
    description:
      - Version of the pipeline being created. Only required during pipeline
        creation. This is how idempotency is achieved.
    required: false
  objects:
    description:
      - List of pipeline Objects
    required: false
  parameters:
    description:
      - List of pipeline parameters
    required: false
  values:
    description:
      - List of pipeline values
    required: false
  timeout:
    description:
      - Time in seconds to wait for the pipeline to transion to the requested
        state, fail otherwise
    required: false
    default: 300
  state:
    description:
      - Requested state of the pipeline
    choices: ['present', 'absent', 'active', 'deactive']
    required: false
    default: present

'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create pipeline
- datapipeline:
    name: test-dp
    version: 1.0
    region: us-west-2
    objects: "{{pipelineObjects}}"
    parameters: "{{pipelineParameters}}"
    values: "{{pipelineValues}}"
    state: present

# Activate pipeline
- datapipeline:
    name: test-dp
    region: us-west-2
    state: active

# Delete pipeline
- datapipeline:
    name: test-dp
    region: us-west-2
    state: absent

'''

RETURN = '''
id:
    description: datapipeline id
    type: int
    sample: df-0669972GNI1WO9T4NFZ
    returned: success
msg:
    description: describes status of the operation
    type: string
'''
import re
import datetime
from functools import partial
try:
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


DP_ACTIVE_STATES = ['ACTIVE', 'SCHEDULED']
DP_INACTIVE_STATES = ['INACTIVE', 'PENDING', 'FINISHED', 'DELETING']
DP_ACTIVATING_STATE = 'ACTIVATING'
DP_DEACTIVATING_STATE = 'DEACTIVATING'
PIPELINE_DOESNT_EXIST = '^.*Pipeline with id: {} does not exist$'


class DataPipelineNotFound(Exception):
    pass


class TimeOutException(Exception):
    pass


def pipeline_id(client, name):
    """Return pipeline id for the given pipeline name

    :param object client: boto3 datapipeline client
    :param string name: pipeline name
    :returns: pipeline id
    :raises: DataPipelineNotFound

    """
    pipelines = client.list_pipelines()
    for dp in pipelines['pipelineIdList']:
        if dp['name'] == name:
            return dp['id']
    else:
        raise DataPipelineNotFound


def pipeline_description(client, dp_id):
    """Return pipeline description list

    :param object client: boto3 datapipeline client
    :returns: pipeline description dictionary
    :raises: DataPipelineNotFound

    """
    try:
        return client.describe_pipelines(pipelineIds=[dp_id])
    except ClientError as e:
        if re.match(PIPELINE_DOESNT_EXIST.format(dp_id), str(e)):
            raise DataPipelineNotFound
        else:
            module.fail_json(msg="Failed to retrieve pipeline description - "+str(e))


def pipeline_field(client, dp_id, field):
    """Return a pipeline field from the pipeline description.

    The available fields are listed in describe_pipelines output.

    :param object client: boto3 datapipeline client
    :param string dp_id: pipeline id
    :param string field: pipeline description field
    :returns: pipeline field information

    """
    dp_description = pipeline_description(client, dp_id)
    for field_key in dp_description['pipelineDescriptionList'][0]['fields']:
        if field_key['key'] == field:
            return field_key['stringValue']
    else:
        raise KeyError("Field key {} not found!".format(field))

pipeline_status = partial(pipeline_field, field='@pipelineState')
pipeline_uniqueid = partial(pipeline_field, field='uniqueId')


def run_with_timeout(timeout, func, *func_args, **func_kwargs):
        """Run func with the provided args and kwargs, and wait utill
        timeout for truthy return value

        :param int timeout: time to wait for status
        :param function func: function to run, should return True or False
        :param args func_args: function args to pass to func
        :param kwargs func_kwargs: function key word args
        :returns: True if func returns truthy within timeout
        :raises: TimeOutException

        """
        start = datetime.datetime.now()
        end = start + datetime.timedelta(seconds=timeout)

        while datetime.datetime.now() < end:
            if func(*func_args, **func_kwargs):
                return True
            else:
                # check every 10s
                time.sleep(10)

        raise TimeOutException


def check_dp_exists(client, dp_id):
    """Check if datapipeline exists

    :param object client: boto3 datapipeline client
    :param string dp_id: pipeline id
    :returns: True or False

    """
    try:
        # pipeline_description raises DataPipelineNotFound
        if pipeline_description(client, dp_id):
            return True
        else:
            return False
    except DataPipelineNotFound:
        return False


def check_dp_status(client, dp_id, status):
    """Checks if datapipeline matches states in status list

    :param object client: boto3 datapipeline client
    :param string dp_id: pipeline id
    :param list status: list of states to check against
    :returns: True or False

    """
    assert type(status) == list
    if pipeline_status(client, dp_id) in status:
        return True
    else:
        return False


def pipeline_status_timeout(client, dp_id, status, timeout):
    args = (client, dp_id, status)
    try:
        return run_with_timeout(timeout, check_dp_status, *args)
    except TimeOutException:
        raise


def pipeline_exists_timeout(client, dp_id, timeout):
    args = (client, dp_id)
    try:
        return run_with_timeout(timeout, check_dp_exists, *args)
    except TimeOutException:
        raise


def activate_pipeline(client, module):
    """Activates pipeline

    """
    dp_name = module.params.get('name')
    timeout = module.params.get('timeout')

    try:
        dp_id = pipeline_id(client, dp_name)
    except DataPipelineNotFound:
        module.fail_json(msg='Data Pipeline {} not found'.format(dp_name))

    if pipeline_status(client, dp_id) in DP_ACTIVE_STATES:
        changed = False
    else:
        client.activate_pipeline(pipelineId=dp_id)
        try:
            pipeline_status_timeout(client, dp_id, status=DP_ACTIVE_STATES,
                                    timeout=timeout)
        except TimeOutException:
            module.fail_json(msg=('Data Pipeline {} failed to activate'
                                  'within timeout {} seconds').format(dp_name,
                                                                      timeout))
        changed = True

    result = {'id': dp_id,
              'msg': 'Data Pipeline {} activated'.format(dp_name)}
    return (changed, result)


def deactivate_pipeline(client, module):
    """Deactivates pipeline

    """
    dp_name = module.params.get('name')
    timeout = module.params.get('timeout')

    try:
        dp_id = pipeline_id(client, dp_name)
    except DataPipelineNotFound:
        module.fail_json(msg='Data Pipeline {} not found'.format(dp_name))

    if pipeline_status(client, dp_id) in DP_INACTIVE_STATES:
        changed = False
    else:
        client.deactivate_pipeline(pipelineId=dp_id)
        try:
            pipeline_status_timeout(client, dp_id, status=DP_INACTIVE_STATES,
                                    timeout=timeout)
        except TimeOutException:
            module.fail_json(msg=('Data Pipeline {} failed to deactivate'
                                  'within timeout {} seconds').format(dp_name,
                                                                      timeout))
        changed = True

    result = {'id': dp_id,
              'msg': 'Data Pipeline {} deactivated'.format(dp_name)}

    return (changed, result)


def _delete_dp_with_check(dp_id, client, timeout):
    client.delete_pipeline(pipelineId=dp_id)
    return pipeline_exists_timeout(client, dp_id, timeout=timeout)


def delete_pipeline(client, module):
    """Deletes pipeline

    """
    dp_name = module.params.get('name')
    timeout = module.params.get('timeout')

    try:
        dp_id = pipeline_id(client, dp_name)
        _delete_dp_with_check(dp_id, client, timeout)
        changed = True
    except DataPipelineNotFound:
        changed = False
    except TimeOutException:
        module.fail_json(msg=('Data Pipeline {} failed to delete'
                              'within timeout {} seconds').format(dp_name,
                                                                  timeout))

    result = {'id': dp_id,
              'msg': 'Data Pipeline {} deleted'.format(dp_name)}

    return (changed, result)


def build_unique_id(dp_name, dp_version):
    return '{0}-{1}'.format(dp_name, dp_version)


def create_pipeline(client, module):
    """Creates datapipeline. Uses version and uniqueId to achieve idempotency.

    """
    dp_name = module.params.get('name')
    dp_version = module.params.get('version')
    objects = module.params.get('objects', None)
    description = module.params.get('description', '')
    if not dp_version:
        module.fail_json(msg='Version is required when creating the pipeline!')
    if objects:
        parameters = module.params.get('parameters')
        values = module.params.get('values')

    unique_id = build_unique_id(dp_name, dp_version)
    result = dict()
    create_dp = False
    try:
        dp_id = pipeline_id(client, dp_name)
        dp_unique_id = pipeline_uniqueid(client, dp_id)
        # delete existing pipeline before creating new one
        if dp_unique_id != unique_id:
            changed, _ = delete_pipeline(client, module)
            create_dp = True
        else:
            changed = False
            msg = 'Data Pipeline {} version {} is present'.format(dp_name,
                                                                  dp_version)
            result = {'id': dp_id,
                      'unique_id': dp_unique_id,
                      'msg': msg}
    except DataPipelineNotFound:
        create_dp = True

    dp = {}
    if create_dp:
        dp = client.create_pipeline(name=dp_name,
                                    uniqueId=unique_id,
                                    description=description)
        dp_id = dp['pipelineId']
        if objects:
            client.put_pipeline_definition(pipelineId=dp_id,
                                           pipelineObjects=objects,
                                           parameterObjects=parameters,
                                           parameterValues=values)
            changed = True

        result = {'id': dp_id,
                  'dp': camel_dict_to_snake_dict(dp),
                  'msg': 'Data Pipeline {} created'.format(dp_name)}

    return (changed, result)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True),
            version=dict(required=False),
            description=dict(required=False, default=''),
            objects=dict(required=False, type='list', default=[]),
            parameters=dict(required=False, type='list', default=[]),
            values=dict(required=False, type='list', default=[]),
            timeout=dict(required=False, type='int', default=300),
            state=dict(default='present', choices=[
                'present', 'absent', 'active', 'deactive'
                ]),
        )
    )
    module = AnsibleModule(argument_spec, supports_check_mode=False)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required for the datapipeline module!')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        if not region:
            module.fail_json(msg="Region must be specified as a parameter, in EC2_REGION or AWS_REGION environment variables or in boto configuration file")
        client = boto3_conn(module, conn_type='client',
                            resource='datapipeline', region=region,
                            endpoint=ec2_url, **aws_connect_kwargs)
    except boto.exception.NoAuthHandlerFound, e:
        module.fail_json(msg="Can't authorize connection - "+str(e))

    state = module.params.get('state')
    if state == 'present':
        (changed, result) = create_pipeline(client, module)
    elif state == 'absent':
        (changed, result) = delete_pipeline(client, module)
    elif state == 'active':
        (changed, result) = activate_pipeline(client, module)
    elif state == 'deactive':
        (changed, result) = deactivate_pipeline(client, module)

    module.exit_json(result=result, changed=changed)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
