# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2017, Opsview Ltd.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import copy
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import _load_params
from ansible.module_utils.basic import to_native
from ansible.module_utils.six import iteritems

try:
    from pyopsview import OpsviewClient
    PYOV_IMPORT_EXC = None
except ImportError as e:
    PYOV_IMPORT_EXC = (to_native(e), traceback.format_exc())

# List of keys which should never be omitted from the module parameters,
# even if they were not specified by the user. These will also, by default,
# be omitted from the final payload.
_MODULE_ONLY_FIELDS = ('username', 'password', 'token', 'endpoint',
                       'verify_ssl', 'object_id', 'state')


def new_module(argspec, always_include=_MODULE_ONLY_FIELDS):
    """Initializes a new AnsibleModule with the specified argument spec,
    removing any fields from the final params unless they've been explicitly
    specified.

    Keys in `always_include` will never be omitted.
    """
    pre_params = copy.deepcopy(_load_params())
    module = AnsibleModule(supports_check_mode=True, argument_spec=argspec)

    # dict(...) creates a shallow copy to prevent changed size during iter
    for (k, v) in iteritems(dict(module.params)):
        if k not in pre_params and v is None and k not in always_include:
            del module.params[k]

    return module


def new_opsview_client(username, endpoint, token=None, password=None, **kwds):
    """Initializes a new OpsviewClient using the parameters specified to the
    module.
    """
    if not (password or token):
        raise ValueError("'password' or 'token' must be specified")

    return OpsviewClient(username=username, endpoint=endpoint, token=token,
                         password=password, **kwds)


def get_config_manager(opsview_client, object_type):
    """Return the configuration manager for a specified object type from the
    specified OpsviewClient instance.
    """
    return getattr(opsview_client.config, object_type)


def find_existing_object(manager, identity, **kwds):
    """Return the first object matching the parameters specified in `ident`.
    """
    return manager.find_one(params=kwds, **identity)


def create_object_payload(module_params, omit_fields=_MODULE_ONLY_FIELDS,
                          payload_finalize_hook=None):
    """Returns a copy of the module parameters correctly formatted for the
    OpsviewClient's manager with any non-object fields removed.
    """
    payload = copy.deepcopy(module_params)
    for field in omit_fields:
        try:
            del payload[field]
        except KeyError:
            pass

    if payload_finalize_hook:
        return payload_finalize_hook(payload)

    return payload


def _cmp_dict(a, b):
    try:
        return any(_cmp_recursive(a[k], b[k]) for k in b)
    except (KeyError, TypeError):
        return True


def _cmp_list(a, b):
    try:
        a_s, b_s = sorted(a), sorted(b)
    except TypeError:
        return True

    try:
        return any(_cmp_recursive(a_s[i], n) for (i, n) in enumerate(b_s))
    except (IndexError, TypeError):
        return True


def _cmp_recursive(a, b):
    """Recursively compare 2 objects. Return True if data in b does
    not match data in a.
    """
    if isinstance(b, dict):
        return _cmp_dict(a, b)
    elif isinstance(b, (list, tuple)):
        return _cmp_list(a, b)

    return a != b


def object_requires_update(encoder, existing, new, pre_compare_hook=None):
    """Compares two objects and returns whether an update is required.
    The encoder is used to ensure that the objects match the required
    serialization format expected by the Opsview API.

    An optional `pre_compare_hook` can be specified which should be a callable
    returning the new object in a format which matches the one returned
    by the Opsview API, if different.
    """
    if pre_compare_hook:
        # Ensure that the original dict is not mutated by the hook function
        new = pre_compare_hook(copy.deepcopy(new))

    existing_encoded, new_encoded = encoder(existing), encoder(new)

    try:
        return _cmp_recursive(existing_encoded, new_encoded)
    except (TypeError, KeyError, AttributeError, IndexError):
        return True


def ensure_absent(manager, existing, check_mode=False):
    """Ensures that the object contained in `existing` is deleted.

    Returns a dictionary to be merged with the arguments to `module.exit_json`,
    indicating whether a change took place.
    """
    changed = (existing is not None)
    if changed and not check_mode:
        manager.delete(existing['id'])

    return {'changed': changed}


def ensure_present(manager, existing, new, check_mode=False):
    """Ensures that the object contained in `existing` is present.

    Returns a dictionary to be merged with the arguments to `module.exit_json`,
    indicating whether a change took place and the Opsview ID of the object.
    """
    changed = (existing is None)
    status = {'changed': changed}

    if changed and not check_mode:
        created = manager.create(**new)
        if 'id' in created:
            status['object_id'] = created['id']

    elif 'id' in existing:
        status['object_id'] = existing['id']

    return status


def ensure_updated(manager, existing, new, check_mode=False,
                   pre_compare_hook=None):
    """Ensures that the object is updated to contain all of the changes
    specified in the `new` object.  The object will be created if it does not
    already exist.

    Returns a dictionary to be merged with the arguments to `module.exit_json`,
    indicating whether a change took place and the Opsview ID of the object.
    """
    if existing is None:
        return ensure_present(manager, existing, new)

    changed = object_requires_update(manager._encode, existing, new,
                                     pre_compare_hook=pre_compare_hook)

    status = {'changed': changed}
    if 'id' in existing:
        status['object_id'] = existing['id']

    if changed and not check_mode:
        manager.update(existing['id'], **new)

    return status


def config_module_main(module, object_type, get_params=None,
                       payload_finalize_hook=None, pre_compare_hook=None):
    """Helper to execute a standard Opsview Configuration module and return
    a dict which can be used as the arguments to module.exit_json
    """
    opsview_client = new_opsview_client(
        username=module.params['username'],
        password=module.params['password'],
        endpoint=module.params['endpoint'],
        token=module.params['token'],
        verify=module.params['verify_ssl'],
    )

    config_manager = get_config_manager(opsview_client, object_type)
    if module.params.get('object_id'):
        identity = {'id': module.params['object_id']}
    elif module.params.get('name'):
        identity = {'name': module.params['name']}
    else:
        raise ValueError("'name' or 'object_id' must be specified")

    if get_params is None:
        get_params = {}

    existing_object = find_existing_object(config_manager, identity,
                                           **get_params)

    if module.params['state'] == 'absent':
        return ensure_absent(config_manager, existing_object,
                             check_mode=module.check_mode)

    payload = create_object_payload(
        module.params, payload_finalize_hook=payload_finalize_hook
    )

    if module.params['state'] == 'present':
        return ensure_present(config_manager, existing_object, payload,
                              check_mode=module.check_mode)

    elif module.params['state'] == 'updated':
        return ensure_updated(config_manager, existing_object, payload,
                              pre_compare_hook=pre_compare_hook,
                              check_mode=module.check_mode)

    raise ValueError("Unknown value for 'state': '%s'" % module.params['state'])
