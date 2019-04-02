#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Huawei
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

###############################################################################
# Documentation
###############################################################################

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ["preview"],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: hwc_smn_topic
description:
    - Represents a SMN notification topic resource.
short_description: Creates a resource of SMNTopic in Huaweicloud Cloud
version_added: '2.8'
author: Huawei Inc. (@huaweicloud)
requirements:
    - requests >= 2.18.4
    - keystoneauth1 >= 3.6.0
options:
    state:
        description:
            - Whether the given object should exist in Huaweicloud Cloud.
        type: str
        choices: ['present', 'absent']
        default: 'present'
    display_name:
        description:
            - Topic display name, which is presented as the name of the email
              sender in an email message. The topic display name contains a
              maximum of 192 bytes.
        type: str
        required: false
    name:
        description:
            - Name of the topic to be created. The topic name is a string of 1
              to 256 characters. It must contain upper- or lower-case letters,
              digits, hyphens (-), and underscores C(_), and must start with a
              letter or digit.
        type: str
        required: true
extends_documentation_fragment: hwc
'''

EXAMPLES = '''
- name: create a smn topic
  hwc_smn_topic:
      identity_endpoint: "{{ identity_endpoint }}"
      user_name: "{{ user_name }}"
      password: "{{ password }}"
      domain_name: "{{ domain_name }}"
      project_name: "{{ project_name }}"
      region: "{{ region }}"
      name: "ansible_smn_topic_test"
      state: present
'''

RETURN = '''
create_time:
    description:
        - Time when the topic was created.
    returned: success
    type: str
display_name:
    description:
        - Topic display name, which is presented as the name of the email
          sender in an email message. The topic display name contains a
          maximum of 192 bytes.
    returned: success
    type: str
name:
    description:
        - Name of the topic to be created. The topic name is a string of 1
          to 256 characters. It must contain upper- or lower-case letters,
          digits, hyphens (-), and underscores C(_), and must start with a
          letter or digit.
    returned: success
    type: str
push_policy:
    description:
        - Message pushing policy. 0 indicates that the message sending
          fails and the message is cached in the queue. 1 indicates that
          the failed message is discarded.
    returned: success
    type: int
topic_urn:
    description:
        - Resource identifier of a topic, which is unique.
    returned: success
    type: str
update_time:
    description:
        - Time when the topic was updated.
    returned: success
    type: str
