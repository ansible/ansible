# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

import json
import pynetbox

API_APPS_ENDPOINTS = dict(
    circuits=[],
    dcim=['device_roles', 'device_types', 'devices', 'sites', 'platforms', 'racks'],
    extras=[],
    ipam=['ip_addresses'],
    secrets=[],
    tenancy=['tenants', 'tenant_groups'],
    virtualization=['clusters']
)

QUERY_TYPES = dict(
    cluster='name',
    device_role='slug',
    device_type='slug',
    manufacturer='slug',
    platform='slug',
    primary_ip='address',
    primary_ip4='address',
    primary_ip6='address',
    rack='slug',
    region='slug',
    site='slug',
    tenant='slug',
    tenant_group='slug'
)

CONVERT_TO_ID = dict(
    cluster='clusters',
    device_role='device_roles',
    device_type='device_types',
    platform='platforms',
    rack='racks',
    site='sites',
    tenant='tenants',
    tenant_group='tenant_groups',
    primary_ip='ip_addresses',
    primary_ip4='ip_addresses',
    primary_ip6='ip_addresses'
)

STATUS_ID = dict(
    offline=0,
    active=1,
    planned=2,
    staged=3,
    failed=4,
    inventory=5
)

FACE_ID = dict(
    front=0,
    rear=1
)

NO_DEFAULT_ID = {
    'primary_ip',
    'primary_ip4',
    'primary_ip6'
}


def find_app(endpoint):
    for key, value in API_APPS_ENDPOINTS.items():
        if endpoint in value:
            nb_app = key
    return nb_app


def find_ids(nb, data):
    for key in data.keys():
        if key in CONVERT_TO_ID.keys():
            endpoint = CONVERT_TO_ID[key]
            search = data[key]
            app = find_app(endpoint)
            nb_app = getattr(nb, app)
            nb_endpoint = getattr(nb_app, endpoint)
            try:
                query_id = nb_endpoint.get(**{QUERY_TYPES.get(key, "q"): search})
            except pynetbox.RequestError as e:
                return e.error
            if query_id:
                data[key] = query_id.id
            elif key in NO_DEFAULT_ID:
                pass
            else:
                data[key] = 1
    return data


def netbox_add(nb, nb_endpoint, data):
    normalized_data = normalize_data(data)
    data = find_ids(nb, normalized_data)
    try:
        return nb_endpoint.create([data])
    except pynetbox.RequestError as e:
        return e.error


def netbox_delete(nb_endpoint, data):
    data = normalize_data(data)
    endpoint = nb_endpoint.get(name=data["name"])
    try:
        results = endpoint.delete()
        if results:
            return 'SUCCESS: %s deleted from Netbox' % (data["name"])
    except AttributeError:
        return 'Endpoint was not found - No changes occurred!'


def normalize_data(data):
    clean_json = data.replace("'", '"')
    data = json.loads(clean_json)
    for key, value in data.items():
        data_type = QUERY_TYPES.get(key, "q")
        if data_type == "slug":
            if " " in value:
                data[key] = value.replace(" ", "-").lower()
            else:
                data[key] = value.lower()
        elif key == "status":
            data["status"] = STATUS_ID.get(data["status"].lower(), 0)
        elif key == "face":
            data["face"] = FACE_ID.get(data["face"].lower(), 0)
    return data

