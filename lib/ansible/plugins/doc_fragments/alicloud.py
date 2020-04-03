# -*- coding: utf-8 -*-

# Copyright: (c) 2017-present Alibaba Group Holding Limited. He Guimin <heguimin36@163.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Alicloud only documentation fragment
    DOCUMENTATION = r'''
options:
  alicloud_access_key:
    description:
      - Alibaba Cloud access key. If not set then the value of environment variable C(ALICLOUD_ACCESS_KEY),
        C(ALICLOUD_ACCESS_KEY_ID) will be used instead.
    aliases: ['access_key_id', 'access_key']
    type: str
  alicloud_secret_key:
    description:
      - Alibaba Cloud secret key. If not set then the value of environment variable C(ALICLOUD_SECRET_KEY),
        C(ALICLOUD_SECRET_ACCESS_KEY) will be used instead.
    aliases: ['secret_access_key', 'secret_key']
    type: str
  alicloud_region:
    description:
      - The Alibaba Cloud region to use. If not specified then the value of environment variable
        C(ALICLOUD_REGION), C(ALICLOUD_REGION_ID) will be used instead.
    aliases: ['region', 'region_id']
    type: str
  alicloud_security_token:
    description:
      - The Alibaba Cloud security token. If not specified then the value of environment variable
        C(ALICLOUD_SECURITY_TOKEN) will be used instead.
    aliases: ['security_token']
    type: str
  alicloud_assume_role:
    description:
      - If provided with a role ARN, Ansible will attempt to assume this role using the supplied credentials.
      - The nested assume_role block supports I(alicloud_assume_role_arn), I(alicloud_assume_role_session_name), I(alicloud_assume_role_session_expiration) and I(alicloud_assume_role_policy)
    type: dict
    aliases: ['assume_role']
  alicloud_assume_role_arn:
    description:
      - The Alibaba Cloud role_arn. The ARN of the role to assume. If ARN is set to an empty string, 
        it does not perform role switching. It supports environment variable ALICLOUD_ASSUME_ROLE_ARN. 
        ansible will execute with provided credentials.
    aliases: ['assume_role_arn']
    type: str
  alicloud_assume_role_session_name:
    description:
      - The Alibaba Cloud session_name. The session name to use when assuming the role. If omitted, 
        'ansible' is passed to the AssumeRole call as session name. It supports environment variable 
        ALICLOUD_ASSUME_ROLE_SESSION_NAME
    aliases: ['assume_role_session_name']
    type: str
  alicloud_assume_role_session_expiration:
    description:
      - The Alibaba Cloud session_expiration. The time after which the established session for assuming 
        role expires. Valid value range 900-3600 seconds. Default to 3600 (in this case Alicloud use own default 
        value). It supports environment variable ALICLOUD_ASSUME_ROLE_SESSION_EXPIRATION
    aliases: ['assume_role_session_expiration']
    type: int
  ecs_role_name:
    description:
      - The RAM Role Name attached on a ECS instance for API operations. You can retrieve this from the 'Access Control' section of the Alibaba Cloud console.
        If you're running Ansible from an ECS instance with RAM Instance using RAM Role, Ansible will just access the metadata U(http://100.100.100.200/latest/meta-data/ram/security-credentials/<ecs_role_name>) to obtain the STS credential.
        This is a preferred approach over any other when running in ECS as you can avoid hard coding credentials. Instead these are leased on-the-fly by Ansible which reduces the chance of leakage.
    aliases: ['role_name'] 
    type: str
  profile:
    description:
      - This is the Alicloud profile name as set in the shared credentials file. It can also be sourced from the ALICLOUD_PROFILE environment variable.
    type: str
  shared_credentials_file:
    description:
      - This is the path to the shared credentials file. It can also be sourced from the ALICLOUD_SHARED_CREDENTIALS_FILE environment variable. 
        If this is not set and a profile is specified, ~/.aliyun/config.json will be used.
    type: str
author:
    - "He Guimin (@xiaozhu36)"
requirements:
    - "python >= 3.6"
extends_documentation_fragment:
    - alicloud
notes:
  - If parameters are not set within the module, the following
    environment variables can be used in decreasing order of precedence
    C(ALICLOUD_ACCESS_KEY) or C(ALICLOUD_ACCESS_KEY_ID),
    C(ALICLOUD_SECRET_KEY) or C(ALICLOUD_SECRET_ACCESS_KEY),
    C(ALICLOUD_REGION) or C(ALICLOUD_REGION_ID),
    C(ALICLOUD_SECURITY_TOKEN)
    C(ALICLOUD_ECS_ROLE_NAME)
    C(ALICLOUD_SHARED_CREDENTIALS_FILE)
    C(ALICLOUD_PROFILE)
    C(ALICLOUD_ASSUME_ROLE_ARN)
    C(ALICLOUD_ASSUME_ROLE_SESSION_NAME)
    C(ALICLOUD_ASSUME_ROLE_SESSION_EXPIRATION)
  - C(ALICLOUD_REGION) or C(ALICLOUD_REGION_ID) can be typically be used to specify the
    ALICLOUD region, when required, but this can also be configured in the footmark config file
    
'''