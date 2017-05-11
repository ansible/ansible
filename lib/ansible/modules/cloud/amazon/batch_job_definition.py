#!/usr/bin/python
# (c) 2017, Jon Meran <jonathan.meran@sonos.com>
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


DOCUMENTATION = '''
---
module: batch_job_definition
short_description: Manage AWS Batch Job Definitions
description:
    - This module allows the management of AWS Batch Job Definitions.
      It is idempotent and supports "Check" mode.  Use module M(batch_compute_environment) to manage the compute
      environment, M(batch_job_queue) to manage job queues, M(batch_job_definition) to manage job definitions.

version_added: "2.4"

author: Jon Meran (@jonmer85)
options:
  job_definition_name:
    description:
      - The name for the job definition
    required: true

  state:
    description:
      - Describes the desired state.
    required: true
    default: "present"
    choices: ["present", "absent"]

  type:
    description:
      - The type of job definition
    required: true

  parameters:
    description:
      - Default parameter substitution placeholders to set in the job definition. Parameters are specified as a
        key-value pair mapping. Parameters in a SubmitJob request override any corresponding parameter defaults from
        the job definition.

  image:
    description:
      - The image used to start a container. This string is passed directly to the Docker daemon. Images in the Docker
        Hub registry are available by default. Other repositories are specified with `` repository-url /image :tag ``.
        Up to 255 letters (uppercase and lowercase), numbers, hyphens, underscores, colons, periods, forward slashes,
        and number signs are allowed. This parameter maps to Image in the Create a container section of the Docker
        Remote API and the IMAGE parameter of docker run.

  vcpus:
    description:
      - The number of vCPUs reserved for the container. This parameter maps to CpuShares in the Create a container
        section of the Docker Remote API and the --cpu-shares option to docker run. Each vCPU is equivalent to
        1,024 CPU shares.

  memory:
    description:
      - The hard limit (in MiB) of memory to present to the container. If your container attempts to exceed the memory
        specified here, the container is killed. This parameter maps to Memory in the Create a container section of the
        Docker Remote API and the --memory option to docker run.

  command:
    description:
      - The command that is passed to the container. This parameter maps to Cmd in the Create a container section of
        the Docker Remote API and the COMMAND parameter to docker run. For more information,
        see https://docs.docker.com/engine/reference/builder/#cmd.

  job_role_arn:
    description:
      - The Amazon Resource Name (ARN) of the IAM role that the container can assume for AWS permissions.

  volumes:
    description:
      - A list of data volumes used in a job. List of dictionaries with the following
        form: { host: { sourcePath: <string> }, name: <string> }

  environment:
    description:
      - The environment variables to pass to a container. This parameter maps to Env in the Create a container section
        of the Docker Remote API and the --env option to docker run. List of dictionaries with the following
        form: { name: <string>, value: <string> }

  mount_points:
    description:
      - The mount points for data volumes in your container. This parameter maps to Volumes in the Create a container
        section of the Docker Remote API and the --volume option to docker run. List of dictionaries with the following
        form: { containerPath: <string>, readOnly: <boolean>, sourceVolume: <string> }

  readonly_root_filesystem:
    description:
      - When this parameter is true, the container is given read-only access to its root file system. This parameter
        maps to ReadonlyRootfs in the Create a container section of the Docker Remote API and the --read-only option
        to docker run.

  privileged:
    description:
      - When this parameter is true, the container is given elevated privileges on the host container instance
        (similar to the root user). This parameter maps to Privileged in the Create a container section of the
        Docker Remote API and the --privileged option to docker run.

  ulimits:
    description:
      - A list of ulimits to set in the container. This parameter maps to Ulimits in the Create a container section
        of the Docker Remote API and the --ulimit option to docker run. List of dictionaries with the following
        form: "{ hardLimit: <int>, name: <string>, softLimit: <int> }".

  user:
    description:
      - The user name to use inside the container. This parameter maps to User in the Create a container section of
        the Docker Remote API and the --user option to docker run.

  attempts:
    description:
      - Retry strategy - The number of times to move a job to the RUNNABLE status. You may specify between 1 and 10
        attempts. If attempts is greater than one, the job is retried if it fails until it has moved to RUNNABLE that
        many times.

requirements:
    - boto3
extends_documentation_fragment:
    - aws
'''

