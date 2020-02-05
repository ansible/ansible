#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Ruben Tsirunyan <rubentsirunyan@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: zabbix_valuemap
short_description: Create/update/delete Zabbix value maps
description:
    - This module allows you to create, modify and delete Zabbix value maps.
version_added: '2.10'
author:
    - "Ruben Tsirunyan (@rubentsirunyan)"
requirements:
    - "zabbix-api >= 0.5.4"
options:
    name:
        type: 'str'
        description:
            - Name of the value map.
        required: true
    state:
        type: 'str'
        description:
            - State of the value map.
            - On C(present), it will create a value map if it does not exist or update the value map if the associated data is different.
            - On C(absent), it will remove the value map if it exists.
        choices: ['present', 'absent']
        default: 'present'
    mappings:
        type: 'list'
        elements: dict
        description:
            - List of value mappings for the value map.
            - Required when I(state=present).
        suboptions:
            value:
                type: 'str'
                description: Original value.
                required: true
            map_to:
                type: 'str'
                description: Value to which the original value is mapped to.
                required: true

extends_documentation_fragment:
    - zabbix
'''

RETURN = r'''
'''

EXAMPLES = r'''
- name: Create a value map
  local_action:
    module: zabbix_valuemap
    server_url: http://zabbix.example.com
    login_user: username
    login_password: password
    name: Numbers
    mappings:
      - value: 1
        map_to: one
      - value: 2
        map_to: two
    state: present
