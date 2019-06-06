#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: zabbix_mediatype
short_description: Create/Update/Delete Zabbix media types
description:
    - This module allows you to create, modify and delete Zabbix media types.
version_added: "2.9"
author:
    - Ruben Tsirunyan (@rubentsirunyan)
requirements:
    - zabbix-api

options:
    name:
        type: 'str'
        description:
            - Name of the media type.
        required: true
    state:
        type: 'str'
        description:
            - Desired state of the mediatype.
            - On C(present), it will create a medatype if it does not exist or update the mediatype if the associated data is different.
            - On C(absent), it will remove the mediatype if it exists.
        choices:
            - present
            - absent
        default: 'present'
        required: true
    type:
        type: 'str'
        description:
            - Type of the media type.
        choices:
            - email
            - script
            - sms
            - jabber
            - ez_texting
        required: true
    status:
        type: 'str'
        description:
            - Whether the media type is enabled or no.
        choices:
            - enabled
            - disabled
        default: 'enabled'
    max_sessions:
        type: 'int'
        description:
            - The maximum number of alerts that can be processed in parallel.
            - Possible range is 0-100
        default: 1
    max_attempts:
        type: 'int'
        description:
            - The maximum number of attempts to send an alert.
            - Possible range is 0-10
        default: 3
    attempt_interval:
        type: 'int'
        description:
            - The interval between retry attempts.
            - Possible range is 0-60
        default: 10
    script_name:
        type: 'str'
        description:
            - The name of the executed script.
            - Required when I(type=script).
    script_params:
        type: 'list'
        description:
            - List of script parameters.
            - Required when I(type=script).
    gsm_modem:
        type: 'str'
        description:
            - Serial device name of the gsm modem.
            - Required when i(type=sms).
    username:
        type: 'str'
        description:
            - Username or Jabber identifier.
            - Required when I(type=jabber) or I(type=ez_texting).
    password:
        type: 'str'
        description:
            - Authentication password.
            - Required when I(type=jabber) or I(type=ez_texting).
    smtp_server:
        type: 'str'
        description:
            - SMTP server host.
            - Required when i(type=email).
    smtp_server_port:
        type: 'int'
        description:
            - SMTP server port.
    smtp_helo:
        type: 'str'
        description:
            - SMTP HELO.
            - Required when i(type=email).
    smtp_email:
        type: 'str'
        description:
            - Email address from which notifications will be sent.
            - Required when i(type=email).
    # TODO: Check not documented parameters for Email types
    message_text_limit:
        type: 'str'
        description:
            - The message text limit.
            - Required when I(type=ez_texting).
            - 160 characters for USA and 136 characters for Canada.
        choices:
            - USA
            - Canada
extends_documentation_fragment:
    - zabbix