EXAMPLES = '''
---
- hosts: localhost
  gather_facts: no
  vars:
    state: present
  tasks:
- name: My Batch Job Definition
  batch_job_definition:
    job_definition_name: My Batch Job Definition
    state: present
    type: container
    parameters:
      Param1: Val1
      Param2: Val2
    image: <Docker Image URL>
    vcpus: 1
    memory: 512
    command:
      - python
      - run_my_script.py
      - arg1
    job_role_arn: <Job Role ARN>
    attempts: 3
  register: job_definition_create_result

- name: show results
  debug: var=job_definition_create_result
'''

RETURN = '''
---
batch_job_definition_action:
    description: describes what action was taken
    returned: success
    type: string
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info, boto3_conn, HAS_BOTO3
from botocore.exceptions import ClientError, ParamValidationError, MissingParametersError

# ---------------------------------------------------------------------------------------------------
#
#   Helper Functions & classes
#
# ---------------------------------------------------------------------------------------------------

# logger = logging.getLogger()
# logging.basicConfig(filename='ansible_debug.log')
# logger.setLevel(logging.DEBUG)


class AWSConnection:
    """
    Create the connection object and client objects as required.
    """

    def __init__(self, ansible_obj, resources, boto3=True):

        try:
            self.region, self.endpoint, aws_connect_kwargs = get_aws_connection_info(ansible_obj, boto3=boto3)

            self.resource_client = dict()
            if not resources:
                resources = ['batch']

            resources.append('iam')

            for resource in resources:
                aws_connect_kwargs.update(dict(region=self.region,
                                               endpoint=self.endpoint,
                                               conn_type='client',
                                               resource=resource
                                               ))
                self.resource_client[resource] = boto3_conn(ansible_obj, **aws_connect_kwargs)

            # if region is not provided, then get default profile/session region
            if not self.region:
                self.region = self.resource_client['batch'].meta.region_name

        except (ClientError, ParamValidationError, MissingParametersError) as e:
            ansible_obj.fail_json(msg="Unable to connect, authorize or access resource: {0}".format(e))

        # set account ID
        try:
            self.account_id = self.resource_client['iam'].get_user()['User']['Arn'].split(':')[4]
        except (ClientError, ValueError, KeyError, IndexError):
            self.account_id = ''

    def client(self, resource='batch'):
        return self.resource_client[resource]


def cc(key):
    """
    Changes python key into Camel case equivalent. For example, 'compute_environment_name' becomes 'computeEnvironmentName'.

    :param key:
    :return:
    """
    components = key.split('_')
    return components[0] + "".join([token.capitalize() for token in components[1:]])


def set_api_params(module, module_params):
    """
    Sets module parameters to those expected by the boto3 API.

    :param module:
    :param module_params:
    :return:
    """

    api_params = dict()

    for param in module_params:
        module_param = module.params.get(param, None)
        if module_param is not None:
            api_params[cc(param)] = module_param
    return api_params


def validate_params(module, aws):
    """
    Performs basic parameter validation.

    :param module:
    :param aws:
    :return:
    """
    return


# ---------------------------------------------------------------------------------------------------
#
#   Batch Job Definition functions
#
# ---------------------------------------------------------------------------------------------------

def get_current_job_definition(module, connection):
    try:
        environments = connection.client().describe_job_definitions(
            jobDefinitionName=module.params['job_definition_name']
        )
        if len(environments) > 0:
            latest_revision = max(map(lambda d: d['revision'], environments['jobDefinitions']))
            latest_definition = next((x for x in environments['jobDefinitions'] if x['revision'] == latest_revision),
                                     None)
            return latest_definition
        return None
    except ClientError:
        return None


def create_job_definition(module, aws):
    """
        Adds a Batch job definition

        :param module:
        :param aws:
        :return:
        """

    client = aws.client('batch')
    changed = False

    # set API parameters
    api_params = set_api_params(module, get_base_params())
    container_properties_params = set_api_params(module, get_container_property_params())
    retry_strategy_params = set_api_params(module, get_retry_strategy_params())

    api_params['retryStrategy'] = retry_strategy_params
    api_params['containerProperties'] = container_properties_params

    try:
        if not module.check_mode:
            client.register_job_definition(**api_params)
        changed = True
    except (ClientError, ParamValidationError, MissingParametersError) as e:
        module.fail_json(msg='Error registering job definition: {0}'.format(e))

    return changed


def get_retry_strategy_params():
    return ('attempts',)


def get_container_property_params():
    return ('image', 'vcpus', 'memory', 'command', 'job_role_arn', 'volumes', 'environment', 'mount_points',
            'readonly_root_filesystem', 'privileged', 'ulimits', 'user')


def get_base_params():
    return ('job_definition_name', 'type', 'parameters')


def get_compute_environment_order_list(module):
    compute_environment_order_list = []
    for ceo in module.params['compute_environment_order']:
        compute_environment_order_list.append(dict(order=ceo['order'], computeEnvironment=ceo['compute_environment']))
    return compute_environment_order_list


def remove_job_definition(module, aws):
    """
    Remove a Batch job definition

    :param module:
    :param aws:
    :return:
    """

    client = aws.client('batch')
    changed = False

    # set API parameters
    api_params = {'jobDefinition': module.params['job_definition_name']}

    try:
        if not module.check_mode:
            client.delete_job_definition(**api_params)
        changed = True
    except (ClientError, ParamValidationError, MissingParametersError) as e:
        module.fail_json(msg='Error removing job definition: {0}'.format(e))
    return changed


def job_definition_equal(module, current_definition):

    equal = True

    for param in get_base_params():
        if module.params.get(param) != current_definition.get(cc(param)):
            equal = False
            break

    for param in get_container_property_params():
        if module.params.get(param) != current_definition.get('containerProperties').get(cc(param)):
            equal = False
            break

    for param in get_retry_strategy_params():
        if module.params.get(param) != current_definition.get('retryStrategy').get(cc(param)):
            equal = False
            break

    return equal


def manage_state(module, aws):

    changed = False
    current_state = 'absent'
    state = module.params['state']
    job_definition_name = module.params['job_definition_name']
    action_taken = 'none'

    check_mode = module.check_mode

    # check if the job definition exists
    current_job_definition = get_current_job_definition(module, aws)
    if current_job_definition:
        current_state = 'present'

    if state == 'present':
        if current_state == 'present':
            # check if definition has changed and register a new version if necessary
            if not job_definition_equal(module, current_job_definition):
                create_job_definition(module, aws)
                action_taken = 'updated with new version'
                changed = True
        else:
            # Create Job definition
            changed = create_job_definition(module, aws)
            action_taken = 'added'

        response = get_current_job_definition(module, aws)
        if not response:
            module.fail_json(msg='Unable to get job definition information after creating/updating')
    else:
        if current_state == 'present':
            # remove the Job definition
            changed = remove_job_definition(module, aws)
            action_taken = 'deregistered'
    return dict(changed=changed, ansible_facts=dict(batch_job_definition_action=action_taken), response=response)


# ---------------------------------------------------------------------------------------------------
#
#   MAIN
#
# ---------------------------------------------------------------------------------------------------

def main():
    """
    Main entry point.

    :return dict: ansible facts
    """

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            state=dict(required=False, default='present', choices=['present', 'absent']),
            job_definition_name=dict(required=True, default=None),
            type=dict(required=True, default=None),
            parameters=dict(type='dict', default=None),
            image=dict(required=True, default=None),
            vcpus=dict(type='int', required=True, default=None),
            memory=dict(type='int', required=True, default=None),
            command=dict(type='list', default=[]),
            job_role_arn=dict(default=None),
            volumes=dict(type='list', default=[]),
            environment=dict(type='list', default=[]),
            mount_points=dict(type='list', default=[]),
            readonly_root_filesystem=dict(default=None),
            privileged=dict(default=None),
            ulimits=dict(type='list', default=[]),
            user=dict(default=None),
            attempts=dict(type='int', default=None),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_together=[]
    )

    # validate dependencies
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required for this module.')

    aws = AWSConnection(module, ['batch'])

    validate_params(module, aws)

    results = manage_state(module, aws)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
