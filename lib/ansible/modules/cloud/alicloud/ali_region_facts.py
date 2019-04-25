#!/usr/bin/python
# -*- coding:utf-8 -*-

# Copyright (c) 2019 Red Hat, Inc
# Author: Alexander Todorov <atodorov@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'supported_by': 'community',
    'status': ['preview']
}

DOCUMENTATION = '''
module: ali_region_facts
short_description: Gather facts about Alibaba Cloud regions.
description:
    - Gather facts about Alibaba Cloud regions.
version_added: '2.8'
author: 'Alexander Todorov (@atodorov)'
options:
  None
extends_documentation_fragment:
    - alicloud
requirements:
    - "python >= 2.6"
    - "footmark >= 1.1.16"
'''

EXAMPLES = '''
# Gather facts about all regions
- ali_region_facts:
'''

RETURN = '''
regions:
    returned: on success
    description: >
        All supported regions. Each element consists of a dict with all the information related
        to that region.
    type: list
    sample: "[{
        {
            "LocalName": "英国 (伦敦)",
            "RegionEndpoint": "ecs.eu-west-1.aliyuncs.com",
            "RegionId": "eu-west-1"
        },
    }]"
'''

import json
import traceback

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.alicloud_ecs import acs_common_argument_spec

HAS_FOOTMARK = False
FOOTMARK_IMP_ERR = None
try:
    from footmark.exception import ECSResponseError
    from aliyunsdkcore.client import AcsClient
    from aliyunsdkecs.request.v20140526.DescribeRegionsRequest import DescribeRegionsRequest

    HAS_FOOTMARK = True
except ImportError:
    FOOTMARK_IMP_ERR = traceback.format_exc()
    HAS_FOOTMARK = False


def main():
    argument_spec = acs_common_argument_spec()
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_FOOTMARK:
        module.fail_json(msg=missing_required_lib('footmark'), exception=FOOTMARK_IMP_ERR)

    try:
        client = AcsClient(module.params['alicloud_access_key'], module.params['alicloud_secret_key'])
        request = DescribeRegionsRequest()
        response = client.do_action_with_exception(request)
        regions = json.loads(response)
    except Exception as e:
        module.fail_json(msg="Unable to describe regions: {0}".format(to_native(e)),
                         exception=traceback.format_exc())

    module.exit_json(regions=[r for r in regions['Regions']['Region']])


if __name__ == '__main__':
    main()
