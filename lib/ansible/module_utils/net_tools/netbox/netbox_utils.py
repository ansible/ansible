# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Mikhail Yohman (@fragmentedpacket) <mikhail.yohman@gmail.com>
# Copyright: (c) 2018, David Gomez (@amb1s1) <david.gomez@networktocode.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

__metaclass__ = type

API_APPS_ENDPOINTS = dict(
    circuits=[],
    dcim=[
        "devices",
        "device_roles",
        "device_types",
        "devices",
        "interfaces",
        "platforms",
        "racks",
        "regions",
        "sites",
    ],
    extras=[],
    ipam=["ip_addresses", "prefixes", "roles", "vlans", "vlan_groups", "vrfs"],
    secrets=[],
    tenancy=["tenants", "tenant_groups"],
    virtualization=["clusters"],
)

QUERY_TYPES = dict(
    cluster="name",
    devices="name",
    device_role="slug",
    device_type="slug",
    manufacturer="slug",
    nat_inside="address",
    nat_outside="address",
    platform="slug",
    primary_ip="address",
    primary_ip4="address",
    primary_ip6="address",
    rack="slug",
    region="slug",
    role="slug",
    site="slug",
    tenant="name",
    tenant_group="slug",
    time_zone="timezone",
    vlan="name",
    vlan_group="slug",
    vrf="name",
)

CONVERT_TO_ID = dict(
    cluster="clusters",
    device="devices",
    device_role="device_roles",
    device_type="device_types",
    interface="interfaces",
    lag="interfaces",
    nat_inside="ip_addresses",
    nat_outside="ip_addresses",
    platform="platforms",
    primary_ip="ip_addresses",
    primary_ip4="ip_addresses",
    primary_ip6="ip_addresses",
    rack="racks",
    region="regions",
    role="roles",
    site="sites",
    tagged_vlans="vlans",
    tenant="tenants",
    tenant_group="tenant_groups",
    untagged_vlan="vlans",
    vlan="vlans",
    vlan_group="vlan_groups",
    vrf="vrfs",
)

FACE_ID = dict(front=0, rear=1)

NO_DEFAULT_ID = set(
    [
        "device",
        "lag",
        "primary_ip",
        "primary_ip4",
        "primary_ip6",
        "role",
        "vlan",
        "vrf",
        "nat_inside",
        "nat_outside",
        "region",
        "untagged_vlan",
        "tagged_vlans",
        "tenant",
    ]
)

DEVICE_STATUS = dict(offline=0, active=1, planned=2, staged=3, failed=4, inventory=5)

IP_ADDRESS_STATUS = dict(active=1, reserved=2, deprecated=3, dhcp=5)

IP_ADDRESS_ROLE = dict(
    loopback=10, secondary=20, anycast=30, vip=40, vrrp=41, hsrp=42, glbp=43, carp=44
)

PREFIX_STATUS = dict(container=0, active=1, reserved=2, deprecated=3)

VLAN_STATUS = dict(active=1, reserved=2, deprecated=3)

SITE_STATUS = dict(active=1, planned=2, retired=4)

INTF_FORM_FACTOR = {
    "virtual": 0,
    "link aggregation group (lag)": 200,
    "100base-tx (10/100me)": 800,
    "1000base-t (1ge)": 1000,
    "10gbase-t (10ge)": 1150,
    "10gbase-cx4 (10ge)": 1170,
    "gbic (1ge)": 1050,
    "sfp (1ge)": 1100,
    "sfp+ (10ge)": 1200,
    "xfp (10ge)": 1300,
    "xenpak (10ge)": 1310,
    "x2 (10ge)": 1320,
    "sfp28 (25ge)": 1350,
    "qsfp+ (40ge)": 1400,
    "cfp (100ge)": 1500,
    "cfp2 (100ge)": 1510,
    "cfp2 (200ge)": 1650,
    "cfp4 (100ge)": 1520,
    "cisco cpak (100ge)": 1550,
    "qsfp28 (100ge)": 1600,
    "qsfp56 (200ge)": 1700,
    "qsfp-dd (400ge)": 1750,
    "ieee 802.11a": 2600,
    "ieee 802.11b/g": 2610,
    "ieee 802.11n": 2620,
    "ieee 802.11ac": 2630,
    "ieee 802.11ad": 2640,
    "gsm": 2810,
    "cdma": 2820,
    "lte": 2830,
    "oc-3/stm-1": 6100,
    "oc-12/stm-4": 6200,
    "oc-48/stm-16": 6300,
    "oc-192/stm-64": 6400,
    "oc-768/stm-256": 6500,
    "oc-1920/stm-640": 6600,
    "oc-3840/stm-1234": 6700,
    "sfp (1gfc)": 3010,
    "sfp (2gfc)": 3020,
    "sfp (4gfc)": 3040,
    "sfp+ (8gfc)": 3080,
    "sfp+ (16gfc)": 3160,
    "sfp28 (32gfc)": 3320,
    "qsfp28 (128gfc)": 3400,
    "t1 (1.544 mbps)": 4000,
    "e1 (2.048 mbps)": 4010,
    "t3 (45 mbps)": 4040,
    "e3 (34 mbps)": 4050,
    "cisco stackwise": 5000,
    "cisco stackwise plus": 5050,
    "cisco flexstack": 5100,
    "cisco flexstack plus": 5150,
    "juniper vcp": 5200,
    "extreme summitstack": 5300,
    "extreme summitstack-128": 5310,
    "extreme summitstack-256": 5320,
    "extreme summitstack-512": 5330,
    "other": 32767,
}

INTF_MODE = {"access": 100, "tagged": 200, "tagged all": 300}

