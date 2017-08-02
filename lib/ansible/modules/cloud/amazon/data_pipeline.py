#!/usr/bin/python
#
# Copyright (c) 2017 Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: data_pipeline
version_added: "2.4"
author:
  - Raghu Udiyar <raghusiddarth@gmail.com> (@raags)
  - Sloane Hertel <shertel@redhat.com>
requirements: [ "boto3" ]
short_description: Create and manage AWS Datapipelines
extends_documentation_fragment:
    - aws
    - ec2
description:
    - Create and manage AWS Datapipelines. Creation is not idempotent in AWS,
      so the uniqueId is created by hashing the options (minus objects) given to the datapipeline.

      The pipeline definition must be in the format given here
      U(http://docs.aws.amazon.com/datapipeline/latest/APIReference/API_PutPipelineDefinition.html#API_PutPipelineDefinition_RequestSyntax).

      Also operations will wait for a configurable amount
      of time to ensure the pipeline is in the requested state.
options:
  name:
    description:
      - The name of the Datapipeline to create/modify/delete.
    required: true
  description:
    description:
      - An optional description for the pipeline being created.
    default: ''
  objects:
    description:
      - A list of pipeline object definitions, each of which is a dict that takes the keys C(id), C(name) and C(fields).
    suboptions:
      id:
        description:
          - The ID of the object.
      name:
        description:
          - The name of the object.
      fields:
        description:
          - A list of dicts that take the keys C(key) and C(stringValue)/C(refValue).
            The value is specified as a reference to another object C(refValue) or as a string value C(stringValue)
            but not as both.
  parameters:
    description:
      - A list of parameter objects (dicts) in the pipeline definition.
    suboptions:
      id:
        description:
          - The ID of the parameter object.
      attributes:
        description:
          - A list of attributes (dicts) of the parameter object. Each attribute takes the keys C(key) and C(stringValue) both
            of which are strings.
  values:
    description:
      - A list of parameter values (dicts) in the pipeline definition. Each dict takes the keys C(id) and C(stringValue) both
        of which are strings.
  timeout:
    description:
      - Time in seconds to wait for the pipeline to transition to the requested state, fail otherwise.
    default: 300
  state:
    description:
      - The requested state of the pipeline.
    choices: ['present', 'absent', 'active', 'inactive']
    default: present
  tags:
    description:
      - A dict of key:value pair(s) to add to the pipeline.
    default: null
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create pipeline
- data_pipeline:
    name: test-dp
    region: us-west-2
    objects: "{{pipelineObjects}}"
    parameters: "{{pipelineParameters}}"
    values: "{{pipelineValues}}"
    tags:
      key1: val1
      key2: val2
    state: present

# Example populating and activating a pipeline that demonstrates two ways of providing pipeline objects
- data_pipeline:
  name: test-dp
  objects:
    - "id": "DefaultSchedule"
      "name": "Every 1 day"
      "fields":
        - "key": "period"
          "stringValue": "1 days"
        - "key": "type"
          "stringValue": "Schedule"
        - "key": "startAt"
          "stringValue": "FIRST_ACTIVATION_DATE_TIME"
    - "id": "Default"
      "name": "Default"
      "fields": [ { "key": "resourceRole", "stringValue": "my_resource_role" },
                  { "key": "role", "stringValue": "DataPipelineDefaultRole" },
                  { "key": "pipelineLogUri", "stringValue": "s3://my_s3_log.txt" },
                  { "key": "scheduleType", "stringValue": "cron" },
                  { "key": "schedule", "refValue": "DefaultSchedule" },
                  { "key": "failureAndRerunMode", "stringValue": "CASCADE" } ]
  state: active

# Activate pipeline
- data_pipeline:
    name: test-dp
    region: us-west-2
    state: active

# Delete pipeline
- data_pipeline:
    name: test-dp
    region: us-west-2
    state: absent

'''

RETURN = '''
changed:
  description: whether the data pipeline has been modified
  type: bool
  returned: always
  sample:
    changed: true
result:
  description:
    - Contains the data pipeline data (data_pipeline) and a return message (msg).
      If the data pipeline exists data_pipeline will contain the keys description, name,
      pipeline_id, state, tags, and unique_id. If the data pipeline does not exist then
      data_pipeline will be an empty dict. The msg describes the status of the operation.
  returned: always
  type: dict
'''

import hashlib
import traceback
import re
import json
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info, boto3_conn, camel_dict_to_snake_dict
from ansible.module_utils._text import to_bytes, to_text

try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


DP_ACTIVE_STATES = ['ACTIVE', 'SCHEDULED']
DP_INACTIVE_STATES = ['INACTIVE', 'PENDING', 'FINISHED', 'DELETING']
DP_ACTIVATING_STATE = 'ACTIVATING'
DP_DEACTIVATING_STATE = 'DEACTIVATING'
PIPELINE_DOESNT_EXIST = '^.*Pipeline with id: {0} does not exist$'


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
        raise DataPipelineNotFound


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
        raise KeyError("Field key {0} not found!".format(field))


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

    for _ in range(timeout // 10):
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
    assert isinstance(status, list)
    if pipeline_field(client, dp_id, field="@pipelineState") in status:
        return True
    else:
        return False


def pipeline_status_timeout(client, dp_id, status, timeout):
    args = (client, dp_id, status)
    return run_with_timeout(timeout, check_dp_status, *args)


def pipeline_exists_timeout(client, dp_id, timeout):
    args = (client, dp_id)
    return run_with_timeout(timeout, check_dp_exists, *args)


def activate_pipeline(client, module):
    """Activates pipeline

    """
    dp_name = module.params.get('name')
    timeout = module.params.get('timeout')

    try:
        dp_id = pipeline_id(client, dp_name)
    except DataPipelineNotFound:
        module.fail_json(msg='Data Pipeline {0} not found'.format(dp_name))

    if pipeline_field(client, dp_id, field="@pipelineState") in DP_ACTIVE_STATES:
        changed = False
    else:
        try:
            client.activate_pipeline(pipelineId=dp_id)
        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidRequestException":
                module.fail_json(msg="You need to populate your pipeline before activation.")
        try:
            pipeline_status_timeout(client, dp_id, status=DP_ACTIVE_STATES,
                                    timeout=timeout)
        except TimeOutException:
            if pipeline_field(client, dp_id, field="@pipelineState") == "FINISHED":
                # activated but completed more rapidly than it was checked
                pass
            else:
                module.fail_json(msg=('Data Pipeline {0} failed to activate '
                                 'within timeout {1} seconds').format(dp_name, timeout))
        changed = True

    data_pipeline = get_result(client, dp_id)
    result = {'data_pipeline': data_pipeline,
              'msg': 'Data Pipeline {0} activated.'.format(dp_name)}

    return (changed, result)


def deactivate_pipeline(client, module):
    """Deactivates pipeline

    """
    dp_name = module.params.get('name')
    timeout = module.params.get('timeout')

    try:
        dp_id = pipeline_id(client, dp_name)
    except DataPipelineNotFound:
        module.fail_json(msg='Data Pipeline {0} not found'.format(dp_name))

    if pipeline_field(client, dp_id, field="@pipelineState") in DP_INACTIVE_STATES:
        changed = False
    else:
        client.deactivate_pipeline(pipelineId=dp_id)
        try:
            pipeline_status_timeout(client, dp_id, status=DP_INACTIVE_STATES,
                                    timeout=timeout)
        except TimeOutException:
            module.fail_json(msg=('Data Pipeline {0} failed to deactivate'
                                  'within timeout {1} seconds').format(dp_name, timeout))
        changed = True

    data_pipeline = get_result(client, dp_id)
    result = {'data_pipeline': data_pipeline,
              'msg': 'Data Pipeline {0} deactivated.'.format(dp_name)}

    return (changed, result)


def _delete_dp_with_check(dp_id, client, timeout):
    client.delete_pipeline(pipelineId=dp_id)
    try:
        pipeline_status_timeout(client=client, dp_id=dp_id, status=[PIPELINE_DOESNT_EXIST], timeout=timeout)
    except DataPipelineNotFound:
        return True


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
        module.fail_json(msg=('Data Pipeline {0} failed to delete'
                              'within timeout {1} seconds').format(dp_name, timeout))
    result = {'data_pipeline': {},
              'msg': 'Data Pipeline {0} deleted'.format(dp_name)}

    return (changed, result)


def build_unique_id(module):
    data = dict(module.params)
    # removing objects from the unique id so we can update objects or populate the pipeline after creation without needing to make a new pipeline
    [data.pop(each, None) for each in ('objects', 'timeout')]
    json_data = json.dumps(data, sort_keys=True).encode("utf-8")
    hashed_data = hashlib.md5(json_data).hexdigest()
    return hashed_data


def format_tags(tags):
    """ Reformats tags

    :param dict tags: dict of data pipeline tags (e.g. {key1: val1, key2: val2, key3: val3})
    :returns: list of dicts (e.g. [{key: key1, value: val1}, {key: key2, value: val2}, {key: key3, value: val3}])

    """
    return [dict(key=k, value=v) for k, v in tags.items()]


def get_result(client, dp_id):
    """ Get the current state of the data pipeline and reformat it to snake_case for exit_json

    :param object client: boto3 datapipeline client
    :param string dp_id: pipeline id
    :returns: reformatted dict of pipeline description

     """
    # pipeline_description returns a pipelineDescriptionList of length 1
    # dp is a dict with keys "description" (str), "fields" (list), "name" (str), "pipelineId" (str), "tags" (dict)
    dp = pipeline_description(client, dp_id)['pipelineDescriptionList'][0]

    # Get uniqueId and pipelineState in fields to add to the exit_json result
    dp["unique_id"] = pipeline_field(client, dp_id, field="uniqueId")
    dp["pipeline_state"] = pipeline_field(client, dp_id, field="@pipelineState")

    # Remove fields; can't make a list snake_case and most of the data is redundant
    del dp["fields"]

    # Note: tags is already formatted fine so we don't need to do anything with it

    # Reformat data pipeline and add reformatted fields back
    dp = camel_dict_to_snake_dict(dp)
    return dp


def diff_pipeline(client, module, objects, unique_id, dp_name):
    """Check if there's another pipeline with the same unique_id and if so, checks if the object needs to be updated
    """
    result = {}
    changed = False
    create_dp = False

    # See if there is already a pipeline with the same unique_id
    unique_id = build_unique_id(module)
    try:
        dp_id = pipeline_id(client, dp_name)
        dp_unique_id = to_text(pipeline_field(client, dp_id, field="uniqueId"))
        if dp_unique_id != unique_id:
            # A change is expected but not determined. Updated to a bool in create_pipeline().
            changed = "NEW_VERSION"
            create_dp = True
        # Unique ids are the same - check if pipeline needs modification
        else:
            dp_objects = client.get_pipeline_definition(pipelineId=dp_id)['pipelineObjects']
            # Definition needs to be updated
            if dp_objects != objects:
                changed, msg = define_pipeline(client, module, objects, dp_id)
            # No changes
            else:
                msg = 'Data Pipeline {0} is present'.format(dp_name)
            data_pipeline = get_result(client, dp_id)
            result = {'data_pipeline': data_pipeline,
                      'msg': msg}
    except DataPipelineNotFound:
            create_dp = True

    return create_dp, changed, result


def define_pipeline(client, module, objects, dp_id):
    """Puts pipeline definition

    """
    dp_name = module.params.get('name')

    if pipeline_field(client, dp_id, field="@pipelineState") == "FINISHED":
        msg = 'Data Pipeline {0} is unable to be updated while in state FINISHED.'.format(dp_name)
        changed = False

    elif objects:
        parameters = module.params.get('parameters')
        values = module.params.get('values')

        try:
            client.put_pipeline_definition(pipelineId=dp_id,
                                           pipelineObjects=objects,
                                           parameterObjects=parameters,
                                           parameterValues=values)
            msg = 'Data Pipeline {0} has been updated.'.format(dp_name)
            changed = True
        except ClientError as e:
            module.fail_json(msg="Failed to put the definition for pipeline {0}. Check that string/reference fields"
                             "are not empty and that the number of objects in the pipeline does not exceed maximum allowed"
                             "objects".format(dp_name), exception=traceback.format_exc())
    else:
        changed = False
        msg = ""

    return changed, msg


def create_pipeline(client, module):
    """Creates datapipeline. Uses uniqueId to achieve idempotency.

    """
    dp_name = module.params.get('name')
    objects = module.params.get('objects', None)
    description = module.params.get('description', '')
    tags = module.params.get('tags')
    timeout = module.params.get('timeout')

    unique_id = build_unique_id(module)
    create_dp, changed, result = diff_pipeline(client, module, objects, unique_id, dp_name)

    if changed == "NEW_VERSION":
        # delete old version
        changed, _ = delete_pipeline(client, module)

    # There isn't a pipeline or it has different parameters than the pipeline in existence.
    if create_dp:
        # Make pipeline
        try:
            tags = format_tags(tags)
            dp = client.create_pipeline(name=dp_name,
                                        uniqueId=unique_id,
                                        description=description,
                                        tags=tags)
            dp_id = dp['pipelineId']
            pipeline_exists_timeout(client, dp_id, timeout)
        except ClientError as e:
            module.fail_json(msg="Failed to create the data pipeline {0}.".format(dp_name), exception=traceback.format_exc())
        except TimeOutException:
            module.fail_json(msg=('Data Pipeline {0} failed to create'
                                  'within timeout {1} seconds').format(dp_name, timeout))
        # Put pipeline definition
        _, msg = define_pipeline(client, module, objects, dp_id)

        changed = True
        data_pipeline = get_result(client, dp_id)
        result = {'data_pipeline': data_pipeline,
                  'msg': 'Data Pipeline {0} created.'.format(dp_name) + msg}

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
            timeout=dict(required=False, type='int', default=300),
            state=dict(default='present', choices=['present', 'absent',
                                                   'active', 'inactive']),
            tags=dict(required=False, type='dict')
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
    except ClientError as e:
        module.fail_json(msg="Can't authorize connection - " + str(e))

    state = module.params.get('state')
    if state == 'present':
        changed, result = create_pipeline(client, module)
    elif state == 'absent':
        changed, result = delete_pipeline(client, module)
    elif state == 'active':
        changed, result = activate_pipeline(client, module)
    elif state == 'inactive':
        changed, result = deactivate_pipeline(client, module)

    module.exit_json(result=result, changed=changed)


if __name__ == '__main__':
    main()
