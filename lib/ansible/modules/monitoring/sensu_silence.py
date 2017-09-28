#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Steven Bambling <smbambling@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: sensu_silence
version_added: "2.4"
author: Steven Bambling(@smbambling)
short_description: Manage Sensu silence entries
description:
  - Create and clear (delete) a silence entries via the Sensu API
    for subscriptions and checks.
options:
  check:
    description:
      - Specifies the check which the silence entry applies to.
  creator:
    description:
      - Specifies the entity responsible for this entry.
  expire:
    description:
      - If specified, the silence entry will be automatically cleared
        after this number of seconds.
  expire_on_resolve:
    description:
      - If specified as true, the silence entry will be automatically
        cleared once the condition it is silencing is resolved.
    type: bool
  reason:
    description:
      - If specified, this free-form string is used to provide context or
        rationale for the reason this silence entry was created.
  state:
    description:
      - Specifies to create or clear (delete) a silence entry via the Sensu API
    required: true
    default: present
    choices: ['present', 'absent']
  subscription:
    description:
      - Specifies the subscription which the silence entry applies to.
      - To create a silence entry for a client append C(client:) to client name.
        Example - C(client:server1.example.dev)
    required: true
    default: []
  url:
    description:
      - Specifies the URL of the Sensu monitoring host server.
    required: false
    default: http://127.0.01:4567
'''

EXAMPLES = '''
# Silence ALL checks for a given client
- name: Silence server1.example.dev
  sensu_silence:
    subscription: client:server1.example.dev
    creator: "{{ ansible_user_id }}"
    reason: Performing maintenance

# Silence specific check for a client
- name: Silence CPU_Usage check for server1.example.dev
  sensu_silence:
    subscription: client:server1.example.dev
    check: CPU_Usage
    creator: "{{ ansible_user_id }}"
    reason: Investigation alert issue

# Silence multiple clients from a dict
  silence:
    server1.example.dev:
      reason: 'Deployment in progress'
    server2.example.dev:
      reason: 'Deployment in progress'

- name: Silence several clients from a dict
  sensu_silence:
    subscription: "client:{{ item.key }}"
    reason: "{{ item.value.reason }}"
    creator: "{{ ansible_user_id }}"
  with_dict: "{{ silence }}"
'''

RETURN = '''
'''


try:
    import json
except ImportError:
    import simplejson as json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


def query(module, url, check, subscription):
    headers = {
        'Content-Type': 'application/json',
    }

    url = url + '/silenced'

    request_data = {
        'check': check,
        'subscription': subscription,
    }

    # Remove keys with None value
    for k, v in dict(request_data).items():
        if v is None:
            del request_data[k]

    response, info = fetch_url(
        module, url, method='GET',
        headers=headers, data=json.dumps(request_data)
    )

    if info['status'] == 500:
        module.fail_json(
            msg="Failed to query silence %s. Reason: %s" % (subscription, info)
        )

    try:
        json_out = json.loads(response.read())
    except:
        json_out = ""

    return False, json_out, False


def clear(module, url, check, subscription):
    # Test if silence exists before clearing
    (rc, out, changed) = query(module, url, check, subscription)

    d = dict((i['subscription'], i['check']) for i in out)
    subscription_exists = subscription in d
    if check and subscription_exists:
        exists = (check == d[subscription])
    else:
        exists = subscription_exists

    # If check/subscription doesn't exist
    # exit with changed state of False
    if not exists:
        return False, out, changed

    # module.check_mode is inherited from the AnsibleMOdule class
    if not module.check_mode:
        headers = {
            'Content-Type': 'application/json',
        }

        url = url + '/silenced/clear'

        request_data = {
            'check': check,
            'subscription': subscription,
        }

        # Remove keys with None value
        for k, v in dict(request_data).items():
            if v is None:
                del request_data[k]

        response, info = fetch_url(
            module, url, method='POST',
            headers=headers, data=json.dumps(request_data)
        )

        if info['status'] != 204:
            module.fail_json(
                msg="Failed to silence %s. Reason: %s" % (subscription, info)
            )

        try:
            json_out = json.loads(response.read())
        except:
            json_out = ""

        return False, json_out, True
    return False, out, True


def create(
        module, url, check, creator, expire,
        expire_on_resolve, reason, subscription):
    (rc, out, changed) = query(module, url, check, subscription)
    for i in out:
        if (i['subscription'] == subscription):
            if (
                    (check is None or check == i['check']) and
                    (
                        creator == '' or
                        creator == i['creator'])and
                    (
                        reason == '' or
                        reason == i['reason']) and
                    (
                        expire is None or expire == i['expire']) and
                    (
                        expire_on_resolve is None or
                        expire_on_resolve == i['expire_on_resolve']
                    )
            ):
                return False, out, False

    # module.check_mode is inherited from the AnsibleMOdule class
    if not module.check_mode:
        headers = {
            'Content-Type': 'application/json',
        }

        url = url + '/silenced'

        request_data = {
            'check': check,
            'creator': creator,
            'expire': expire,
            'expire_on_resolve': expire_on_resolve,
            'reason': reason,
            'subscription': subscription,
        }

        # Remove keys with None value
        for k, v in dict(request_data).items():
            if v is None:
                del request_data[k]

        response, info = fetch_url(
            module, url, method='POST',
            headers=headers, data=json.dumps(request_data)
        )

        if info['status'] != 201:
            module.fail_json(
                msg="Failed to silence %s. Reason: %s" %
                (subscription, info['msg'])
            )

        try:
            json_out = json.loads(response.read())
        except:
            json_out = ""

        return False, json_out, True
    return False, out, True


def main():
    module = AnsibleModule(
        argument_spec=dict(
            check=dict(required=False),
            creator=dict(required=False),
            expire=dict(required=False),
            expire_on_resolve=dict(type='bool', required=False),
            reason=dict(required=False),
            state=dict(default='present', choices=['present', 'absent']),
            subscription=dict(required=True),
            url=dict(required=False, default='http://127.0.01:4567'),
        ),
        supports_check_mode=True
    )

    url = module.params['url']
    check = module.params['check']
    creator = module.params['creator']
    expire = module.params['expire']
    expire_on_resolve = module.params['expire_on_resolve']
    reason = module.params['reason']
    subscription = module.params['subscription']
    state = module.params['state']

    if state == 'present':
        (rc, out, changed) = create(
            module, url, check, creator,
            expire, expire_on_resolve, reason, subscription
        )

    if state == 'absent':
        (rc, out, changed) = clear(module, url, check, subscription)

    if rc != 0:
        module.fail_json(msg="failed", result=out)
    module.exit_json(msg="success", result=out, changed=changed)


if __name__ == '__main__':
    main()
