#!/usr/bin/python

'''LogicMonitor Ansible module for managing device groups
   Copyright (C) 2015  LogicMonitor

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software Foundation,
   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA'''


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

RETURN = '''
---
success:
    description: flag indicating that execution was successful
    returned: success
    type: boolean
    sample: True
id:
    description: the id of the device
    returned: success
    type: str
    sample: 1
name:
    description: the host name or IP address of the device
    returned: success
    type: str
    sample: server.logicmonitor.com
display_name:
    description: the display name of the device
    returned: success
    type: str
    sample: my web server
description:
    description: the device description
    returned: success
    type: str
    sample: this is my web server
disable_alerting:
    description: indicates whether alerting is disabled (true) or enabled (false) for this device
    returned: success
    type: boolean
    sample: False
current_collector_id:
    description:
    returned: success
    type: str
    sample: 1
custom_properties:
    description: custom properties for the device
    returned: success
    type: list
    sample: [ { "name" : "location", "value" : "Santa Barbara,CA"}, { "name" : "snmp.version", "value" : "v3" } ]
system_properties:
    description: system properties for the device
    returned: success
    type: list
    sample: [ { "name" : "system.collectorplatform", "value" : "linux"}, { "name" : "system.devicetype", "value" : "0" } ]
...
'''


DOCUMENTATION = '''
---
module: logicmonitor_device
short_description: Manage LogicMonitor devices
description:
  - LogicMonitor is a hosted, full-stack, infrastructure monitoring platform.
  - This module manages devices within your LogicMonitor account.
version_added: '2.4'
author: [Jeff Wozniak (@woz5999)]
notes:
  - You must have an existing LogicMonitor account for this module to function.
  - The specified token Access Id and Access Key must have sufficient permission to perform the requested actions
requirements: ['An existing LogicMonitor account', 'Linux']
options:
  state:
    description:
      - Whether to ensure that the resource is present or absent
    required: true
    default: null
    choices: ['present', 'absent']
  account:
    description:
      - LogicMonitor account name
    required: true
    default: null
  access_id:
    description:
      - LogicMonitor API Token Access ID
    required: true
    default: null
  access_key:
    description:
      - LogicMonitor API Token Access Key
    required: true
    default: null
  preferred_collector_id:
    description:
      - The Id of the preferred collector assigned to monitor the device
    required: true
    default: null
  name:
    description:
      - The host name or IP address of the device
    required: false
    default: hostname -f
  display_name:
    description:
      - The display name of the device
    required: false
    default: hostname -f
  description:
    description:
      - The device description
    required: false
    default: ''
  properties:
    description:
      - A dictionary of properties associated with this device group
    required: false
    default: {}
  groups:
    description:
        - A list of groups that the device should be a member of
    required: false
    default: []
  disable_alerting:
    description:
      - Indicates whether alerting is disabled (true) or enabled (false) for this device
    required: false
    default: false
    type: bool
...
'''

