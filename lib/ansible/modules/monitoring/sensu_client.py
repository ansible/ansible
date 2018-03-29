#!/usr/bin/python

# (c) 2017, Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: sensu_client
author: "David Moreau Simard (@dmsimard)"
short_description: Manages Sensu client configuration
version_added: 2.4
description:
  - Manages Sensu client configuration.
  - 'For more information, refer to the Sensu documentation: U(https://sensuapp.org/docs/latest/reference/clients.html)'
options:
  state:
    description:
      - Whether the client should be present or not
    choices: [ 'present', 'absent' ]
    default: present
  name:
    description:
      - A unique name for the client. The name cannot contain special characters or spaces.
    default: System hostname as determined by Ruby Socket.gethostname (provided by Sensu)
  address:
    description:
      - An address to help identify and reach the client. This is only informational, usually an IP address or hostname.
    default: Non-loopback IPv4 address as determined by Ruby Socket.ip_address_list (provided by Sensu)
  subscriptions:
    description:
      - An array of client subscriptions, a list of roles and/or responsibilities assigned to the system (e.g. webserver).
      - These subscriptions determine which monitoring checks are executed by the client, as check requests are sent to subscriptions.
      - The subscriptions array items must be strings.
    required: True
  safe_mode:
    description:
      - If safe mode is enabled for the client. Safe mode requires local check definitions in order to accept a check request and execute the check.
    type: bool
    default: 'no'
  redact:
    description:
      - Client definition attributes to redact (values) when logging and sending client keepalives.
  socket:
    description:
      - The socket definition scope, used to configure the Sensu client socket.
  keepalives:
    description:
      - If Sensu should monitor keepalives for this client.
    type: bool
    default: 'yes'
  keepalive:
    description:
      - The keepalive definition scope, used to configure Sensu client keepalives behavior (e.g. keepalive thresholds, etc).
  registration:
    description:
      - The registration definition scope, used to configure Sensu registration event handlers.
  deregister:
    description:
      - If a deregistration event should be created upon Sensu client process stop.
    type: bool
    default: 'no'
  deregistration:
    description:
      - The deregistration definition scope, used to configure automated Sensu client de-registration.
  ec2:
    description:
      - The ec2 definition scope, used to configure the Sensu Enterprise AWS EC2 integration (Sensu Enterprise users only).
  chef:
    description:
      - The chef definition scope, used to configure the Sensu Enterprise Chef integration (Sensu Enterprise users only).
  puppet:
    description:
      - The puppet definition scope, used to configure the Sensu Enterprise Puppet integration (Sensu Enterprise users only).
  servicenow:
    description:
      - The servicenow definition scope, used to configure the Sensu Enterprise ServiceNow integration (Sensu Enterprise users only).
notes:
  - Check mode is supported
'''

EXAMPLES = '''
# Minimum possible configuration
- name: Configure Sensu client
  sensu_client:
    subscriptions:
      - default

# With customization
- name: Configure Sensu client
  sensu_client:
    name: "{{ ansible_fqdn }}"
    address: "{{ ansible_default_ipv4['address'] }}"
    subscriptions:
      - default
      - webserver
    redact:
      - password
    socket:
      bind: 127.0.0.1
      port: 3030
    keepalive:
      thresholds:
        warning: 180
        critical: 300
      handlers:
        - email
      custom:
        - broadcast: irc
      occurrences: 3
  register: client
  notify:
    - Restart sensu-client

- name: Secure Sensu client configuration file
  file:
    path: "{{ client['file'] }}"
    owner: "sensu"
    group: "sensu"
    mode: "0600"

- name: Delete the Sensu client configuration
  sensu_client:
    state: "absent"
'''

RETURN = '''
config:
  description: Effective client configuration, when state is present
  returned: success
  type: dict
  sample: {'name': 'client', 'subscriptions': ['default']}
file:
  description: Path to the client configuration file
  returned: success
  type: string
  sample: "/etc/sensu/conf.d/client.json"
'''

import json
import os

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            state=dict(type='str', required=False, choices=['present', 'absent'], default='present'),
            name=dict(type='str', required=False),
            address=dict(type='str', required=False),
            subscriptions=dict(type='list', required=False),
            safe_mode=dict(type='bool', required=False, default=False),
            redact=dict(type='list', required=False),
            socket=dict(type='dict', required=False),
            keepalives=dict(type='bool', required=False, default=True),
            keepalive=dict(type='dict', required=False),
            registration=dict(type='dict', required=False),
            deregister=dict(type='bool', required=False),
            deregistration=dict(type='dict', required=False),
            ec2=dict(type='dict', required=False),
            chef=dict(type='dict', required=False),
            puppet=dict(type='dict', required=False),
            servicenow=dict(type='dict', required=False)
        ),
        required_if=[
            ['state', 'present', ['subscriptions']]
        ]
    )

    state = module.params['state']
    path = "/etc/sensu/conf.d/client.json"

    if state == 'absent':
        if os.path.exists(path):
            if module.check_mode:
                msg = '{path} would have been deleted'.format(path=path)
                module.exit_json(msg=msg, changed=True)
            else:
                try:
                    os.remove(path)
                    msg = '{path} deleted successfully'.format(path=path)
                    module.exit_json(msg=msg, changed=True)
                except OSError as e:
                    msg = 'Exception when trying to delete {path}: {exception}'
                    module.fail_json(
                        msg=msg.format(path=path, exception=str(e)))
        else:
            # Idempotency: it's okay if the file doesn't exist
            msg = '{path} already does not exist'.format(path=path)
            module.exit_json(msg=msg)

    # Build client configuration from module arguments
    config = {'client': {}}
    args = ['name', 'address', 'subscriptions', 'safe_mode', 'redact',
            'socket', 'keepalives', 'keepalive', 'registration', 'deregister',
            'deregistration', 'ec2', 'chef', 'puppet', 'servicenow']

    for arg in args:
        if arg in module.params and module.params[arg] is not None:
            config['client'][arg] = module.params[arg]

    # Load the current config, if there is one, so we can compare
    current_config = None
    try:
        current_config = json.load(open(path, 'r'))
    except (IOError, ValueError):
        # File either doesn't exist or it's invalid JSON
        pass

    if current_config is not None and current_config == config:
        # Config is the same, let's not change anything
        module.exit_json(msg='Client configuration is already up to date',
                         config=config['client'],
                         file=path)

    # Validate that directory exists before trying to write to it
    if not module.check_mode and not os.path.exists(os.path.dirname(path)):
        try:
            os.makedirs(os.path.dirname(path))
        except OSError as e:
            module.fail_json(msg='Unable to create {0}: {1}'.format(os.path.dirname(path),
                                                                    str(e)))

    if module.check_mode:
        module.exit_json(msg='Client configuration would have been updated',
                         changed=True,
                         config=config['client'],
                         file=path)

    try:
        with open(path, 'w') as client:
            client.write(json.dumps(config, indent=4))
            module.exit_json(msg='Client configuration updated',
                             changed=True,
                             config=config['client'],
                             file=path)
    except (OSError, IOError) as e:
        module.fail_json(msg='Unable to write file {0}: {1}'.format(path,
                                                                    str(e)))

if __name__ == '__main__':
    main()
