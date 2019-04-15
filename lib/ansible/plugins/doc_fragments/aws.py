# -*- coding: utf-8 -*-

# Copyright: (c) 2014, Will Thames <will@thames.id.au>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # AWS only documentation fragment
    DOCUMENTATION = r'''
options:
  debug_botocore_endpoint_logs:
    description:
      - Use a botocore.endpoint logger to parse the unique (rather than total) "resource:action" API calls made during a task, outputing
        the set to the resource_actions key in the task results. Use the aws_resource_action callback to output to total list made during
        a playbook. The ANSIBLE_DEBUG_BOTOCORE_LOGS environment variable may also be used.
    type: bool
    default: 'no'
    version_added: "2.8"
  ec2_url:
    description:
      - Url to use to connect to EC2 or your Eucalyptus cloud (by default the module will use EC2 endpoints).
        Ignored for modules where region is required. Must be specified for all other modules if region is not used.
        If not set then the value of the EC2_URL environment variable, if any, is used.
    type: str
  aws_secret_key:
    description:
      - AWS secret key. If not set then the value of the AWS_SECRET_ACCESS_KEY, AWS_SECRET_KEY, or EC2_SECRET_KEY environment variable is used.
    type: str
    aliases: [ ec2_secret_key, secret_key ]
  aws_access_key:
    description:
      - AWS access key. If not set then the value of the AWS_ACCESS_KEY_ID, AWS_ACCESS_KEY or EC2_ACCESS_KEY environment variable is used.
    type: str
    aliases: [ ec2_access_key, access_key ]
  security_token:
    description:
      - AWS STS security token. If not set then the value of the AWS_SECURITY_TOKEN or EC2_SECURITY_TOKEN environment variable is used.
    type: str
    aliases: [ access_token ]
    version_added: "1.6"
  validate_certs:
    description:
      - When set to "no", SSL certificates will not be validated for boto versions >= 2.6.0.
    type: bool
    default: yes
    version_added: "1.5"
  profile:
    description:
      - Uses a boto profile. Only works with boto >= 2.24.0.
    type: str
    version_added: "1.6"
requirements:
  - python >= 2.6
  - boto
notes:
  - If parameters are not set within the module, the following
    environment variables can be used in decreasing order of precedence
    C(AWS_URL) or C(EC2_URL),
    C(AWS_ACCESS_KEY_ID) or C(AWS_ACCESS_KEY) or C(EC2_ACCESS_KEY),
    C(AWS_SECRET_ACCESS_KEY) or C(AWS_SECRET_KEY) or C(EC2_SECRET_KEY),
    C(AWS_SECURITY_TOKEN) or C(EC2_SECURITY_TOKEN),
    C(AWS_REGION) or C(EC2_REGION)
  - Ansible uses the boto configuration file (typically ~/.boto) if no
    credentials are provided. See https://boto.readthedocs.io/en/latest/boto_config_tut.html
  - C(AWS_REGION) or C(EC2_REGION) can be typically be used to specify the
    AWS region, when required, but this can also be configured in the boto config file
'''
