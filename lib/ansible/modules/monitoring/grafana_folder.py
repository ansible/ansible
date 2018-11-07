#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Martin Wang (@martinwangjian)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.1'
}

DOCUMENTATION = '''
---
module: grafana_folder
author:
  - Martin Wang (@martinwangjian)
version_added: "2.8"
short_description: Manage Grafana folder
description:
  - Create, update, delete Grafana folder via API.
options:
  url:
    description:
      - The Grafana URL.
    required: true
    aliases: [ grafana_url ]
  url_username:
    description:
      - The Grafana API user.
    default: admin
    aliases: [ grafana_user ]
  url_password:
    description:
      - The Grafana API password.
    default: admin
    aliases: [ grafana_password ]
  grafana_api_key:
    description:
      - The Grafana API key.
      - If set, I(grafana_user) and I(grafana_password) will be ignored.
  org_id:
    description:
      - The Grafana Organisation ID where the folder will be imported / exported.
      - Not used when I(grafana_api_key) is set, because the grafana_api_key only belongs to one organisation..
    default: 1
  state:
    description:
      - State of the folder.
    required: true
    choices: [ absent, present ]
    default: present
  uid:
    required: false
    description:
      - uid of the folder.
  title:
    description:
      - title of the folder when C(state) is C(present).
  overwrite:
    description:
      - Override existing folder when C(state) is C(present).
    type: bool
    default: 'no'
  client_cert:
    required: false
    description:
      - TLS certificate path used by ansible to query grafana api
  client_key:
    required: false
    description:
      - TLS private key path used by ansible to query grafana api
  validate_certs:
    description:
      - Whether to validate the Grafana certificate.
    type: bool
    default: 'yes'
  use_proxy:
    description:
      - Boolean of whether or not to use proxy.
    default: 'yes'
    type: bool
'''

EXAMPLES = '''
- hosts: localhost
  tasks:
    - name: create folder with title
      grafana_folder:
        grafana_url: http://grafana.company.com
        grafana_api_key: "{{ grafana_api_key }}"
        state: present
        title: "toto"

    - name: create folder with uid
      grafana_folder:
        grafana_url: http://grafana.company.com
        grafana_api_key: "{{ grafana_api_key }}"
        state: present
        uid: "a"
        title: "a"

    - name: delete folder
      grafana_folder:
        grafana_url: http://grafana.company.com
        grafana_user: "admin"
        grafana_password: "{{ grafana_password }}"
        state: absent
        uid: "b"

    - name: update folder
      grafana_folder:
        grafana_url: http://grafana.company.com
        grafana_user: "admin"
        grafana_password: "{{ grafana_password }}"
        state: present
        uid: "c"
        title: "d"

    - name: update folder
      grafana_folder:
        grafana_url: http://grafana.company.com
        grafana_user: "admin"
        grafana_password: "{{ grafana_password }}"
        state: present
        uid: "c"
        title: "e"
        overwrite: yes
'''