'''


import atexit
import traceback

try:
    from zabbix_api import ZabbixAPI
    HAS_ZABBIX_API = True
except ImportError:
    ZBX_IMP_ERR = traceback.format_exc()
    HAS_ZABBIX_API = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib


def construct_parameters(**kwargs):
    """Translates data to a format suitable for Zabbix API

    Args:
        **kwargs: Arguments passed to the module.

    Returns:
        A dictionary of arguments in a format that is understandable by Zabbix API.
    """
    if kwargs['mappings'] is None:
        return dict(
            name=kwargs['name']
        )
    return dict(
        name=kwargs['name'],
        mappings=[
            dict(
                value=mapping['value'],
                newvalue=mapping['map_to']
            ) for mapping in kwargs['mappings']
        ]
    )


def check_if_valuemap_exists(module, zbx, name):
    """Checks if value map exists.

    Args:
        module: AnsibleModule object
        zbx: ZabbixAPI object
        name: Zabbix valuemap name

    Returns:
        tuple: First element is True if valuemap exists and False otherwise.
               Second element is a dictionary of valuemap object if it exists.
    """
    try:
        valuemap_list = zbx.valuemap.get({
            'output': 'extend',
            'selectMappings': 'extend',
            'filter': {'name': [name]}
        })
        if len(valuemap_list) < 1:
            return False, None
        else:
            return True, valuemap_list[0]
    except Exception as e:
        module.fail_json(msg="Failed to get ID of the valuemap '{name}': {e}".format(name=name, e=e))


def diff(existing, new):
    """Constructs the diff for Ansible's --diff option.

    Args:
        existing (dict): Existing valuemap data.
        new (dict): New valuemap data.

    Returns:
        A dictionary like {'before': existing, 'after': new}
        with filtered empty values.
    """
    before = {}
    after = {}
    for key in new:
        before[key] = existing[key]
        if new[key] is None:
            after[key] = ''
        else:
            after[key] = new[key]
    return {'before': before, 'after': after}


def get_update_params(module, zbx, existing_valuemap, **kwargs):
    """Filters only the parameters that are different and need to be updated.

    Args:
        module: AnsibleModule object.
        zbx: ZabbixAPI object.
        existing_valuemap (dict): Existing valuemap.
        **kwargs: Parameters for the new valuemap.

    Returns:
        A tuple where the first element is a dictionary of parameters
        that need to be updated and the second one is a dictionary
        returned by diff() function with
        existing valuemap data and new params passed to it.
    """

    params_to_update = {}
    if sorted(existing_valuemap['mappings'], key=lambda k: k['value']) != sorted(kwargs['mappings'], key=lambda k: k['value']):
        params_to_update['mappings'] = kwargs['mappings']
    return params_to_update, diff(existing_valuemap, kwargs)


def delete_valuemap(module, zbx, valuemap_id):
    try:
        return zbx.valuemap.delete([valuemap_id])
    except Exception as e:
        module.fail_json(msg="Failed to delete valuemap '{_id}': {e}".format(_id=valuemap_id, e=e))


def update_valuemap(module, zbx, **kwargs):
    try:
        valuemap_id = zbx.valuemap.update(kwargs)
    except Exception as e:
        module.fail_json(msg="Failed to update valuemap '{_id}': {e}".format(_id=kwargs['valuemapid'], e=e))


def create_valuemap(module, zbx, **kwargs):
    try:
        valuemap_id = zbx.valuemap.create(kwargs)
    except Exception as e:
        module.fail_json(msg="Failed to create valuemap '{name}': {e}".format(name=kwargs['description'], e=e))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
            name=dict(type='str', required=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            mappings=dict(
                type='list',
                elements='dict',
                options=dict(
                    value=dict(type='str', required=True),
                    map_to=dict(type='str', required=True)
                )
            ),
            timeout=dict(type='int', default=10)
        ),
        supports_check_mode=True,
        required_if=[
            ['state', 'present', ['mappings']],
        ]
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg=missing_required_lib('zabbix-api', url='https://pypi.org/project/zabbix-api/'), exception=ZBX_IMP_ERR)

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    name = module.params['name']
    state = module.params['state']
    mappings = module.params['mappings']
    timeout = module.params['timeout']

    zbx = None
    # login to zabbix
    try:
        zbx = ZabbixAPI(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password,
                        validate_certs=validate_certs)
        zbx.login(login_user, login_password)
        atexit.register(zbx.logout)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    valuemap_exists, valuemap_object = check_if_valuemap_exists(module, zbx, name)

    parameters = construct_parameters(
        name=name,
        mappings=mappings
    )

    if valuemap_exists:
        valuemap_id = valuemap_object['valuemapid']
        if state == 'absent':
            if module.check_mode:
                module.exit_json(
                    changed=True,
                    msg="Value map would have been deleted. Name: {name}, ID: {_id}".format(
                        name=name,
                        _id=valuemap_id
                    )
                )
            valuemap_id = delete_valuemap(module, zbx, valuemap_id)
            module.exit_json(
                changed=True,
                msg="Value map deleted. Name: {name}, ID: {_id}".format(
                    name=name,
                    _id=valuemap_id
                )
            )
        else:
            params_to_update, diff = get_update_params(module, zbx, valuemap_object, **parameters)
            if params_to_update == {}:
                module.exit_json(
                    changed=False,
                    msg="Value map is up to date: {name}".format(name=name)
                )
            else:
                if module.check_mode:
                    module.exit_json(
                        changed=True,
                        diff=diff,
                        msg="Value map would have been updated. Name: {name}, ID: {_id}".format(
                            name=name,
                            _id=valuemap_id
                        )
                    )
                valuemap_id = update_valuemap(
                    module, zbx,
                    valuemapid=valuemap_id,
                    **params_to_update
                )
                module.exit_json(
                    changed=True,
                    diff=diff,
                    msg="Value map updated. Name: {name}, ID: {_id}".format(
                        name=name,
                        _id=valuemap_id
                    )
                )
    else:
        if state == "absent":
            module.exit_json(changed=False)
        else:
            if module.check_mode:
                module.exit_json(
                    changed=True,
                    msg="Value map would have been created. Name: {name}, ID: {_id}".format(
                        name=name,
                        _id=valuemap_id
                    )
                )
            valuemap_id = create_valuemap(module, zbx, **parameters)
            module.exit_json(
                changed=True,
                msg="Value map created: {name}, ID: {_id}".format(
                    name=name,
                    _id=valuemap_id
                )
            )


if __name__ == '__main__':
    main()
