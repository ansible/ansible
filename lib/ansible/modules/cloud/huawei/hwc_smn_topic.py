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

from ansible.module_utils.hwc_utils import (Config, HwcClientException,
                                            HwcModule, navigate_value,
                                            are_different_dicts, is_empty_value,
                                            build_path, get_region)
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

    config = Config(module, "smn")

    state = module.params['state']

    if not module.params.get("id"):
        module.params['id'] = get_resource_id(config)

    fetch = None
    link = self_link(module)
    # the link will include Nones if required format parameters are missed
    if not re.search('/None/|/None$', link):
        client = config.client(get_region(module), "smn", "project")
        fetch = fetch_resource(module, client, link)
    changed = False

    if fetch:
        if state == 'present':
            expect = _get_resource_editable_properties(module)
            current_state = response_to_hash(module, fetch)
            current = {'display_name': current_state['display_name']}
            if are_different_dicts(expect, current):
                if not module.check_mode:
                    fetch = update(config)
                    fetch = response_to_hash(module, fetch)
                changed = True
            else:
                fetch = current_state
        else:
            if not module.check_mode:
                delete(config)
                fetch = {}
            changed = True
    else:
        if state == 'present':
            if not module.check_mode:
                fetch = create(config)
                fetch = response_to_hash(module, fetch)
            changed = True
        else:
            fetch = {}

    fetch.update({'changed': changed})

    module.exit_json(**fetch)


def create(config):
    module = config.module
    client = config.client(get_region(module), "smn", "project")

    link = "notifications/topics"
    r = None
    try:
        r = client.post(link, create_resource_opts(module))
    except HwcClientException as ex:
        msg = ("module(hwc_smn_topic): error creating "
               "resource, error: %s" % str(ex))
        module.fail_json(msg=msg)

    return get_resource(config, r)


def update(config):
    module = config.module
    client = config.client(get_region(module), "smn", "project")

    link = self_link(module)
    try:
        client.put(link, update_resource_opts(module))
    except HwcClientException as ex:
        msg = ("module(hwc_smn_topic): error updating "
               "resource, error: %s" % str(ex))
        module.fail_json(msg=msg)

    return fetch_resource(module, client, link)


def delete(config):
    module = config.module
    client = config.client(get_region(module), "smn", "project")

    link = self_link(module)
    try:
        client.delete(link)
    except HwcClientException as ex:
        msg = ("module(hwc_smn_topic): error deleting "
               "resource, error: %s" % str(ex))
        module.fail_json(msg=msg)


def fetch_resource(module, client, link):
    try:
        return client.get(link)
    except HwcClientException as ex:
        msg = ("module(hwc_smn_topic): error fetching "
               "resource, error: %s" % str(ex))
        module.fail_json(msg=msg)


def get_resource(config, result):
    module = config.module
    client = config.client(get_region(module), "smn", "project")

    v = ""
    try:
        v = navigate_value(result, ['topic_urn'])
    except Exception as ex:
        module.fail_json(msg=str(ex))

    d = {'topic_urn': v}
    url = build_path(module, 'notifications/topics/{topic_urn}', d)

    return fetch_resource(module, client, url)


def get_resource_id(config):
    module = config.module
    client = config.client(get_region(module), "smn", "project")

    link = "notifications/topics"
    query_link = "?offset={offset}&limit=10"
    link += query_link

    p = {'offset': 0}
    v = module.params.get('name')
    ids = set()
    while True:
        r = None
        try:
            r = client.get(link.format(**p))
        except Exception:
            pass
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


def self_link(module):
    return build_path(module, "notifications/topics/{id}")


def create_resource_opts(module):
    params = dict()

    v = module.params.get('display_name')
    if not is_empty_value(v):
        params["display_name"] = v

    v = module.params.get('name')
    if not is_empty_value(v):
        params["name"] = v

    return params


def update_resource_opts(module):
    params = dict()

    v = module.params.get('display_name')
    if not is_empty_value(v):
        params["display_name"] = v

    return params


def _get_resource_editable_properties(module):
    return {
        "display_name": module.params.get("display_name"),
    }


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
