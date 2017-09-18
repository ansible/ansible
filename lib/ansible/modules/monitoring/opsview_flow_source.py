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
module: opsview_flow_source
short_description: Manages Opsview sFlow and NetFlow sources
description:
  - Manages sFlow and NetFlow sources in Opsview.
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
      - Must correspond with the host name in Opsview.
    required: true
  collector:
    description:
      - The name of the flow collector as configured in Opsview.
    required: true
  flow_type:
    description:
      - The flow protocol to be used.
    choices: [netflow, sflow]
    default: netflow
  alt_address:
    description:
      - IP address from which flow data will be received if different from the
        address stored for the host in Opsview.
"""

EXAMPLES = """\
---
- name: Create Flow Source in Opsview
  opsview_flow_source:
    username: admin
    password: initial
    endpoint: https://opsview.example.com
    state: updated
    name: cisco-uk-01
    flow_type: sflow
    alt_address: 10.0.17.24
    collector: Master Collector
"""

ARG_SPEC = {
    "username": {
        "required": True
    },
    "endpoint": {
        "required": True
    },
    "password": {
        "no_log": True
    },
    "token": {
        "no_log": True
    },
    "verify_ssl": {
        "default": True
    },
    "state": {
        "choices": [
            "updated",
            "present",
            "absent"
        ],
        "default": "updated"
    },
    "object_id": {
        "type": "int"
    },
    "name": {
        "required": True,
    },
    "collector": {
        "required": True,
    },
    "flow_type": {
        "default": "netflow",
        "choices": ["netflow", "sflow"],
    },
    "alt_address": {},
}


try:
    from pyopsview import OpsviewClient
    import six
    HAS_PYOV = True
except ImportError:
    HAS_PYOV = False


# The attribute for the client's manager
MANAGER_OBJ_TYPE = 'flowsources'
# Additional parameters used to GET existing objects
GET_PARAMS = {}
# Fields which are part of the module but are not part of the object
NON_OBJECT_FIELDS = ('username', 'password', 'token', 'endpoint', 'verify_ssl',
                     'object_id', 'state')


def hook_trans_compare(params):
    """Hook to transform the Ansible parameters prior to comparing them against
    the existing object. This does not affect the final payload used for
    actually updating the object.
    """
    if 'collector' in params and 'collector_id' not in params:
        # Get the collector by name
        collector = ovclient.config.flowcollectors\
            .find_one(name=params['collector'])

        if not collector:
            module.fail_json(msg='No flow collector exists with name \'%s\'' %
                             params['collector'])

        # Set the collector ID and unset the collector name
        params['collector_id'] = collector.get('id')

    # Ensure that the flow type is lowercased
    params['flow_type'] = params['flow_type'].lower()

    if 'host_id' not in params:
        # Get the IP address of the host by name
        host = ovclient.config.hosts.find_one(name=params['name'])
        if not host:
            module.fail_json(msg='No host exists with name \'%s\'' %
                             params['name'])

        # Set the host ID
        params['host_id'] = host.get('id')

    if 'address' not in params:
        # Set the host IP address and set the override flag if necessary
        src_addr = params.get('alt_address')
        if not src_addr:
            src_addr = host['address']

        params['ip_override'] = (src_addr != host['address'])
        params['address'] = src_addr

    for field in ('collector', 'name', 'alt_address'):
        try:
            del params[field]
        except KeyError:
            pass

    return params


def hook_trans_payload(params):
    """Hook to transform the Ansible parameters prior to creating/updating the
    object. This does not affect the comparison of objects when introspecting
    whether the object needs to be updated.
    """
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

    global ovclient
    try:
        ovclient = OpsviewClient(username=username, token=token,
                                 endpoint=endpoint, password=password, **kwds)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

    return ovclient


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

    import json
    with open('/tmp/x.json', 'a') as f:
        json.dump([old_encoded, new_encoded], f)

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
    host_manager = get_config_manager(ov_client, 'hosts')

    existing_host = find_existing_obj(
        host_manager, {'name': module.params['name']}
    )

    if existing_host and 'id' in existing_host:
        existing_obj = find_existing_obj(
            manager, {'host_id': existing_host['id']}, GET_PARAMS
        )
    else:
        existing_obj = None

    # Get the callable for achieving the desired state
    state_handler = STATE_HANDLERS[module.params['state']]
    assert callable(state_handler)

    # Should return a dictionary to be kwarg'd to exit_json
    summary = state_handler(manager, existing_obj)
    module.exit_json(**summary)


if __name__ == '__main__':
    main()
