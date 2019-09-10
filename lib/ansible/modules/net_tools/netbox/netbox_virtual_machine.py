#!/usr/bin/env python

# import module snippets
import json
import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.net_tools.netbox.netbox_utils import (
    find_ids,
    normalize_data,
    create_netbox_object,
    delete_netbox_object,
    update_netbox_object,
    VIRTUAL_MACHINE_STATUS,
    FACE_ID
)

PYNETBOX_IMP_ERR = None
try:
    import pynetbox
    HAS_PYNETBOX = True
except ImportError:
    PYNETBOX_IMP_ERR = traceback.format_exc()
    HAS_PYNETBOX = False

def main():
    '''
    Main entry point for module execution
    '''
    argument_spec = dict(
        netbox_url=dict(type="str", required=True),
        netbox_token=dict(type="str", required=True, no_log=True),
        data=dict(type="dict", required=True),
        state=dict(required=False, default='present', choices=['present', 'absent']),
        validate_certs=dict(type="bool", default=True)
    )

    global module
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    # Fail module if pynetbox is not installed
    if not HAS_PYNETBOX:
        module.fail_json(msg=missing_required_lib('pynetbox'), exception=PYNETBOX_IMP_ERR)

    # Fail if virtual_machine name is not given
    if not module.params["data"].get("name"):
        module.fail_json(msg="missing virtual_machine name")

    # Assign variables to be used with module
    app = 'virtualization'
    endpoint = 'virtual-machines'
    url = module.params["netbox_url"]
    token = module.params["netbox_token"]
    data = module.params["data"]
    state = module.params["state"]
    validate_certs = module.params["validate_certs"]

    # Attempt to create Netbox API object
    try:
       nb = pynetbox.api(url, token=token, ssl_verify=validate_certs)
    except Exception:
        module.fail_json(msg="Failed to establish connection to Netbox API")
    try:
        nb_app = getattr(nb, app)
    except AttributeError:
        module.fail_json(msg="Incorrect application specified: %s" % (app))

    nb_endpoint = getattr(nb_app, endpoint)
    norm_data = normalize_data(data)
    try:
        if 'present' in state:
            result = ensure_virtual_machine_present(nb, nb_endpoint, norm_data)
        else:
            result = ensure_virtual_machine_absent(nb_endpoint, norm_data)
        return module.exit_json(**result)
    except pynetbox.RequestError as e:
        return module.fail_json(msg=json.loads(e.error))
    except ValueError as e:
        return module.fail_json(msg=str(e))

def _find_ids(nb, data):
    if data.get("status"):
        data["status"] = VIRTUAL_MACHINE_STATUS.get(data["status"].lower())
    if data.get("face"):
        data["face"] = FACE_ID.get(data["face"].lower())
    return find_ids(nb, data)

def ensure_virtual_machine_present(nb, nb_endpoint, normalized_data):
    '''
    :returns dict(virtual_machine, msg, changed, diff): dictionary resulting of the request,
        where `virtual_machine` is the serialized virtual_machine fetched or newly created in
        Netbox
    '''
    data = _find_ids(nb, normalized_data)
    nb_virtual_machine = nb_endpoint.get(name=data["name"])
    result = {}
    if not nb_virtual_machine:
        virtual_machine, diff = create_netbox_object(nb_endpoint, data, module.check_mode)
        msg = "Virtual_Machine %s created" % (data["name"])
        changed = True
        result["diff"] = diff
    else:
        virtual_machine, diff = update_netbox_object(nb_virtual_machine, data, module.check_mode)
        if virtual_machine is False:
            module.fail_json(
                msg="Request failed, couldn't update virtual_machine: %s" % data["name"]
            )
        if diff:
            msg = "Virtual_Machine %s updated" % (data["name"])
            changed = True
            result["diff"] = diff
        else:
            msg = "Virtual_Machine %s already exists" % (data["name"])
            changed = False
    result.update({"virtual_machine": virtual_machine, "changed": changed, "msg": msg})
    return result

def ensure_virtual_machine_absent(nb_endpoint, data):
    '''
    :returns dict(msg, changed, diff)
    '''
    nb_virtual_machine = nb_endpoint.get(name=data["name"])
    result = {}
    if nb_virtual_machine:
        dummy, diff = delete_netbox_object(nb_virtual_machine, module.check_mode)
        msg = 'Virtual_Machine %s deleted' % (data["name"])
        changed = True
        result["diff"] = diff
    else:
        msg = 'Virtual_Machine %s already absent' % (data["name"])
        changed = False

    result.update({"changed": changed, "msg": msg})
    return result

if __name__ == '__main__':
    main()
