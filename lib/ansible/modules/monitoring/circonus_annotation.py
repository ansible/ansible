#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2014-2015, Epic Games, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: circonus_annotation
short_description: create an annotation in circonus
description:
    - Create an annotation event with a given category, title and description. Optionally start, end or durations can be provided
author: "Nick Harring (@NickatEpic)"
version_added: 2.0
requirements:
    - requests (either >= 2.0.0 for Python 3, or >= 1.0.0 for Python 2)
notes:
    - Check mode isn't supported.
options:
    api_key:
        description:
           - Circonus API key
        required: true
    category:
        description:
           - Annotation Category
        required: true
    description:
        description:
            - Description of annotation
        required: true
    title:
        description:
            - Title of annotation
        required: true
    start:
        description:
            - Unix timestamp of event start
        default: I(now)
    stop:
        description:
            - Unix timestamp of event end
        default: I(now) + I(duration)
    duration:
        description:
            - Duration in seconds of annotation
        default: 0
'''
EXAMPLES = '''
# Create a simple annotation event with a source, defaults to start and end time of now
- circonus_annotation:
    api_key: XXXXXXXXXXXXXXXXX
    title: App Config Change
    description: This is a detailed description of the config change
    category: This category groups like annotations
# Create an annotation with a duration of 5 minutes and a default start time of now
- circonus_annotation:
    api_key: XXXXXXXXXXXXXXXXX
    title: App Config Change
    description: This is a detailed description of the config change
    category: This category groups like annotations
    duration: 300
# Create an annotation with a start_time and end_time
- circonus_annotation:
    api_key: XXXXXXXXXXXXXXXXX
    title: App Config Change
    description: This is a detailed description of the config change
    category: This category groups like annotations
    start_time: 1395940006
    end_time: 1395954407
'''

RETURN = '''
annotation:
    description: details about the created annotation
    returned: success
    type: complex
    contains:
        _cid:
            description: annotation identifier
            returned: success
            type: string
            sample: /annotation/100000
        _created:
            description: creation timestamp
            returned: success
            type: int
            sample: 1502236928
        _last_modified:
            description: last modification timestamp
            returned: success
            type: int
            sample: 1502236928
        _last_modified_by:
            description: last modified by
            returned: success
            type: string
            sample: /user/1000
        category:
            description: category of the created annotation
            returned: success
            type: string
            sample: alerts
        title:
            description: title of the created annotation
            returned: success
            type: string
            sample: WARNING
        description:
            description: description of the created annotation
            returned: success
            type: string
            sample: Host is down.
        start:
            description: timestamp, since annotation applies
            returned: success
            type: int
            sample: Host is down.
        stop:
            description: timestamp, since annotation ends
            returned: success
            type: string
            sample: Host is down.
        rel_metrics:
            description: Array of metrics related to this annotation, each metrics is a string.
            returned: success
            type: list
            sample:
                - 54321_kbps
'''
import json
import time
import traceback
from distutils.version import LooseVersion

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import PY3
from ansible.module_utils._text import to_native


def check_requests_dep(module):
    """Check if an adequate requests version is available"""
    if not HAS_REQUESTS:
        module.fail_json(msg='requests is required for this module')
    else:
        required_version = '2.0.0' if PY3 else '1.0.0'
        if LooseVersion(requests.__version__) < LooseVersion(required_version):
            module.fail_json(msg="'requests' library version should be >= %s, found: %s." % (required_version, requests.__version__))


def post_annotation(annotation, api_key):
    ''' Takes annotation dict and api_key string'''
    base_url = 'https://api.circonus.com/v2'
    anootate_post_endpoint = '/annotation'
    resp = requests.post(base_url + anootate_post_endpoint,
                         headers=build_headers(api_key), data=json.dumps(annotation))
    resp.raise_for_status()
    return resp


def create_annotation(module):
    ''' Takes ansible module object '''
    annotation = {}
    duration = module.params['duration']
    if module.params['start'] is not None:
        start = module.params['start']
    else:
        start = int(time.time())
    if module.params['stop'] is not None:
        stop = module.params['stop']
    else:
        stop = int(time.time()) + duration
    annotation['start'] = start
    annotation['stop'] = stop
    annotation['category'] = module.params['category']
    annotation['description'] = module.params['description']
    annotation['title'] = module.params['title']
    return annotation


def build_headers(api_token):
    '''Takes api token, returns headers with it included.'''
    headers = {'X-Circonus-App-Name': 'ansible',
               'Host': 'api.circonus.com', 'X-Circonus-Auth-Token': api_token,
               'Accept': 'application/json'}
    return headers


def main():
    '''Main function, dispatches logic'''
    module = AnsibleModule(
        argument_spec=dict(
            start=dict(type='int'),
            stop=dict(type='int'),
            category=dict(required=True),
            title=dict(required=True),
            description=dict(required=True),
            duration=dict(default=0, type='int'),
            api_key=dict(required=True, no_log=True)
        )
    )

    check_requests_dep(module)

    annotation = create_annotation(module)
    try:
        resp = post_annotation(annotation, module.params['api_key'])
    except requests.exceptions.RequestException as e:
        module.fail_json(msg='Request Failed', reason=to_native(e), exception=traceback.format_exc())
    module.exit_json(changed=True, annotation=resp.json())


if __name__ == '__main__':
    main()
