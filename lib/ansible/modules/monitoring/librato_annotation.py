#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (C) Seth Edwards, 2014
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: librato_annotation
short_description: create an annotation in librato
description:
    - Create an annotation event on the given annotation stream :name. If the annotation stream does not exist, it will be created automatically
version_added: "1.6"
author: "Seth Edwards (@sedward)"
requirements: []
options:
    user:
        description:
           - Librato account username
        required: true
    api_key:
        description:
           - Librato account api key
        required: true
    name:
        description:
            - The annotation stream name
            - If the annotation stream does not exist, it will be created automatically
        required: false
    title:
        description:
            - The title of an annotation is a string and may contain spaces
            - The title should be a short, high-level summary of the annotation e.g. v45 Deployment
        required: true
    source:
        description:
            - A string which describes the originating source of an annotation when that annotation is tracked across multiple members of a population
        required: false
    description:
        description:
            - The description contains extra meta-data about a particular annotation
            - The description should contain specifics on the individual annotation e.g. Deployed 9b562b2 shipped new feature foo!
        required: false
    start_time:
        description:
            - The unix timestamp indicating the time at which the event referenced by this annotation started
        required: false
    end_time:
        description:
            - The unix timestamp indicating the time at which the event referenced by this annotation ended
            - For events that have a duration, this is a useful way to annotate the duration of the event
        required: false
    links:
        description:
            - See examples
        required: true
'''

EXAMPLES = '''
# Create a simple annotation event with a source
- librato_annotation:
    user: user@example.com
    api_key: XXXXXXXXXXXXXXXXX
    title: App Config Change
    source: foo.bar
    description: This is a detailed description of the config change

# Create an annotation that includes a link
- librato_annotation:
    user: user@example.com
    api_key: XXXXXXXXXXXXXXXXXX
    name: code.deploy
    title: app code deploy
    description: this is a detailed description of a deployment
    links:
      - rel: example
        href: http://www.example.com/deploy

# Create an annotation with a start_time and end_time
- librato_annotation:
    user: user@example.com
    api_key: XXXXXXXXXXXXXXXXXX
    name: maintenance
    title: Maintenance window
    description: This is a detailed description of maintenance
    start_time: 1395940006
    end_time: 1395954406
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


def post_annotation(module):
    user = module.params['user']
    api_key = module.params['api_key']
    name = module.params['name']
    title = module.params['title']

    url = 'https://metrics-api.librato.com/v1/annotations/%s' % name
    params = {}
    params['title'] = title

    if module.params['source'] is not None:
        params['source'] = module.params['source']
    if module.params['description'] is not None:
        params['description'] = module.params['description']
    if module.params['start_time'] is not None:
        params['start_time'] = module.params['start_time']
    if module.params['end_time'] is not None:
        params['end_time'] = module.params['end_time']
    if module.params['links'] is not None:
        params['links'] = module.params['links']

    json_body = module.jsonify(params)

    headers = {}
    headers['Content-Type'] = 'application/json'

    # Hack send parameters the way fetch_url wants them
    module.params['url_username'] = user
    module.params['url_password'] = api_key
    response, info = fetch_url(module, url, data=json_body, headers=headers)
    if info['status'] != 200:
        module.fail_json(msg="Request Failed", reason=info.get('msg', ''), status_code=info['status'])
    response = response.read()
    module.exit_json(changed=True, annotation=response)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            user=dict(required=True),
            api_key=dict(required=True),
            name=dict(required=False),
            title=dict(required=True),
            source=dict(required=False),
            description=dict(required=False),
            start_time=dict(required=False, default=None, type='int'),
            end_time=dict(require=False, default=None, type='int'),
            links=dict(type='list')
        )
    )

    post_annotation(module)


if __name__ == '__main__':
    main()
