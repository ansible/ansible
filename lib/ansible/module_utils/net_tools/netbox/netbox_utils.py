# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Mikhail Yohman (@fragmentedpacket) <mikhail.yohman@gmail.com>
# Copyright: (c) 2018, David Gomez (@amb1s1) <david.gomez@networktocode.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

__metaclass__ = type

# Import necessary packages
import traceback
from ansible.module_utils.compat import ipaddress
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule, missing_required_lib

PYNETBOX_IMP_ERR = None
try:
    import pynetbox

    HAS_PYNETBOX = True
except ImportError:
    PYNETBOX_IMP_ERR = traceback.format_exc()
    HAS_PYNETBOX = False

API_APPS_ENDPOINTS = dict(
    circuits=[],
    dcim=[
        "devices",
        "device_roles",
        "device_types",
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
    device="name",
    device_role="slug",
    device_type="slug",
    manufacturer="slug",
    nat_inside="address",
    nat_outside="address",
    platform="slug",
    primary_ip="address",
    primary_ip4="address",
    primary_ip6="address",
    rack="name",
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
        "role",
        "untagged_vlan",
        "tagged_vlans",
        "tenant",
    ]
)

ENDPOINT_NAME_MAPPING = {
    "devices": "device",
    "interfaces": "interface",
    "ip_addresses": "ip_address",
    "prefixes": "prefix",
    "sites": "site",
    "tenants": "tenant",
}

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
    "2.5gbase-t (2.5ge)": 1120,
    "5gbase-t (5ge)": 1130,
    "sfp+ (10ge)": 1200,
    "xfp (10ge)": 1300,
    "xenpak (10ge)": 1310,
    "x2 (10ge)": 1320,
    "sfp28 (25ge)": 1350,
    "qsfp+ (40ge)": 1400,
    "qsfp28 (50ge)": 1420,
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
    "device": set(["name"]),
    "interface": set(["name", "device"]),
    "ip_address": set(["address", "vrf"]),
    "lag": set(["name"]),
    "nat_inside": set(["vrf", "address"]),
    "prefix": set(["prefix", "vrf"]),
    "site": set(["name"]),
    "vlan": set(["name", "site", "vlan_group", "tenant"]),
    "untagged_vlan": set(["name", "site", "vlan_group", "tenant"]),
    "tagged_vlans": set(["name", "site", "vlan_group", "tenant"]),
}

QUERY_PARAMS_IDS = set(["device", "vrf", "site", "vlan_group", "tenant"])

REQUIRED_ID_FIND = {
    "devices": [{"status": DEVICE_STATUS, "face": FACE_ID}],
    "interfaces": [{"form_factor": INTF_FORM_FACTOR, "mode": INTF_MODE}],
    "ip_addresses": [{"status": IP_ADDRESS_STATUS, "role": IP_ADDRESS_ROLE}],
    "prefixes": [{"status": PREFIX_STATUS}],
    "sites": [{"status": SITE_STATUS}],
}