EXAMPLES = '''
# creating a device
---
- hosts: all
  vars:
    account: myaccount
    access_id: access_id
    access_key: access_key
  tasks:
    - logicmonitor_device:
        account: '{{ account }}'
        access_id: '{{ access_id }}'
        access_key: '{{ access_key }}'
        state: present
        description: Device added by Ansible
        name: server1.test.net
        display_name: server1
        groups: /AnsibleDevices/WebServers,/Production
        preferred_collector_id: 1
        properties:
          snmp.community: commstring
          environment: production

# removing a device
---
- hosts: all
  vars:
    account: myaccount
    access_id: access_id
    access_key: access_key
  tasks:
    - logicmonitor_device:
        account: '{{ account }}'
        access_id: '{{ access_id }}'
        access_key: '{{ access_key }}'
        name: server1.test.net
        preferred_collector_id: 1
        state: absent
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import BOOLEANS
import socket
import types

try:
    import logicmonitor
    from logicmonitor.rest import ApiException
    HAS_LM = True
except ImportError:
    HAS_LM = False

HAS_LIB_JSON = True
try:
    import json
    # Detect the python-json library which is incompatible
    # Look for simplejson if that's the case
    try:
        if (
            not isinstance(json.loads, types.FunctionType) or
            not isinstance(json.dumps, types.FunctionType)
        ):
            raise ImportError
    except AttributeError:
        raise ImportError
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        print(
            '\n{"msg": "Error: ansible requires the stdlib json or ' +
            'simplejson module, neither was found!", "failed": true}'
        )
        HAS_LIB_JSON = False
    except SyntaxError:
        print(
            '\n{"msg": "SyntaxError: probably due to installed simplejson ' +
            'being for a different python version", "failed": true}'
        )
        HAS_LIB_JSON = False


def get_client(params, module):
    # Configure API key authorization: LMv1

    logicmonitor.configuration.host = logicmonitor.configuration.host.replace(
        'localhost',
        params['account'] + '.logicmonitor.com'
    )
    logicmonitor.configuration.api_key['id'] = params['access_id']
    logicmonitor.configuration.api_key['Authorization'] = params['access_key']

    # create an instance of the API class
    return logicmonitor.DefaultApi(logicmonitor.ApiClient())


def get_obj(client, params, module):
    try:
        obj = logicmonitor.RestDevice(
            custom_properties=format_custom_properties(params['properties']),
            description=params['description'],
            disable_alerting=bool(params['disable_alerting']),
            preferred_collector_id=params['preferred_collector_id'],
            scan_config_id=0
        )

        if 'name' in params and params['name']:
            obj.name = params['name']
        else:
            # if name not specified, default to fqdn
            obj.name = socket.getfqdn()

        if 'display_name' in params and params['display_name']:
            obj.display_name = params['display_name']
        else:
            # if display name not set, default to host name
            obj.display_name = obj.name

        # find and format device group ids into comma-delimited string
        if 'groups' in params and len(params['groups']) > 0:
            all_found = True
            device_group_ids = []
            unknown_device_groups = []

            for group in params['groups']:
                device_group = find_device_group(client, group, module)
                if device_group is not None:
                    device_group_ids.append(str(device_group.id))
                else:
                    all_found = False
                    unknown_device_groups.append(group)

            if all_found is True:
                obj.host_group_ids = ','.join(device_group_ids)
            else:
                module.fail_json(msg='Unknown device group(s) ' +
                                 ','.join(unknown_device_groups),
                                 change=False,
                                 failed=True)
        else:
            # default to root device group
            obj.host_group_ids = '1'
        return obj
    except Exception as e:
        err = 'Exception creating object: ' + str(e) + '\n'
        module.fail_json(msg=err, changed=False, failed=True)


def set_update_fields(obj_1, obj_2):
    # set immutable fields for updating object
    obj_1.id = obj_2.id
    obj_1.name = obj_2.name
    return obj_1


def compare_obj(obj_1, obj_2):
    return (
        compare_objects(obj_1, obj_2) and
        compare_props(obj_1.custom_properties, obj_2.custom_properties)
    )


def compare_objects(group_1, group_2):
    exclude_keys = {
        'custom_properties': 'custom_properties'
    }

    dict_1 = {}
    dict_2 = {}
    # determine if the compare objects are dicts or classes
    if isinstance(group_1, dict):
        dict_1 = group_1
    else:
        dict_1 = group_1.to_dict()

    if isinstance(group_2, dict):
        dict_2 = group_2
    else:
        dict_2 = group_2.to_dict()

    for k in dict_1:
        if k in exclude_keys:
            continue
        if dict_1[k] is not None and k in dict_2 and dict_2[k] is not None:
            if str(dict_1[k]) != str(dict_2[k]):
                return False
    for k in dict_2:
        if k in exclude_keys:
            continue
        if dict_2[k] is not None and k in dict_1 and dict_1[k] is not None:
            if str(dict_1[k]) != str(dict_2[k]):
                return False
    return True


def compare_props(props_1, props_2):
    # system properties are immutable and automatically applied
    # ignore them when doing compare
    p_1 = remove_system_props(props_1)
    p_2 = remove_system_props(props_2)
    return compare_objects(p_1, p_2)


def remove_system_props(props):
    ret = {}
    for item in props:
        name = ''
        value = ''

        if isinstance(item, 'dict'):
            if item['name'].startswith('system'):
                name = item['name']
                value = item['value']
        elif isinstance(item, logicmonitor.NameAndValue):
            name = item.name
            value = item.value
        ret[name] = value
    return ret


def find_device_group(client, full_path, module):
    module.debug('finding device group ' + str(full_path))
    # trim leading / if it exists
    full_path = full_path.lstrip('/')

    device_groups = None
    try:
        device_groups = client.get_device_group_list()
    except ApiException as e:
        err = 'Exception when calling get_device_group_list: ' + str(e) + '\n'
        module.fail_json(msg=err, changed=False, failed=True)

    if device_groups.status != 200:
        err = (
            'Error ' + str(device_groups.status) +
            ' calling get_device_group_list: ' + str(e) + '\n'
        )
        module.fail_json(msg=err, changed=False, failed=True)

    # look for matching device group
    for item in device_groups.data.items:
        if item.full_path == full_path:
            return item
    return None


def find_obj(client, params, module):
    if 'display_name' in params and params['display_name']:
        module.debug('finding device ' + str(params['display_name']))
    elif 'name' in params and params['name']:
        module.debug('finding device ' + str(params['name']))

    devices = None
    try:
        devices = client.get_device_list()
    except ApiException as e:
        err = 'Exception when calling get_device_list: ' + str(e) + '\n'
        module.fail_json(msg=err, changed=False, failed=True)

    if devices.status != 200:
        err = (
            'Error ' + str(devices.status) +
            ' calling get_device_list: ' + str(e) + '\n'
        )
        module.fail_json(msg=err, changed=False, failed=True)

    # display name is globally unique, so prefer that match
    if 'display_name' in params and params['display_name']:
        for item in devices.data.items:
            if item.display_name == params['display_name']:
                return item

    if 'name' not in params and params['name']:
        return None

    for item in devices.data.items:
        if item.name == params['name']:
            collector = find_collector(
                client,
                params['preferred_collector_id'],
                module
            )
            if collector is None:
                return None

            if item.current_collector_id == collector.id:
                return item
    return None


def find_collector(client, id, module):
    module.debug('finding collector ' + str(id))

    collector = None
    try:
        collector = client.get_collector_by_id(id)
    except ApiException as e:
        err = 'Exception when calling get_collector_by_id: ' + str(e) + '\n'
        module.fail_json(msg=err, changed=False, failed=True)

    if collector.status != 200:
        err = (
            'Error ' + str(collector.status) +
            ' calling get_collector_by_id: ' + str(e) + '\n'
        )
        module.fail_json(msg=err, changed=False, failed=True)
    return collector


def add_obj(client, device, module):
    module.debug('adding device ' + device.name)

    resp = None
    try:
        resp = client.add_device(device)
    except ApiException as e:
        err = 'Exception when calling add_device: ' + str(e) + '\n'
        module.fail_json(msg=err, changed=False, failed=True)

    if resp.status != 200:
        if resp.status == 600:
            # Status 600: The record already exists
            return device

        err = (
            'Status ' + str(resp.status) + ' calling add_device\n' +
            str(resp.errmsg)
        )
        module.fail_json(msg=err, changed=False, failed=True)
    return resp.data


def delete_obj(client, device, module):
    module.debug('deleting device ' + str(device.name))
    resp = None
    try:
        resp = client.delete_device(str(device.id))
    except ApiException as e:
        err = (
            'Exception when calling delete_device: ' + str(e) +
            '\n'
        )
        module.fail_json(msg=err, changed=False, failed=True)

    if resp.status != 200:
        err = (
            'Status ' + str(resp.status) +
            ' calling delete_device\n' +
            str(resp.errmsg)
        )
        module.fail_json(msg=err, changed=False, failed=True)
    return resp


def update_obj(client, device, module):
    module.debug('updating device ' + str(device.name))

    resp = None
    try:
        resp = client.update_device(device, str(device.id))
    except ApiException as e:
        err = (
            'Exception when calling update_device: ' + str(e) +
            '\n'
        )
        module.fail_json(msg=err, changed=False, failed=True)

    if resp.status != 200:
        err = (
            'Status ' + str(resp.status) +
            ' calling update_device\n' +
            str(resp.errmsg)
        )
        module.fail_json(msg=err, changed=False, failed=True)
    return resp


def format_custom_properties(properties):
    ret = []

    for k in properties:
        ret.append({
            'name': str(k),
            'value': str(properties[k])
        })
    return ret


def succeed(changed, obj, module):
    return module.exit_json(
        changed=changed,
        success=True,
        id=str(obj.id),
        name=obj.name,
        display_name=obj.display_name,
        description=obj.description,
        disable_alerting=obj.disable_alerting,
        current_collector_id=str(obj.current_collector_id),
        custom_properties=obj.custom_properties,
        system_properties=obj.system_properties
    )


def ensure_present(client, params, module):
    obj = get_obj(client, params, module)

    found_obj = find_obj(client, params, module)
    if found_obj is None:
        if not module.check_mode:
            add_obj(client, obj, module)
        succeed(True, obj, module)
    if not compare_obj(obj, found_obj):
        if not module.check_mode:
            # set known fields required for updating object
            obj = set_update_fields(obj, found_obj)
            update_obj(client, obj, module)
        succeed(True, obj, module)
    succeed(False, obj, module)


def ensure_absent(client, params, module):
    obj = find_obj(client, params, module)
    if obj is None:
        succeed(False, obj, module)
    else:
        if not module.check_mode:
            delete_obj(client, obj, module)
        succeed(True, obj, module)


def selector(module):
    '''Figure out which object and which actions
    to take given the right parameters'''

    client = get_client(module.params, module)

    if module.params['state'].lower() == 'present':
        ensure_present(client, module.params, module)
    elif module.params['state'].lower() == 'absent':
        ensure_absent(client, module.params, module)
    else:
        errmsg = ('Error: Unexpected state \'' + module.params['state'] +
                  '\' was specified.')
        module.fail_json(msg=errmsg)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=True, default=None, choices=[
                'absent',
                'present'
            ]),
            account=dict(required=True, default=None),
            access_id=dict(required=True, default=None),
            access_key=dict(required=True, default=None, no_log=True),

            description=dict(required=False, default=''),
            disable_alerting=dict(
                required=False,
                default='false',
                type='bool',
                choices=BOOLEANS
            ),
            display_name=dict(required=False, default=None),
            groups=dict(required=False, default=[], type='list'),
            name=dict(required=False, default=None),
            preferred_collector_id=dict(required=True, default=None),
            properties=dict(required=False, default={}, type='dict')
        ),
        supports_check_mode=True
    )

    if HAS_LIB_JSON is not True:
        module.fail_json(msg='Unable to load JSON library')
    if not HAS_LM:
        module.fail_json(msg='logicmonitor required for this module')

    selector(module)


if __name__ == '__main__':
    main()
