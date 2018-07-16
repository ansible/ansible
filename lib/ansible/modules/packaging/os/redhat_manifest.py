#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Sean O'Keeffe <seanokeeffe797@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Reference: https://docs.ansible.com/ansible/2.6/dev_guide/developing_modules_general.html

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: redhat_manifest
short_description: Interact with a Red Hat Satellite Subscription Manifest
description:
    - Download and modify a Red Hat Satellite Subscription Manifest
author:
    - "Sean O'Keeffe (@sean797)"
version_added: "2.7"
options:
    name:
        description:
           - Manifest Name
    uuid:
        description:
           - Manifest uuid
    username:
        description:
            - Red Hat Portal username
        required: true
    password:
        description:
            - Red Hat Portal password
        required: true
    pool_id:
        description:
            - Subscription pool_id
    quantity:
        description:
            - quantity of pool_id Subscriptions
        type: int
    pool_state:
        description:
            - Subscription state
        default: present
        choices:
            - present
            - absent
    state:
        description:
            - Manifest state
        default: present
        choices:
            - present
            - absent
    path:
        description:
            - path to export the manifest
        type: path
    validate_certs:
        description:
            - Validate Portal SSL
        default: True
        type: bool
    portal:
        description:
            - Red Hat Portal subscription access address
        default: https://subscription.rhn.redhat.com
'''

EXAMPLES = '''
- name: Create katello.example.com manifest and add 7 subs
  redhat_manifest:
    name: "katello.example.com"
    username: "john-smith"
    password: "changeme"
    pool_id: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    quantity: 7

- name: Ensure my manifest has 10 of one subs and export
  redhat_manifest:
    uuid: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
    username: john-smith
    password: changeme
    pool_id: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    quantity: 10
    path: /tmp/manifest.zip

- name: Remove all of one subs from katello.example.com
  redhat_manifest:
    name: katello.example.com
    username: john-smith
    password: changeme
    pool_id: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    pool_state: absent
'''

RETURN = '''# '''

try:
    import json
except ImportError:
    import simplejson as json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native
from ansible.module_utils._text import to_text


def fetch_portal(module, path, method, data=None, accept_header='application/json'):
    url = module.params['portal'] + path
    headers = {'accept': accept_header,
               'content-type': 'application/json'}
    resp, info = fetch_url(module, url, json.dumps(data), headers, method)
    if resp is None:
        try:
            error = json.loads(info['body'])['displayMessage']
        except:
            error = info['msg']
        module.fail_json(msg="%s to %s failed, got %s" % (method, url, error))
    return resp, info


def create_manifest(module):
    path = "/subscription/consumers"
    data = {'name': module.params['name'],
            'type': "satellite",
            'owner': module.params['rhsm_owner'],
            # TODO: Make these 2 configurable, we need to work out which horribly
            # undocumented API to use.
            'facts': {'distributor_version': 'sat-6.0',
                      'system.certificate_version': '3.2'}}
    resp, info = fetch_portal(module, path, 'POST', data)
    return json.loads(to_text(resp.read()))


def delete_manifest(module, uuid):
    path = "/subscription/consumers/%s" % uuid
    resp, info = fetch_portal(module, path, 'DELETE')
    if not info['status'] == 204:
        module.fail_json(msg="Got status %s attempting to delete manifest, expected 204" % (info['status']))


def get_manifest(module):
    path = "/subscription/owners/%s/consumers?type=satellite" % (module.params['rhsm_owner'])
    resp, info = fetch_portal(module, path, 'GET')
    manifests = json.loads(to_text(resp.read()))
    if module.params['name']:
        attr = 'name'
    if module.params['uuid']:
        attr = 'uuid'
    manifest = [m for m in manifests if m[attr] == module.params[attr]]
    if manifest:
        if module.params['state'] == 'present':
            return manifest[0], False
        if module.params['state'] == 'absent':
            if not module.check_mode:
                return delete_manifest(module, manifest[0]['uuid']), True
            return False, True
    elif module.params['state'] == 'present':
        if not module.check_mode:
            return create_manifest(module), True
        return False, True
    return False, False


