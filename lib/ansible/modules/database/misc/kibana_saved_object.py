#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2019, Ruben Tsirunyan @rubentsirunyan
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: kibana_saved_object
short_description: Manage Kibana saved objects
description:
    - This module can be used to Create/Update/Delete Kibana saved objects.
version_added: "2.8"
author: Ruben Tsirunyan (@rubentsirunyan)
options:
    id:
      type: str
      description:
        - ID of the object.
      required: True
    state:
      type: str
      description:
        - Desired state of the object.
      choices: ["present", "absent"]
      default: present
    kibana_url:
      type: str
      description:
        - The URL of Kibana.
    user:
      type: str
      description:
        - A username for the module to use for authentication.
    password:
      type: str
      description:
        - A password for the module to use for authentication.
    searchguard_tenant:
      type: str
      description:
        - Searchguard tenant to use.
    timeout:
      type: int
      description:
        - Request timeout. 
        - Should be provided in seconds.
      default: 30
    type:
      type: str
      description:
        - Type of the saved object.
      choices:
        - visualization
        - dashboard
        - search
        - index-pattern
        - config
        - timelion-sheet
    content:
      type: path
      description:
        - Path of the attributes file.
        - TODO: Change the name
    overwrite:
      type: bool
      description:
        - Overwrite the object.
      default: false