'''

###############################################################################
# Imports
###############################################################################

from ansible.module_utils.hwc_utils import (HwcSession, HwcModule,
                                            DictComparison, navigate_hash,
                                            remove_nones_from_dict,
                                            remove_empty_from_dict,
                                            are_dicts_different)
import json
import re

###############################################################################
# Main
###############################################################################


def main():
    """Main function"""

    module = HwcModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'],
                       type='str'),
            display_name=dict(type='str'),
            name=dict(required=True, type='str')
        ),
        supports_check_mode=True,
    )

    session = HwcSession(module, "app")

    state = module.params['state']

    if not module.params.get("id"):
        module.params['id'] = get_resource_id(session)

    fetch = None
    link = self_link(session)
    # the link will include Nones if required format parameters are missed
    if not re.search('/None/|/None$', link):
        fetch = fetch_resource(session, link)
    changed = False

    if fetch:
        if state == 'present':
            expect = _get_resource_editable_properties(module)
            current_state = response_to_hash(module, fetch)
            if are_dicts_different(expect, current_state):
                if not module.check_mode:
                    fetch = update(session)
                    fetch = response_to_hash(module, fetch)
                changed = True
            else:
                fetch = current_state
        else:
            if not module.check_mode:
                delete(session)
                fetch = {}
            changed = True
    else:
        if state == 'present':
            if not module.check_mode:
                fetch = create(session)
                fetch = response_to_hash(module, fetch)
            changed = True
        else:
            fetch = {}

    fetch.update({'changed': changed})

    module.exit_json(**fetch)


def create(session):
    link = collection(session)
    module = session.module
    success_codes = [201, 202]
    r = return_if_object(module,
                         session.post(link, create_resource_opts(module)),
                         success_codes)

    return get_resource(session, r)


def update(session):
    link = self_link(session)
    success_codes = [201, 202]
    module = session.module
    r = return_if_object(module, session.put(link, update_resource_opts(module)), success_codes)

    return get_resource(session, r)


def delete(session):
    link = self_link(session)
    success_codes = [202, 204]
    return_if_object(session.module, session.delete(link), success_codes, False)


def link_wrapper(f):
    def _wrapper(module, *args, **kwargs):
        try:
            return f(module, *args, **kwargs)
        except KeyError as ex:
            module.fail_json(
                msg="Mapping keys(%s) are not found in generating link." % ex)

    return _wrapper


def return_if_object(module, response, success_codes, has_content=True):
    code = response.status_code

    # If not found, return nothing.
    if code == 404:
        return None

    if not success_codes:
        success_codes = [200, 201, 202, 203, 204, 205, 206, 207, 208, 226]
    # If no content, return nothing.
    if code in success_codes and not has_content:
        return None

    result = None
    try:
        result = response.json()
    except getattr(json.decoder, 'JSONDecodeError', ValueError) as inst:
        module.fail_json(msg="Invalid JSON response with error: %s" % inst)

    if code not in success_codes:
        msg = navigate_hash(result, ['message'])
        if msg:
            module.fail_json(msg=msg)
        else:
            module.fail_json(msg="operation failed, return code=%d" % code)

    return result


def fetch_resource(session, link, success_codes=None):
    if not success_codes:
        success_codes = [200]
    return return_if_object(session.module, session.get(link), success_codes)


def get_resource(session, result):
    combined = session.module.params.copy()
    combined['topic_urn'] = navigate_hash(result, ['topic_urn'])
    url = 'notifications/topics/{topic_urn}'.format(**combined)

    e = session.get_service_endpoint('compute')
    url = e.replace("ecs", "smn") + url
    return fetch_resource(session, url)


def get_resource_id(session):
    module = session.module
    link = list_link(session, {'limit': 10, 'offset': '{offset}'})
    p = {'offset': 0}
    v = module.params.get('name')
    ids = set()
    while True:
        r = fetch_resource(session, link.format(**p))
        if r is None:
            break
        r = r.get('topics', [])
        if r == []:
            break
        for i in r:
            if i.get('name') == v:
                ids.add(i.get('topic_urn'))
        if len(ids) >= 2:
            module.fail_json(msg="Multiple resources are found")

        p['offset'] += 1

    return ids.pop() if ids else None


@link_wrapper
def list_link(session, extra_data=None):
    url = "{endpoint}notifications/topics?limit={limit}&offset={offset}"

    combined = session.module.params.copy()
    if extra_data:
        combined.update(extra_data)

    e = session.get_service_endpoint('compute')
    combined['endpoint'] = e.replace("ecs", "smn")

    return url.format(**combined)


@link_wrapper
def self_link(session):
    url = "{endpoint}notifications/topics/{id}"

    combined = session.module.params.copy()

    e = session.get_service_endpoint('compute')
    combined['endpoint'] = e.replace("ecs", "smn")

    return url.format(**combined)


@link_wrapper
def collection(session):
    url = "{endpoint}notifications/topics"

    combined = session.module.params.copy()

    e = session.get_service_endpoint('compute')
    combined['endpoint'] = e.replace("ecs", "smn")

    return url.format(**combined)


def create_resource_opts(module):
    request = remove_empty_from_dict({
        u'display_name': module.params.get('display_name'),
        u'name': module.params.get('name')
    })
    return request


def update_resource_opts(module):
    request = remove_nones_from_dict({
        u'display_name': module.params.get('display_name')
    })
    return request


def _get_resource_editable_properties(module):
    return remove_nones_from_dict({
        "display_name": module.params.get("display_name"),
    })


def response_to_hash(module, response):
    """Remove unnecessary properties from the response.
       This is for doing comparisons with Ansible's current parameters.
    """
    return {
        u'create_time': response.get(u'create_time'),
        u'display_name': response.get(u'display_name'),
        u'name': response.get(u'name'),
        u'push_policy': _push_policy_convert_from_response(
            response.get('push_policy')),
        u'topic_urn': response.get(u'topic_urn'),
        u'update_time': response.get(u'update_time')
    }


def _push_policy_convert_from_response(value):
    return {
        0: "the message sending fails and is cached in the queue",
        1: "the failed message is discarded",
    }.get(int(value))


if __name__ == '__main__':
    main()
