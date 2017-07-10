#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, Anders Ingemann <aim@secoya.dk>
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
#

ANSIBLE_METADATA = {'metadata_version': '1.0',
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
    choices: [ 'yes', 'no' ]
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


def sensu_subscription(module, path, name, state='present', backup=False):
    changed = False
    reasons = []

    try:
        import json
    except ImportError:
        import simplejson as json

    try:
        config = json.load(open(path))
    except IOError:
        e = get_exception()
        if e.errno is 2:  # File not found, non-fatal
            if state == 'absent':
                reasons.append('file did not exist and state is `absent\'')
                return changed, reasons
            config = {}
        else:
            module.fail_json(msg=str(e))
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
        except IOError:
            e = get_exception()
            module.fail_json(msg='Failed to write to file %s: %s' % (path, str(e)))

    return changed, reasons


def main():
    arg_spec = {'name':   {'type': 'str', 'required': True},
                'path':   {'type': 'str', 'default': '/etc/sensu/conf.d/subscriptions.json'},
                'state':  {'type': 'str', 'default': 'present', 'choices': ['present', 'absent']},
                'backup': {'type': 'str', 'default': 'no', 'type': 'bool'},
                }

    module = AnsibleModule(argument_spec=arg_spec,
                           supports_check_mode=True)

    path = module.params['path']
    name = module.params['name']
    state = module.params['state']
    backup = module.params['backup']

    changed, reasons = sensu_subscription(module, path, name, state, backup)

    module.exit_json(path=path, name=name, changed=changed, msg='OK', reasons=reasons)

from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
