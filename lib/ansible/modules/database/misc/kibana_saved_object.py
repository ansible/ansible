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
        - A username for the module to use for Digest, Basic or WSSE authentication.
      aliases: [url_username]
    password:
      type: str
      description:
        - A password for the module to use for Digest, Basic or WSSE authentication.
      aliases: [url_password]
    force_basic_auth:
      type: bool
      description:
        - The library used by the module only sends authentication information when a webservice
          responds to an initial request with a 401 status. Since some basic auth services do not properly
          send a 401, logins will fail. This option forces the sending of the Basic authentication header
          upon initial request.
      default: false
    use_proxy:
      type: bool
      description:
        - if C(false), it will not use a proxy, even if one is defined in
          an environment variable on the target hosts.
      default: true
    validate_certs:
      description:
        - If C(false), SSL certificates will not be validated.  This should only
          set to C(false) used on personally controlled sites using self-signed
          certificates.
      type: bool
      default: 'true'
    client_cert:
      description:
        - PEM formatted certificate chain file to be used for SSL client
          authentication. This file can also include the key as well, and if
          the key is included, I(client_key) is not required
    client_key:
      description:
        - PEM formatted file that contains your private key to be used for SSL
          client authentication. If I(client_cert) contains both the certificate
          and key, this option is not required.
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
      type: dict
      description:
        - Body of the object.
        - Should contain "attributes" dictionary.
        - JSON file can be used like '{{ lookup("template", "content.json.j2") }}'
        - See L(Kibana saved object API documentation) for details.
    overwrite:
      type: bool
      description:
        - Overwrite the object.
      default: false
'''

EXAMPLES = '''
- name: Create an index pattern
  kibana_saved_object:
    id: my-pattern
    state: present
    type: index-pattern
    kibana_url: http://192.168.0.42:5601/
    content:
      attributes:
        title: my-pattern-*

- name: Create an index pattern with searchguard enabled
  kibana_saved_object:
    id: my-pattern
    state: present
    type: index-pattern
    kibana_url: http://192.168.0.42:5601/
    content:
      attributes:
        title: my-pattern-*
    user: ansible
    password: s3cr3t
    force_basic_auth: true
    searchguard_tenant: my_application

- name: Create an index pattern using a jinja template
  kibana_saved_object:
    id: my-pattern
    state: present
    type: index-pattern
    kibana_url: http://192.168.0.42:5601/
    content: '{{ lookup("template", "content.json.j2") }}'
    searchguard_tenant: my_application
'''

RETURN = '''
msg:
  description: The result of the operation
  returned: always
  type: str
  sample: 'Object has been created: my-pattern'
object_id:
  description: ID of the saved object
  returned: always
  type: str
  sample: 'my-pattern'
object_type:
  description: ID of the saved object
  returned: always
  type: str
  sample: 'index-pattern'
