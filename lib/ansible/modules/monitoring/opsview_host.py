#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import copy
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import to_native
from ansible.module_utils.basic import _load_params

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """\
---
module: opsview_host
short_description: Manages Opsview hosts
description:
  - Manages hosts within Opsview.
version_added: '2.5'
author: Joshua Griffiths (@jpgxs)
requirements: [pyopsview]
options:
  username:
    description:
      - Username for the Opsview API.
    required: true
  endpoint:
    description:
      - Opsview API endpoint, including schema.
      - The C(/rest) suffix is optional.
    required: true
  token:
    description:
      - API token, usually returned by the C(opsview_login) module.
      - Required unless C(password) is specified.
  password:
    description:
      - Password for the Opsview API.
  verify_ssl:
    description:
      - Enable SSL verification for HTTPS endpoints.
      - Alternatively, a path to a CA can be provided.
    default: 'yes'
  state:
    description:
      - C(present) and C(updated) will create the object if it doesn't exist.
      - C(updated) will ensure that the object attributes are up to date with
        the given options.
      - C(absent) will ensure that the object is removed if it exists.
      - The object is identified by C(object_id) if specified. Otherwise, it is
        identified by C(name)
    choices: [updated, present, absent]
    default: updated
  object_id:
    description:
      - The internal ID of the object. If specified, the object will be
        found by ID instead of by C(name).
      - Usually only useful for renaming objects.
  name:
    description:
      - Unique name for the object. Will be used to identify existing objects
        unless C(object_id) is specified.
    required: true
  address:
    description:
      - Primary network address for the host.
    required: true
  host_group:
    description:
      - Host group to assign this host to.
    required: true
  monitored_by:
    description:
      - The monitoring server/cluster which will monitor this host.
    default: Master Monitoring Server
  alias:
    description:
      - Alternative name for this host as shown in the UI.
  check_attempts:
    description:
      - The number of checks before the host enters a HARD state.
    default: '2'
  check_command:
    description:
      - Name of the command used for monitoring this host.
    default: ping
  check_interval:
    description:
      - Number of seconds between each host check execution.
    default: '600'
  check_period:
    description:
      - Timeperiod within which this host will be monitored.
    default: 24x7
  description:
    description:
      - User-defined description for this host.
  enable_snmp:
    description:
      - Enable active SNMP checks for this host.
    choices: ['yes', 'no']
  encrypted_rancid_password:
    description:
      - The password for logging into the host with RANCID.
      - Must be pre-encrypted with the opsview_crypt utility.
  encrypted_snmp_community:
    description:
      - The community string to be used with SNMP 1/2c
      - Must be pre-encrypted with the opsview_crypt utility.
  encrypted_snmpv3_auth_password:
    description:
      - The authentication password to be used with SNMP v3
      - Must be pre-encrypted with the opsview_crypt utility.
  encrypted_snmpv3_priv_password:
    description:
      - The privacy password to be used with SNMP v3
      - Must be pre-encrypted with the opsview_crypt utility.
  event_handler:
    description:
      - Script to execute whenever a state change occurs for this host.
  event_handler_always_exec:
    description:
      - Execute the event handler after every check result.
    choices: ['yes', 'no']
  flap_detection_enabled:
    description:
      - Enable flapping states for this host.
    default: 'yes'
    choices: ['yes', 'no']
  hashtags:
    description:
      - List of Hashtags to be applied to this host.
  host_templates:
    description:
      - List of Host Templates to be applied to this host
  icon:
    description:
      - The name of the icon to be used for this host.
  notification_interval:
    description:
      - Number of seconds between sending re-notifications for this host when
        it is in DOWN or UNREACHABLE states.
  notification_options:
    description:
      - Comma-separated list of states to notify on.
      - C(u)=UNREACHABLE, C(d)=DOWN, C(r)=RECOVERY, C(f)=FLAPPING.
    default: u,d,r
  notification_period:
    description:
      - Timeperiod within which notifications for this host will be sent.
    default: 24x7
  other_addresses:
    description:
      - Comma-separated list of additional network addresses for this host.
  parents:
    description:
      - List of host names (as configured in Opsview) which directly determine
        the reachability of this host. For example, the network switches
        connected to this host.
  rancid_auto_enable:
    description:
      - Host has autoenable when connecting to this host with RANCID.
    choices: ['yes', 'no']
  rancid_connection_type:
    description:
      - Method used for connecting to this host with RANCID.
    choices: [ssh, telnet]
    default: ssh
  rancid_password:
    description:
      - Password for logging into the host with RANCID.
      - C(encrypted_rancid_password) is preferred.
  rancid_username:
    description:
      - Username for logging into the host with RANCID.
  rancid_vendor:
    description:
      - The host's vendor, as configured in RANCID. You may have to consult the
        UI for the full list of options.
  retry_check_interval:
    description:
      - Number of seconds between rechecks before a HARD state.
  service_checks:
    description:
      - A list of discrete Service Checks to add to the host, aside from those
        specified via Host Templates.
      - See examples for the argument format.
  snmp_community:
    description:
      - The community string to be used with SNMP 1/2c.
      - C(encrypted_snmp_community) is preferred.
  snmp_extended_throughput_data:
    description:
      - Turn on the collection of broadcast, multicast and and unicast stats.
    choices: ['yes', 'no']
  snmp_max_msg_size:
    description:
      - The maximum message size, in octets, for SNMP messages. For default,
        use 0.
    default: '0'
  snmp_port:
    description:
      - The listening SNMP port on the host.
    default: '161'
  snmp_use_getnext:
    description:
      - Use SNMP C(GetNext) instead of SNMP C(GetBulk).
    choices: ['yes', 'no']
  snmp_use_ifname:
    description:
      - Use SNMP C(ifName) instead of SNMP C(ifDescr).
    choices: ['yes', 'no']
  snmp_version:
    description:
      - The SNMP protocol version to use.
    choices: ['1', '2c', '3']
    default: '2c'
  snmpv3_auth_password:
    description:
      - The authentication password to be used with SNMP v3.
      - C(encrypted_snmpv3_auth_password) is preferred.
  snmpv3_auth_protocol:
    description:
      - The authentication protocol to be used with SNMP v3.
    choices: [md5, sha]
  snmpv3_priv_password:
    description:
      - The privacy password to be used with SNMP v3.
      - C(encrypted_snmpv3_priv_password) is preferred.
  snmpv3_priv_protocol:
    description:
      - The privacy protocol to be used with SNMP v3.
    choices: [des, aes, aes128]
  snmpv3_username:
    description:
      - The username to be used with SNMP v3.
  tidy_ifdescr_level:
    description:
      - Level of cleaning to do on the C(ifDescr) to reduce the length of
        interface names.
      - Refer to https://knowledge.opsview.com/docs/host#section-interfaces
    choices: [0, 1, 2, 3, 4, 5]
  use_rancid:
    description:
      - Enable RANCID.
    choices: ['yes', 'no']
  variables:
    description:
      - List of variables to apply to the host.
      - See the examples for the argument format.
"""

