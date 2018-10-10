# -*- coding: utf-8 -*-
# Copyright: (c) 2018, David Gomez (@amb1s1) <david.gomez@networktocode.com>
# Copyright: (c) 2018, Mikhail Yohman (@fragmentedpacket) <mikhail.yohman@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
try:
    import pynetbox
except ImportError:
    raise 'pynetbox is required for this module'

API_APPS_ENDPOINTS = dict(
    circuits=[],
    dcim=['device_roles', 'device_types', 'devices', 'interfaces', 'platforms', 'racks', 'sites'],
    extras=[],
    ipam=['ip_addresses', 'prefixes', 'vrfs'],
    secrets=[],
    tenancy=['tenants', 'tenant_groups'],
    virtualization=['clusters']
)

QUERY_TYPES = dict(
    cluster='name',
    device_role='slug',
    device_type='slug',
    manufacturer='slug',
    nat_inside='address',
    nat_outside='address',
    platform='slug',
    primary_ip='address',
    primary_ip4='address',
    primary_ip6='address',
    rack='slug',
    region='slug',
    site='slug',
    tenant='slug',
    tenant_group='slug',
    vrf='name'
)

CONVERT_TO_ID = dict(
    cluster='clusters',
    device_role='device_roles',
    device_type='device_types',
    interface='interfaces',
    nat_inside='ip_addresses',
    nat_outside='ip_addresses',
    platform='platforms',
    primary_ip='ip_addresses',
    primary_ip4='ip_addresses',
    primary_ip6='ip_addresses',
    rack='racks',
    site='sites',
    tenant='tenants',
    tenant_group='tenant_groups',
    vrf='vrfs'
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

DEVICE_STATUS = dict(
    offline=0,
    active=1,
    planned=2,
    staged=3,
    failed=4,
    inventory=5
)

IP_ADDRESS_STATUS = dict(
    active=1,
    reserved=2,
    deprecated=3,
    dhcp=5
)

IP_ADDRESS_ROLE = dict(
    loopback=10,
    secondary=20,
    anycast=30,
    vip=40,
    vrrp=41,
    hsrp=42,
    glbp=43,
    carp=44
)

PREFIX_STATUS = dict(
    container=0,
    active=1,
    reserved=2,
    deprecated=3
)

VLAN_STATUS = dict(
    active=1,
    reserved=2,
    deprecated=3
)


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
            #if 'int' in key:
            #    try:
            #        query_id = nb_endpoint.get(**{"name": data[key]["name"], "device": data[key]["device"]})
            #    except pynetbox.RequestError as e:
            #        return e.error
            try:
                query_id = nb_endpoint.get(**{QUERY_TYPES.get(key, "q"): search})
            except pynetbox.RequestError as e:
                return e.error

            if key in NO_DEFAULT_ID:
                pass
            elif query_id:
                data[key] = query_id.id
            else:
                data[key] = 1
    return data


def netbox_create_device(nb, nb_endpoint, data):
    norm_data = normalize_data(data)
    if norm_data.get("status"):
            norm_data["status"] = DEVICE_STATUS.get(norm_data["status"].lower(), 0)
    if norm_data.get("face"):
        norm_data["face"] = FACE_ID.get(norm_data["face"].lower(), 0)
    data = find_ids(nb, norm_data)
    try:
        return nb_endpoint.create([norm_data])
    except pynetbox.RequestError as e:
        return e.error


def netbox_delete_device(nb_endpoint, data):
    norm_data = normalize_data(data)
    endpoint = nb_endpoint.get(name=norm_data["name"])
    try:
        if endpoint.delete():
            return 'SUCCESS: %s deleted from Netbox' % (norm_data["name"])
    except AttributeError:
        return 'FAILED: %s not found' % (norm_data["name"])


def netbox_create_ip_address(nb, nb_endpoint, data):
    norm_data = normalize_data(data)
    if norm_data.get("status"):
        norm_data["status"] = IP_ADDRESS_STATUS.get(norm_data["status"].lower())
    if norm_data.get("role"):
        norm_data["role"] = IP_ADDRESS_ROLE.get(norm_data["role"].lower())

    data = find_ids(nb, norm_data)
    try:
        return nb_endpoint.create([norm_data])
    except pynetbox.RequestError as e:
        return e.error


def netbox_delete_ip_address(nb_endpoint, data):
    norm_data = normalize_data(data)
    endpoint = nb_endpoint.get(address=norm_data["address"])
    try:
        if endpoint.delete():
            return 'SUCCESS: %s deleted from Netbox' % (norm_data["address"])
    except AttributeError:
        return 'FAILED: %s not found' % (norm_data["address"])


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
    return data