RETURN = '''
---
uid:
  description: uid of the created / updated / deleted folder.
  returned: success
  type: string
  sample: 000000063

version:
  description: version of the created / updated folder.
  returned: success
  type: string
  sample: 000000063
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url, url_argument_spec
from ansible.module_utils._text import to_native

__metaclass__ = type


class GrafanaAPIException(Exception):
    pass


def grafana_switch_organisation(module, grafana_url, org_id, headers):
    r, info = fetch_url(module, '%s/api/user/using/%s' % (grafana_url, org_id), headers=headers, method='POST')
    if info['status'] != 200:
        raise GrafanaAPIException('Unable to switch to organization %s : %s' % (org_id, info))


def grafana_headers(module, data):
    headers = {'content-type': 'application/json; charset=utf8'}
    if 'grafana_api_key' in data and data['grafana_api_key']:
        headers['Authorization'] = "Bearer %s" % data['grafana_api_key']
    else:
        module.params['force_basic_auth'] = True
        grafana_switch_organisation(module, data['grafana_url'], data['org_id'], headers)

    return headers


def grafana_folder_exists_with_uid(module, grafana_url, uid, headers):
    folder_exists = False
    uid_found = None
    title_found = None
    id_found = None
    version_found = None

    r, info = fetch_url(module, '%s/api/folders/%s' % (grafana_url, uid), headers=headers, method='GET')

    if info['status'] == 200:
        folder_exists = True
        try:
            response = json.loads(r.read())
            uid_found = response['uid']
            title_found = response['title']
            id_found = response['id']
            version_found = response['version']
        except Exception as e:
            raise GrafanaAPIException(e)
    elif info['status'] == 404:
        folder_exists = False
    else:
        raise GrafanaAPIException('Unable to get folder %s : %s' % (uid, info))

    return folder_exists, uid_found, title_found, id_found, version_found


def grafana_folder_exists_with_title(module, grafana_url, title, headers):
    folder_exists = False
    uid_found = None
    title_found = None
    id_found = None
    version_found = None

    r, info = fetch_url(module, '%s/api/folders' % grafana_url, headers=headers, method='GET')

    if info['status'] == 200:
        try:
            responses = json.loads(r.read())
            for folder in responses:
                if folder['title'] == title:
                    folder_exists = True
                    uid_found = folder['uid']
                    title_found = folder['title']
                    id_found = folder['id']
        except Exception as e:
            raise GrafanaAPIException(e)
    elif info['status'] == 404:
        folder_exists = False
    else:
        raise GrafanaAPIException('Unable to get folders with title %s : %s' % (title, info))

    return folder_exists, uid_found, title_found, id_found, version_found


def grafana_create_folder(module, data):
    # define http header
    headers = grafana_headers(module, data)

    title = data.get('title')
    payload = {'title': title}

    # test if folder already exists
    if 'uid' in data and data['uid']:
        uid = data.get('uid')
        payload['uid'] = uid
        folder_exists, uid_found, title_found, id_found, version_found = grafana_folder_exists_with_uid(module, data['grafana_url'], uid, headers=headers)
    else:
        folder_exists, uid_found, title_found, id_found, version_found = grafana_folder_exists_with_title(module, data['grafana_url'], title, headers=headers)

    result = {}
    if folder_exists is True:
        if title == title_found:
            # unchanged
            result['uid'] = uid_found
            result['id'] = id_found
            result['msg'] = "Folder '%s' unchanged." % title_found
            result['changed'] = False
        else:
            # update
            if 'overwrite' in data and data['overwrite']:
                payload['overwrite'] = True
            else:
                payload['version'] = version_found

            r, info = fetch_url(module, '%s/api/folders/%s' % (data['grafana_url'], uid), data=json.dumps(payload), headers=headers, method='PUT')
            if info['status'] == 200:
                try:
                    response = json.loads(r.read())
                    result['uid'] = response['uid']
                    result['id'] = response['id']
                    result['version'] = response['version']
                except Exception as e:
                    raise GrafanaAPIException(e)
                result['msg'] = "Folder %s updated" % uid
                result['changed'] = True
            else:
                body = json.loads(info['body'])
                raise GrafanaAPIException('Unable to update the folder %s : %s' % (uid, body))
    else:
        # create
        r, info = fetch_url(module, '%s/api/folders' % data['grafana_url'], data=json.dumps(payload), headers=headers, method='POST')
        if info['status'] == 200:
            result['changed'] = True
            try:
                response = json.loads(r.read())
                result['uid'] = response['uid']
                result['id'] = response['id']
                result['version'] = response['version']
                result['msg'] = "folder %s created" % response['uid']
            except Exception as e:
                raise GrafanaAPIException(e)
        else:
            raise GrafanaAPIException('Unable to create the new folder %s : %s - %s.' % (uid, info['status'], info))

    return result


def grafana_delete_folder(module, data):
    # define http headers
    headers = grafana_headers(module, data)

    # test if folder already exists
    if 'uid' in data and data['uid']:
        uid = data.get('uid')
        folder_exists, uid_found, title_found, id_found, version_found = grafana_folder_exists_with_uid(module, data['grafana_url'], uid, headers=headers)
    elif 'title' in data and data['title']:
        title = data.get('title')
        folder_exists, uid_found, title_found, id_found, version_found = grafana_folder_exists_with_title(module, data['grafana_url'], title, headers=headers)
    else:
        raise GrafanaAPIException('Unable to delete folders without title or uid')

    result = {}
    if folder_exists is True:
        # delete
        r, info = fetch_url(module, '%s/api/folders/%s' % (data['grafana_url'], uid_found), headers=headers, method='DELETE')
        if info['status'] == 200:
            result['msg'] = "Folder %s deleted" % uid_found
            result['changed'] = True
            result['uid'] = uid_found
        else:
            raise GrafanaAPIException('Unable to delete the Folder %s : %s' % (uid_found, info))
    else:
        # Folder does not exist, do nothing
        result = {'msg': "Folder does not exist.",
                  'changed': False}

    return result


def main():
    # use the predefined argument spec for url
    argument_spec = url_argument_spec()
    # remove unnecessary arguments
    del argument_spec['force']
    del argument_spec['force_basic_auth']
    del argument_spec['http_agent']
    argument_spec.update(
        state=dict(choices=['present', 'absent'], default='present'),
        url=dict(aliases=['grafana_url'], required=True),
        url_username=dict(aliases=['grafana_user'], default='admin'),
        url_password=dict(aliases=['grafana_password'], default='admin', no_log=True),
        grafana_api_key=dict(type='str', no_log=True),
        org_id=dict(default=1, type='int'),
        uid=dict(type='str'),
        title=dict(default='', type='str'),
        overwrite=dict(type='bool', default=False)
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        required_together=[['url_username', 'url_password', 'org_id']],
        mutually_exclusive=[['grafana_user', 'grafana_api_key']],
    )

    try:
        if module.params['state'] == 'present':
            result = grafana_create_folder(module, module.params)
        elif module.params['state'] == 'absent':
            result = grafana_delete_folder(module, module.params)
        else:
            raise GrafanaAPIException("Unknown state - get neither 'present' nor 'absent'")
    except GrafanaAPIException as e:
        module.fail_json(
            failed=True,
            msg="error : %s" % to_native(e)
        )
        return
    module.exit_json(
        failed=False,
        **result
    )
    return


if __name__ == '__main__':
    main()
