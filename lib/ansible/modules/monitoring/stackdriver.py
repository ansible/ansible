#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''

module: stackdriver
short_description: Send code deploy and annotation events to stackdriver
description:
  - Send code deploy and annotation events to Stackdriver
version_added: "1.6"
author: "Ben Whaley (@bwhaley)"
options:
  key:
    description:
      - API key.
    required: true
    default: null
  event:
    description:
      - The type of event to send, either annotation or deploy
    choices: ['annotation', 'deploy']
    required: false
    default: null
  revision_id:
    description:
      - The revision of the code that was deployed. Required for deploy events
    required: false
    default: null
  deployed_by:
    description:
      - The person or robot responsible for deploying the code
    required: false
    default: "Ansible"
  deployed_to:
    description:
      - "The environment code was deployed to. (ie: development, staging, production)"
    required: false
    default: null
  repository:
    description:
      - The repository (or project) deployed
    required: false
    default: null
  msg:
    description:
      - The contents of the annotation message, in plain text.  Limited to 256 characters. Required for annotation.
    required: false
    default: null
  annotated_by:
    description:
      - The person or robot who the annotation should be attributed to.
    required: false
    default: "Ansible"
  level:
    description:
      - one of INFO/WARN/ERROR, defaults to INFO if not supplied.  May affect display.
    choices: ['INFO', 'WARN', 'ERROR']
    required: false
    default: 'INFO'
  instance_id:
    description:
      - id of an EC2 instance that this event should be attached to, which will limit the contexts where this event is shown
    required: false
    default: null
  event_epoch:
    description:
      - "Unix timestamp of where the event should appear in the timeline, defaults to now. Be careful with this."
    required: false
    default: null
'''

EXAMPLES = '''
- stackdriver:
    key: AAAAAA
    event: deploy
    deployed_to: production
    deployed_by: leeroyjenkins
    repository: MyWebApp
    revision_id: abcd123

- stackdriver:
    key: AAAAAA
    event: annotation
    msg: Greetings from Ansible
    annotated_by: leeroyjenkins
    level: WARN
    instance_id: i-abcd1234
'''

# ===========================================
# Stackdriver module specific support methods.
#

import json
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url


def send_deploy_event(module, key, revision_id, deployed_by='Ansible', deployed_to=None, repository=None):
    """Send a deploy event to Stackdriver"""
    deploy_api = "https://event-gateway.stackdriver.com/v1/deployevent"

    params = {}
    params['revision_id'] = revision_id
    params['deployed_by'] = deployed_by
    if deployed_to:
        params['deployed_to'] = deployed_to
    if repository:
        params['repository'] = repository

    return do_send_request(module, deploy_api, params, key)


def send_annotation_event(module, key, msg, annotated_by='Ansible', level=None, instance_id=None, event_epoch=None):
    """Send an annotation event to Stackdriver"""
    annotation_api = "https://event-gateway.stackdriver.com/v1/annotationevent"

    params = {}
    params['message'] = msg
    if annotated_by:
        params['annotated_by'] = annotated_by
    if level:
        params['level'] = level
    if instance_id:
        params['instance_id'] = instance_id
    if event_epoch:
        params['event_epoch'] = event_epoch

    return do_send_request(module, annotation_api, params, key)


def do_send_request(module, url, params, key):
    data = json.dumps(params)
    headers = {
        'Content-Type': 'application/json',
        'x-stackdriver-apikey': key
    }
    response, info = fetch_url(module, url, headers=headers, data=data, method='POST')
    if info['status'] != 200:
        module.fail_json(msg="Unable to send msg: %s" % info['msg'])


# ===========================================
# Module execution.
#

def main():

    module = AnsibleModule(
        argument_spec=dict(
            key=dict(required=True),
            event=dict(required=True, choices=['deploy', 'annotation']),
            msg=dict(),
            revision_id=dict(),
            annotated_by=dict(default='Ansible'),
            level=dict(default='INFO', choices=['INFO', 'WARN', 'ERROR']),
            instance_id=dict(),
            event_epoch=dict(),
            deployed_by=dict(default='Ansible'),
            deployed_to=dict(),
            repository=dict(),
        ),
        supports_check_mode=True
    )

    key = module.params["key"]
    event = module.params["event"]

    # Annotation params
    msg = module.params["msg"]
    annotated_by = module.params["annotated_by"]
    level = module.params["level"]
    instance_id = module.params["instance_id"]
    event_epoch = module.params["event_epoch"]

    # Deploy params
    revision_id = module.params["revision_id"]
    deployed_by = module.params["deployed_by"]
    deployed_to = module.params["deployed_to"]
    repository = module.params["repository"]

    ##################################################################
    # deploy requires revision_id
    # annotation requires msg
    # We verify these manually
    ##################################################################

    if event == 'deploy':
        if not revision_id:
            module.fail_json(msg="revision_id required for deploy events")
        try:
            send_deploy_event(module, key, revision_id, deployed_by, deployed_to, repository)
        except Exception as e:
            module.fail_json(msg="unable to sent deploy event: %s" % to_native(e),
                             exception=traceback.format_exc())

    if event == 'annotation':
        if not msg:
            module.fail_json(msg="msg required for annotation events")
        try:
            send_annotation_event(module, key, msg, annotated_by, level, instance_id, event_epoch)
        except Exception as e:
            module.fail_json(msg="unable to sent annotation event: %s" % to_native(e),
                             exception=traceback.format_exc())

    changed = True
    module.exit_json(changed=changed, deployed_by=deployed_by)


if __name__ == '__main__':
    main()
