#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2018, Samuel Carpentier <samuelcarpentier0@gmail.ca>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_notification
author: "Samuel Carpentier (@samcarpentier)"
version_added: "2.8"
short_description: create, update, or destroy Ansible Tower notification.
description:
    - Create, update, or destroy Ansible Tower notifications. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name of the notification.
      required: True
    description:
      description:
        - The description of the notification.
      required: False
    organization:
      description:
        - The organization the notification belongs to.
      required: False
    notification_type:
      description:
        - The type of notification to be sent.
      required: True
      choices: ["email", "slack", "twilio", "pagerduty", "hipchat", "webhook", "irc"]
    notification_configuration:
      description:
        - The notification configuration file. Note providing this field would disable all notification-configuration-related fields.
      required: False
    username:
      description:
        - The mail server username. Required if I(notification_type=email).
      required: False
    sender:
      description:
        - The sender email address. Required if I(notification_type=email).
      required: False
    recipients:
      description:
        - The recipients email addresses. Required if I(notification_type=email).
      required: False
    use_tls:
      description:
        - The TLS trigger. Required if I(notification_type=email).
      required: False
      type: bool
    host:
      description:
        - The mail server host. Required if I(notification_type=email).
      required: False
    use_ssl:
      description:
        - The SSL trigger. Required if I(notification_type=email) or if I(notification_type=irc).
      required: False
      type: bool
    password:
      description:
        - The mail server password. Required if I(notification_type=email) or if I(notification_type=irc).
      required: False
    port:
      description:
        - The mail server port. Required if I(notification_type=email) or if I(notification_type=irc).
      required: False
    channels:
      description:
        - The destination Slack channels. Required if I(notification_type=slack).
      required: False
      type: list
    token:
      description:
        - The access token. Required if I(notification_type=slack), if I(notification_type=pagerduty) or if I(notification_type=hipchat).
      required: False
    account_token:
      description:
        - The Twillio account token. Required if I(notification_type=twillio).
      required: False
    from_number:
      description:
        - The source phone number. Required if I(notification_type=twillio).
      required: False
    to_numbers:
      description:
        - The destination phone numbers. Required if I(notification_type=twillio).
      required: False
    account_sid:
      description:
        - The Twillio accound SID. Required if I(notification_type=twillio).
      required: False
    subdomain:
      description:
        - The PagerDuty subdomain. Required if I(notification_type=pagerduty).
      required: False
    service_key:
      description:
        - The PagerDuty service/integration API key. Required if I(notification_type=pagerduty).
      required: False
    client_name:
      description:
        - The PagerDuty client identifier. Required if I(notification_type=pagerduty).
      required: False
    message_from:
      description:
        - The label to be shown with the notification. Required if I(notification_type=hipchat).
      required: False
    api_url:
      description:
        - The HipChat API URL. Required if I(notification_type=hipchat).
      required: False
    color:
      description:
        - The notification color. Required if I(notification_type=hipchat).
      required: False
      choices: ["yellow", "green", "red", "purple", "gray", "random"]
    rooms:
      description:
        - HipChat rooms to send the notification to. Required if I(notification_type=hipchat).
      required: False
      type: list
    notify:
      description:
        - The notify channel trigger. Required if I(notification_type=hipchat).
      required: False
      type: bool
    url:
      description:
        - The target URL. Required if I(notification_type=webhook).
      required: False
    headers:
      description:
        - The HTTP headers as JSON string. Required if I(notification_type=webhook).
      required: False
    server:
      description:
        - The IRC server address. Required if I(notification_type=irc).
      required: False
    nickname:
      description:
        - The IRC nickname. Required if I(notification_type=irc).
      required: False
    targets:
      description:
        - The destination channels or users. Required if I(notification_type=irc).
      required: False
      type: list
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
extends_documentation_fragment: tower
'''


EXAMPLES = '''
- name: Add Slack notification
  tower_notification:
    name: slack notification
    notification_type: slack
    channels:
      - general
    token: cefda9e2be1f21d11cdd9452f5b7f97fda977f42
    state: present
    tower_config_file: "~/tower_cli.cfg"

- name: Add webhook notification
  tower_notification:
    name: webhook notification
    notification_type: webhook
    url: http://www.example.com/hook
    headers:
      X-Custom-Header: value123
    state: present
    tower_config_file: "~/tower_cli.cfg"

- name: Add email notification
  tower_notification:
    name: email notification
    notification_type: email
    username: user
    password: s3cr3t
    sender: tower@example.com
    recipients:
      - user1@example.com
    host: smtp.example.com
    port: 25
    use_tls: no
    use_ssl: no
    state: present
    tower_config_file: "~/tower_cli.cfg"

- name: Add twilio notification
  tower_notification:
    name: twilio notification
    notification_type: twilio
    account_token: a_token
    account_sid: a_sid
    from_number: '+15551112222'
    to_numbers:
      - '+15553334444'
    state: present
    tower_config_file: "~/tower_cli.cfg"

- name: Add PagerDuty notification
  tower_notification:
    name: pagerduty notification
    notification_type: pagerduty
    token: a_token
    subdomain: sub
    client_name: client
    service_key: a_key
    state: present
    tower_config_file: "~/tower_cli.cfg"

