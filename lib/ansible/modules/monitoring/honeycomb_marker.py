#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2019 Will Thames <will@thames.id.au>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: honeycomb_marker
author: "Will Thames (@willthames)"
version_added: "2.10"
short_description: Send markers to honeycomb.io
description:
   - Send markers to honeycomb.io (see U(https://docs.honeycomb.io/working-with-your-data/customizing-your-query/markers/)
options:
  api_host:
    description: Honeycomb API endpoint
    default: https://api.honeycomb.com
    type: str
  write_key:
    description: Honeycomb write key
      - API token.
    required: true
    type: str
  dataset:
    description: Dataset to add the marker
    required: true
    type: str
  message:
    description:
      - Contents of the marker's message.
        It is recommended to have one or both of C(message) and C(type)
    type: str
  start_time:
    description: Time the marker starts
    type: int
  end_time:
    description: Time the marker ends
    type: int
  url:
    description: URL the marker represents
    type: str
  type:
    description:
      - Type of marker.
        It is recommended to have one or both of C(message) and C(type)
    type: str
'''

EXAMPLES = '''
- honeycomb_marker:
    write_key: AAAAAA
    message: build 192837
    type: deploy
'''

RETURN = '''
created_at:
  description: Time marker was created
  returned: always
  type: str
  sample: '2019-11-06T06:41:40Z'
end_time:
  description: End time of marker
  returned: when present in the marker
  type: int
  sample: 1573021871
id:
  description: ID of the marker
  returned: always
  type: str
  sample: 7fuXWCnrUDZ
message:
  description: Description of the marker
  returned: when present in the marker
  type: str
  sample: build 192837
start_time:
  description: Start time of marker
  returned: always
  type: int
  sample: 1573021812
type:
  description: Type of marker
  returned: when present in the marker
  type: str
  sample: deploy
updated_at:
  description: Time marker was updated (same as creation time here)
  returned: always
  type: str
  sample: '2019-11-06T06:41:40Z'
'''

import json
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url


# ===========================================
# Module execution.
#

def main():

    module = AnsibleModule(
        argument_spec=dict(
            api_host=dict(default="https://api.honeycomb.com"),
            write_key=dict(required=True, no_log=True),
            dataset=dict(required=True),
            start_time=dict(type='int'),
            end_time=dict(type='int'),
            url=dict(),
            message=dict(),
            type=dict()
        ),
        supports_check_mode=True
    )

    url = "%s/1/markers/%s" % (module.params['api_host'], module.params['dataset'])

    # If we're in check mode, just exit pretending like we succeeded
    if module.check_mode:
        module.exit_json(changed=True)

    try:
        data = dict()
        for key in ['start_time', 'end_time', 'url', 'message', 'type']:
            if module.params.get(key) is not None:
                data[key] = module.params[key]
        response, info = fetch_url(module, url, method="POST",
                                   headers={"X-Honeycomb-Team": module.params['write_key']},
                                   data=json.dumps(data))
    except Exception as e:
        module.fail_json(msg='Unable to notify Honeycomb: %s' % to_native(e),
                         exception=traceback.format_exc())

    if info['status'] < 0 or info['status'] >= 400:
        module.fail_json(**info)
    else:
        module.exit_json(**json.load(response))


if __name__ == '__main__':
    main()
