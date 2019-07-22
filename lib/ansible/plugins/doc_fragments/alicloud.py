# -*- coding: utf-8 -*-

# Copyright: (c) 2017 Alibaba Group Holding Limited. He Guimin <heguimin36@163.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Alicloud only documentation fragment
    DOCUMENTATION = r'''
options:
  alicloud_access_key:
    description:
    - Aliyun Cloud access key.
    - If not set then the value of environment variable C(ALICLOUD_ACCESS_KEY),
      C(ALICLOUD_ACCESS_KEY_ID) will be used instead.
    type: str
    aliases: [ access_key_id, access_key ]
  alicloud_secret_key:
    description:
    - Aliyun Cloud secret key.
    - If not set then the value of environment variable C(ALICLOUD_SECRET_KEY),
      C(ALICLOUD_SECRET_ACCESS_KEY) will be used instead.
    type: str
    aliases: [ secret_access_key, secret_key ]
  alicloud_region:
    description:
    - The Aliyun Cloud region to use.
    - If not specified then the value of environment variable
      C(ALICLOUD_REGION), C(ALICLOUD_REGION_ID) will be used instead.
    type: str
    aliases: [ region, region_id ]
  alicloud_security_token:
    description:
    - The Aliyun Cloud security token.
    - If not specified then the value of environment variable
      C(ALICLOUD_SECURITY_TOKEN) will be used instead.
    type: str
    aliases: [ security_token ]
author:
- He Guimin (@xiaozhu36)
requirements:
- python >= 2.6
extends_documentation_fragment:
- alicloud
notes:
  - If parameters are not set within the module, the following
    environment variables can be used in decreasing order of precedence
    C(ALICLOUD_ACCESS_KEY) or C(ALICLOUD_ACCESS_KEY_ID),
    C(ALICLOUD_SECRET_KEY) or C(ALICLOUD_SECRET_ACCESS_KEY),
    C(ALICLOUD_REGION) or C(ALICLOUD_REGION_ID),
    C(ALICLOUD_SECURITY_TOKEN)
  - C(ALICLOUD_REGION) or C(ALICLOUD_REGION_ID) can be typically be used to specify the
    ALICLOUD region, when required, but this can also be configured in the footmark config file
'''