- name: Add HipChat notification
  tower_notification:
    name: hipchat notification
    notification_type: hipchat
    token: a_token
    message_from: user1
    api_url: https://hipchat.example.com
    color: red
    rooms:
      - room-A
    notify: yes
    state: present
    tower_config_file: "~/tower_cli.cfg"

- name: Add IRC notification
  tower_notification:
    name: irc notification
    notification_type: irc
    nickname: tower
    password: s3cr3t
    targets:
      - user1
    port: 8080
    server: irc.example.com
    use_ssl: no
    state: present
    tower_config_file: "~/tower_cli.cfg"

- name: Delete notification
  tower_notification:
    name: old notification
    notification_type: email
    state: absent
    tower_config_file: "~/tower_cli.cfg"
'''


RETURN = ''' # '''


from ansible.module_utils.ansible_tower import TowerModule, tower_auth_config, tower_check_mode

try:
    import tower_cli
    import tower_cli.utils.exceptions as exc

    from tower_cli.conf import settings
except ImportError:
    pass


def main():
    argument_spec = dict(
        name=dict(required=True),
        description=dict(required=False),
        organization=dict(required=False),
        notification_type=dict(required=True, choices=['email', 'slack', 'twilio', 'pagerduty', 'hipchat', 'webhook', 'irc']),
        notification_configuration=dict(required=False),
        username=dict(required=False),
        sender=dict(required=False),
        recipients=dict(required=False, type='list'),
        use_tls=dict(required=False, type='bool'),
        host=dict(required=False),
        use_ssl=dict(required=False, type='bool'),
        password=dict(required=False, no_log=True),
        port=dict(required=False, type='int'),
        channels=dict(required=False, type='list'),
        token=dict(required=False, no_log=True),
        account_token=dict(required=False, no_log=True),
        from_number=dict(required=False),
        to_numbers=dict(required=False, type='list'),
        account_sid=dict(required=False),
        subdomain=dict(required=False),
        service_key=dict(required=False, no_log=True),
        client_name=dict(required=False),
        message_from=dict(required=False),
        api_url=dict(required=False),
        color=dict(required=False, choices=['yellow', 'green', 'red', 'purple', 'gray', 'random']),
        rooms=dict(required=False, type='list'),
        notify=dict(required=False, type='bool'),
        url=dict(required=False),
        headers=dict(required=False, type='dict', default={}),
        server=dict(required=False),
        nickname=dict(required=False),
        targets=dict(required=False, type='list'),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    name = module.params.get('name')
    description = module.params.get('description')
    organization = module.params.get('organization')
    notification_type = module.params.get('notification_type')
    notification_configuration = module.params.get('notification_configuration')
    username = module.params.get('username')
    sender = module.params.get('sender')
    recipients = module.params.get('recipients')
    use_tls = module.params.get('use_tls')
    host = module.params.get('host')
    use_ssl = module.params.get('use_ssl')
    password = module.params.get('password')
    port = module.params.get('port')
    channels = module.params.get('channels')
    token = module.params.get('token')
    account_token = module.params.get('account_token')
    from_number = module.params.get('from_number')
    to_numbers = module.params.get('to_numbers')
    account_sid = module.params.get('account_sid')
    subdomain = module.params.get('subdomain')
    service_key = module.params.get('service_key')
    client_name = module.params.get('client_name')
    message_from = module.params.get('message_from')
    api_url = module.params.get('api_url')
    color = module.params.get('color')
    rooms = module.params.get('rooms')
    notify = module.params.get('notify')
    url = module.params.get('url')
    headers = module.params.get('headers')
    server = module.params.get('server')
    nickname = module.params.get('nickname')
    targets = module.params.get('targets')
    state = module.params.get('state')

    json_output = {'notification': name, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        notification_template = tower_cli.get_resource('notification_template')

        try:
            org_res = tower_cli.get_resource('organization')
            org = org_res.get(name=organization)

            if state == 'present':
                result = notification_template.modify(name=name, description=description, organization=org['id'],
                                                      notification_type=notification_type,
                                                      notification_configuration=notification_configuration,
                                                      username=username, sender=sender, recipients=recipients,
                                                      use_tls=use_tls, host=host, use_ssl=use_ssl, password=password,
                                                      port=port, channels=channels, token=token,
                                                      account_token=account_token, from_number=from_number,
                                                      to_numbers=to_numbers, account_sid=account_sid,
                                                      subdomain=subdomain, service_key=service_key,
                                                      client_name=client_name, message_from=message_from,
                                                      api_url=api_url, color=color, rooms=rooms, notify=notify,
                                                      url=url, headers=headers, server=server, nickname=nickname,
                                                      targets=targets, create_on_missing=True)
                json_output['id'] = result['id']
            elif state == 'absent':
                result = notification_template.delete(name=name)
        except (exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update notification template, organization not found: {0}'.format(excinfo), changed=False)
        except (exc.ConnectionError, exc.BadRequest, exc.AuthError) as excinfo:
            module.fail_json(msg='Failed to update notification template: {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
