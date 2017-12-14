#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# pylint: disable=C0413,C0111,C0301,W0612
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: icinga2_host
version_added: "2.4"
author: "J. M. Becker (@techzilla)"
short_description: Update Host on Icinga2
description:
   - Update Host on Icinga2 (see https://docs.icinga.com/icinga2/latest/doc/module/icinga2/chapter/icinga2-api)
options:
  url_username:
    description:
      - API User
    default: null
    required: true
  url_password:
    description:
      - API User's Password
    default: null
    required: false
  baseurl:
    description:
      - Icinga2 API Master URL
    default: null
    required: true
  name:
    description:
      - Name of host Object
    default: null
    required: true
  templates:
    description:
      - A list of Icinga2 templates
    default: null
    required: false
  attrs:
    description:
      - A dictionary of key/value attr pairs
    default: null
    required: false
  state:
    description:
      - State of host object
    choices: [ "present", "absent" ]
    default: "present"
    required: false

requirements: []
'''

EXAMPLES = '''
- icinga2_host:
    url_username: icinga2
    url_password: password123
    baseurl: https://localhost:5665
    name: hostname.example.com
    templates:
      - generic-host
    attrs:
      address: 192.168.1.2
      vars.os: Linux
    state: present
'''

RETURN = '''#'''

import collections

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url, url_argument_spec


class AnsibleIcinga2Server(object):

    def __init__(self, module, baseurl):
        self.module = module
        self.params = self.module.params
        self.baseurl = baseurl

    def create_hostobject(self, name):
        url = "%sv1/objects/hosts/%s" % (self.baseurl, name)
        data = {}
        data['templates'] = self.module.params.get('templates')
        data['attrs'] = self.module.params.get('attrs')

        response, info = fetch_url(
            self.module,
            url,
            data=self.module.jsonify(data),
            headers={'Accept': 'application/json'},
            method='PUT')

        if not info['status'] == 200:
            self.module.fail_json(msg="Failed to create hostobject " +
                                  str(info["status"]) + " " + info["msg"])

        return response, info

    def update_hostobject(self, name):

        response, info = self.delete_hostobject(name)
        response, info = self.create_hostobject(name)

        return response, info

    def delete_hostobject(self, name):

        url = "%sv1/objects/hosts/%s?cascade=1" % (self.baseurl, name)

        response, info = fetch_url(
            self.module,
            url,
            headers={'Accept': 'application/json'},
            method='DELETE')

        if not info['status'] == 200:
            self.module.fail_json(msg="Failed to delete hostobject " +
                                  str(info["status"]) + " " + info["msg"])

        return response, info

    def check_hostobject(self, name):

        url = "%sv1/objects/hosts/%s" % (self.baseurl, name)

        response, info = fetch_url(
            self.module,
            url)

        if not (info['status'] == 404 or info['status'] == 200):
            self.module.fail_json(msg="Failed to check hostobject " +
                                  str(info["status"]) + " " + info["msg"])

        return response, info


def dict_flatten(dict1, parent_key='', sep='.'):
    items = []
    for key, val in dict1.items():
        new_key = parent_key + sep + key if parent_key else key
        if isinstance(val, collections.MutableMapping):
            items.extend(dict_flatten(val, new_key, sep=sep).items())
        else:
            items.append((new_key, val))
    return dict(items)


def dict_compare(dict1, dict2):
    dict1_keys = set(dict1.keys())
    dict2_keys = set(dict2.keys())
    intersect_keys = dict1_keys.intersection(dict2_keys)
    added = dict1_keys - dict2_keys
    removed = dict2_keys - dict1_keys
    modified = set(o for o in intersect_keys if dict1[o] != dict2[o])
    same = set(o for o in intersect_keys if dict1[o] == dict2[o])
    return added, removed, modified, same


def main():
    # Module arguments
    argument_spec = url_argument_spec()
    argument_spec.update(
        url_password=dict(no_log=True, default=None),
        baseurl=dict(required=True, default=None),
        name=dict(required=True, default=None),
        templates=dict(type='list', default=[]),
        attrs=dict(type='dict'),
        state=dict(
            default='present',
            choices=['absent', 'present']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    state = module.params['state']
    baseurl = module.params['baseurl']
    name = module.params['name']

    server = AnsibleIcinga2Server(module, baseurl)
    check_hostobject_response, check_hostobject_info = server.check_hostobject(
        name)

    if state == 'absent':
        if check_hostobject_info['status'] == 404:
            changed = False
        if check_hostobject_info['status'] == 200:
            changed = True
            if not module.check_mode:
                changed_hostobject_response, changed_hostobject_info = server.delete_hostobject(
                    name)
    if state == 'present':
        if check_hostobject_info['status'] == 404:
            changed = True
            if not module.check_mode:
                changed_hostobject_response, changed_hostobject_info = server.create_hostobject(
                    name)
        if check_hostobject_info['status'] == 200:
            attrs = module.params.get('attrs')

            check_hostobject_response_read = check_hostobject_response.read()
            results = module.from_json(check_hostobject_response_read)
            results_attrs = dict_flatten(results['results'][0]['attrs'])

            added, removed, modified, same = dict_compare(
                attrs, results_attrs)

            if len(added) > 0 or len(modified) > 0:
                changed = True
                if not module.check_mode:
                    changed_hostobject_response, changed_hostobject_info = server.update_hostobject(
                        name)
            else:
                changed = False

    if 'changed_hostobject_info' in locals():
        hostobject_info = changed_hostobject_info
    else:
        hostobject_info = check_hostobject_info

    module.exit_json(changed=changed, **hostobject_info)

if __name__ == '__main__':
    main()
