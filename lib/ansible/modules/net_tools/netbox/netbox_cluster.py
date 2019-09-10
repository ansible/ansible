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

    # Fail if cluster name is not given
    if not module.params["data"].get("name"):
        module.fail_json(msg="missing cluster name")

    # Assign variables to be used with module
    app = 'virtualization'
    endpoint = 'clusters'
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
            result = ensure_cluster_present(nb, nb_endpoint, norm_data)
        else:
            result = ensure_cluster_absent(nb_endpoint, norm_data)
        return module.exit_json(**result)
    except pynetbox.RequestError as e:
        return module.fail_json(msg=json.loads(e.error))
    except ValueError as e:
        return module.fail_json(msg=str(e))

def _find_ids(nb, data):
    if data.get("status"):
        data["status"] = CLUSTER_STATUS.get(data["status"].lower())
    if data.get("face"):
        data["face"] = FACE_ID.get(data["face"].lower())
    return find_ids(nb, data)

def ensure_cluster_present(nb, nb_endpoint, normalized_data):
    '''
    :returns dict(cluster, msg, changed, diff): dictionary resulting of the request,
        where `cluster` is the serialized cluster fetched or newly created in
        Netbox
    '''
    data = _find_ids(nb, normalized_data)
    nb_cluster = nb_endpoint.get(name=data["name"])
    result = {}
    if not nb_cluster:
        cluster, diff = create_netbox_object(nb_endpoint, data, module.check_mode)
        msg = "Cluster %s created" % (data["name"])
        changed = True
        result["diff"] = diff
    else:
        cluster, diff = update_netbox_object(nb_cluster, data, module.check_mode)
        if cluster is False:
            module.fail_json(
                msg="Request failed, couldn't update cluster: %s" % data["name"]
            )
        if diff:
            msg = "Cluster %s updated" % (data["name"])
            changed = True
            result["diff"] = diff
        else:
            msg = "Cluster %s already exists" % (data["name"])
            changed = False
    result.update({"cluster": cluster, "changed": changed, "msg": msg})
    return result

def ensure_cluster_absent(nb_endpoint, data):
    '''
    :returns dict(msg, changed, diff)
    '''
    nb_cluster = nb_endpoint.get(name=data["name"])
    result = {}
    if nb_cluster:
        dummy, diff = delete_netbox_object(nb_cluster, module.check_mode)
        msg = 'Cluster %s deleted' % (data["name"])
        changed = True
        result["diff"] = diff
    else:
        msg = 'Cluster %s already absent' % (data["name"])
        changed = False

    result.update({"changed": changed, "msg": msg})
    return result

if __name__ == '__main__':
    main()