EXAMPLES = """\
---
- name: Create Host in Opsview
  opsview_host:
    username: admin
    # Providing a token from the opsview_login module is preferred to using a
    # password and is much faster.
    password: initial
    endpoint: https://opsview.example.com
    state: updated
    name: web-uk-01
    address: 127.214.167.12
    host_group: web-uk
    monitored_by: ov-cluster-uk
    alias: Web UK 01
    hashtags:
      - Production
      - Production - UK
      - Production - UK - Web
    host_templates:
      - Application - Apache2
      - OS - Opsview Agent
      - Network - Base
    icon: SYMBOL - Web Site
    parents:
      - switch-uk-01
      - switch-uk-02
    service_checks:
      # Add a Service Check
      - HTTP / SSL
      # Add a Service Check with alternative arguments
      - name: HTTPS Certificate Expiration Check
        exception: -H $HOSTADDRESS$ -C 30,14
      # Add a Service Check with a timed exception
      - name: Unix Load Average
        timed_exception:
          timeperiod: nonworkhours
          args: -H $HOSTADDRESS$ -c check_load -a '-w 5,4,3 -c 7,6,5'
      # Remove a Service Check from an applied Host Template
      - name: Unix Swap
        remove_service_check: true
    variables:
      # Arguments 1-4 can be provided as argN
      # Encrypted arguments 1-4 can be provided as encrypted_argN
      - name: DISK
        value: /
        arg1: -w 10% -c 5%
      - name: DISK
        value: /var
"""

