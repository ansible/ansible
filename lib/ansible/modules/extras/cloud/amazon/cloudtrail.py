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

DOCUMENTATION = """
---
module: cloudtrail
short_description: manage CloudTrail creation and deletion
description:
  - Creates or deletes CloudTrail configuration. Ensures logging is also enabled.
version_added: "2.0"
author:
    - "Ansible Core Team"
    - "Ted Timmons"
requirements:
  - "boto >= 2.21"
options:
  state:
    description:
      - add or remove CloudTrail configuration.
    required: true
    choices: ['enabled', 'disabled']
  name:
    description:
      - name for given CloudTrail configuration.
      - This is a primary key and is used to identify the configuration.
  s3_bucket_prefix:
    description:
      - bucket to place CloudTrail in.
      - this bucket should exist and have the proper policy. See U(http://docs.aws.amazon.com/awscloudtrail/latest/userguide/aggregating_logs_regions_bucket_policy.html)
      - required when state=enabled.
    required: false
  s3_key_prefix:
    description:
      - prefix to keys in bucket. A trailing slash is not necessary and will be removed.
    required: false
  include_global_events:
    description:
      - record API calls from global services such as IAM and STS?
    required: false
    default: false
    choices: ["true", "false"]

  aws_secret_key:
    description:
      - AWS secret key. If not set then the value of the AWS_SECRET_KEY environment variable is used.
    required: false
    default: null
    aliases: [ 'ec2_secret_key', 'secret_key' ]
    version_added: "1.5"
  aws_access_key:
    description:
      - AWS access key. If not set then the value of the AWS_ACCESS_KEY environment variable is used.
    required: false
    default: null
    aliases: [ 'ec2_access_key', 'access_key' ]
    version_added: "1.5"
  region:
    description:
      - The AWS region to use. If not specified then the value of the EC2_REGION environment variable, if any, is used.
    required: false
    aliases: ['aws_region', 'ec2_region']
    version_added: "1.5"

extends_documentation_fragment: aws
"""

EXAMPLES = """
  - name: enable cloudtrail
    local_action: cloudtrail
      state: enabled
      name: main
      s3_bucket_name: ourbucket
      s3_key_prefix: cloudtrail
      region: us-east-1

  - name: enable cloudtrail with different configuration
    local_action: cloudtrail
      state: enabled
      name: main
      s3_bucket_name: ourbucket2
      s3_key_prefix: ''
      region: us-east-1

  - name: remove cloudtrail
    local_action: cloudtrail
      state: disabled
      name: main
      region: us-east-1
"""

HAS_BOTO = False
try:
    import boto
    import boto.cloudtrail
    from boto.regioninfo import RegionInfo
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import connect_to_aws, ec2_argument_spec, get_ec2_creds


class CloudTrailManager:
    """Handles cloudtrail configuration"""

    def __init__(self, module, region=None, **aws_connect_params):
        self.module = module
        self.region = region
        self.aws_connect_params = aws_connect_params
        self.changed = False

        try:
            self.conn = connect_to_aws(boto.cloudtrail, self.region, **self.aws_connect_params)
        except boto.exception.NoAuthHandlerFound as e:
            self.module.fail_json(msg=str(e))

    def view_status(self, name):
        return self.conn.get_trail_status(name)

    def view(self, name):
        ret = self.conn.describe_trails(trail_name_list=[name])
        trailList = ret.get('trailList', [])
        if len(trailList) == 1:
          return trailList[0]
        return None

    def exists(self, name=None):
        ret = self.view(name)
        if ret:
          return True
        return False

    def enable_logging(self, name):
        '''Turn on logging for a cloudtrail that already exists. Throws Exception on error.'''
        self.conn.start_logging(name)


    def enable(self, **create_args):
        return self.conn.create_trail(**create_args)

    def update(self, **create_args):
        return self.conn.update_trail(**create_args)

    def delete(self, name):
        '''Delete a given cloudtrial configuration. Throws Exception on error.'''
        self.conn.delete_trail(name)



def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state={'required': True, 'choices': ['enabled', 'disabled']},
        name={'required': True, 'type': 'str'},
        s3_bucket_name={'required': False, 'type': 'str'},
        s3_key_prefix={'default': '', 'required': False, 'type': 'str'},
        include_global_events={'default': True, 'required': False, 'type': 'bool'},
    ))
    required_together = (['state', 's3_bucket_name'])

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True, required_together=required_together)

    if not HAS_BOTO:
      module.fail_json(msg='boto is required.')

    ec2_url, access_key, secret_key, region = get_ec2_creds(module)
    aws_connect_params = dict(aws_access_key_id=access_key,
                              aws_secret_access_key=secret_key)

    if not region:
        module.fail_json(msg="Region must be specified as a parameter, in EC2_REGION or AWS_REGION environment variables or in boto configuration file")

    ct_name = module.params['name']
    s3_bucket_name = module.params['s3_bucket_name']
    # remove trailing slash from the key prefix, really messes up the key structure.
    s3_key_prefix = module.params['s3_key_prefix'].rstrip('/')

    include_global_events = module.params['include_global_events']

    #if module.params['state'] == 'present' and 'ec2_elbs' not in module.params:
    #    module.fail_json(msg="ELBs are required for registration or viewing")

    cf_man = CloudTrailManager(module, region=region, **aws_connect_params)

    results = { 'changed': False }
    if module.params['state'] == 'enabled':
        results['exists'] = cf_man.exists(name=ct_name)
        if results['exists']:
            results['view'] = cf_man.view(ct_name)
            # only update if the values have changed.
            if results['view']['S3BucketName']              != s3_bucket_name or \
              results['view'].get('S3KeyPrefix', '')      != s3_key_prefix  or \
              results['view']['IncludeGlobalServiceEvents'] != include_global_events:
                if not module.check_mode:
                    results['update'] = cf_man.update(name=ct_name, s3_bucket_name=s3_bucket_name, s3_key_prefix=s3_key_prefix, include_global_service_events=include_global_events)
                results['changed'] = True
        else:
            if not module.check_mode:
                # doesn't exist. create it.
                results['enable'] = cf_man.enable(name=ct_name, s3_bucket_name=s3_bucket_name, s3_key_prefix=s3_key_prefix, include_global_service_events=include_global_events)
            results['changed'] = True

        # given cloudtrail should exist now. Enable the logging.
        results['view_status'] = cf_man.view_status(ct_name)
        results['was_logging_enabled'] = results['view_status'].get('IsLogging', False)
        if not results['was_logging_enabled']:
            if not module.check_mode:
                cf_man.enable_logging(ct_name)
                results['logging_enabled'] = True
            results['changed'] = True

    # delete the cloudtrai
    elif module.params['state'] == 'disabled':
        # check to see if it exists before deleting.
        results['exists'] = cf_man.exists(name=ct_name)
        if results['exists']:
            # it exists, so we should delete it and mark changed.
            if not module.check_mode:
                cf_man.delete(ct_name)
            results['changed'] = True

    module.exit_json(**results)


if __name__ == '__main__':
    main()