class NetboxModule(object):
    """
    Initialize connection to Netbox, sets AnsibleModule passed in to
    self.module to be used throughout the class
    """

    def __init__(self, module, endpoint, nb_client=None):
        self.module = module
        self.state = self.module.params["state"]
        self.check_mode = self.module.check_mode
        self.endpoint = endpoint

        if not HAS_PYNETBOX:
            self.module.fail_json(
                msg=missing_required_lib("pynetbox"), exception=PYNETBOX_IMP_ERR
            )
        # These should not be required after making connection to Netbox
        url = self.module.params["netbox_url"]
        token = self.module.params["netbox_token"]
        ssl_verify = self.module.params["validate_certs"]

        # Attempt to initiate connection to Netbox
        if nb_client is None:
            self.nb = self._connect_netbox_api(url, token, ssl_verify)
        else:
            self.nb = nb_client

        # These methods will normalize the regular data
        norm_data = self._normalize_data(module.params["data"])
        choices_data = self._change_choices_id(self.endpoint, norm_data)
        self.data = self._find_ids(choices_data)

    def _connect_netbox_api(self, url, token, ssl_verify):
        try:
            return pynetbox.api(url, token=token, ssl_verify=ssl_verify)
        except Exception:
            self.module.fail_json(msg="Failed to establish connection to Netbox API")

    def _handle_errors(self, msg):
        """
        Returns message and changed = False
        :params msg (str): Message indicating why there is no change
        """
        if msg:
            self.module.exit_json(msg=msg, changed=False)

    def _build_diff(self, before=None, after=None):
        """Builds diff of before and after changes"""
        return {"before": before, "after": after}

    def _get_query_param_id(self, match, data):
        """Used to find IDs of necessary searches when required under _build_query_params
        :returns id (int) or data (dict): Either returns the ID or original data passed in
        :params match (str): The key within the user defined data that is required to have an ID
        :params data (dict): User defined data passed into the module
        """
        if isinstance(data.get(match), int):
            return data[match]
        else:
            endpoint = CONVERT_TO_ID[match]
            app = self._find_app(endpoint)
            nb_app = getattr(self.nb, app)
            nb_endpoint = getattr(nb_app, endpoint)
            result = nb_endpoint.get(**{QUERY_TYPES.get(match): data[match]})
            if result:
                return result.id
            else:
                return data

    def _build_query_params(self, parent, module_data, child=None):
        """
        :returns dict(query_dict): Returns a query dictionary built using mappings to dynamically
        build available query params for Netbox endpoints
        :params parent(str): This is either a key from `_find_ids` or a string passed in to determine
        which keys in the data that we need to use to construct `query_dict`
        :params module_data(dict): Uses the data provided to the Netbox module
        :params child(dict): This is used within `_find_ids` and passes the inner dictionary
        to build the appropriate `query_dict` for the parent
        """
        query_dict = dict()
        query_params = ALLOWED_QUERY_PARAMS.get(parent)
        if child:
            matches = query_params.intersection(set(child.keys()))
        else:
            matches = query_params.intersection(set(module_data.keys()))

        for match in matches:
            if match in QUERY_PARAMS_IDS:
                if child:
                    query_id = self._get_query_param_id(match, child)
                else:
                    query_id = self._get_query_param_id(match, module_data)
                query_dict.update({match + "_id": query_id})
            else:
                if child:
                    value = child.get(match)
                else:
                    value = module_data.get(match)
                query_dict.update({match: value})

        if parent == "lag":
            query_dict.update({"form_factor": 200})
            if isinstance(module_data["device"], int):
                query_dict.update({"device_id": module_data["device"]})
            else:
                query_dict.update({"device": module_data["device"]})

        elif parent == "prefix" and module_data.get("parent"):
            query_dict.update({"prefix": module_data["parent"]})

        return query_dict

    def _change_choices_id(self, endpoint, data):
        """Used to change data that is static and under _choices for the application.
        ex. DEVICE_STATUS
        :returns data (dict): Returns the user defined data back with updated fields for _choices
        :params endpoint (str): The endpoint that will be used for mapping to required _choices
        :params data (dict): User defined data passed into the module
        """
        required_choices = REQUIRED_ID_FIND[endpoint]
        for choice in required_choices:
            for key, value in choice.items():
                if data.get(key):
                    data[key] = value[data[key].lower()]
        return data

    def _find_app(self, endpoint):
        """Dynamically finds application of endpoint passed in using the
        API_APPS_ENDPOINTS for mapping
        :returns nb_app (str): The application the endpoint lives under
        :params endpoint (str): The endpoint requiring resolution to application
        """
        for k, v in API_APPS_ENDPOINTS.items():
            if endpoint in v:
                nb_app = k
        return nb_app

    def _find_ids(self, data):
        """Will find the IDs of all user specified data if resolvable
        :returns data (dict): Returns the updated dict with the IDs of user specified data
        :params data (dict): User defined data passed into the module
        """
        for k, v in data.items():
            if k in CONVERT_TO_ID:
                endpoint = CONVERT_TO_ID[k]
                search = v
                app = self._find_app(endpoint)
                nb_app = getattr(self.nb, app)
                nb_endpoint = getattr(nb_app, endpoint)

                if isinstance(v, dict):
                    query_params = self._build_query_params(k, data, v)
                    query_id = nb_endpoint.get(**query_params)

                elif isinstance(v, list):
                    id_list = list()
                    for list_item in v:
                        norm_data = self._normalize_data(list_item)
                        temp_dict = self._build_query_params(k, data, norm_data)
                        query_id = nb_endpoint.get(**temp_dict)
                        if query_id:
                            id_list.append(query_id.id)
                        else:
                            self._handle_errors(msg="%s not found" % (list_item))

                else:
                    try:
                        query_id = nb_endpoint.get(**{QUERY_TYPES.get(k, "q"): search})
                    except ValueError:
                        self._handle_errors(
                            msg="Multiple results found while searching for key: %s"
                            % (k)
                        )

                if isinstance(v, list):
                    data[k] = id_list
                elif isinstance(v, int):
                    pass
                elif query_id:
                    data[k] = query_id.id
                else:
                    self._handle_errors(msg="Could not resolve id of %s: %s" % (k, v))

        return data

    def _to_slug(self, value):
        """
        :returns slug (str): Slugified value
        :params value (str): Value that needs to be changed to slug format
        """
        if " " in value:
            slug = value.replace(" ", "-").lower()
        else:
            slug = value.lower()
        return slug

    def _normalize_data(self, data):
        """
        :returns data (dict): Normalized module data to formats accepted by Netbox searches
        such as changing from user specified value to slug
        ex. Test Rack -> test-rack
        :params data (dict): Original data from Netbox module
        """
        for k, v in data.items():
            if isinstance(v, dict):
                for subk, subv in v.items():
                    sub_data_type = QUERY_TYPES.get(subk, "q")
                    if sub_data_type == "slug":
                        data[k][subk] = self._to_slug(subv)
            else:
                data_type = QUERY_TYPES.get(k, "q")
                if data_type == "slug":
                    data[k] = self._to_slug(v)
                elif data_type == "timezone":
                    if " " in v:
                        data[k] = v.replace(" ", "_")
        if self.endpoint == "sites":
            site_slug = self._to_slug(data["name"])
            data["slug"] = site_slug

        return data

    def _create_netbox_object(self, nb_endpoint, data):
        """Create a Netbox object.
        :returns tuple(serialized_nb_obj, diff): tuple of the serialized created
        Netbox object and the Ansible diff.
        """
        if self.check_mode:
            nb_obj = data
        else:
            try:
                nb_obj = nb_endpoint.create(data)
            except pynetbox.RequestError as e:
                self._handle_errors(msg=e.error)

        diff = self._build_diff(before={"state": "absent"}, after={"state": "present"})
        return nb_obj, diff

    def _delete_netbox_object(self):
        """Delete a Netbox object.
        :returns diff (dict): Ansible diff
        """
        if not self.check_mode:
            self.nb_object.delete()

        diff = self._build_diff(before={"state": "present"}, after={"state": "absent"})
        return diff

    def _update_netbox_object(self, data):
        """Update a Netbox object.
        :returns tuple(serialized_nb_obj, diff): tuple of the serialized updated
        Netbox object and the Ansible diff.
        """
        serialized_nb_obj = self.nb_object.serialize()
        updated_obj = serialized_nb_obj.copy()
        updated_obj.update(data)
        if serialized_nb_obj == updated_obj:
            return serialized_nb_obj, None
        else:
            data_before, data_after = {}, {}
            for key in data:
                try:
                    if serialized_nb_obj[key] != updated_obj[key]:
                        data_before[key] = serialized_nb_obj[key]
                        data_after[key] = updated_obj[key]
                except KeyError:
                    self._handle_errors(
                        msg="%s does not exist on existing object. Check to make sure valid field."
                        % (key)
                    )

            if not self.check_mode:
                self.nb_object.update(data)
                updated_obj = self.nb_object.serialize()

            diff = self._build_diff(before=data_before, after=data_after)
            return updated_obj, diff

    def _ensure_object_exists(self, nb_endpoint, endpoint_name, name, data):
        """Used when `state` is present to make sure object exists or if the object exists
        that it is updated
        :params nb_endpoint (pynetbox endpoint object): This is the nb endpoint to be used
        to create or update the object
        :params endpoint_name (str): Endpoint name that was created/updated. ex. device
        :params name (str): Name of the object
        :params data (dict): User defined data passed into the module
        """
        if not self.nb_object:
            self.nb_object, diff = self._create_netbox_object(nb_endpoint, data)
            self.result["msg"] = "%s %s created" % (endpoint_name, name)
            self.result["changed"] = True
            self.result["diff"] = diff
        else:
            self.nb_object, diff = self._update_netbox_object(data)
            if self.nb_object is False:
                self._handle_errors(
                    msg="Request failed, couldn't update device: %s" % name
                )
            if diff:
                self.result["msg"] = "%s %s updated" % (endpoint_name, name)
                self.result["changed"] = True
                self.result["diff"] = diff
            else:
                self.result["msg"] = "%s %s already exists" % (endpoint_name, name)

    def _ensure_object_absent(self, endpoint_name, name):
        """Used when `state` is absent to make sure object does not exist
        :params endpoint_name (str): Endpoint name that was created/updated. ex. device
        :params name (str): Name of the object
        """
        if self.nb_object:
            diff = self._delete_netbox_object()
            self.result["msg"] = "%s %s deleted" % (endpoint_name, name)
            self.result["changed"] = True
            self.result["diff"] = diff
        else:
            self.result["msg"] = "%s %s already absent" % (endpoint_name, name)

    def run(self):
        """
        Must be implemented in subclasses
        """
        raise NotImplementedError