ARG_SPEC = {
    "address": {
        "required": True
    },
    "alias": {},
    "check_attempts": {
        "default": 2,
        "type": "int"
    },
    "check_command": {
        "default": "ping"
    },
    "check_interval": {
        "default": 600,
        "type": "int"
    },
    "check_period": {
        "default": "24x7"
    },
    "description": {},
    "enable_snmp": {
        "type": "bool"
    },
    "encrypted_rancid_password": {
        "no_log": True
    },
    "encrypted_snmp_community": {
        "no_log": True
    },
    "encrypted_snmpv3_auth_password": {
        "no_log": True
    },
    "encrypted_snmpv3_priv_password": {
        "no_log": True
    },
    "endpoint": {
        "required": True
    },
    "event_handler": {},
    "event_handler_always_exec": {
        "type": "bool"
    },
    "flap_detection_enabled": {
        "default": True,
        "type": "bool"
    },
    "hashtags": {
        "type": "list"
    },
    "host_group": {
        "required": True
    },
    "host_templates": {
        "type": "list"
    },
    "icon": {},
    "monitored_by": {
        "default": "Master Monitoring Server"
    },
    "name": {
        "required": True
    },
    "notification_interval": {
        "type": "int"
    },
    "notification_options": {
        "default": "u,d,r"
    },
    "notification_period": {
        "default": "24x7"
    },
    "object_id": {
        "type": "int"
    },
    "other_addresses": {},
    "parents": {
        "type": "list"
    },
    "password": {
        "no_log": True
    },
    "rancid_auto_enable": {
        "type": "bool"
    },
    "rancid_connection_type": {
        "choices": ["ssh", "telnet"],
        "default": "ssh"
    },
    "rancid_password": {
        "no_log": True
    },
    "rancid_username": {},
    "rancid_vendor": {},
    "retry_check_interval": {
        "type": "int"
    },
    "service_checks": {
        "type": "list"
    },
    "snmp_community": {
        "no_log": True
    },
    "snmp_extended_throughput_data": {
        "type": "bool"
    },
    "snmp_max_msg_size": {
        "default": 0,
        "type": "int"
    },
    "snmp_port": {
        "default": 161,
        "type": "int"
    },
    "snmp_use_getnext": {
        "type": "bool"
    },
    "snmp_use_ifname": {
        "type": "bool"
    },
    "snmp_version": {
        "choices": [
            "1",
            "2c",
            "3"
        ],
        "default": "2c"
    },
    "snmpv3_auth_password": {
        "no_log": True
    },
    "snmpv3_auth_protocol": {
        "choices": [
            "md5",
            "sha"
        ]
    },
    "snmpv3_priv_password": {
        "no_log": True
    },
    "snmpv3_priv_protocol": {
        "choices": [
            "des",
            "aes",
            "aes128"
        ]
    },
    "snmpv3_username": {},
    "state": {
        "choices": [
            "updated",
            "present",
            "absent"
        ],
        "default": "updated"
    },
    "tidy_ifdescr_level": {
        "choices": [0, 1, 2, 3, 4, 5],
        "type": "int"
    },
    "token": {
        "no_log": True
    },
    "use_rancid": {
        "type": "bool"
    },
    "username": {
        "required": True
    },
    "variables": {
        "type": "list"
    },
    "verify_ssl": {
        "default": True
    }
}


try:
    from pyopsview import OpsviewClient
    import six
    HAS_PYOV = True
except ImportError:
    HAS_PYOV = False


# The attribute for the client's manager
MANAGER_OBJ_TYPE = 'hosts'
# Additional parameters used to GET existing objects
GET_PARAMS = {'include_encrypted': '1'}
# Fields which are part of the module but are not part of the object
NON_OBJECT_FIELDS = ('username', 'password', 'token', 'endpoint', 'verify_ssl',
                     'object_id', 'state')


def hook_trans_compare(params):
    """Hook to transform the Ansible parameters prior to comparing them against
    the existing object. This does not affect the final payload used for
    actually updating the object.
    """
    # Ensure that the notification options are duly sorted
    if params.get('notification_options'):
        option_sort_order = {'u': 0, 'd': 1, 'r': 2, 'f': 3}
        notif_opts = params['notification_options'].lower().split(',').sort(
            key=lambda x: option_sort_order.get(x, 99)
        )
        params['notification_options'] = notif_opts

    # Ensure that string value for icon gets passed as the icon name
    if isinstance(params.get('icon'), six.string_types):
        params['icon'] = {'name': params['icon']}

    return params


def hook_trans_payload(params):
    """Hook to transform the Ansible parameters prior to creating/updating the
    object. This does not affect the comparison of objects when introspecting
    whether the object needs to be updated.
    """
    # Warn if unencrypted passwords have been specified
    PASSWORD_FIELDS = ('rancid_password', 'snmp_community',
                       'snmpv3_auth_password', 'snmpv3_priv_password')

    for pwd_field in PASSWORD_FIELDS:
        if params.get(pwd_field):
            warn('Consider using \'encrypted_%s\' instead of \'%s\'.' % (
                pwd_field, pwd_field
            ))

    return hook_trans_compare(params)


def init_module():
    # Load the parameters before they are parsed to identify which parameters
    # were actually specified so that values which were omitted can be removed
    # from the payload. Makes a deep copy to be 100% that the structure doesn't
    # get changed externally
    initial_params = copy.deepcopy(_load_params())

    global module
    module = AnsibleModule(supports_check_mode=True, argument_spec=ARG_SPEC)

    # dict(...) creates a shallow copy to prevent changing size during iter
    for (key, value) in six.iteritems(dict(module.params)):
        if key not in initial_params and value is None and \
                key not in NON_OBJECT_FIELDS:
            del module.params[key]

    return module