'''

EXAMPLES = '''
'''

RETURN = '''
'''

import os
import requests
import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def get_request_params(module, object_id, object_type, kibana_url, 
                       timeout, content={}, overwrite=False,
                       username=None, password=None, tenant=None, proxy=None):

    url = "{}/api/saved_objects/{}/{}".format(kibana_url, object_type, object_id)
    headers = {'kbn-xsrf': 'true'}
    auth = ()
    proxies = {}
    query_params = {}
    if any(item is not None for item in [username, password]):
        auth = (username, password)
    if tenant is not None:
        headers['sgtenant'] = tenant
    if proxy is not None:
        proxies['http'] = proxy
        proxies['https'] = proxy
    if overwrite:
        query_params['overwrite'] = True
    return {
        'url': url,
        'headers': headers,
        'auth': auth,
        'proxies': proxies,
        'query_params': query_params,
        'data': content
    }


def are_different(module, existing_object, object_id, object_type, content):
    object_json = existing_object.json()
    if object_json['id'] == object_id and object_json['type'] == object_type \
       and object_json.get('attributes') == content.get('attributes') \
       and object_json.get('references') == content.get('references'):
        return False
    else:
        return True


def get_object(module, object_id, object_type, kibana_url, timeout,
               username=None, password=None, tenant=None, proxy=None):
    
    request_params = get_request_params(
        module=module,
        object_id=object_id,
        object_type=object_type,
        kibana_url=kibana_url,
        username=username,
        password=password,
        tenant=tenant,
        proxy=proxy,
        timeout=timeout
    )
    try:
        return requests.get(request_params['url'],
                            auth=request_params['auth'],
                            headers=request_params['headers'],
                            proxies=request_params['proxies'])
    except Exception as e:
        module.fail_json(msg="An error occured while trying to get the object '{}'. {}".format(object_id, to_native(e)))


def create_object(module, object_id, object_type, kibana_url, content, timeout,
                  username=None, password=None, tenant=None, proxy=None,
                  overwrite=False):

    request_params = get_request_params(
        module=module,
        object_id=object_id,
        object_type=object_type,
        kibana_url=kibana_url,
        content=content,
        username=username,
        password=password,
        tenant=tenant,
        proxy=proxy,
        timeout=timeout,
        overwrite=overwrite
    )
    try:
        return requests.post(request_params['url'],
                            auth=request_params['auth'],
                            headers=request_params['headers'],
                            proxies=request_params['proxies'],
                            params=request_params['query_params'],
                            json=request_params['data'])

    except Exception as e:
        module.fail_json(msg="An error occured while trying to get the object '{}'. {}".format(object_id, to_native(e)))


def update_object(module, object_id, object_type, kibana_url, content, timeout,
                  username=None, password=None, tenant=None, proxy=None):

    request_params = get_request_params(
        module=module,
        object_id=object_id,
        object_type=object_type,
        kibana_url=kibana_url,
        content=content,
        username=username,
        password=password,
        tenant=tenant,
        proxy=proxy,
        timeout=timeout
    )
    try:
        return requests.put(request_params['url'],
                            auth=request_params['auth'],
                            headers=request_params['headers'],
                            proxies=request_params['proxies'],
                            params=request_params['query_params'],
                            json=request_params['data'])

    except Exception as e:
        module.fail_json(msg="An error occured while trying to get the object '{}'. {}".format(object_id, to_native(e)))


def delete_object(module, object_id, object_type, kibana_url, timeout, 
                  username=None, password=None, tenant=None, proxy=None):

    request_params = get_request_params(
        module=module,
        object_id=object_id,
        object_type=object_type,
        kibana_url=kibana_url,
        username=username,
        password=password,
        tenant=tenant,
        proxy=proxy,
        timeout=timeout,
    )
    try:
        return requests.delete(request_params['url'],
                               auth=request_params['auth'],
                               headers=request_params['headers'],
                               proxies=request_params['proxies'],
                               params=request_params['query_params'],
                               json=request_params['data'])

    except Exception as e:
        module.fail_json(msg="An error occured while trying to get the object '{}'. {}".format(object_id, to_native(e)))


def is_object_present(module, object_id, object_type, kibana_url, timeout,
                      username=None, password=None, tenant=None, proxy=None):
    r = get_object(
        module=module,
        object_id=object_id,
        object_type=object_type,
        kibana_url=kibana_url,
        username=username,
        password=password,
        tenant=tenant,
        proxy=proxy,
        timeout=timeout
    )

    if r.status_code == 404:
        return False, None
    elif r.status_code == 200:
        return True, r
    else:
        module.fail_json(msg="Got status other then 200 or 404")


def main():
    module = AnsibleModule(
        argument_spec=dict(
            id=dict(type='str'),
            type=dict(type='str', required=True,
                      choices=[
                          'visualization',
                          'dashboard',
                          'search',
                          'index-pattern',
                          'config',
                          'timelion-sheet'
                      ]),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            content=dict(type='dict', required=True),
            kibana_url=dict(type='str', required=True),
            timeout=dict(type='float', default="30"),
            overwrite=dict(type='bool', default=False),
            user=dict(type='str'),
            password=dict(type='str'),
            searchguard_tenant=dict(type='str'),
            proxy=dict(type='str')
        ),
        supports_check_mode=True,
    )

    object_id = module.params['id']
    object_type = module.params['type']
    state = module.params['state']
    content = module.params['content']
    kibana_url = module.params['kibana_url']
    timeout = module.params['timeout']
    overwrite = module.params['overwrite']
    user = module.params['user']
    password = module.params['password']
    searchguard_tenant = module.params['searchguard_tenant']
    proxy = module.params['proxy']

     
    present, existing_object = is_object_present(
        module=module,
        object_id=object_id,
        object_type=object_type,
        kibana_url=kibana_url,
        username=user,
        password=password,
        tenant=searchguard_tenant,
        proxy=proxy,
        timeout=timeout
    )

    if state == 'present':
        if present and not overwrite:
            if are_different(module=module,
                             existing_object=existing_object,
                             object_id=object_id,
                             object_type=object_type,
                             content=content):
                # Update object
                r = update_object(
                    module=module,
                    object_id=object_id,
                    object_type=object_type,
                    kibana_url=kibana_url,
                    content=content,
                    username=user,
                    password=password,
                    tenant=searchguard_tenant,
                    proxy=proxy,
                    timeout=timeout,
                )
                module.exit_json(changed=True, object_id=object_id, msg="Object has been updated: {}".format(object_id))
            else:
                module.exit_json(changed=False, object_id=object_id, msg="Object already exists: {}".format(object_id))
        if present and overwrite:
            # Overwrite object
            r = create_object(
                module=module,
                object_id=object_id,
                object_type=object_type,
                kibana_url=kibana_url,
                content=content,
                username=user,
                password=password,
                tenant=searchguard_tenant,
                proxy=proxy,
                timeout=timeout,
                overwrite=True
            )
            module.exit_json(changed=True, object_id=object_id, msg="Object has been overwritten: {}".format(object_id))
        if not present:
            # Create object
            r = create_object(
                module=module,
                object_id=object_id,
                object_type=object_type,
                kibana_url=kibana_url,
                content=content,
                username=user,
                password=password,
                tenant=searchguard_tenant,
                proxy=proxy,
                timeout=timeout
            )
            module.exit_json(changed=True, object_id=object_id, msg="Object has been created: {}".format(object_id))
    if state == 'absent':
        if not present:
            module.exit_json(changed=False, object_id=object_id, msg="object does not exist")
        if present:
            r = delete_object(
                module=module,
                object_id=object_id,
                object_type=object_type,
                kibana_url=kibana_url,
                username=user,
                password=password,
                tenant=searchguard_tenant,
                proxy=proxy,
                timeout=timeout
            )
            module.exit_json(changed=True, object_id=object_id, msg="Object has been deleted: {}".format(object_id))


if __name__ == '__main__':
    main()