'''


import os
import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url, url_argument_spec


def get_request_params(object_id, object_type, kibana_url,
                       content=None, overwrite=False, tenant=None):

    url = "{0}/api/saved_objects/{1}/{2}".format(kibana_url, object_type, object_id)
    headers = {'kbn-xsrf': 'true'}
    data = ''
    if content is not None:
        data = json.dumps(content)
        headers['Content-Type'] = 'application/json'
    if tenant is not None:
        headers['sgtenant'] = tenant
    if overwrite:
        url += '?overwrite=true'
    return url, headers, data


def are_different(module, existing_object, object_id, object_type, content):
    existing_object = json.loads(existing_object)
    if existing_object['id'] == object_id and existing_object['type'] == object_type \
       and existing_object.get('attributes') == content.get('attributes') \
       and existing_object.get('references') == content.get('references'):
        return False
    else:
        return True


def get_object(module, object_id, object_type, kibana_url,
               timeout, tenant=None):

    url, headers, _ = get_request_params(
        object_id=object_id,
        object_type=object_type,
        kibana_url=kibana_url,
        tenant=tenant,
    )
    try:
        return fetch_url(module, url,
                         method='GET',
                         headers=headers,
                         timeout=timeout)
    except Exception as e:
        try:
            if e.code == 404:
                return e
        except Exception:
            module.fail_json(msg="An error occured while trying to get the object '{0}'. {1}".format(object_id, to_native(e)))


def create_object(module, object_id, object_type, kibana_url, content,
                  timeout, tenant=None, overwrite=False):

    url, headers, data = get_request_params(
        object_id=object_id,
        object_type=object_type,
        kibana_url=kibana_url,
        content=content,
        tenant=tenant,
        overwrite=overwrite
    )
    try:
        return fetch_url(module, url,
                         method='POST',
                         headers=headers,
                         data=data,
                         timeout=timeout)
    except Exception as e:
        module.fail_json(msg="An error occured while trying to get the object '{0}'. {1}".format(object_id, to_native(e)))


def update_object(module, object_id, object_type, kibana_url, content,
                  timeout, tenant=None):

    url, headers, data = get_request_params(
        object_id=object_id,
        object_type=object_type,
        kibana_url=kibana_url,
        content=content,
        tenant=tenant,
    )
    try:
        return fetch_url(module, url,
                         method='PUT',
                         headers=headers,
                         data=data,
                         timeout=timeout)
    except Exception as e:
        module.fail_json(msg="An error occured while trying to get the object '{0}'. {1}".format(object_id, to_native(e)))


def delete_object(module, object_id, object_type, kibana_url,
                  timeout, tenant=None):

    url, headers, _ = get_request_params(
        object_id=object_id,
        object_type=object_type,
        kibana_url=kibana_url,
        tenant=tenant,
    )
    try:
        return fetch_url(module, url,
                         method='DELETE',
                         headers=headers,
                         timeout=timeout)
    except Exception as e:
        module.fail_json(msg="An error occured while trying to get the object '{0}'. {1}".format(object_id, to_native(e)))


def is_object_present(module, object_id, object_type, kibana_url,
                      timeout, tenant=None):

    r, r_info = get_object(
        module=module,
        object_id=object_id,
        object_type=object_type,
        kibana_url=kibana_url,
        tenant=tenant,
        timeout=timeout
    )

    try:
        if r_info['status'] == 404:
            return False, None
        elif r_info['status'] == 200:
            return True, r.read()
        else:
            module.fail_json(msg="Got status other then 200 or 404. {0}".format(r_info))
    except Exception as e:
        module.fail_json(msg="An error occured while trying to get the object '{0}'. {1}".format(object_id, to_native(e)))


def main():
    argument_spec = url_argument_spec()
    del argument_spec['http_agent'], argument_spec['force'], argument_spec['url']
    argument_spec.update(dict(
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
        timeout=dict(type='int', default=30),
        overwrite=dict(type='bool', default=False),
        url_username=dict(type='str', aliases=['user']),
        url_password=dict(type='str', aliases=['password'], no_log=True),

        searchguard_tenant=dict(type='str'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    object_id = module.params['id']
    object_type = module.params['type']
    state = module.params['state']
    content = module.params['content']
    kibana_url = module.params['kibana_url']
    timeout = module.params['timeout']
    overwrite = module.params['overwrite']
    searchguard_tenant = module.params['searchguard_tenant']
    user = module.params['url_username']
    password = module.params['url_password']

    present, existing_object = is_object_present(
        module=module,
        object_id=object_id,
        object_type=object_type,
        kibana_url=kibana_url,
        tenant=searchguard_tenant,
        timeout=timeout
    )

    if state == 'present':
        if present and not overwrite:
            if are_different(module=module,
                             existing_object=existing_object,
                             object_id=object_id,
                             object_type=object_type,
                             content=content):
                if module.check_mode:
                    module.exit_json(changed=True, object_id=object_id,
                                     object_type=object_type,
                                     msg="Object would have been updated if check mode had not been spacified: {0}".format(object_id))
                # Update object
                r = update_object(
                    module=module,
                    object_id=object_id,
                    object_type=object_type,
                    kibana_url=kibana_url,
                    content=content,
                    tenant=searchguard_tenant,
                    timeout=timeout,
                )
                module.exit_json(changed=True, object_id=object_id,
                                 object_type=object_type,
                                 msg="Object has been updated: {0}".format(object_id))
            else:
                module.exit_json(changed=False, object_id=object_id,
                                 object_type=object_type,
                                 msg="Object already exists: {0}".format(object_id))
        if present and overwrite:
            if module.check_mode:
                module.exit_json(changed=True, object_id=object_id,
                                 object_type=object_type,
                                 msg="Object would have been overwritten if check mode had not been spacified: {0}".format(object_id))
            # Overwrite object
            r = create_object(
                module=module,
                object_id=object_id,
                object_type=object_type,
                kibana_url=kibana_url,
                content=content,
                tenant=searchguard_tenant,
                timeout=timeout,
                overwrite=True
            )
            module.exit_json(changed=True, object_id=object_id,
                             object_type=object_type,
                             msg="Object has been overwritten: {0}".format(object_id))
        if not present:
            # Create object
            if module.check_mode:
                module.exit_json(changed=True, object_id=object_id,
                                 object_type=object_type,
                                 msg="Object would have been created if check mode had not been spacified: {0}".format(object_id))
            r = create_object(
                module=module,
                object_id=object_id,
                object_type=object_type,
                kibana_url=kibana_url,
                content=content,
                tenant=searchguard_tenant,
                timeout=timeout
            )
            module.exit_json(changed=True, object_id=object_id,
                             object_type=object_type,
                             msg="Object has been created: {0}".format(object_id))
    if state == 'absent':
        if not present:
            module.exit_json(changed=False, object_id=object_id,
                             object_type=object_type,
                             msg="Object does not exist: {0}".format(object_id))

        if present:
            if module.check_mode:
                module.exit_json(changed=True, object_id=object_id,
                                 object_type=object_type,
                                 msg="Object would have been deleted if check mode had not been spacified: {0}".format(object_id))
            r = delete_object(
                module=module,
                object_id=object_id,
                object_type=object_type,
                kibana_url=kibana_url,
                tenant=searchguard_tenant,
                timeout=timeout
            )
            module.exit_json(changed=True, object_id=object_id,
                             object_type=object_type,
                             msg="Object has been deleted: {0}".format(object_id))


if __name__ == '__main__':
    main()