def warn(message):
    module._warnings.append(message)
    module.log('[WARNING] ' + message)


def init_client(username, endpoint, token=None, password=None, **kwds):
    if not (password or token):
        module.fail_json(msg='\'password\' or \'token\' must be specified')

    if password and not token:
        warn('Consider using \'token\' instead of \'password\'. '
             'See the \'opsview_login\' module.')

    try:
        return OpsviewClient(username=username, token=token, endpoint=endpoint,
                             password=password, **kwds)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


def get_config_manager(client, object_type):
    try:
        return getattr(client.config, object_type)
    except AttributeError as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


def find_existing_obj(manager, ident, additional_params={}):
    try:
        return manager.find_one(params=additional_params, **ident)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


def object_payload():
    """Builds the object configuration which will be passed to the client by
    removing the module-specific fields and calling the transform hook.
    """
    init_payload = copy.deepcopy(module.params)
    for field in NON_OBJECT_FIELDS:
        try:
            del init_payload[field]
        except KeyError:
            pass

    init_payload = hook_trans_payload(init_payload)
    assert isinstance(init_payload, dict)
    return init_payload


def ensure_absent(manager, existing_obj):
    changed = (existing_obj is not None)

    if changed and not module.check_mode:
        manager.delete(existing_obj['id'])

    return {'changed': changed}


def ensure_present(manager, existing_obj):
    changed = (existing_obj is None)
    status = {'changed': changed}

    if changed and not module.check_mode:
        new_obj = object_payload()

        created_obj = manager.create(**new_obj)
        if 'id' in created_obj:
            status['object_id'] = created_obj['id']

    return status


def ensure_updated(manager, existing_obj):
    if existing_obj is None:
        return ensure_present(manager, existing_obj)

    new_obj = object_payload()

    # Compare the objects to identify whether an update is required
    changed = requires_update(manager._encode, existing_obj, new_obj)
    status = {'changed': changed, 'object_id': existing_obj['id']}

    if changed and not module.check_mode:
        manager.update(existing_obj['id'], **new_obj)

    return status


def _cmp_mapping(old, new):
    if type(old) != type(new):
        return True

    if len(old) != len(new):
        return True

    try:
        return any(cmp_recursive(old[k], new[k]) for k in six.iterkeys(new))
    except (KeyError, TypeError):
        return True


def _cmp_list(old, new):
    if type(old) != type(new):
        return True

    if len(old) != len(new):
        return True

    try:
        old_s, new_s = sorted(old), sorted(new)
    except TypeError:
        return True

    try:
        return any(cmp_recursive(old_s[i], n) for (i, n) in enumerate(new_s))
    except (IndexError, TypeError):
        return True


def cmp_recursive(obj_old, obj_new):
    if isinstance(obj_new, dict):
        return _cmp_mapping(obj_old, obj_new)
    elif isinstance(obj_new, (list, tuple)):
        return _cmp_list(obj_old, obj_new)
    else:
        return obj_old != obj_new

    return False


def requires_update(encoder, obj_old, obj_new):
    """Compares encoded copies of the existing and new objects to assertain
    whether an update is required. Only compares fields which exist in the new
    object.
    """
    assert callable(encoder)
    assert isinstance(obj_old, dict)
    assert isinstance(obj_new, dict)

    obj_new = hook_trans_compare(copy.deepcopy(obj_new))
    assert isinstance(obj_new, dict)

    try:
        old_encoded, new_encoded = encoder(obj_old), encoder(obj_new)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    assert isinstance(old_encoded, dict)
    assert isinstance(new_encoded, dict)

    try:
        return cmp_recursive(old_encoded, new_encoded)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())


STATE_HANDLERS = {
    'absent': ensure_absent,
    'present': ensure_present,
    'updated': ensure_updated,
}


def main():
    init_module()

    if not HAS_PYOV:
        module.fail_json(msg='pyopsview is required')

    ov_client = init_client(username=module.params['username'],
                            password=module.params['password'],
                            endpoint=module.params['endpoint'],
                            token=module.params['token'],
                            verify=module.params['verify_ssl'])

    manager = get_config_manager(ov_client, MANAGER_OBJ_TYPE)

    # Identify the object by ID if given, otherwise name.
    if module.params.get('object_id'):
        ident = {'id': module.params['object_id']}
    elif module.params.get('name'):
        ident = {'name': module.params['name']}

    existing_obj = find_existing_obj(manager, ident, GET_PARAMS)

    # Get the callable for achieving the desired state
    state_handler = STATE_HANDLERS[module.params['state']]
    assert callable(state_handler)

    # Should return a dictionary to be kwarg'd to exit_json
    summary = state_handler(manager, existing_obj)
    module.exit_json(**summary)


if __name__ == '__main__':
    main()