ALLOWED_QUERY_PARAMS = {
    "interface": set(["name", "device"]),
    "lag": set(["name"]),
    "nat_inside": set(["vrf", "address"]),
    "vlan": set(["name", "site", "vlan_group", "tenant"]),
    "untagged_vlan": set(["name", "site", "vlan_group", "tenant"]),
    "tagged_vlans": set(["name", "site", "vlan_group", "tenant"]),
}

QUERY_PARAMS_IDS = set(["vrf", "site", "vlan_group", "tenant"])


def _build_diff(before=None, after=None):
    return {"before": before, "after": after}


def create_netbox_object(nb_endpoint, data, check_mode):
    """Create a Netbox object.
    :returns tuple(serialized_nb_obj, diff): tuple of the serialized created
    Netbox object and the Ansible diff.
    """
    if check_mode:
        serialized_nb_obj = data
    else:
        nb_obj = nb_endpoint.create(data)
        try:
            serialized_nb_obj = nb_obj.serialize()
        except AttributeError:
            serialized_nb_obj = nb_obj

    diff = _build_diff(before={"state": "absent"}, after={"state": "present"})
    return serialized_nb_obj, diff


def delete_netbox_object(nb_obj, check_mode):
    """Delete a Netbox object.
    :returns tuple(serialized_nb_obj, diff): tuple of the serialized deleted
    Netbox object and the Ansible diff.
    """
    if not check_mode:
        nb_obj.delete()

    diff = _build_diff(before={"state": "present"}, after={"state": "absent"})
    return nb_obj.serialize(), diff


def update_netbox_object(nb_obj, data, check_mode):
    """Update a Netbox object.
    :returns tuple(serialized_nb_obj, diff): tuple of the serialized updated
    Netbox object and the Ansible diff.
    """
    serialized_nb_obj = nb_obj.serialize()
    updated_obj = serialized_nb_obj.copy()
    updated_obj.update(data)
    if serialized_nb_obj == updated_obj:
        return serialized_nb_obj, None
    else:
        data_before, data_after = {}, {}
        for key in data:
            if serialized_nb_obj[key] != updated_obj[key]:
                data_before[key] = serialized_nb_obj[key]
                data_after[key] = updated_obj[key]

        if not check_mode:
            nb_obj.update(data)
            updated_obj = nb_obj.serialize()

        diff = _build_diff(before=data_before, after=data_after)
        return updated_obj, diff


def _get_query_param_id(nb, match, child):
    endpoint = CONVERT_TO_ID[match]
    app = find_app(endpoint)
    nb_app = getattr(nb, app)
    nb_endpoint = getattr(nb_app, endpoint)
    result = nb_endpoint.get(**{QUERY_TYPES.get(match): child[match]})
    if result:
        return result.id
    else:
        return child


def find_app(endpoint):
    for k, v in API_APPS_ENDPOINTS.items():
        if endpoint in v:
            nb_app = k
    return nb_app


def build_query_params(nb, parent, module_data, child):
    query_dict = dict()
    query_params = ALLOWED_QUERY_PARAMS.get(parent)
    matches = query_params.intersection(set(child.keys()))
    for match in matches:
        if match in QUERY_PARAMS_IDS:
            value = _get_query_param_id(nb, match, child)
            query_dict.update({match + "_id": value})
        else:
            value = child.get(match)
            query_dict.update({match: value})

    if parent == "lag":
        query_dict.update({"form_factor": 200})
        if isinstance(module_data["device"], int):
            query_dict.update({"device_id": module_data["device"]})
        else:
            query_dict.update({"device": module_data["device"]})

    return query_dict


def find_ids(nb, data):
    for k, v in data.items():
        if k in CONVERT_TO_ID:
            endpoint = CONVERT_TO_ID[k]
            search = v
            app = find_app(endpoint)
            nb_app = getattr(nb, app)
            nb_endpoint = getattr(nb_app, endpoint)

            if isinstance(v, dict):
                query_params = build_query_params(nb, k, data, v)
                query_id = nb_endpoint.get(**query_params)

            elif isinstance(v, list):
                id_list = list()
                for index in v:
                    norm_data = normalize_data(index)
                    temp_dict = build_query_params(nb, k, data, norm_data)
                    query_id = nb_endpoint.get(**temp_dict)
                    if query_id:
                        id_list.append(query_id.id)
                    else:
                        return ValueError("%s not found" % (index))

            else:
                try:
                    query_id = nb_endpoint.get(**{QUERY_TYPES.get(k, "q"): search})
                except ValueError:
                    raise ValueError(
                        "Multiple results found while searching for key: %s" % (k)
                    )

            if isinstance(v, list):
                data[k] = id_list
            elif query_id:
                data[k] = query_id.id
            elif k in NO_DEFAULT_ID:
                pass
            else:
                raise ValueError("Could not resolve id of %s: %s" % (k, v))

    return data


def normalize_data(data):
    for k, v in data.items():
        if isinstance(v, dict):
            for subk, subv in v.items():
                sub_data_type = QUERY_TYPES.get(subk, "q")
                if sub_data_type == "slug":
                    if "-" in subv:
                        data[k][subk] = subv.replace(" ", "").lower()
                    elif " " in subv:
                        data[k][subk] = subv.replace(" ", "-").lower()
                    else:
                        data[k][subk] = subv.lower()
        else:
            data_type = QUERY_TYPES.get(k, "q")
            if data_type == "slug":
                if "-" in v:
                    data[k] = v.replace(" ", "").lower()
                elif " " in v:
                    data[k] = v.replace(" ", "-").lower()
                else:
                    data[k] = v.lower()
            elif data_type == "timezone":
                if " " in v:
                    data[k] = v.replace(" ", "_")

    return data