def get_owner(module):
    path = "/subscription/users/%s/owners" % (module.params['username'])
    resp, info = fetch_portal(module, path, 'GET')
    return json.loads(to_text(resp.read()))[0]['key']


def get_subs(module, manifest):
    path = "/subscription/consumers/%s/entitlements" % (manifest['uuid'])
    resp, info = fetch_portal(module, path, 'GET')
    all_subs = json.loads(to_text(resp.read()))
    subs = [s for s in all_subs if s['pool']['id'] == module.params['pool_id']]
    return subs


def get_remove_or_attach_sub(module, manifest):
    changed = False
    subs = get_subs(module, manifest)
    if subs:
        if module.params['pool_state'] == 'present':
            sub_quantity = sum(s['quantity'] for s in subs)
            while sub_quantity > module.params['quantity']:
                if not module.check_mode:
                    remove_sub(module, manifest, subs[0])
                else:
                    break
                changed = True
                subs = get_subs(module, manifest)
                sub_quantity = sum(s['quantity'] for s in subs)
            if sub_quantity < module.params['quantity']:
                difference = module.params['quantity'] - sub_quantity
                if not module.check_mode:
                    attach_sub(module, manifest, difference)
                changed = True
        elif module.params['pool_state'] == 'absent':
            if not module.check_mode:
                for sub in subs:
                    remove_sub(module, manifest, sub)
            changed = True
    elif module.params['pool_state'] == 'present':
        if not module.check_mode:
            attach_sub(module, manifest, module.params['quantity'])
        changed = True
    return changed


def remove_sub(module, manifest, sub):
    path = "/subscription/consumers/%s/entitlements/%s" % (manifest['uuid'], sub['id'])
    fetch_portal(module, path, 'DELETE')


def attach_sub(module, manifest, quantity):
    path = "/subscription/consumers/%s/entitlements?pool=%s&quantity=%s" % (manifest['uuid'], module.params['pool_id'], quantity)
    fetch_portal(module, path, 'POST')


def export_manifest(module, manifest):
    path = "/subscription/consumers/%s/export" % (manifest['uuid'])
    try:
        resp, info = fetch_portal(module, path, 'GET', accept_header='application/zip')
        if not module.check_mode:
            with open(module.params['path'], 'wb') as f:
                while True:
                    data = resp.read(65536)  # 64K
                    if not data:
                        break
                    f.write(data)
    except Exception as e:
        module.fail_json(msg="Failure downloading manifest, %s" % to_native(e))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str'),
            uuid=dict(type='str'),
            username=dict(required=True, no_log=True),
            password=dict(required=True, no_log=True),
            pool_id=dict(type='str'),
            quantity=dict(type='int'),
            pool_state=dict(choices=['present', 'absent'], default='present'),
            state=dict(choices=['present', 'absent'], default='present'),
            path=dict(type='path'),
            validate_certs=dict(default=True, type='bool'),
            portal=dict(default='https://subscription.rhn.redhat.com'),
        ),
        required_one_of=[['name', 'uuid']],
        supports_check_mode=True,
    )

    name = module.params['name']
    username = module.params['username']
    password = module.params['password']

    # Hack to add options the way fetch_url expects
    module.params['url_username'] = username
    module.params['url_password'] = password
    module.params['force_basic_auth'] = True

    module.params['rhsm_owner'] = get_owner(module)

    manifest, man_changed = get_manifest(module)
    if module.params['pool_id'] and manifest:
        sub_changed = get_remove_or_attach_sub(module, manifest)
    else:
        sub_changed = False

    if module.params['path'] and manifest:
        export_manifest(module, manifest)

    changed = man_changed or sub_changed
    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
