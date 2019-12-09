# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Mikhail Yohman (@fragmentedpacket) <mikhail.yohman@gmail.com>
# Copyright: (c) 2018, David Gomez (@amb1s1) <david.gomez@networktocode.com>
# Copyright: (c) 2019, Alexander Stauch (@BlackestDawn) <blacke4dawn@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import traceback

PYNETBOX_IMP_ERR = None
try:
    import pynetbox
    HAS_PYNETBOX = True
except ImportError:
    PYNETBOX_IMP_ERR = traceback.format_exc()
    HAS_PYNETBOX = False

from ansible.module_utils.basic import missing_required_lib

# Currently supported API endpoints by app type
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

# Query-param and field-name mapping
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

# Data-spec key and endpoint mapping where we may convert the data-spec key to ID
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

# Name value mapping for device face-panels
FACE_ID = dict(front=0, rear=1)

# Data-spec keys where we can convert to ID that are not set by default
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

# Netbox display-name to internal ID mappings for status/role
DEVICE_STATUS = dict(offline=0, active=1, planned=2, staged=3, failed=4, inventory=5)

IP_ADDRESS_STATUS = dict(active=1, reserved=2, deprecated=3, dhcp=5)

IP_ADDRESS_ROLE = dict(
    loopback=10, secondary=20, anycast=30, vip=40, vrrp=41, hsrp=42, glbp=43, carp=44
)

PREFIX_STATUS = dict(container=0, active=1, reserved=2, deprecated=3)

VLAN_STATUS = dict(active=1, reserved=2, deprecated=3)

SITE_STATUS = dict(active=1, planned=2, retired=4)

# Name value mapping for interfaces
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

# Name value mapping for interface modes
INTF_MODE = {"access": 100, "tagged": 200, "tagged all": 300}

# Currently supported query types/params
ALLOWED_QUERY_PARAMS = {
    "interface": set(["name", "device"]),
    "lag": set(["name"]),
    "nat_inside": set(["vrf", "address"]),
    "vlan": set(["name", "site", "vlan_group", "tenant"]),
    "untagged_vlan": set(["name", "site", "vlan_group", "tenant"]),
    "tagged_vlans": set(["name", "site", "vlan_group", "tenant"]),
}

# Query-params that should rather be done by ID
QUERY_PARAMS_IDS = set(["vrf", "site", "vlan_group", "tenant"])

# Default query param per endpoint
DEFAULT_QUERY_PARAM = {
    "devices": "name",
    "device_roles": "name",
    "device_types": "model",
    "interfaces": "name",
    "platforms": "name",
    "racks": "name",
    "regions": "name",
    "sites": "name",
    "ip_addresses": "address",
    "prefixes": "prefix",
    "roles": "name",
    "vlans": "name",
    "vlan_groups": "name",
    "vrfs": "name",
    "tenants": "name",
    "tenant_groups": "name",
    "clusters": "name"
}


# Some helper functions
def build_diff(before=None, after=None, these_keys_only=None):
    """Returns dict containing the difference between before and after inputs"""
    all_keys = these_keys_only or list(set(before.keys()) | set(after.keys()))
    data_before, data_after = {}, {}
    for key in all_keys:
        if key not in before:
            data_after[key] = after[key]
        elif key not in after:
            data_before[key] = before[key]
        else:
            if after[key] != before[key]:
                data_before[key] = before[key]
                data_after[key] = after[key]
    return {"before": data_before, "after": data_after}


def find_app(endpoint):
    """Find an endpoint's corresponding app"""
    for k, v in API_APPS_ENDPOINTS.items():
        if endpoint in v:
            return k


def connect_to_api(module):
    """Helps connect to Netbox's API"""
    url = module.params['netbox_url']
    token = module.params['netbox_token']
    validate_certs = module.params['validate_certs']
    if not url:
        module.fail_json(msg="URL parameter missing, please specify it in task")
    if not token:
        module.fail_json(msg="Token parameter missing, please specify it in task")

    try:
        nb_obj = pynetbox.api(url, token=token, ssl_verify=validate_certs)
        nb_obj.ipam.choices()
    except pynetbox.core.query.RequestError as request_err:
        if request_err.error.startswith("{"):
            err = eval(request_err.error)
            if 'detail' in err:
                err_msg = err['detail']
            else:
                err_msg = str(err)
        else:
            err_msg = request_err
        module.fail_json(msg="Request failed: %s" % (err_msg))
    except Exception as generic_err:
        module.fail_json(msg="Unknown error while connecting to Netbox API: %s" % (generic_err))

    return nb_obj