'''

EXAMPLES = '''
'''

try:
    from zabbix_api import ZabbixAPI, ZabbixAPISubClass

    HAS_ZABBIX_API = True
except ImportError:
    HAS_ZABBIX_API = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import container_to_bytes


def to_numeric_value(value, strs):
    try:
        return str(strs[value])
    except Exception as e:
        return None


def validate_params(module, params):
    for param in params:
        if module.params[param[0]] == param[1]:
            if None in [module.params[i] for i in param[2]]:
                module.fail_json(msg="Following arguments are required when {} is {}: {}".format(param[0], param[1], ', '.join(param[2])))


def construct_parameters(**kwargs):
    """
    Returns a dict of parameters only related to the specified `transport_type`
    """
    if kwargs['transport_type'] == 'email':
        return dict(
            description=kwargs['name'],
            status=to_numeric_value(kwargs['status'],
                                    {'enabled': 0,
                                     'disabled': 1}),
            type=to_numeric_value(kwargs['transport_type'],
                                  {'email': 0,
                                   'script': 1,
                                   'sms': 2,
                                   'jabber': 3,
                                   'ez_texting': 100}),
            maxsessions=str(kwargs['max_sessions']),
            maxattempts=str(kwargs['max_attempts']),
            attempt_interval=str(kwargs['attempt_interval']),
            smtp_server=kwargs['smtp_server'],
            smtp_port=str(kwargs['smtp_server_port']),
            smtp_helo=kwargs['smtp_helo'],
            smtp_email=kwargs['smtp_email'],
            smtp_security=to_numeric_value(str(kwargs['smtp_security']),
                                           {'None': 0,
                                            'STARTTLS': 1,
                                            'SSL/TLS': 2}),
            smtp_authentication=to_numeric_value(str(kwargs['smtp_authentication']),
                                                 {'False': 0,
                                                  'True': 1}),
            smtp_verify_host=to_numeric_value(str(kwargs['smtp_verify_host']),
                                              {'False': 0,
                                               'True': 1}),
            smtp_verify_peer=to_numeric_value(str(kwargs['smtp_verify_peer']),
                                              {'False': 0,
                                               'True': 1}),
            username=kwargs['username'],
            passwd=kwargs['password']
        )

    elif kwargs['transport_type'] == 'script':
        if kwargs['script_params'] is None:
            _script_params = ''  # ZBX-15706
        else:
            _script_params = '\n'.join(str(i) for i in kwargs['script_params']) + '\n'
        return dict(
            description=kwargs['name'],
            status=to_numeric_value(kwargs['status'],
                                    {'enabled': 0,
                                     'disabled': 1}),
            type=to_numeric_value(kwargs['transport_type'],
                                  {'email': 0,
                                   'script': 1,
                                   'sms': 2,
                                   'jabber': 3,
                                   'ez_texting': 100}),
            maxsessions=str(kwargs['max_sessions']),
            maxattempts=str(kwargs['max_attempts']),
            attempt_interval=str(kwargs['attempt_interval']),
            exec_path=kwargs['script_name'],
            exec_params=_script_params
        )
    elif kwargs['transport_type'] == 'sms':
        return dict(
            description=kwargs['name'],
            status=to_numeric_value(kwargs['status'],
                                    {'enabled': 0,
                                     'disabled': 1}),
            type=to_numeric_value(kwargs['transport_type'],
                                  {'email': 0,
                                   'script': 1,
                                   'sms': 2,
                                   'jabber': 3,
                                   'ez_texting': 100}),
            maxsessions=str(kwargs['max_sessions']),
            maxattempts=str(kwargs['max_attempts']),
            attempt_interval=str(kwargs['attempt_interval']),
            gsm_modem=kwargs['gsm_modem']
        )
    elif kwargs['transport_type'] == 'jabber':
        return dict(
            description=kwargs['name'],
            status=to_numeric_value(kwargs['status'],
                                    {'enabled': 0,
                                     'disabled': 1}),
            type=to_numeric_value(kwargs['transport_type'],
                                  {'email': 0,
                                   'script': 1,
                                   'sms': 2,
                                   'jabber': 3,
                                   'ez_texting': 100}),
            maxsessions=str(kwargs['max_sessions']),
            maxattempts=str(kwargs['max_attempts']),
            attempt_interval=str(kwargs['attempt_interval']),
            username=kwargs['username'],
            passwd=kwargs['password']
        )
    elif kwargs['transport_type'] == 'ez_texting':
        return dict(
            description=kwargs['name'],
            status=to_numeric_value(kwargs['status'],
                                    {'enabled': 0,
                                     'disabled': 1}),
            type=to_numeric_value(kwargs['transport_type'],
                                  {'email': 0,
                                   'script': 1,
                                   'sms': 2,
                                   'jabber': 3,
                                   'ez_texting': 100}),
            maxsessions=str(kwargs['max_sessions']),
            maxattempts=str(kwargs['max_attempts']),
            attempt_interval=str(kwargs['attempt_interval']),
            username=kwargs['username'],
            passwd=kwargs['password'],
            exec_path=to_numeric_value(kwargs['message_text_limit'],
                                       {'USA': 0,
                                        'Canada': 1}),
        )


def check_if_mediatype_exists(module, zbx, name):
    """
    Check if mediatype exists and return a typle like (bool('exists or not'), id or None)
    """
    try:
        mediatype_list = zbx.mediatype.get({
            'output': 'extend',
            'filter': {'description': [name]}
        })
        if len(mediatype_list) < 1:
            return False, None
        else:
            return True, mediatype_list[0]['mediatypeid']
    except Exception as e:
        module.fail_json(msg="Failed to get ID of the mediatype '{}': {}".format(name, e))


def difference(module, zbx, mediatype_id, **kwargs):
    existing_mediatype = container_to_bytes(zbx.mediatype.get({
        'output': 'extend',
        'mediatypeids': [mediatype_id]
    })[0])
    if existing_mediatype['type'] != kwargs['type']:
        return kwargs
    else:
        _diff = {}
        for key in kwargs:
            if (not (kwargs[key] is None and existing_mediatype[key] == '')) and kwargs[key] != existing_mediatype[key]:
                _diff[key] = kwargs[key]
        return _diff


def delete_mediatype(module, zbx, mediatype_id):
    try:
        return zbx.mediatype.delete([mediatype_id])
    except Exception as e:
        module.fail_json(msg="Failed to delete mediatype '{}': {}".format(mediatype_id, e))


def update_mediatype(module, zbx, **kwargs):
    try:
        pass
        mediatype_id = zbx.mediatype.update(kwargs)
    except Exception as e:
        module.fail_json(msg="Failed to update mediatype '{}': {}".format(kwargs['mediatypeid'], e))


def create_mediatype(module, zbx, **kwargs):
    try:
        mediatype_id = zbx.mediatype.create(kwargs)
    except Exception as e:
        module.fail_json(msg="Failed to create mediatype '{}': {}".format(kwargs['description'], e))


def main():
    argument_spec = dict(
        server_url=dict(type='str', required=True, aliases=['url']),
        login_user=dict(type='str', required=True),
        login_password=dict(type='str', required=True, no_log=True),
        http_login_user=dict(type='str', required=False, default=None),
        http_login_password=dict(type='str', required=False, default=None, no_log=True),
        validate_certs=dict(type='bool', required=False, default=True), timeout=dict(type='int', default=10),
        name=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        type=dict(type='str', choices=['email', 'script', 'sms', 'jabber', 'ez_texting'], required=True),
        status=dict(type='str', default='enabled', choices=['enabled', 'disabled'], required=False),
        max_sessions=dict(type='int', default=1, choices=range(100), required=False),
        max_attempts=dict(type='int', default=3, choices=range(10), required=False),
        attempt_interval=dict(type='int', default=10, choices=range(60), required=False),
        # Script
        script_name=dict(type='str', required=False),
        script_params=dict(type='list', required=False),
        # SMS
        gsm_modem=dict(type='str', required=False),
        # Jabber
        username=dict(type='str', required=False),
        password=dict(type='str', required=False),
        # Email
        smtp_server=dict(type='str', default='localhost', required=False),
        smtp_server_port=dict(type='int', default=25, required=False),
        smtp_helo=dict(type='str', default='localhost', required=False),
        smtp_email=dict(type='str', required=False),
        smtp_security=dict(type='str', required=False),
        smtp_authentication=dict(type='bool', default=False, required=False),
        smtp_verify_host=dict(type='bool', default=False, required=False),
        smtp_verify_peer=dict(type='bool', default=False, required=False),
        # EZ Text
        message_text_limit=dict(type='str', required=False, choices=['USA', 'Canada'])
    )

    required_params = [
        ['type', 'email', ['smtp_email']],
        ['type', 'script', ['script_name']],
        ['type', 'sms', ['gsm_modem']],
        ['type', 'jabber', ['username', 'password']],
        ['type', 'ez_texting', ['username', 'password', 'message_text_limit']],
        ['smtp_authentication', True, ['username', 'password']]
    ]

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    if module.params['state'] == 'present':
        validate_params(module, required_params)

    if not HAS_ZABBIX_API:
        module.fail_json(msg="Missing required zabbix-api module (check docs or install with: pip install zabbix-api)")

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    state = module.params['state']
    timeout = module.params['timeout']
    name = module.params['name']
    transport_type = module.params['type']
    status = module.params['status']
    max_sessions = module.params['max_sessions']
    max_attempts = module.params['max_attempts']
    attempt_interval = module.params['attempt_interval']
    # Script
    script_name = module.params['script_name']
    script_params = module.params['script_params']
    # SMS
    gsm_modem = module.params['gsm_modem']
    # Jabber
    username = module.params['username']
    password = module.params['password']
    # Email
    smtp_server = module.params['smtp_server']
    smtp_server_port = module.params['smtp_server_port']
    smtp_helo = module.params['smtp_helo']
    smtp_email = module.params['smtp_email']
    smtp_security = module.params['smtp_security']
    smtp_authentication = module.params['smtp_authentication']
    smtp_verify_host = module.params['smtp_verify_host']
    smtp_verify_peer = module.params['smtp_verify_peer']
    # EZ Text
    message_text_limit = module.params['message_text_limit']

    zbx = None

    # login to zabbix
    try:
        zbx = ZabbixAPI(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password,
                        validate_certs=validate_certs)
        zbx.login(login_user, login_password)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    mediatype_exists, mediatype_id = check_if_mediatype_exists(module, zbx, name)

    parameters = construct_parameters(
        name=name,
        transport_type=transport_type,
        status=status,
        max_sessions=max_sessions,
        max_attempts=max_attempts,
        attempt_interval=attempt_interval,
        script_name=script_name,
        script_params=script_params,
        gsm_modem=gsm_modem,
        username=username,
        password=password,
        smtp_server=smtp_server,
        smtp_server_port=smtp_server_port,
        smtp_helo=smtp_helo,
        smtp_email=smtp_email,
        smtp_security=smtp_security,
        smtp_authentication=smtp_authentication,
        smtp_verify_host=smtp_verify_host,
        smtp_verify_peer=smtp_verify_peer,
        message_text_limit=message_text_limit
    )

    if mediatype_exists:
        # TODO: Check mode!!!
        if state == 'absent':
            mediatype_id = delete_mediatype(module, zbx, mediatype_id)
            module.exit_json(changed=True, msg="Mediatype deleted. Name: {}, ID: {}".format(name, mediatype_id))
        else:
            diff = difference(module, zbx, mediatype_id, **parameters)
            if diff == {}:
                module.exit_json(changed=False, msg="Mediatype is up to date: {}".format(name))
            else:
                mediatype_id = update_mediatype(
                    module, zbx,
                    mediatypeid=mediatype_id,
                    **diff
                )
                module.exit_json(changed=True, msg="Mediatype updated. Name: {}, ID: {}".format(name, mediatype_id))
    else:
        if state == "absent":
            module.exit_json(changed=False)
        else:
            mediatype_id = create_mediatype(module, zbx, **parameters)
            module.exit_json(changed=True, msg="Mediatype created: {}, ID: {}".format(name, mediatype_id))


if __name__ == '__main__':
    main()
