#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Google
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# ----------------------------------------------------------------------------
#
#     ***     AUTO GENERATED CODE    ***    AUTO GENERATED CODE     ***
#
# ----------------------------------------------------------------------------
#
#     This file is automatically generated by Magic Modules and manual
#     changes will be clobbered when the file is regenerated.
#
#     Please read more about how to change this file at
#     https://www.github.com/GoogleCloudPlatform/magic-modules
#
# ----------------------------------------------------------------------------

from __future__ import absolute_import, division, print_function

__metaclass__ = type

################################################################################
# Documentation
################################################################################

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ["preview"], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: gcp_pubsub_subscription
description:
- A named resource representing the stream of messages from a single, specific topic,
  to be delivered to the subscribing application.
short_description: Creates a GCP Subscription
version_added: 2.6
author: Google Inc. (@googlecloudplatform)
requirements:
- python >= 2.6
- requests >= 2.18.4
- google-auth >= 1.3.0
options:
  state:
    description:
    - Whether the given object should exist in GCP
    choices:
    - present
    - absent
    default: present
  name:
    description:
    - Name of the subscription.
    required: false
  topic:
    description:
    - A reference to a Topic resource.
    - 'This field represents a link to a Topic resource in GCP. It can be specified
      in two ways. First, you can place in the name of the resource here as a string
      Alternatively, you can add `register: name-of-resource` to a gcp_pubsub_topic
      task and then set this topic field to "{{ name-of-resource }}"'
    required: false
  push_config:
    description:
    - If push delivery is used with this subscription, this field is used to configure
      it. An empty pushConfig signifies that the subscriber will pull and ack messages
      using API methods.
    required: false
    suboptions:
      push_endpoint:
        description:
        - A URL locating the endpoint to which messages should be pushed.
        - For example, a Webhook endpoint might use "U(https://example.com/push".)
        required: false
  ack_deadline_seconds:
    description:
    - This value is the maximum time after a subscriber receives a message before
      the subscriber should acknowledge the message. After message delivery but before
      the ack deadline expires and before the message is acknowledged, it is an outstanding
      message and will not be delivered again during that time (on a best-effort basis).
    - For pull subscriptions, this value is used as the initial value for the ack
      deadline. To override this value for a given message, call subscriptions.modifyAckDeadline
      with the corresponding ackId if using pull. The minimum custom deadline you
      can specify is 10 seconds. The maximum custom deadline you can specify is 600
      seconds (10 minutes).
    - If this parameter is 0, a default value of 10 seconds is used.
    - For push delivery, this value is also used to set the request timeout for the
      call to the push endpoint.
    - If the subscriber never acknowledges the message, the Pub/Sub system will eventually
      redeliver the message.
    required: false
extends_documentation_fragment: gcp
'''

EXAMPLES = '''
- name: create a topic
  gcp_pubsub_topic:
      name: "topic-subscription"
      project: "{{ gcp_project }}"
      auth_kind: "{{ gcp_cred_kind }}"
      service_account_file: "{{ gcp_cred_file }}"
      state: present
  register: topic

- name: create a subscription
  gcp_pubsub_subscription:
      name: "test_object"
      topic: "{{ topic }}"
      ack_deadline_seconds: 300
      project: "test_project"
      auth_kind: "serviceaccount"
      service_account_file: "/tmp/auth.pem"
      state: present
'''

RETURN = '''
name:
  description:
  - Name of the subscription.
  returned: success
  type: str
topic:
  description:
  - A reference to a Topic resource.
  returned: success
  type: str
pushConfig:
  description:
  - If push delivery is used with this subscription, this field is used to configure
    it. An empty pushConfig signifies that the subscriber will pull and ack messages
    using API methods.
  returned: success
  type: complex
  contains:
    pushEndpoint:
      description:
      - A URL locating the endpoint to which messages should be pushed.
      - For example, a Webhook endpoint might use "U(https://example.com/push".)
      returned: success
      type: str
ackDeadlineSeconds:
  description:
  - This value is the maximum time after a subscriber receives a message before the
    subscriber should acknowledge the message. After message delivery but before the
    ack deadline expires and before the message is acknowledged, it is an outstanding
    message and will not be delivered again during that time (on a best-effort basis).
  - For pull subscriptions, this value is used as the initial value for the ack deadline.
    To override this value for a given message, call subscriptions.modifyAckDeadline
    with the corresponding ackId if using pull. The minimum custom deadline you can
    specify is 10 seconds. The maximum custom deadline you can specify is 600 seconds
    (10 minutes).
  - If this parameter is 0, a default value of 10 seconds is used.
  - For push delivery, this value is also used to set the request timeout for the
    call to the push endpoint.
  - If the subscriber never acknowledges the message, the Pub/Sub system will eventually
    redeliver the message.
  returned: success
  type: int