def netbox_argument_spec():
    """Returns a dict of the defualt argument specification for Netbox"""
    return dict(
        netbox_url=dict(
            type="str",
            required=True
        ),
        netbox_token=dict(
            type="str",
            required=True,
            no_log=True
        ),
        data=dict(
            type="dict",
            required=True
        ),
        validate_certs=dict(
            type="bool",
            default=True
        )
    )


# Main class
class PyNetboxBase(object):
    def __init__(self, module):
        """Constructor"""
        # Fail module if pynetbox is not installed
        if not HAS_PYNETBOX:
            module.fail_json(msg=missing_required_lib('pynetbox'), exception=PYNETBOX_IMP_ERR)

        self.module = module
        self.params = module.params
        self.check_mode = module.check_mode
        # Use this to store final results
        self.result = dict(changed=False)

        # Default parameter usage for various tasks and status messages
        # 'type': Displayname for object-type in status messages
        # 'success': Data-parameter that accompanies 'type' when success
        # 'fail': Data-parameter that accompanies 'type' when failure
        # 'rname': Dict-name for return data
        # 'search': Comma-separated string or dict (with values) of default params to use to search for existing objects
        self.param_usage = {
            'type': "Object",
            'success': None,
            'fail': None,
            'rname': "object",
            'search': None
        }

        # Attempt to create Netbox API object
        self.nb_base = connect_to_api(self.module)
        self.nb_endpoint = None

        # Normalize, check, and do custom adaptation to data-spec
        if not isinstance(self.params['data'], dict):
            self.module.fail_json({"msg": "Improper or malformed data provided: %s" % (self.params['data'])})
        self.normalized_data = self._normalize_data(self.params['data'])
        self._check_and_adapt_data()
        # Check if state supplied
        if 'state' in self.params:
            self.state = self.params['state']

    # Methods intended to be overriden in sub-class as necessary
    # These show minimum viable versions
    def run_module(self):
        """
        Main method for running the Ansible module
        Override as needed
        """
        # Checks for existing object, and creates or updates as needed
        if self.state == "present":
            self.ensure_object_present()

        # Deletes object if present
        elif self.state == "absent":
            self.ensure_object_absent()

        # Unknown state
        else:
            self.module.fail_json(msg="Invalid state %s" % self.state)
        self.module.exit_json(**self.result)

    def _check_and_adapt_data(self):
        """
        App/endpoint specific checking and handling of data
        Override as needed
        """
        pass

    def _multiple_results_error(self, data=None):
        """
        Error message return for when object retrieval results in multiple objects
        Override as needed
        """
        return {'msg': "Returned more than one result", 'changed': False}

    # All following methods are intended only for class-internal use
    # Netbox object manipulation
    def ensure_object_present(self, query_params=None, data=None, endpoint=None, obj_name=None, success_param=None, fail_param=None):
        """Checks for the specified object in Netbox and creates or updates it if necessary"""
        nb_object = self._retrieve_object(query_params, endpoint)
        if nb_object:
            self._update_object(nb_object, data, obj_name, success_param)
        else:
            self._create_object(data, endpoint, obj_name, success_param)

    def ensure_object_absent(self, query_params=None, endpoint=None, obj_name=None, success_param=None, fail_param=None):
        """Checks for the specified object in Netbox and removes if present"""
        nb_object = self._retrieve_object(query_params, endpoint)
        if nb_object:
            self._delete_object(nb_object, obj_name, success_param)
        else:
            if obj_name is None:
                obj_name = self.param_usage['type']
            if success_param is None:
                success_param = self.param_usage['success']
            self.result['msg'] = "%s '%s' already absent" % (obj_name.capitalize(), self.normalized_data[success_param])

    def _create_object(self, data=None, endpoint=None, obj_name=None, success_param=None, fail_param=None):
        """Create a Netbox object."""
        if data is None:
            data = self.normalized_data
        if obj_name is None:
            obj_name = self.param_usage['type']
        if success_param is None:
            success_param = self.param_usage['success']
        if fail_param is None:
            fail_param = self.param_usage['fail']
        nb_endpoint = self._get_endpoint(endpoint)
        self.result.update({
            self.param_usage['rname']: data,
            'diff': dict(before={"state": "absent"}, after={"state": "present"})
        })
        if not self.check_mode:
            try:
                nb_obj = nb_endpoint.create(data)
                try:
                    self.result[self.param_usage['rname']] = nb_obj.serialize()
                except AttributeError:
                    self.result[self.param_usage['rname']] = nb_obj
                self.result.update({
                    'changed': True,
                    'msg': "Successfully created %s: %s" % (obj_name, self.result[self.param_usage['rname']][success_param])
                })
            except pynetbox.RequestError as e:
                self.module.fail_json(msg="Failed to create %s: %s. Error was: %s" % (obj_name, self.normalized_data[fail_param], e.error))

    def _delete_object(self, nb_obj, obj_name=None, success_param=None, fail_param=None):
        """Delete supplied Netbox object"""
        if obj_name is None:
            obj_name = self.param_usage['type']
        if success_param is None:
            success_param = self.param_usage['success']
        if fail_param is None:
            fail_param = self.param_usage['fail']
        self.result.update({
            self.param_usage['rname']: nb_obj.serialize(),
            'diff': dict(before={"state": "present"}, after={"state": "absent"})
        })
        if not self.check_mode:
            try:
                nb_obj.delete()
                self.result.update({
                    'changed': True,
                    'msg': "Successfully removed %s: %s" % (obj_name, self.normalized_data[success_param])
                })
            except pynetbox.RequestError:
                self.module.fail_json(msg="Failed to remove %s: %s" % (obj_name, self.normalized_data[fail_param]))

    def _update_object(self, nb_obj, data=None, obj_name=None, success_param=None, fail_param=None):
        """Update supplied Netbox object"""
        if nb_obj is None:
            self.module.fail_json(msg="No object supplied for update request")
        if data is None:
            data = self.normalized_data
        if obj_name is None:
            obj_name = self.param_usage['type']
        if success_param is None:
            success_param = self.param_usage['success']
        if fail_param is None:
            fail_param = self.param_usage['fail']
        serialized_nb_obj = nb_obj.serialize()
        updated_obj = serialized_nb_obj.copy()
        updated_obj.update(data)
        self.result.update({
            self.param_usage['rname']: serialized_nb_obj,
            'diff': None,
            'msg': "Nothing to be done for %s: %s" % (obj_name, self.normalized_data[success_param])
        })
        if serialized_nb_obj != updated_obj:
            self.result.update({
                'diff': build_diff(
                    before=serialized_nb_obj, after=updated_obj, these_keys_only=data.keys()
                ),
                self.param_usage['rname']: updated_obj
            })
            if not self.check_mode:
                if nb_obj.update(data):
                    updated_obj = nb_obj.serialize()
                    self.result.update({
                        'changed': True,
                        'msg': "Successfully updated %s: %s" % (obj_name, self.normalized_data[success_param])
                    })
                else:
                    self.module.fail_json(msg="Failed to update %s: %s" % (obj_name, self.normalized_data[fail_param]))

    # Helper methods
    def _set_endpoint(self, endpoint=None):
        """Sets the default Netbox endpoint to work against"""
        self.nb_endpoint = self._validate_endpoint(endpoint)
        if not self.nb_endpoint:
            self.module.fail_json(msg="Incorrect or unsupported endpoint specified: %s" % (endpoint))

    def _get_endpoint(self, endpoint=None):
        """
        Returns the specified Netbox endpoint as a Netbox object,
        if nothing specified returns the default endpoint
        """
        if endpoint is None:
            return self.nb_endpoint
        else:
            return self._validate_endpoint(endpoint)

    def _validate_endpoint(self, endpoint=None):
        """
        Checks validity of endpoint via object-type or string
        :returns object: Netbox endpoint object
        """
        try:
            if (
                    isinstance(endpoint, pynetbox.core.endpoint.Endpoint) or
                    isinstance(endpoint, pynetbox.core.endpoint.DetailEndpoint)
            ):
                return endpoint
            elif endpoint in API_APPS_ENDPOINTS[find_app(endpoint)]:
                nb_app = getattr(self.nb_base, find_app(endpoint))
                return getattr(nb_app, endpoint)
            else:
                self.module.fail_json(msg="Incorrect or unsupported endpoint specified: %s" % (endpoint))
        except KeyError:
            self.module.fail_json(msg="Incorrect or unsupported endpoint specified: %s" % (endpoint))

    def _retrieve_object(self, query_params=None, endpoint=None):
        """
        Retrieve a Netbox object from specified endpoint
        :returns object: Netbox Object
        """
        if query_params is None:
            query_params = self.param_usage['search']
        nb_endpoint = self._get_endpoint(endpoint)
        try:
            if isinstance(query_params, str):
                search = dict()
                for param in query_params.split(','):
                    search[param] = self.normalized_data[param]
                return nb_endpoint.get(**search)
            elif isinstance(query_params, dict):
                return nb_endpoint.get(**query_params)
            elif isinstance(query_params, int):
                return nb_endpoint.get(query_params)
            else:
                self.module.fail_json(msg="Invalid query parameter type: %s" % (type(query_params)))
        except Exception:
            self.module.fail_json(**self._multiple_results_error(query_params))

    def _retrieve_object_id(self, query_params=None, endpoint=None):
        """
        Retrieve the ID of a Netbox object from specified endpoint
        :returns int: Netbox Object ID
        """
        nb_obj = self._retrieve_object(query_params, endpoint)
        if getattr(nb_obj, 'id'):
            return int(nb_obj.id)
        else:
            self.module.fail_json(msg="Could not retrieve ID from object: %s" % (nb_obj.serialize()))

    def _find_ids(self, data=None):
        """
        Finds IDs for supplied data-spec params
        :returns dict(data): dict of data-spec where relevant keys' value has
        been replaced with their corresponding ID
        """
        if data is None:
            data = self.normalized_data
        for search_param, search_value in data.items():
            if search_param in CONVERT_TO_ID:
                endpoint = CONVERT_TO_ID[search_param]
                app = find_app(endpoint)
                nb_app = getattr(self.nb_base, app)
                nb_endpoint = getattr(nb_app, endpoint)

                if isinstance(search_value, dict):
                    query_params = self._build_query_params(search_param, search_value)
                    query_id = nb_endpoint.get(**query_params)

                elif isinstance(search_value, list):
                    id_list = list()
                    for sub_value in search_value:
                        norm_data = self._normalize_data(sub_value)
                        temp_dict = self._build_query_params(search_param, norm_data)
                        query_id = nb_endpoint.get(**temp_dict)
                        if query_id:
                            id_list.append(query_id.id)
                        else:
                            return ValueError("%s not found" % (sub_value))

                else:
                    try:
                        query_id = nb_endpoint.get(**{QUERY_TYPES.get(search_param, "q"): search_value})
                    except ValueError:
                        raise ValueError(
                            "Multiple results found while searching for key: %s" % (search_param)
                        )

                if isinstance(search_value, list):
                    data[search_param] = id_list
                elif query_id:
                    data[search_param] = query_id.id
                elif search_param in NO_DEFAULT_ID:
                    pass
                else:
                    raise ValueError("Could not resolve id of %s: %s" % (search_param, search_value))

        return data

    def _build_query_params(self, search_param, search_value, module_data=None):
        """
        Builds a query parameter for a specific Netbox object
        :returns dict(query_dict): dict of query parameters where unnecessary ones are removed
        and ID is potentially added
        """
        if module_data is None:
            module_data = self.normalized_data
        query_dict = dict()
        query_params = ALLOWED_QUERY_PARAMS.get(search_param)
        matches = query_params.intersection(set(search_value.keys()))
        for match in matches:
            if match in QUERY_PARAMS_IDS:
                value = self._get_query_param_id(match, search_value)
                query_dict.update({match + "_id": value})
            else:
                value = search_value.get(match)
                query_dict.update({match: value})

        if search_param == "lag":
            query_dict.update({"form_factor": 200})
            if isinstance(module_data["device"], int):
                query_dict.update({"device_id": module_data["device"]})
            else:
                query_dict.update({"device": module_data["device"]})

        return query_dict

    def _get_query_param_id(self, query_param, query_value):
        """
        Gets ID of specific netbox-object
        :returns: either ID-value or original search param
        """
        endpoint = CONVERT_TO_ID[query_param]
        app = find_app(endpoint)
        nb_app = getattr(self.nb_base, app)
        nb_endpoint = getattr(nb_app, endpoint)
        result = nb_endpoint.get(**{QUERY_TYPES.get(query_param): query_value[query_param]})
        if result:
            return result.id
        else:
            return query_value

    def _normalize_data(self, data=None):
        """Normalizes data to align with query type"""
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
