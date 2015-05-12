#!/usr/bin/python

# (c) 2014-2015, Epic Games, Inc.

import requests
import time
import json

DOCUMENTATION = '''
---
module: circonus_annotation
short_description: create an annotation in circonus
description:
    - Create an annotation event with a given category, title and description. Optionally start, end or durations can be provided
author: Nick Harring
version_added: 2.0
requirements:
    - urllib3
    - requests
    - time
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
            - Unix timestamp of event start, defaults to now
        required: false
    stop:
        description:
            - Unix timestamp of event end, defaults to now + duration
        required: false
    duration:
        description:
            - Duration in seconds of annotation, defaults to 0
        required: false
'''
EXAMPLES = '''
# Create a simple annotation event with a source, defaults to start and end time of now
- circonus_annotation:
    api_key: XXXXXXXXXXXXXXXXX
    title: 'App Config Change'
    description: 'This is a detailed description of the config change'
    category: 'This category groups like annotations'
# Create an annotation with a duration of 5 minutes and a default start time of now
- circonus_annotation:
    api_key: XXXXXXXXXXXXXXXXX
    title: 'App Config Change'
    description: 'This is a detailed description of the config change'
    category: 'This category groups like annotations'
    duration: 300
# Create an annotation with a start_time and end_time
- circonus_annotation:
    api_key: XXXXXXXXXXXXXXXXX
    title: 'App Config Change'
    description: 'This is a detailed description of the config change'
    category: 'This category groups like annotations'
    start_time: 1395940006
    end_time: 1395954407
'''
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
    if module.params['duration'] != None:
        duration = module.params['duration']
    else:
        duration = 0
    if module.params['start'] != None:
        start = module.params['start']
    else:
        start = int(time.time())
    if module.params['stop'] != None:
        stop = module.params['stop']
    else:
        stop = int(time.time())+ duration
    annotation['start'] = int(start)
    annotation['stop'] = int(stop)
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
            start=dict(required=False, type='int'),
            stop=dict(required=False, type='int'),
            category=dict(required=True),
            title=dict(required=True),
            description=dict(required=True),
            duration=dict(required=False, type='int'),
            api_key=dict(required=True)
            )
        )
    annotation = create_annotation(module)
    try:
        resp = post_annotation(annotation, module.params['api_key'])
    except requests.exceptions.RequestException as e:
        module.fail_json(msg='Request Failed', reason=e)
    module.exit_json(changed=True, annotation=resp.json())

from ansible.module_utils.basic import AnsibleModule
main()