'''

################################################################################
# Imports
################################################################################

from ansible.module_utils.gcp_utils import navigate_hash, GcpSession, GcpModule, GcpRequest, remove_nones_from_dict, replace_resource_dict
import json

################################################################################
# Main
################################################################################


def main():
    """Main function"""

    module = GcpModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            name=dict(type='str'),
            topic=dict(),
            push_config=dict(type='dict', options=dict(push_endpoint=dict(type='str'))),
            ack_deadline_seconds=dict(type='int'),
        )
    )

    if not module.params['scopes']:
        module.params['scopes'] = ['https://www.googleapis.com/auth/pubsub']

    state = module.params['state']

    fetch = fetch_resource(module, self_link(module))
    changed = False

    if fetch:
        if state == 'present':
            if is_different(module, fetch):
                update(module, self_link(module))
                fetch = fetch_resource(module, self_link(module))
                changed = True
        else:
            delete(module, self_link(module))
            fetch = {}
            changed = True
    else:
        if state == 'present':
            fetch = create(module, self_link(module))
            changed = True
        else:
            fetch = {}

    fetch.update({'changed': changed})

    module.exit_json(**fetch)


def create(module, link):
    auth = GcpSession(module, 'pubsub')
    return return_if_object(module, auth.put(link, resource_to_request(module)))


def update(module, link):
    module.fail_json(msg="Subscription cannot be edited")


def delete(module, link):
    auth = GcpSession(module, 'pubsub')
    return return_if_object(module, auth.delete(link))


def resource_to_request(module):
    request = {
        u'name': module.params.get('name'),
        u'topic': replace_resource_dict(module.params.get(u'topic', {}), 'name'),
        u'pushConfig': SubscriptionPushconfig(module.params.get('push_config', {}), module).to_request(),
        u'ackDeadlineSeconds': module.params.get('ack_deadline_seconds'),
    }
    request = encode_request(request, module)
    return_vals = {}
    for k, v in request.items():
        if v or v is False:
            return_vals[k] = v

    return return_vals


def fetch_resource(module, link, allow_not_found=True):
    auth = GcpSession(module, 'pubsub')
    return return_if_object(module, auth.get(link), allow_not_found)


def self_link(module):
    return "https://pubsub.googleapis.com/v1/projects/{project}/subscriptions/{name}".format(**module.params)


def collection(module):
    return "https://pubsub.googleapis.com/v1/projects/{project}/subscriptions".format(**module.params)


def return_if_object(module, response, allow_not_found=False):
    # If not found, return nothing.
    if allow_not_found and response.status_code == 404:
        return None

    # If no content, return nothing.
    if response.status_code == 204:
        return None

    try:
        module.raise_for_status(response)
        result = response.json()
    except getattr(json.decoder, 'JSONDecodeError', ValueError):
        module.fail_json(msg="Invalid JSON response with error: %s" % response.text)

    result = decode_request(result, module)

    if navigate_hash(result, ['error', 'errors']):
        module.fail_json(msg=navigate_hash(result, ['error', 'errors']))

    return result


def is_different(module, response):
    request = resource_to_request(module)
    response = response_to_hash(module, response)
    request = decode_request(request, module)

    # Remove all output-only from response.
    response_vals = {}
    for k, v in response.items():
        if k in request:
            response_vals[k] = v

    request_vals = {}
    for k, v in request.items():
        if k in response:
            request_vals[k] = v

    return GcpRequest(request_vals) != GcpRequest(response_vals)


# Remove unnecessary properties from the response.
# This is for doing comparisons with Ansible's current parameters.
def response_to_hash(module, response):
    return {
        u'name': response.get(u'name'),
        u'topic': response.get(u'topic'),
        u'pushConfig': SubscriptionPushconfig(response.get(u'pushConfig', {}), module).from_response(),
        u'ackDeadlineSeconds': response.get(u'ackDeadlineSeconds'),
    }


def decode_request(response, module):
    if 'name' in response:
        response['name'] = response['name'].split('/')[-1]

    if 'topic' in response:
        response['topic'] = response['topic'].split('/')[-1]

    return response


def encode_request(request, module):
    request['topic'] = '/'.join(['projects', module.params['project'], 'topics', request['topic']])
    request['name'] = '/'.join(['projects', module.params['project'], 'subscriptions', module.params['name']])

    return request


class SubscriptionPushconfig(object):
    def __init__(self, request, module):
        self.module = module
        if request:
            self.request = request
        else:
            self.request = {}

    def to_request(self):
        return remove_nones_from_dict({u'pushEndpoint': self.request.get('push_endpoint')})

    def from_response(self):
        return remove_nones_from_dict({u'pushEndpoint': self.request.get(u'pushEndpoint')})


if __name__ == '__main__':
    main()
