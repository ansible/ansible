#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Anders Ingemann <aim@secoya.dk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: sensu_subscription
short_description: Manage Sensu subscriptions
version_added: 2.2
description:
  - Manage which I(sensu channels) a machine should subscribe to
options:
  name:
    description:
      - The name of the channel
    required: true
  state:
    description:
      - Whether the machine should subscribe or unsubscribe from the channel
    choices: [ 'present', 'absent' ]
    required: false
    default: present
  path:
    description:
      - Path to the subscriptions json file
    required: false
    default: /etc/sensu/conf.d/subscriptions.json
  backup:
    description:
      - Create a backup file (if yes), including the timestamp information so you
      - can get the original file back if you somehow clobbered it incorrectly.
    type: bool
    required: false
    default: no
requirements: [ ]
author: Anders Ingemann
'''

RETURN = '''
reasons:
    description: the reasons why the moule changed or did not change something
    returned: success
    type: list
    sample: ["channel subscription was absent and state is `present'"]
'''

EXAMPLES = '''
# Subscribe to the nginx channel
- name: subscribe to nginx checks
  sensu_subscription: name=nginx

# Unsubscribe from the common checks channel
- name: unsubscribe from common checks
  sensu_subscription: name=common state=absent
'''
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


def sensu_subscription(module, path, name, state='present', backup=False):
    changed = False
    reasons = []

    try:
        import json
    except ImportError:
        import simplejson as json

    try:
        config = json.load(open(path))
    except IOError as e:
        if e.errno is 2:  # File not found, non-fatal
            if state == 'absent':
                reasons.append('file did not exist and state is `absent\'')
                return changed, reasons
            config = {}
        else:
            module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    except ValueError:
        msg = '{path} contains invalid JSON'.format(path=path)
        module.fail_json(msg=msg)

    if 'client' not in config:
        if state == 'absent':
            reasons.append('`client\' did not exist and state is `absent\'')
            return changed, reasons
        config['client'] = {}
        changed = True
        reasons.append('`client\' did not exist')

    if 'subscriptions' not in config['client']:
        if state == 'absent':
            reasons.append('`client.subscriptions\' did not exist and state is `absent\'')
            return changed, reasons
        config['client']['subscriptions'] = []
        changed = True
        reasons.append('`client.subscriptions\' did not exist')

    if name not in config['client']['subscriptions']:
        if state == 'absent':
            reasons.append('channel subscription was absent')
            return changed, reasons
        config['client']['subscriptions'].append(name)
        changed = True
        reasons.append('channel subscription was absent and state is `present\'')
    else:
        if state == 'absent':
            config['client']['subscriptions'].remove(name)
            changed = True
            reasons.append('channel subscription was present and state is `absent\'')

    if changed and not module.check_mode:
        if backup:
            module.backup_local(path)
        try:
            open(path, 'w').write(json.dumps(config, indent=2) + '\n')
        except IOError as e:
            module.fail_json(msg='Failed to write to file %s: %s' % (path, to_native(e)),
                             exception=traceback.format_exc())

    return changed, reasons


def main():
    arg_spec = {'name': {'type': 'str', 'required': True},
                'path': {'type': 'str', 'default': '/etc/sensu/conf.d/subscriptions.json'},
                'state': {'type': 'str', 'default': 'present', 'choices': ['present', 'absent']},
                'backup': {'type': 'bool', 'default': 'no'},
                }

    module = AnsibleModule(argument_spec=arg_spec,
                           supports_check_mode=True)

    path = module.params['path']
    name = module.params['name']
    state = module.params['state']
    backup = module.params['backup']

    changed, reasons = sensu_subscription(module, path, name, state, backup)

    module.exit_json(path=path, name=name, changed=changed, msg='OK', reasons=reasons)


if __name__ == '__main__':
    main()
