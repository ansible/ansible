# (c) 2014, Will Thames <will@thames.id.au>
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


class ModuleDocFragment(object):

    # AWS only documentation fragment
    DOCUMENTATION = """
options:
  ec2_url:
    description:
      - Url to use to connect to EC2 or your Eucalyptus cloud (by default the module will use EC2 endpoints).
        Ignored for modules where region is required. Must be specified for all other modules if region is not used.
        If not set then the value of the EC2_URL environment variable, if any, is used.
  aws_secret_key:
    description:
      - AWS secret key. If not set then the value of the AWS_SECRET_ACCESS_KEY, AWS_SECRET_KEY, or EC2_SECRET_KEY environment variable is used.
    aliases: [ 'ec2_secret_key', 'secret_key' ]
  aws_access_key:
    description:
      - AWS access key. If not set then the value of the AWS_ACCESS_KEY_ID, AWS_ACCESS_KEY or EC2_ACCESS_KEY environment variable is used.
    aliases: [ 'ec2_access_key', 'access_key' ]
  security_token:
    description:
      - AWS STS security token. If not set then the value of the AWS_SECURITY_TOKEN or EC2_SECURITY_TOKEN environment variable is used.
    aliases: [ 'access_token' ]
    version_added: "1.6"
  validate_certs:
    description:
      - When set to "no", SSL certificates will not be validated for boto versions >= 2.6.0.
    type: bool
    default: 'yes'
    version_added: "1.5"
  profile:
    description:
      - Uses a boto profile. Only works with boto >= 2.24.0.
    version_added: "1.6"
requirements:
  - "python >= 2.6"
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
"""
