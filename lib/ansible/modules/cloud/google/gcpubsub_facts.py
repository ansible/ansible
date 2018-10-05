#!/usr/bin/python
# Copyright 2016 Google Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gcpubsub_facts
version_added: "2.3"
short_description: List Topics/Subscriptions and Messages from Google PubSub.
description:
    - List Topics/Subscriptions from Google PubSub.  Use the gcpubsub module for
      topic/subscription management.
      See U(https://cloud.google.com/pubsub/docs) for an overview.
requirements:
  - "python >= 2.6"
  - "google-auth >= 0.5.0"
  - "google-cloud-pubsub >= 0.22.0"
notes:
  - list state enables user to list topics or subscriptions in the project.  See examples for details.
author:
  - "Tom Melendez (@supertom) <tom@supertom.com>"
options:
  topic:
    description:
       - GCP pubsub topic name.  Only the name, not the full path, is required.
    required: False
  view:
    description:
       - Choices are 'topics' or 'subscriptions'
    required: True
  state:
    description:
       - list is the only valid option.
    required: False
'''

EXAMPLES = '''
## List all Topics in a project
- gcpubsub_facts:
    view: topics
    state: list

## List all Subscriptions in a project
- gcpubsub_facts:
    view: subscriptions
    state: list

## List all Subscriptions for a Topic in a project
- gcpubsub_facts:
    view: subscriptions
    topic: my-topic
    state: list
'''

RETURN = '''
subscriptions:
    description: List of subscriptions.
    returned: When view is set to subscriptions.
    type: list
    sample: ["mysubscription", "mysubscription2"]
topic:
    description: Name of topic. Used to filter subscriptions.
    returned: Always
    type: str
    sample: "mytopic"
topics:
    description: List of topics.
    returned: When view is set to topics.
    type: list
    sample: ["mytopic", "mytopic2"]
'''

try:
    from ast import literal_eval
    HAS_PYTHON26 = True
except ImportError:
    HAS_PYTHON26 = False

try:
    from google.cloud import pubsub
    HAS_GOOGLE_CLOUD_PUBSUB = True
except ImportError as e:
    HAS_GOOGLE_CLOUD_PUBSUB = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gcp import check_min_pkg_version, get_google_cloud_credentials


def list_func(data, member='name'):
    """Used for state=list."""
    return [getattr(x, member) for x in data]


def main():
    module = AnsibleModule(argument_spec=dict(
        view=dict(choices=['topics', 'subscriptions'], default='topics'),
        topic=dict(required=False),
        state=dict(choices=['list'], default='list'),
        service_account_email=dict(),
        credentials_file=dict(),
        project_id=dict(), ),)

    if not HAS_PYTHON26:
        module.fail_json(
            msg="GCE module requires python's 'ast' module, python v2.6+")

    if not HAS_GOOGLE_CLOUD_PUBSUB:
        module.fail_json(msg="Please install google-cloud-pubsub library.")

    CLIENT_MINIMUM_VERSION = '0.22.0'
    if not check_min_pkg_version('google-cloud-pubsub', CLIENT_MINIMUM_VERSION):
        module.fail_json(msg="Please install google-cloud-pubsub library version %s" % CLIENT_MINIMUM_VERSION)

    mod_params = {}
    mod_params['state'] = module.params.get('state')
    mod_params['topic'] = module.params.get('topic')
    mod_params['view'] = module.params.get('view')

    creds, params = get_google_cloud_credentials(module)
    pubsub_client = pubsub.Client(project=params['project_id'], credentials=creds, use_gax=False)
    pubsub_client.user_agent = 'ansible-pubsub-0.1'

    json_output = {}
    if mod_params['view'] == 'topics':
        json_output['topics'] = list_func(pubsub_client.list_topics())
    elif mod_params['view'] == 'subscriptions':
        if mod_params['topic']:
            t = pubsub_client.topic(mod_params['topic'])
            json_output['subscriptions'] = list_func(t.list_subscriptions())
        else:
            json_output['subscriptions'] = list_func(pubsub_client.list_subscriptions())

    json_output['changed'] = False
    json_output.update(mod_params)
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
