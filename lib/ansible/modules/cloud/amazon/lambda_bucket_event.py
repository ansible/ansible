#!/usr/bin/python
# (c) 2019, XLAB d.o.o <www.xlab.si>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: lambda_bucket_event
short_description: Creates, updates or deletes S3 Bucket notification for lambda
description:
    - This module allows the management of AWS Lambda function bucket event mappings via the
      Ansible framework. Use module M(lambda) to manage the lambda function itself, M(lambda_alias)
      to manage function aliases and M(lambda_policy) to modify lambda permissions.
notes:
    - This module heavily depends on M(lambda_policy) as you need to allow C(lambda:InvokeFunction)
       permission for your lambda function.
version_added: "2.9"

author:
    - XLAB d.o.o. (@xlab-si)
options:
  event_name:
    description:
      - unique name for event notification on bucket
    required: True
    type: str
  lambda_function_arn:
    description:
      - The ARN of the lambda function.
    required: true
    aliases: ['function_arn']
    type: str
  bucket_name:
    description:
      - S3 bucket name
    required: True
    type: str
  state:
    description:
      - Describes the desired state.
    required: true
    default: "present"
    choices: ["present", "absent"]
    type: str
  alias:
    description:
      - Name of the function alias. Mutually exclusive with C(version).
    required: true
    type: str
  version:
    description:
      -  Version of the Lambda function. Mutually exclusive with C(alias).
    required: false
    type: int
  events:
    description:
      - Events that you want to be triggering notifications. You can select multiple events to send
        to the same destination, you can set up different events to send to different destinations,
        and you can set up a prefix or suffix for an event. However, for each bucket,
        individual events cannot have multiple configurations with overlapping prefixes or
        suffixes that could match the same object key.
    required: True
    choices: ['s3:ObjectCreated:*', 's3:ObjectCreated:Put', 's3:ObjectCreated:Post',
              's3:ObjectCreated:Copy', 's3:ObjectCreated:CompleteMultipartUpload',
              's3:ObjectRemoved:*', 's3:ObjectRemoved:Delete',
              's3:ObjectRemoved:DeleteMarkerCreated', 's3:ObjectRestore:Post',
              's3:ObjectRestore:Completed', 's3:ReducedRedundancyLostObject']
    type: list
  prefix:
    description:
      - Optional prefix to limit the notifications to objects with keys that start with matching
        characters.
    required: false
    type: str
  suffix:
    description:
      - Optional suffix to limit the notifications to objects with keys that end with matching
        characters.
    required: false
    type: str
requirements:
    - boto3
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
---
# Example that creates a lambda event notification for a bucket
- hosts: localhost
  gather_facts: no
  tasks:
  - name: Process jpg image
    lambda_bucket_event:
      state: present
      event_name: on_file_add_or_remove
      bucket_name: test-bucket
      function_name: arn:aws:lambda:us-east-2:526810320200:function:test-lambda
      events: ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
      prefix: images/
      suffix: .jpg
'''

RETURN = '''
'''

from ansible.module_utils.aws.core import AnsibleAWSModule

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # will be protected by AnsibleAWSModule


class AmazonBucket:
    def __init__(self, client, bucket_name):
        self.client = client
        self.bucket_name = bucket_name
        self._full_config_cache = None

    def _full_config(self):
        if self._full_config_cache is None:
            self._full_config_cache = [Config.from_api(cfg) for cfg in
                                       self.client.get_bucket_notification_configuration(
                                           Bucket=self.bucket_name).get(
                                           'LambdaFunctionConfigurations', list())]
        return self._full_config_cache

    def current_config(self, config_name):
        for config in self._full_config():
            if config.raw['Id'] == config_name:
                return config

    def apply_config(self, desired):
        configs = [cfg.raw for cfg in self._full_config() if cfg.name != desired.raw['Id']]
        configs.append(desired.raw)
        self._upload_bucket_config(configs)

    def delete_config(self, desired):
        configs = [cfg.raw for cfg in self._full_config() if cfg.name != desired.raw['Id']]
        self._upload_bucket_config(configs)

    def _upload_bucket_config(self, config):
        self.client.put_bucket_notification_configuration(
            Bucket=self.bucket_name,
            NotificationConfiguration={
                'LambdaFunctionConfigurations': config
            })


class Config:
    def __init__(self, content):
        self._content = content
        self.name = content['Id']

    @property
    def raw(self):
        return self._content

    def __eq__(self, other):
        if other:
            return self.raw == other.raw
        return False

    @classmethod
    def from_params(cls, **params):
        function_arn = params['lambda_function_arn']

        qualifier = None
        if params['version'] > 0:
            qualifier = str(params['version'])
        elif params['alias']:
            qualifier = str(params['alias'])
        if qualifier:
            params['lambda_function_arn'] = '{0}:{1}'.format(function_arn, qualifier)

        return cls({
            'Id': params['event_name'],
            'LambdaFunctionArn': params['lambda_function_arn'],
            'Events': sorted(params['events']),
            'Filter': {
                'Key': {
                    'FilterRules': [{
                        'Name': 'Prefix',
                        'Value': params['prefix']
                    }, {
                        'Name': 'Suffix',
                        'Value': params['suffix']
                    }]
                }
            }
        })

    @classmethod
    def from_api(cls, config):
        return cls(config)


def main():
    event_types = ['s3:ObjectCreated:*', 's3:ObjectCreated:Put', 's3:ObjectCreated:Post',
                   's3:ObjectCreated:Copy', 's3:ObjectCreated:CompleteMultipartUpload',
                   's3:ObjectRemoved:*', 's3:ObjectRemoved:Delete',
                   's3:ObjectRemoved:DeleteMarkerCreated', 's3:ObjectRestore:Post',
                   's3:ObjectRestore:Completed', 's3:ReducedRedundancyLostObject']
    argument_spec = dict(
        state=dict(required=False, default='present', choices=['present', 'absent']),
        event_name=dict(required=True),
        lambda_function_arn=dict(default=None, aliases=['function_arn']),
        bucket_name=dict(required=True),
        events=dict(type='list', default=None, choices=event_types),
        prefix=dict(required=False, default=''),
        suffix=dict(required=False, default=''),
        alias=dict(required=False, default=None),
        version=dict(type='int', required=False, default=0),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[['alias', 'version']],
        required_if=[['state', 'present', ['events', 'lambda_function_arn']]]
    )

    bucket = AmazonBucket(module.client('s3'), module.params['bucket_name'])
    current = bucket.current_config(module.params['event_name'])
    desired = Config.from_params(**module.params)

    state = module.params['state']
    try:
        if (state == 'present' and current == desired) or (state == 'absent' and not current):
            changed = False
        elif module.check_mode:
            changed = True
        elif state == 'present':
            changed = True
            bucket.apply_config(desired)
        elif state == 'absent':
            changed = True
            bucket.delete_config(desired)
    except (ClientError, BotoCoreError) as e:
        module.fail_json(msg='{0}'.format(e))

    module.exit_json(**dict(changed=changed))


if __name__ == '__main__':
    main()
