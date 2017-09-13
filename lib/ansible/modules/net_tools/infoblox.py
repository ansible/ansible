#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: infoblox
author: "Joan Miquel Luque (@xoanmi)"
short_description: Manage Infoblox via Web API
description:
  - Manage Infoblox IPAM and DNS via Web API
version_added: "2.4"
requirements:
  - "requests >= 2.9.1"
options:
  server:
    description:
      - Infoblox IP/URL
    required: True
  username:
    description:
      - Infoblox username
      - The user must have API privileges
    required: True
  password:
    description:
      - Infoblox password
    required: True
  action:
    description:
      - Action to perform
    required: True
    choices: ["get_aliases", "get_cname", "get_a_record", "get_host", "get_network", "get_range", "get_next_available_ip", "get_fixedaddress",
              "get_ipv6network", "get_ptr_record", "get_srv_record", "get_auth_zone", "get_forward_zone", "get_delegated_zone",
              "add_alias", "add_cname", "add_host", "add_ipv6_host", "create_ptr_record", "get_txt_record", "get_network_container",
              "create_a_record", "create_srv_record", "create_auth_zone", "create_forward_zone", "create_delegated_zone", "create_txt_record",
              "create_network_container", "set_a_record", "set_name", "set_extattr", "update_a_record", "update_srv_record",
              "update_ptr_record", "update_cname_record", "update_auth_zone", "update_forward_zone", "update_txt_record",
              "update_network_container", "update_host_record", "delete_alias", "delete_cname", "delete_a_record", "delete_fixedaddress",
              "delete_host", "delete_ptr_record", "delete_srv_record", "reserve_next_available_ip"]
  host:
    description:
      - Hostname variable to search, add or delete host object
      - The hostname must be in fqdn format
    required: False
  network:
    description:
      - Network address
      - Must be indicated as a CDIR format or 192.168.1.0 format
    required: False
    default: False
  start_addr:
    description:
      - Starting address for a range
      - Must be indicated as 192.168.1.0 format
    required: False
    default: False
  end_addr:
    description:
      - Ending address for a range
      - Must be indicated as 192.168.1.0 format
    required: False
    default: False
  address:
    description:
      - IP Address
    required: False
    default: False
  addresses:
    description:
      - IP Addresses
    required: False
    default: False
  attr_name:
    description:
      - Extra Attribute name
    required: False
  attr_value:
    description:
      - Extra Attribute value
    required: False
  comment:
    description:
      - Object comment
      - This comment will be added when the module create any object
    required: False
    default: "Object managed by ansible-infoblox module"
  api_version:
    description:
      - Infoblox Web API user to perfom actions
    required: False
    default: "1.7.1"
  dns_view:
    description:
      - Infoblox DNS View
    required: False
    default: "Private"
  net_view:
    description:
      - Infoblox Network View
    required: False
    default: "default"
  ttl:
    description:
      - DNS time-to-live
    required: False
    default: None
"""

EXAMPLES = """
---
- hosts: localhost
  connection: local
  gather_facts: False

  tasks:
  - name: Add host
    infoblox:
      server: 192.168.1.1
      username: admin
      password: admin
      action: add_host
      network: 192.168.1.0/24
      host: "{{ item }}"
    with_items:
      - test01.local
      - test02.local
    register: infoblox
"""

RETURN = """
hostname:
  description: Hostname of the object
  returned: success
  type: str
  sample: test1.local
result:
  description: result returned by the infoblox web API
  returned: success
  type: list
  sample: [['...', '...'], ['...'], ['...']]
"""

from ansible.module_utils.basic import AnsibleModule
from copy import copy

_RETURN_FIELDS_PROPERTY = "_return_fields"
_COMMENT_PROPERTY = "comment"
_TTL_PROPERTY = "ttl"
_USE_TTL_PROPERTY = "use_ttl"
_NAME_PROPERTY = "name"
_VIEW_PROPERTY = "view"
_IPV4_ADDRESS_PROPERTY = "ipv4addr"
_IPV6_ADDRESS_PROPERTY = "ipv6addr"
_ID_PROPERTY = "_ref"
_PTRDNAME_PROPERTY = "ptrdname"
_EXT_ATTR_PROPERTY = "extattrs"
_TXT_PROPERTY = "text"
_PORT_PROPERTY = "port"
_PRIORITY_PROPERTY = "priority"
_WEIGHT_PROPERTY = "weight"
_TARGET_PROPERTY = "target"
_MAC_PROPERTY = "mac"
_CANONICAL_PROPERTY = "canonical"
_IPV4_ADDRS_PROPERTY = "ipv4addrs"
_IPV6_ADDRS_PROPERTY = "ipv6addrs"
_FQDN_PROPERTY = "fqdn"
_FORWARD_TO_PROPERTY = "forward_to"
_NETWORK_PROPERTY = "network"
_NETWORK_CONTAINER_PROPERTY = "network_container"
_NETWORK_VIEW_PROPERTY = "network_view"
_DELEGATE_TO_PROPERTY = "delegate_to"

try:
    import requests
    requests.packages.urllib3.disable_warnings()
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ---------------------------------------------------------------------------
# Infoblox
# ---------------------------------------------------------------------------


class Infoblox(object):
    """
    Class for manage all the REST API calls with the Infoblox appliances
    """

    def __init__(self, module, server, username, password, api_version, dns_view, net_view):
        self.module = module
        self.dns_view = dns_view
        self.net_view = net_view
        self.auth = (username, password)

        self.base_url = "https://{host}/wapi/v{version}/".format(
            host=server, version=api_version)
        self.model_list = [_COMMENT_PROPERTY, _TTL_PROPERTY, _USE_TTL_PROPERTY, _NAME_PROPERTY,
                           _VIEW_PROPERTY, _IPV4_ADDRESS_PROPERTY, _IPV6_ADDRESS_PROPERTY,
                           _ID_PROPERTY, _PTRDNAME_PROPERTY, _EXT_ATTR_PROPERTY, _TXT_PROPERTY,
                           _PORT_PROPERTY, _PRIORITY_PROPERTY, _WEIGHT_PROPERTY, _TARGET_PROPERTY,
                           _MAC_PROPERTY, _CANONICAL_PROPERTY, _IPV4_ADDRS_PROPERTY,
                           _IPV6_ADDRS_PROPERTY, _FQDN_PROPERTY, _FORWARD_TO_PROPERTY,
                           _NETWORK_PROPERTY, _NETWORK_VIEW_PROPERTY, _DELEGATE_TO_PROPERTY]

    def invoke(self, method, tail, ok_codes=(200,), **params):
        """
        Perform the HTTPS request by using rest api
        """
        request = getattr(requests, method)
        response = request(self.base_url + tail,
                           auth=self.auth, verify=False, **params)

        if response.status_code not in ok_codes:
            raise Exception(response.json())
        else:
            payload = response.json()

        if isinstance(payload, dict) and "text" in payload:
            raise Exception(payload["text"])
        else:
            return payload

    def _return_property(self, base, property_list=[]):
        return_property = []
        if base:
            return_property.extend([_NAME_PROPERTY, _TTL_PROPERTY, _USE_TTL_PROPERTY,
                                    _VIEW_PROPERTY, _COMMENT_PROPERTY, _EXT_ATTR_PROPERTY])
        for current_property in property_list:
            return_property.append(current_property)
        return return_property

    def _make_model(self, model_dict):
        return_model = {}
        for model in self.model_list:
            if model_dict.get(model) or model_dict.get(model) is False:
                return_model[model] = model_dict.get(model)
        return return_model


    # ---------------------------------------------------------------------------
    # get_network()
    # ---------------------------------------------------------------------------
    def get_network(self, network=None, filters=None):
        """
        Search network in infoblox by using rest api
        Network format supported:
            - 192.168.1.0
            - 192.168.1.0/24
        """
        if not network and not filters:
            self.module.fail_json(msg="You must specify the option 'network' or 'filters'.")
        elif not network and not filters:
            self.module.fail_json(msg="Specify either 'network' or 'filter', but not both.")
        elif network:
            params = {_NETWORK_PROPERTY: network, _NETWORK_VIEW_PROPERTY: self.net_view}
            return self.invoke("get", "network", params=params)
        elif filters:
            list_of_filters = ['network?']
            if not isinstance(filters, list):
                self.module.fail_json(msg="Specify a list of dicts with keys of 'filter' and 'value'")
            for current_filter in filters:
                if not isinstance(current_filter, dict):
                    self.module.fail_json(msg="Please ensure each element is a dict with 'filter' and 'value' as keys")
                elif not current_filter.get('filter') or not current_filter.get('value'):
                    self.module.fail_json(msg="Please ensure each element is a dict with 'filter' and 'value' as keys")
                list_of_filters.append(current_filter.get('filter') + '=' + current_filter.get('value'))
                list_of_filters.append('&')
            list_of_filters.pop()
            out_filter = "".join(list_of_filters)
            params = {_NETWORK_PROPERTY: network, _NETWORK_VIEW_PROPERTY: self.net_view}
            return self.invoke("get", out_filter, params=params)
        else:
            self.module.fail_json(msg="Unknown get_network issue.")
            

    # ---------------------------------------------------------------------------
    # get_range()
    # ---------------------------------------------------------------------------
    def get_range(self, start_addr, end_addr):
        """
        Search range in infoblox by using rest api
        Starting and ending address format supported:
            - 192.168.1.0
        """
        if not start_addr:

            self.module.fail_json(
                msg="You must specify the option 'start_addr.")
        if not end_addr:
            self.module.fail_json(msg="You must specify the option 'end_addr.")
        params = {"start_addr": start_addr,
                  "end_addr": end_addr, _NETWORK_VIEW_PROPERTY: self.net_view}
        return self.invoke("get", "range", params=params)

    # ---------------------------------------------------------------------------
    # get_ipv6network()
    # ---------------------------------------------------------------------------
    def get_ipv6network(self, network):
        """
        Search ipv6 network in infoblox by using rest api
        Network format supported:
            - ipv6-cidr notation
        """
        if not network:

            self.module.fail_json(msg="You must specify the option 'network'.")
        params = {_NETWORK_PROPERTY: network, _NETWORK_VIEW_PROPERTY: self.net_view}
        return self.invoke("get", "ipv6network", params=params)

    # ---------------------------------------------------------------------------
    # get_next_available_ip()
    # ---------------------------------------------------------------------------
    def get_next_available_ip(self, network_ref):
        """
        Return next available ip in a network range
        """
        if not network_ref:
            self.module.exit_json(
                msg="You must specify the option 'network_ref'.")
        params = {"_function": "next_available_ip"}
        return self.invoke("post", network_ref, ok_codes=(200,), params=params)

    # ---------------------------------------------------------------------------
    # get_next_available_network()
    # ---------------------------------------------------------------------------
    def get_next_available_network(self, network_container, cidr):
        """
        Return next available ip in a network range
        """
        network_containter_info = self.get_network_container(network_container)
        if len(network_containter_info) < 1:
            self.module.fail_json(msg="Network Container does not exist.")
        network_ref = network_containter_info[0].get('_ref').split(':')[0]

        if not network_ref:
            self.module.exit_json(
                msg="Container was not found.")
        params = {"_function": "next_available_network", "cidr": cidr, "num": 1 }
        #raise Exception([network_ref, params])
        return self.invoke("post", network_ref, ok_codes=(200,), params=params)

    # ---------------------------------------------------------------------------
    # reserve_next_available_ip()
    # ---------------------------------------------------------------------------
    def reserve_next_available_ip(self, network, mac_addr=None,
                                  comment=None, extattrs=None):
        """
        Reserve ip address via fixedaddress in infoblox by using rest api
        """
        if comment is None:
            comment = "IP reserved via ansible infoblox self.module"
        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        model = {_IPV4_ADDRESS_PROPERTY: "func:nextavailableip:" + network, _MAC_PROPERTY: mac,
                 _COMMENT_PROPERTY: comment, _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("post", "fixedaddress?_return_fields=ipv4addr", ok_codes=(200, 201, 400), json=model)

    # ---------------------------------------------------------------------------
    # get_fixedaddress()
    # ---------------------------------------------------------------------------
    def get_fixedaddress(self, address):
        """
        Search FIXEDADDRESS reserve by address in infoblox through the rest api
        """
        params = {"ipv4addr": address}
        return self.invoke("get", "fixedaddress", params=params)

    # ---------------------------------------------------------------------------
    # get_cname_object()
    # ---------------------------------------------------------------------------
    def get_cname_object(self, cname):
        object_ref = None
        cnames = self.get_cname(cname)

        _ref = None
        canonical = None
        if isinstance(cnames, list) and len(cnames) > 0:
            detail = cnames[0]
            _ref = detail.get('_ref')
        if _ref:
            object_ref = _ref.split(':')[0] + ':' + _ref.split(':')[1]
            canonical = cnames[0].get('canonical')
        return object_ref, canonical

    # ---------------------------------------------------------------------------
    # get_cname()
    # ---------------------------------------------------------------------------
    def get_cname(self, cname):
        """
        Search CNAME by FQDN in infoblox by using rest api
        """
        if not cname:
            self.module.fail_json(msg="You must specify the option 'cname'.")

        params = {_NAME_PROPERTY: cname, _VIEW_PROPERTY: self.dns_view}
        return self.invoke("get", "record:cname", params=params)

    # ---------------------------------------------------------------------------
    # create_cname()
    # ---------------------------------------------------------------------------
    def create_cname(self, cname, canonical, comment=None, ttl=None, extattrs=None):
        """
        Add CNAME in infoblox by using rest api
        """
        if cname is None or canonical is None:
            self.module.exit_json(
                msg="You must specify the option 'name' and 'canonical'.")
        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        object_ref, current_canonical = self.get_cname_object(cname)

        if object_ref:
            if current_canonical != canonical:
                msg = 'Canonical name is {} and {} is not the same ' \
                      'please use update_cname_record'.format(current_canonical, canonical)
                self.module.fail_json(msg=msg)
            self.module.exit_json(msg='CNAME Exists')

        model = {_NAME_PROPERTY: cname, _CANONICAL_PROPERTY: canonical,
                 _VIEW_PROPERTY: self.dns_view, _COMMENT_PROPERTY: comment,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("post", "record:cname", ok_codes=(200, 201, 400), json=model)

    # ---------------------------------------------------------------------------
    # update_cname_record()
    # ---------------------------------------------------------------------------
    def update_cname_record(self, desired_cname, desired_canonical, current, comment=None, ttl=None, extattrs=None):
        """
        Update alias for a cname entry
        """

        if not isinstance(current, dict):
            self.module.fail_json(msg="The 'current' check is not a dict")
        elif not current.get('cname'):
            self.module.fail_json(msg="The 'current' dict must contain a 'cname' key")
        else:
            current_cname = current.get('cname')

        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        object_ref, current_canonical = self.get_cname_object(current_cname)
        if object_ref is None:

            self.module.fail_json(
                msg="Name {} was not found.".format(current_cname))
        if current_canonical == desired_canonical:
            self.module.exit_json(msg='Canonical Exists')

        model = {_NAME_PROPERTY: desired_cname, _CANONICAL_PROPERTY: desired_canonical,
                 _VIEW_PROPERTY: self.dns_view, _COMMENT_PROPERTY: comment,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("put", object_ref, json=model)

    # ---------------------------------------------------------------------------
    # delete_cname_record()
    # ---------------------------------------------------------------------------
    def delete_cname_record(self, cname):
        """
        Delete cname object
        """
        object_ref, _ = self.get_cname_object(current_cname)
        return self.delete_object(object_ref)

    # ---------------------------------------------------------------------------
    # get_a_object()
    # ---------------------------------------------------------------------------
    def get_a_object(self, name, address):
        object_ref = None
        a_records = self.get_a_record(name)

        for a_record in a_records:
            if a_record.get(_IPV4_ADDRESS_PROPERTY) == address:
                key_out = a_record.get('_ref')
                object_ref = key_out.split(':')[0] + ':' + key_out.split(':')[1]
                break
        return object_ref

    # ---------------------------------------------------------------------------
    # get_a_record()
    # ---------------------------------------------------------------------------
    def get_a_record(self, name):
        """
        Retrieves information about the A record with the given name.
        """
        if not name:
            self.module.fail_json(msg="You must specify the option 'name'.")

        property_list = [_IPV4_ADDRESS_PROPERTY]
        my_property = self._return_property(True, property_list)
        params = {_NAME_PROPERTY: name, _VIEW_PROPERTY: self.dns_view,
                  _RETURN_FIELDS_PROPERTY: my_property}
        return self.invoke("get", "record:a", params=params)

    # ---------------------------------------------------------------------------
    # create_a_record()
    # ---------------------------------------------------------------------------
    def create_a_record(self, name, address, comment=None, ttl=None, extattrs=None):
        """
        Creates an A record with the given name that points to the given IP address.

        For documentation on how to use the related part of the InfoBlox WAPI, refer to:
        https://ipam.illinois.edu/wapidoc/objects/record.a.html
        """
        if not name or not address:
            self.module.exit_json(
                msg="You must specify the option 'name' and 'address'.")
        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        object_ref = self.get_a_object(name, address)
        if object_ref:
            self.module.exit_json(msg='A record Exists')

        model = {_NAME_PROPERTY: name, _IPV4_ADDRESS_PROPERTY: address,
                 _VIEW_PROPERTY: self.dns_view, _COMMENT_PROPERTY: comment,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("post", "record:a", ok_codes=(200, 201, 400), json=model)

    # ---------------------------------------------------------------------------
    # update_a_record()
    # ---------------------------------------------------------------------------
    def update_a_record(self, desired_name, desired_address, current, comment=None, ttl=None, extattrs=None):
        """
        Update an A record
        """
        if not isinstance(current, dict):
            self.module.fail_json(msg="The 'current' check is not a dict")
        elif not current.get('name') or not current.get('address'):
            self.module.fail_json(msg="The 'current' dict must contain a 'name' and 'address' key")
        else:
            current_name = current.get('name')
            current_address = current.get('address')

        object_ref = self.get_a_object(desired_name, desired_address)
        if object_ref:
            self.module.exit_json(msg='A record Exists')

        object_ref = None
        a_records = self.get_a_record(current_name)

        for a_record in a_records:
            if a_record.get('name') == current_name:
                key_out = a_record.get('_ref')
                object_ref = key_out.split(':')[0] + ':' + key_out.split(':')[1]
                break

        if not object_ref:
            msg = "IP {} and ptrdname {} pair was not found.".format(current_ip, current_name)
            self.module.fail_json(msg=msg)

        if object_ref is None:
            self.module.fail_json(msg="Name {} was not found.".format(current_name))
        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        model = {_NAME_PROPERTY: desired_name, _IPV4_ADDRESS_PROPERTY: desired_address,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
                 _COMMENT_PROPERTY: comment, _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("put", object_ref, json=model)

    # ---------------------------------------------------------------------------
    # delete_a_record()
    # ---------------------------------------------------------------------------
    def delete_a_record(self, name, address):
        """
        Delete a record object
        """
        object_ref = self.get_a_object(name, address)
        if object_ref:
            return self.delete_object(object_ref)
        else:
            self.module.exit_json(msg='Object deleted already')

    # ---------------------------------------------------------------------------
    # get_ptr_object()
    # ---------------------------------------------------------------------------
    def get_ptr_object(self, address, name):
        object_ref = None
        ptrs = self.get_ptr_record(address)

        for ptr in ptrs:
            if ptr.get('ptrdname') == name:
                key_out = ptr.get('_ref')
                object_ref = key_out.split(':')[0] + ':' + key_out.split(':')[1]
                break
        return object_ref

    # ---------------------------------------------------------------------------
    # get_ptr_record()
    # ---------------------------------------------------------------------------
    def get_ptr_record(self, address):
        """
        Retrieves information about the PTR record with the given address.
        """
        if not address:
            self.module.fail_json(msg="You must specify the option 'address'.")

        property_list = [_IPV4_ADDRESS_PROPERTY, _PTRDNAME_PROPERTY]
        my_property = self._return_property(True, property_list)
        params = {_IPV4_ADDRESS_PROPERTY: address, _VIEW_PROPERTY: self.dns_view,
                  _RETURN_FIELDS_PROPERTY: my_property}
        return self.invoke("get", "record:ptr", params=params)

    # ---------------------------------------------------------------------------
    # create_ptr_record()
    # ---------------------------------------------------------------------------
    def create_ptr_record(self, name, address, comment=None, ttl=None, extattrs=None):
        """
        Creates an PTR record with the given name that points to the given IP address.
        For documentation on how to use the related part of the InfoBlox WAPI, refer to:
        https://ipam.illinois.edu/wapidoc/objects/record.ptr.html
        """
        if not name or not address:
            self.module.exit_json(
                msg="You must specify the option 'name' and 'address'.")
        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        object_ref = self.get_ptr_object(address, name)
        if object_ref:
            self.module.exit_json(msg='PTR Exists')

        model = {_PTRDNAME_PROPERTY: name, _NAME_PROPERTY: name, _IPV4_ADDRESS_PROPERTY: address,
                 _VIEW_PROPERTY: self.dns_view, _COMMENT_PROPERTY: comment,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("post", "record:ptr", ok_codes=(200, 201, 400), json=model)

    # ---------------------------------------------------------------------------
    # update_ptr_record()
    # ---------------------------------------------------------------------------
    def update_ptr_record(self, desired_name, desired_address, current, comment=None, ttl=None, extattrs=None):
        """
        Update alias for a ptr record
        """
        if not isinstance(current, dict):
            self.module.fail_json(msg="The 'current' check is not a dict{}".format(current))
        elif not current.get('name') or not current.get('address'):
            self.module.fail_json(msg="The 'current' dict must contain a 'address' and 'name' key")
        else:
            current_name = current.get('name')
            current_address = current.get('address')

        object_ref = self.get_ptr_object(desired_address, desired_name)
        if object_ref:
            self.module.exit_json(msg='PTR Exists')

        object_ref = None
        ptrs = self.get_ptr_record(current_address)
        for current_ptr in ptrs:
            if current_ptr.get('ptrdname') == current_name:
                key_out = current_ptr.get('_ref')
                object_ref = key_out.split(':')[0] + ':' + key_out.split(':')[1]
                break

        if object_ref is None:
            self.module.fail_json(msg="IP {} and ptrdname {} pair was not found.".format(current_ip, current_name))

        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        model = {_PTRDNAME_PROPERTY: desired_name,
                 _IPV4_ADDRESS_PROPERTY: desired_address,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("put", object_ref, json=model)

    # ---------------------------------------------------------------------------
    # delete_ptr_record()
    # ---------------------------------------------------------------------------
    def delete_ptr_record(self, name, address):
        """
        Delete cname object
        """
        object_ref = self.get_ptr_object(address, name)
        if object_ref:
            return self.delete_object(object_ref)
        else:
            self.module.exit_json(msg='Object deleted already')

    # ---------------------------------------------------------------------------
    # get_srv_object()
    # ---------------------------------------------------------------------------
    def get_srv_object(self, name):
        object_ref = None
        srvs = self.get_srv_record(name)
        if srvs:
            key_out = srvs[0].get('_ref')
            object_ref = key_out.split(':')[0] + ':' + key_out.split(':')[1]
        return object_ref

    # ---------------------------------------------------------------------------
    # get_srv_record()
    # ---------------------------------------------------------------------------
    def get_srv_record(self, name):
        """
        Retrieves information about the SRV record with the given name.
        """
        if not name:
            self.module.fail_json(msg="You must specify the option 'address'.")
        property_list = [_VIEW_PROPERTY, _COMMENT_PROPERTY, _TTL_PROPERTY, _EXT_ATTR_PROPERTY,
                         _WEIGHT_PROPERTY, _PORT_PROPERTY, _PRIORITY_PROPERTY, _TARGET_PROPERTY]
        my_property = self._return_property(True, property_list)
        params = {_NAME_PROPERTY: name, _VIEW_PROPERTY: self.dns_view,
                  _RETURN_FIELDS_PROPERTY: my_property}
        return self.invoke("get", "record:srv", params=params)

    # ---------------------------------------------------------------------------
    # create_srv_record()
    # ---------------------------------------------------------------------------
    def create_srv_record(self, name, srv_attr, comment=None, ttl=None, extattrs=None):
        """
        Creates an SRV record with the name and .
        For documentation on how to use the related part of the InfoBlox WAPI, refer to:
        https://ipam.illinois.edu/wapidoc/objects/record.srv.html
        """

        if not isinstance(srv_attr, dict):
            self.module.fail_json(msg="The variable 'srv_attr' is not a dict")
        for attr in ['port', 'priority', 'dns_target', 'weight']:
            if not srv_attr.get(attr):
                self.module.fail_json(msg="The 'srv_attr' dict must contain a '{}' key".format(attr))

        object_ref = self.get_srv_object(name)
        if object_ref:
            self.module.exit_json(msg='SRV Exists')

        port = srv_attr.get('port')
        priority = srv_attr.get('priority')
        dns_target = srv_attr.get('dns_target')
        weight = srv_attr.get('weight')

        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        model = {_NAME_PROPERTY: name, _PORT_PROPERTY: port,
                 _PRIORITY_PROPERTY: priority, _TARGET_PROPERTY: dns_target,
                 _WEIGHT_PROPERTY: weight,
                 _VIEW_PROPERTY: self.dns_view, _COMMENT_PROPERTY: comment,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("post", "record:srv", ok_codes=(200, 201, 400), json=model)

    # ---------------------------------------------------------------------------
    # update_srv_record()
    # ---------------------------------------------------------------------------
    def update_srv_record(self, desired_name, srv_attr, current_name, comment=None, ttl=None, extattrs=None):
        """
        Update svr record for a named entry
        """

        if not isinstance(srv_attr, dict):
            self.module.fail_json(msg="The variable 'srv_attr' is not a dict")

        port = srv_attr.get('port')
        priority = srv_attr.get('priority')
        dns_target = srv_attr.get('dns_target')
        weight = srv_attr.get('weight')
        current_name = current_name.get('name')

        object_ref = None
        srvs = self.get_srv_record(current_name)

        for srv in srvs:
            if srv.get('name') == current_name:
                key_out = srv.get('_ref')
                object_ref = key_out.split(':')[0] + ':' + key_out.split(':')[1]
                break

        if object_ref is None:
            self.module.fail_json(msg="Name {} was not found.".format(current_name))

        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        model = {_PORT_PROPERTY: port,
                 _PRIORITY_PROPERTY: priority, _TARGET_PROPERTY: dns_target,
                 _WEIGHT_PROPERTY: weight, _COMMENT_PROPERTY: comment,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("put", object_ref, json=model)

    # ---------------------------------------------------------------------------
    # delete_srv_record()
    # ---------------------------------------------------------------------------
    def delete_srv_record(self, name):
        """
        Delete srv record object
        """
        object_ref = self.get_srv_object(name)
        if object_ref:
            return self.delete_object(object_ref)
        else:
            self.module.exit_json(msg='Object deleted already')

    # ---------------------------------------------------------------------------
    # get_txt_record()
    # ---------------------------------------------------------------------------
    def get_txt_record(self, name):
        """
        Retrieves information about the PTR record with the given name.
        """
        if not name:
            self.module.fail_json(msg="You must specify the option 'name'.")

        property_list = [_NAME_PROPERTY, _COMMENT_PROPERTY, _TXT_PROPERTY, _TTL_PROPERTY,
                         _EXT_ATTR_PROPERTY, _COMMENT_PROPERTY]
        my_property = self._return_property(True, property_list)
        params = {_NAME_PROPERTY: name, _VIEW_PROPERTY: self.dns_view,
                  _RETURN_FIELDS_PROPERTY: my_property}
        return self.invoke("get", "record:txt", params=params)

    # ---------------------------------------------------------------------------
    # create_txt_record()
    # ---------------------------------------------------------------------------
    def create_txt_record(self, name, txt, comment=None, ttl=None, extattrs=None):
        """
        Creates an PTR record with the given name that points to the given IP address.
        For documentation on how to use the related part of the InfoBlox WAPI, refer to:
        https://ipam.illinois.edu/wapidoc/objects/record.txt.html
        """
        if not name or not txt:
            self.module.exit_json(
                msg="You must specify the option 'name' and 'txt'.")
        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        current_txts = self.get_txt_record(name)
        if current_txts:
            for current_txt in current_txts:
                if current_txt.get(_TXT_PROPERTY) == txt:
                    self.module.exit_json(msg='TXT object exist')
        model = {_NAME_PROPERTY: name, _TXT_PROPERTY: txt,
                 _VIEW_PROPERTY: self.dns_view,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
                 _COMMENT_PROPERTY: comment, _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("post", "record:txt", ok_codes=(200, 201, 400), json=model)

    # ---------------------------------------------------------------------------
    # update_txt_record()
    # ---------------------------------------------------------------------------
    def update_txt_record(self, desired_name, desired_txt, current, comment=None, ttl=None, extattrs=None):
        """
        Update alias for a txt record
        """

        if not isinstance(current, dict):
            self.module.fail_json(msg="The 'current' check is not a dict")
        elif not current.get('name'):
            self.module.fail_json(msg="The 'current' dict must contain a 'name' key")
        else:
            current_name = current.get('name')

        current_txts = self.get_txt_record(desired_name)
        if current_txts:
            for current_txt in current_txts:
                if current_txt.get(_TXT_PROPERTY) == desired_txt:
                    self.module.exit_json(msg='TXT object exist')

        object_ref = None
        current_txt = current.get('current_txt')
        first_found = current.get('first_found')
        if first_found is not None and current_txt is not None:
            self.module.fail_json(
                msg="Please Specify either current_txt or first_found, but not both.")
        elif first_found is None and current_txt is None:
            self.module.fail_json(
                msg="The 'current' dict must have either 'current_txt' or 'first_found' as a key.")

        txts = self.get_txt_record(current_name)
        if current_txt:
            for index, current_txt in entxts:
                if current_txt.get('name') == current_name and current_txt.get('txt') == current_txt:
                    my_entry = index
        else:
            my_entry = 0

        used_txt = txts[my_entry]
        key_out = used_txt.get('_ref')
        object_ref = key_out.split(':')[0] + ':' + key_out.split(':')[1]

        if object_ref is None:

            self.module.fail_json(
                msg="Name {} was not found.".format(current_name))
            self.module.exit_json(
                msg="Name {} was not found.".format(current_name))
        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        model = {_NAME_PROPERTY: desired_name, _TXT_PROPERTY: desired_txt,
                 _VIEW_PROPERTY: self.dns_view,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
                 _COMMENT_PROPERTY: comment, _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("put", object_ref, json=model)

    # ---------------------------------------------------------------------------
    # delete_txt_record()
    # ---------------------------------------------------------------------------
    def delete_txt_record(self, name):
        """
        Delete txt record object
        """
        object_ref = self.get_txt_object(name)
        if object_ref:
            return self.delete_object(object_ref)
        else:
            self.module.exit_json(msg='Object deleted already')

    # ---------------------------------------------------------------------------
    # get_aliases()
    # ---------------------------------------------------------------------------
    def get_aliases(self, host):
        """
        Get all the aliases on a host
        """
        if not host:
            self.module.fail_json(msg="You must specify the option 'host'.")
        params = {"name": host, "view": self.dns_view}
        return self.invoke("get", "record:host?_return_fields%2B=aliases", params=params)

    # ---------------------------------------------------------------------------
    # update_host_alias()
    # ---------------------------------------------------------------------------
    def update_host_alias(self, object_ref, alias, extattrs=None):
        """
        Update alias for a host
        """
        if not object_ref:
            self.module.fail_json(msg="Object _ref required!")
        if extattrs is not None:
            extattrs = self.add_attr(extattrs)
        return self.invoke("put", object_ref, json=alias)

    # ---------------------------------------------------------------------------
    # get_host_by_name()
    # ---------------------------------------------------------------------------
    def get_host_by_name(self, host):
        """
        Search host by FQDN in infoblox by using rest api
        """
        if not host:

            self.module.fail_json(msg="You must specify the option 'host'.")
        params = {"name": host, "_return_fields+": "comment,extattrs",
                  "view": self.dns_view}
        return self.invoke("get", "record:host", params=params)

    # ---------------------------------------------------------------------------
    # get_host_object()
    # ---------------------------------------------------------------------------
    def get_host_object(self, name, address):
        object_ref = None
        hosts = self.get_host_by_name(name)

        for host in hosts:
            if host.get(_IPV4_ADDRESS_PROPERTY) == address:
                key_out = host.get('_ref')
                object_ref = key_out.split(':')[0] + ':' + key_out.split(':')[1]
                break
        return object_ref

    # ---------------------------------------------------------------------------
    # create_host_record()
    # ---------------------------------------------------------------------------
    def create_host_record(self, host, address, network_ref=None, comment=None, ttl=None, extattrs=None):
        """
        Add host in infoblox by using rest api
        """
        if not host:
            self.module.fail_json(
                msg="You must specify the hostname parameter 'host'.")

        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        if network_ref is not None:
            address = "func:nextavailableip:" + network_ref
        elif address:
            object_ref = self.get_host_object(host, address)
            if object_ref:
                self.module.exit_json(msg='A record Exists')
            object_ref = self.get_host_by_name(host)
            if object_ref:
                self.module.fail_json(msg='HOST record already exists, please use update')
        else:
            raise Exception("Function options missing!")

        model = {_NAME_PROPERTY: host, _IPV4_ADDRS_PROPERTY: [{_IPV4_ADDRESS_PROPERTY: address}],
                 _VIEW_PROPERTY: self.dns_view,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
                 _COMMENT_PROPERTY: comment, _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("post", "record:host", ok_codes=(200, 201, 400), json=model)

    # ---------------------------------------------------------------------------
    # update_host_record()
    # ---------------------------------------------------------------------------
    def update_host_record(self, desired_name, desired_address, current, comment=None, ttl=None, extattrs=None):
        """
        Update a host record
        """
        if not isinstance(current, dict):
            self.module.fail_json(msg="The 'current' check is not a dict")
        elif not current.get('host') or not current.get('address'):
            self.module.fail_json(msg="The 'current' dict must contain a 'host' and 'address' key")
        else:
            current_name = current.get('host')
            current_address = current.get('address')

        object_ref = None
        hosts = self.get_host_by_name(current_name)
        for current_host in hosts:
            if current_host.get('name') == current_name:
                key_out = current_host.get('_ref')
                object_ref = key_out.split(
                    ':')[0] + ':' + key_out.split(':')[1]
                comment = current_host.get('comment')
                ttl = current_host.get('ttl')
                addrs = current_host.get('ipv4addrs')
                break

        if object_ref is None:
            self.module.exit_json(msg="IP {} and ptrdname {} pair was not found.".format(
                current_ip, current_name))
        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        if current_address != desired_address:
            addr_object_ref = None
            if addrs is not None:
                for addr in addrs:
                    if addr.get('ipv4addr') == current_address:
                        key_out = current_host.get('_ref')
                        addr_object_ref = key_out.split(
                            ':')[0] + ':' + key_out.split(':')[1]
                        break
            if addr_object_ref is None:

                self.module.exit_json(
                    msg="IP {} was not found.".format(current_address))
            addr_model = {"ipv4addrs": [{"ipv4addr": desired_address}]}
            self.invoke("put", object_ref, json=addr_model)

        model = {_NAME_PROPERTY: desired_name,
                 _VIEW_PROPERTY: self.dns_view,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
                 _COMMENT_PROPERTY: comment, _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("put", object_ref, json=model)

    # ---------------------------------------------------------------------------
    # create_ipv6_host_record()
    # ---------------------------------------------------------------------------
    def create_ipv6_host_record(self, host, network, address, comment=None, ttl=None, extattrs=None):
        """
        Add host in infoblox by using rest api
        """
        if not host:
            self.module.fail_json(msg="You must specify the option 'host'.")

        if network:
            address = "func:nextavailableip:" + network
        elif address:
            pass
        else:
            raise Exception("Function options missing!")

        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        model = {_NAME_PROPERTY: host, _IPV6ADDRS_PROPERTY: [{"ipv6addr": address}],
                 _VIEW_PROPERTY: self.dns_view,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
                 _COMMENT_PROPERTY: comment, _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("post", "record:host?_return_fields=ipv6addrs", ok_codes=(200, 201, 400), json=payload)

    # ---------------------------------------------------------------------------
    # get_auth_zone()
    # ---------------------------------------------------------------------------
    def get_auth_zone(self, fqdn):
        """
        Search for Authoritative Zone in infoblox by fqdn
        """
        if fqdn is None:
            self.module.fail_json(msg="You must specify the option 'name'.")

        params = {_FQDN_PROPERTY: fqdn, _VIEW_PROPERTY: self.dns_view}
        return self.invoke("get", "zone_auth", params=params)

    # ---------------------------------------------------------------------------
    # create_auth_zone()
    # ---------------------------------------------------------------------------
    def create_auth_zone(self, fqdn,
                         comment=None, ttl=None, extattrs=None):
        """
        Add FQDN in infoblox by using rest api
        """
        if fqdn is None:
            self.module.fail_json(msg="You must specify the option 'fqdn'.")

        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        object_ref = None
        fqdns = self.get_auth_zone(fqdn)

        for current_fqdn in fqdns:
            if current_fqdn.get('fqdn') == fqdn:
                msg = "FQDN {} already exists.".format(fqdn)
                self.module.exit_json(msg=msg)

        model = {_FQDN_PROPERTY: fqdn,
                 _VIEW_PROPERTY: self.dns_view, _COMMENT_PROPERTY: comment,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("post", "zone_auth", ok_codes=(200, 201, 400), json=model)

    # ---------------------------------------------------------------------------
    # update_auth_zone()
    # ---------------------------------------------------------------------------
    def update_auth_zone(self, current_fqdn,
                         comment=None, ttl=None, extattrs=None):
        """
        Update alias for a cname entry
        """
        object_ref = None
        fqdns = self.get_auth_zone(current_fqdn)

        for fqdn in fqdns:
            if fqdn.get('fqdn') == current_fqdn:
                key_out = fqdn.get('_ref')
                object_ref = key_out.split(':')[0]
                break

        if not object_ref:
            msg = "FQDN {} was not found.".format(current_fqdn)
            self.module.fail_json(msg=msg)

        if object_ref is None:
            self.module.fail_json(
                msg="Name {} was not found.".format(current_name))
        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        model = {_VIEW_PROPERTY: self.dns_view, _COMMENT_PROPERTY: comment,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("put", object_ref, json=model)

    # ---------------------------------------------------------------------------
    # get_forward_zone()
    # ---------------------------------------------------------------------------
    def get_forward_zone(self, fqdn):
        """
        Search for Forward Zone in infoblox by fqdn
        """
        if fqdn is None:
            self.module.fail_json(msg="You must specify the option 'fqdn'.")

        params = {_FQDN_PROPERTY: fqdn, _VIEW_PROPERTY: self.dns_view}
        return self.invoke("get", "zone_forward", params=params)

    # ---------------------------------------------------------------------------
    # create_forward_zone()
    # ---------------------------------------------------------------------------
    def create_forward_zone(self, fqdn, name, address,
                            comment=None, ttl=None, extattrs=None):
        """
        Add FQDN in infoblox by using rest api
        """
        if fqdn is None:
            self.module.fail_json(msg="You must specify the option 'fqdn'.")

        if extattrs is not None:
            extattrs = self.add_attr(extattrs)
        if name != "dns-server":
            self.module.fail_json(msg="Currently only support dns-server.")

        if len(self.get_forward_zone(fqdn)) > 0:
            self.module.exit_json(msg="Network already exists.")

        forward_to = [{_NAME_PROPERTY: name, "address": address}]
        model = {_FQDN_PROPERTY: fqdn, _FORWARD_TO_PROPERTY: forward_to,
                 _VIEW_PROPERTY: self.dns_view, _COMMENT_PROPERTY: comment,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("post", "zone_forward", ok_codes=(200, 201, 400), json=model)

    # ---------------------------------------------------------------------------
    # update_forward_zone()
    # ---------------------------------------------------------------------------
    def update_forward_zone(self, current_fqdn, desired_name, desired_address,
                            comment=None, ttl=None, extattrs=None):
        """
        Update forward zone entry
        """

        object_ref = None
        fqdns = self.get_forward_zone(current_fqdn)

        for fqdn in fqdns:
            if fqdn.get('fqdn') == current_fqdn:
                key_out = fqdn.get('_ref')
                object_ref = key_out.split(':')[0]
                break

        if not object_ref:
            msg = "FQDN {} was not found.".format(current_fqdn)
            self.module.fail_json(msg=msg)

        if object_ref is None:
            self.module.fail_json(
                msg="FQDN {} was not found.".format(current_fqdn))
        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        forward_to = [
            {_NAME_PROPERTY: desired_name, "address": desired_address}]
        model = {_FORWARD_TO_PROPERTY: forward_to,
                 _VIEW_PROPERTY: self.dns_view, _COMMENT_PROPERTY: comment,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("put", object_ref, json=model)

    # ---------------------------------------------------------------------------
    # get_delegated_zone()
    # ---------------------------------------------------------------------------
    def get_delegated_zone(self, fqdn):
        """
        Search for Authoritative Zone in infoblox by fqdn
        """
        if fqdn is None:
            self.module.fail_json(msg="You must specify the option 'name'.")

        params = {_FQDN_PROPERTY: fqdn, _VIEW_PROPERTY: self.dns_view}
        return self.invoke("get", "zone_delegated", params=params)

    # ---------------------------------------------------------------------------
    # create_delegated_zone()
    # ---------------------------------------------------------------------------
    def create_delegated_zone(self, fqdn, delegate_to,
                              comment=None, ttl=None, extattrs=None):
        """
        Add FQDN in infoblox by using rest api
        """
        if fqdn is None:
            self.module.fail_json(msg="You must specify the option 'fqdn'.")

        if isinstance(delegate_to, dict):
            copy_delegate_to = delegate_to
            delegate_to = []
            delegate_to.append(copy_delegate_to)
        if not isinstance(delegate_to, list):
            self.module.fail_json(msg="delegate_to was not a list or a dict.")

        for delegate in delegate_to:
            if not isinstance(delegate, dict):
                self.module.fail_json(msg="Each element of delegate_to must be a dict, {} is not.".format(delegate))
            if delegate.get('name') and delegate.get('address'):
                pass
            else:
                msg = "Each element of delegate_to must have a 'name' and 'address' key, which is the only supported method {} ".format(delegate)
                msg = str(delegate)
                self.module.fail_json(msg=msg)

        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        model = {_FQDN_PROPERTY: fqdn, _DELEGATE_TO_PROPERTY: delegate_to,
                 _VIEW_PROPERTY: self.dns_view, _COMMENT_PROPERTY: comment,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("post", "zone_delegated", ok_codes=(200, 201, 400), json=model)

    # ---------------------------------------------------------------------------
    # create_network()
    # ---------------------------------------------------------------------------
    def create_network(self, network, comment=None, ttl=None, extattrs=None):
        """
        Creates an PTR record with the given name that points to the given IP address.
        For documentation on how to use the related part of the InfoBlox WAPI, refer to:
        https://ipam.illinois.edu/wapidoc/objects/record.ptr.html
        """
        if not network:
            self.module.fail_json(msg="You must specify the option 'name' and 'address'.")
        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        if len(self.get_network(network)) > 0:
            self.module.exit_json(msg="Network already exists.")

        model = {_NETWORK_CONTAINER_PROPERTY: network, _NETWORK_PROPERTY: network,
                 _COMMENT_PROPERTY: comment,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("post", "network", ok_codes=(200, 201, 400), json=model)

    # ---------------------------------------------------------------------------
    # get_network_container()
    # ---------------------------------------------------------------------------
    def get_network_container(self, network):
        """
        Search for IPAM network in infoblox by network
        """
        if network is None:
            self.module.fail_json(msg="You must specify the option 'network'.")
        property_list = [_NETWORK_CONTAINER_PROPERTY,
                         _NETWORK_VIEW_PROPERTY, _NETWORK_PROPERTY]
        my_property = self._return_property(False, property_list)
        params = {_NETWORK_PROPERTY: network,
                  _RETURN_FIELDS_PROPERTY: my_property}
        return self.invoke("get", "networkcontainer", params=params)

    # ---------------------------------------------------------------------------
    # create_network_container()
    # ---------------------------------------------------------------------------
    def create_network_container(self, network, comment=None, ttl=None, extattrs=None):
        """
        Creates an PTR record with the given name that points to the given IP address.
        For documentation on how to use the related part of the InfoBlox WAPI, refer to:
        https://ipam.illinois.edu/wapidoc/objects/record.ptr.html
        """
        if not network:
            self.module.fail_json(msg="You must specify the option 'name' and 'address'.")
        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        if len(self.get_network_container(network)) > 0:
            self.module.exit_json(msg="Network already exists.")

        model = {_NETWORK_CONTAINER_PROPERTY: network, _NETWORK_PROPERTY: network,
                 _COMMENT_PROPERTY: comment,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("post", "networkcontainer", ok_codes=(200, 201, 400), json=model)

    # ---------------------------------------------------------------------------
    # update_network_container()
    # ---------------------------------------------------------------------------
    def update_network_container(self, current_network, comment=None, ttl=None, extattrs=None):
        """
        Update svr record for a named entry
        """
        object_ref = None
        net_containers = self.get_network_container(current_network)

        for net_container in net_containers:
            if net_container.get(_NETWORK_PROPERTY) == current_network:
                key_out = net_container.get('_ref')
                object_ref = key_out.split(':')[0]
                break

        if object_ref is None:
            self.module.fail_json(msg="Name {} was not found.".format(current_network))
        if extattrs is not None:
            extattrs = self.add_attr(extattrs)

        model = {_COMMENT_PROPERTY: comment, _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("put", object_ref, json=model)

    # ---------------------------------------------------------------------------
    # delete_object()
    # ---------------------------------------------------------------------------
    def delete_object(self, obj_ref):
        """
        Delete object in infoblox by using rest api
        """
        if not obj_ref:
            self.module.fail_json(msg="Object _ref required!")
        return self.invoke("delete", obj_ref, ok_codes=(200, 404))

    # ---------------------------------------------------------------------------
    # set_name()
    # ---------------------------------------------------------------------------
    def set_name(self, object_ref, name):
        """
        Update the name of a object
        """
        if not object_ref:
            self.module.exit_json(
                msg="You must specify the option 'object_ref'.")
        payload = {"name": name}
        return self.invoke("put", object_ref, json=payload)

    # ---------------------------------------------------------------------------
    # set_extattr()
    # ---------------------------------------------------------------------------
    def set_extattr(self, object_ref, attr_name, attr_value):
        """
        Update the extra attribute value
        """
        if not object_ref:
            self.module.fail_json(msg="You must specify the option 'object_ref''.")
        payload = {"extattrs": {attr_name: {"value": attr_value}}}
        return self.invoke("put", object_ref, json=payload)

    def add_attr(self, attributes):
        if isinstance(attributes, dict):
            out_attributes = []
            out_attributes.append(attributes)
        elif attributes is None or attributes == '':
            return None
        elif isinstance(attributes, list):
            out_attributes = attributes
        else:
            self.module.fail_json(
                msg="Use only a single {key:val} pair or list of [{key:val}, {key:val}] pair  " + "{}.".format(attributes))

        attr = {}
        for item in out_attributes:
            if isinstance(item, dict) and len(item.keys()) > 1:
                self.module.fail_json(msg="A dict was sent with more then one key/val pair. Please use {key:val } only .")
            elif len(item.keys()) == 1 and len(item.values()) == 1:
                attr[item.keys()[0]] = {'value': item.values()[0]}
            else:
                self.module.fail_json(msg="A dict was sent with more then one key/val pair. Please use {key:val } only .")
        return attr


def _are_records_equivalent(a_record_1, a_record_2):
    """
    Checks whether the given records are equivalent (ignoring irrelevant properties).
    :param a_record_1: first A record
    :param a_record_2: second A record
    :return: whether the records are equivalent
    """
    a_record_1 = copy(a_record_1)
    a_record_2 = copy(a_record_2)

    ignore_properties = {_ID_PROPERTY}
    if not (a_record_1.get(_USE_TTL_PROPERTY, True) or a_record_2.get(_USE_TTL_PROPERTY, True)):
        # Not using TTL property therefore we don't care what the TTL value
        # is
        ignore_properties.add(_TTL_PROPERTY)

    for property in ignore_properties:
        for a_record in [a_record_1, a_record_2]:
            a_record.pop(property, None)

    return a_record_1 == a_record_2


def _is_int(s):
    if s is None or s == '':
        return None
    try:
        return int(s)
    except ValueError:
        self.module.fail_json(msg="TTL must be an int or be able to convert into an int.")

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------


def main():
    """
    Ansible module to manage infoblox opeartion by using rest api
    """
    module = AnsibleModule(
        argument_spec=dict(
            server=dict(required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            action=dict(required=True, choices=[
                "get_aliases", "get_cname", "get_a_record", "get_host", "get_network", "get_range",
                "get_next_available_ip", "get_fixedaddress", "get_ipv6network", "get_ptr_record",
                "get_srv_record", "get_auth_zone", "get_forward_zone", "get_delegated_zone",
                "add_alias", "add_cname", "add_host", "add_ipv6_host", "create_ptr_record",
                "get_txt_record", "get_network_container", "get_next_available_network",
                "create_a_record", "create_srv_record", "create_auth_zone", "create_forward_zone",
                "create_delegated_zone", "create_txt_record", "create_network_container",
                "create_network",
                "set_a_record", "set_name", "set_extattr", "update_a_record", "update_srv_record",
                "update_ptr_record", "update_cname_record", "update_auth_zone", "update_forward_zone",
                "update_txt_record", "update_network_container", "update_host_record",
                "delete_alias", "delete_cname", "delete_a_record", "delete_fixedaddress", "delete_host",
                "delete_ptr_record", "delete_srv_record",
                "reserve_next_available_ip"
            ]),
            host=dict(required=False),
            network=dict(required=False),
            start_addr=dict(required=False),
            end_addr=dict(required=False),
            object_ref=dict(required=False),
            name=dict(required=False, type='str'),
            address=dict(required=False),
            addresses=dict(required=False, type="list"),
            alias=dict(required=False),
            attr_name=dict(required=False),
            attr_value=dict(required=False),
            cname=dict(required=False, type='str'),
            current=dict(required=False, type="dict"),
            canonical=dict(required=False, type='str'),
            srv_attr=dict(required=False, type="dict"),
            txt=dict(required=False, type='str'),
            fqdn=dict(required=False, type="raw"),
            filters=dict(required=False, type="raw"),
            delegate_to=dict(required=False, type='raw'),
            cidr=dict(required=False, type='raw'),
            comment=dict(required=False,
                         default="Object managed by ansible-infoblox module"),
            api_version=dict(required=False, default="1.7.1"),
            dns_view=dict(required=False, default="default"),
            net_view=dict(required=False, default="default"),
            extattrs=dict(required=False, default=None, type='raw'),
            ttl=dict(required=False)
        ),
        #mutually_exclusive=[
        #    ["network", "address"],
        #    ["addresses", "address"],
        #    ["host", "cname"]
        #],
        #required_together=[
        #    ["attr_name", "attr_value"],
            # ["object_ref","name"]
        #],
        supports_check_mode=True,
    )

    if not HAS_REQUESTS:
        module.fail_json(
            msg="Library 'requests' is required. Use 'sudo pip install requests' to fix it.")

    """
    Global vars
    """
    server = module.params["server"]
    username = module.params["username"]
    password = module.params["password"]
    action = module.params["action"]
    host = module.params["host"]
    object_ref = module.params["object_ref"]
    name = module.params["name"]
    network = module.params["network"]
    start_addr = module.params["start_addr"]
    end_addr = module.params["end_addr"]
    address = module.params["address"]
    addresses = module.params["addresses"]
    alias = module.params["alias"]
    attr_name = module.params["attr_name"]
    attr_value = module.params["attr_value"]
    extattrs = module.params["extattrs"]
    cname = module.params["cname"]
    canonical = module.params["canonical"]
    comment = module.params["comment"]
    current = module.params.get("current")
    api_version = module.params["api_version"]
    dns_view = module.params["dns_view"]
    net_view = module.params["net_view"]
    txt = module.params["txt"]
    filters = module.params["filters"]
    srv_attr = module.params["srv_attr"]
    delegate_to = module.params["delegate_to"]
    fqdn = module.params["fqdn"]
    ttl = _is_int(module.params["ttl"])
    cidr = _is_int(module.params["cidr"])

    infoblox = Infoblox(module, server, username, password,
                        api_version, dns_view, net_view)

    if action == "get_network":
        if network:
            result = infoblox.get_network(network)
            if result:
                module.exit_json(result=result)
            else:
                module.exit_json(msg="Network %s not found" % network)
        elif filters:
            result = infoblox.get_network(None, filters)
            if isinstance(result, list):
                module.exit_json(result=result)
            #elif result == []:
            #    module.exit_json(result=result)
            else:
                module.exit_json(msg="There was an issue with get_network filters")
        else:
            raise Exception(
                "You must specify the option 'network' or 'address'.")

    if action == "get_range":
        if start_addr and end_addr:
            result = infoblox.get_range(start_addr, end_addr)
            if result:
                module.exit_json(result=result)
            else:
                module.exit_json(msg="Range %s not found" % network)
        else:
            raise Exception(
                "You must specify the options 'start_addr' and 'end_addr'.")

    elif action == "get_ipv6network":
        if network:
            result = infoblox.get_ipv6network(network)
            if result:
                module.exit_json(result=result)
            else:
                module.exit_json(msg="IPv6 Network %s not found" % network)
        else:
            raise Exception(
                "You must specify the option 'network' or 'address'.")

    elif action == "get_next_available_ip":
        if network:
            result = infoblox.get_network(network)
        elif start_addr and end_addr:
            result = infoblox.get_range(start_addr, end_addr)
        else:
            module.exit_json(msg="You must specify the option 'network'.")
        #return result
        if result:
            network_ref = result[0]["_ref"]
            result = infoblox.get_next_available_ip(network_ref)
            if result:
                ip = result["ips"][0]
                module.exit_json(result=ip)
            else:
                module.fail_json(
                    msg="No available IPs in network: %s" % network)
        else:
            module.fail_json(
                msg="No available IPs in network: %s" % network)

    elif action == "get_next_available_network":
        result = infoblox.get_next_available_network(network, cidr)
        if result:
            module.exit_json(msg=result)
        else:
            module.fail_json(msg="You must specify the option 'network'.")

    elif action == "reserve_next_available_ip":
        result = infoblox.reserve_next_available_ip(network)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()

    elif action == "get_fixedaddress":
        result = infoblox.get_fixedaddress(address)
        if result:
            module.exit_json(result=result)
        else:
            module.exit_json(msg="FIXEDADDRESS %s not found" % address)

    elif action == "get_aliases":
        result = infoblox.get_aliases(host)
        if result:
            if "aliases" in result[0]:
                module.exit_json(result=result[0]["aliases"])
            else:
                module.exit_json(msg="Aliases not found for host %s" % host)
        else:
            module.exit_json(msg="Host %s not found" % host)

    elif action == "get_cname":
        result = infoblox.get_cname(cname)
        if result:
            module.exit_json(result=result)
        else:
            module.exit_json(msg="CNAME %s not found" % cname)

    elif action == "get_a_record":
        result = infoblox.get_a_record(name)
        if result:
            module.exit_json(result=result)
        else:
            module.exit_json(msg="No A record for name %s" % name)

    elif action == "get_host":
        result = infoblox.get_host_by_name(host)
        if result:
            module.exit_json(result=result)
        else:
            module.exit_json(msg="Host %s not found" % host)

    elif action == "add_alias":
        result = infoblox.get_aliases(host)
        if result:
            object_ref = result[0]["_ref"]
            aliases = {}
            if "aliases" in result[0]:
                alias_list = result[0]["aliases"]
            else:
                alias_list = []
            alias_list.append(alias)
            aliases["aliases"] = alias_list
            result = infoblox.update_host_alias(object_ref, aliases)
            if result:
                module.exit_json(changed=True, result=result)
            else:
                raise Exception()
        else:
            module.exit_json(msg="Host %s not found" % host)

    elif action == "add_cname":
        result = infoblox.create_cname(cname, canonical, comment)
        if result:
            result = infoblox.get_cname(cname)
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()

    elif action == "set_a_record":
        if not address and not addresses:
            module.fail_json(msg="Must specify `address` xor `addresses`")
        if address:
            addresses = {address}
            del address
        addresses = set(addresses)

        a_records = infoblox.get_a_record(name)
        desired_a_records = {address: _create_a_record_model(name, address, infoblox.dns_view, comment, ttl)
                             for address in addresses}

        a_records_to_delete = []
        a_records_to_update = []
        a_records_to_leave = []

        for a_record in a_records:
            address = a_record[_IPV4_ADDRESS_PROPERTY]
            if address not in addresses:
                a_records_to_delete.append(a_record)
            else:
                if _are_records_equivalent(desired_a_records[address], a_record):
                    a_records_to_leave.append(a_record)
                else:
                    a_records_to_update.append(a_record)

        # Note: being lazy and doing an update using a delete + create
        for a_record in a_records_to_delete + a_records_to_update:
            infoblox.delete_object(a_record[_ID_PROPERTY])

        addresses_of_a_records_to_create = {a_record[_IPV4_ADDRESS_PROPERTY] for a_record in a_records_to_update} \
            | (addresses - {a_record[_IPV4_ADDRESS_PROPERTY] for a_record in a_records_to_leave})

        if len(addresses_of_a_records_to_create) == 0:
            module.exit_json(changed=False, result=a_records)
        else:
            for address in addresses_of_a_records_to_create:
                infoblox.create_a_record(name, address, comment, ttl, extattrs)

            # Validation
            set_a_records = infoblox.get_a_record(name)
            assert len(set_a_records) == len(
                addresses) == len(desired_a_records)
            for a_record in set_a_records:
                assert _are_records_equivalent(
                    desired_a_records[a_record[_IPV4_ADDRESS_PROPERTY]], a_record)

            module.exit_json(changed=True, result=set_a_records)

    elif action == "add_host":
        network_ref = None
        if network:
            network_ref = infoblox.get_network(network)
        elif start_addr and end_addr:
            network_ref = infoblox.get_range(start_addr, end_addr)
        elif address:
            # Fix for when network or range is not needed
            pass
        else:
            raise Exception("No network or range start/end address specified")
        if network_ref:
            network_ref = network_ref[0]["_ref"]  # Break ref out of dict
            result = infoblox.create_host_record(host, address, network_ref, comment, ttl, extattrs)
        elif address:
            # Fix for when network or range is not needed
            result = infoblox.create_host_record(host, address, None, comment, ttl, extattrs)
        else:
            raise Exception("No network/range found for specified parameters")
        if result:
            result = infoblox.get_host_by_name(host)
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()

    elif action == "add_ipv6_host":
        result = infoblox.create_ipv6_host_record(
            host, network, address, comment)
        if result:
            result = infoblox.get_host_by_name(host)
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()

    elif action == "delete_alias":
        result = infoblox.get_aliases(host)
        if result:
            if "aliases" in result[0]:
                object_ref = result[0]["_ref"]
                alias_list = result[0]["aliases"]
                alias_list.remove(alias)
                aliases = dict()
                aliases["aliases"] = alias_list
                result = infoblox.update_host_alias(object_ref, aliases)
                if result:
                    module.exit_json(changed=True, result=result)
                else:
                    raise Exception()
            else:
                module.exit_json(msg="No aliases found in Host %s" % host)
        else:
            module.exit_json(msg="Host %s not found" % host)

    elif action == "delete_host":
        result = infoblox.get_host_by_name(host)
        if result:
            result = infoblox.delete_object(result[0]["_ref"])
            module.exit_json(changed=True, result=result,
                             msg="Object {name} deleted".format(name=host))
        else:
            module.exit_json(msg="Host %s not found" % host)

    elif action == "delete_fixedaddress":
        result = infoblox.get_fixedaddress(address)
        if result:
            result = infoblox.delete_object(result[0]["_ref"])
            module.exit_json(changed=True, result=result,
                             msg="Object {name} deleted".format(name=address))
        else:
            module.exit_json(msg="Fixedaddress %s not found" % address)

    elif action == "delete_cname":
        result = infoblox.get_cname(cname)
        if result:
            result = infoblox.delete_object(result[0]["_ref"])
            module.exit_json(changed=True, result=result,
                             msg="Object {name} deleted".format(name=cname))
        else:
            module.exit_json(msg="CNAME %s not found" % cname)

    elif action == "delete_a_record":
        if address:
            result = infoblox.delete_a_record(name, address)
            if result:
                module.exit_json(changed=True, result=result)
            else:
                raise Exception()
        result = infoblox.get_a_record(name)
        if result:
            result = infoblox.delete_object(result[0]["_ref"])
            module.exit_json(changed=True, result=result,
                             msg="Object {name} deleted".format(name=name))
        else:
            module.exit_json(msg="A record with name %s not found" % name)

    elif action == "set_name":
        result = infoblox.set_name(object_ref, name)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()

    elif action == "set_extattr":
        result = infoblox.get_host_by_name(host)
        if result:
            host_ref = result[0]["_ref"]
            result = infoblox.set_extattr(host_ref, attr_name, attr_value)
            if result:
                module.exit_json(changed=True, result=result)
            else:
                raise Exception()
    elif action == "get_ptr_record":
        result = infoblox.get_ptr_record(address)
        if result:
            module.exit_json(result=result)
        else:
            raise Exception()
    elif action == "create_ptr_record":
        result = infoblox.create_ptr_record(name, address, comment, ttl, extattrs)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()
    elif action == "update_ptr_record":
        result = infoblox.update_ptr_record(name, address, current, comment, ttl, extattrs)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()
    elif action == "delete_ptr_record":
        result = infoblox.delete_ptr_record(name, address)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()
    elif action == "update_cname_record":
        result = infoblox.update_cname_record(cname, canonical, current, comment, ttl, extattrs)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()
    elif action == "delete_cname_record":
        result = infoblox.delete_cname_record(cname)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()
    elif action == "get_a_record":
        result = infoblox.get_a_record(name)
        if result:
            module.exit_json(result=result)
        else:
            raise Exception()
    elif action == "create_a_record":
        result = infoblox.create_a_record(name, address, comment, ttl, extattrs)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()
    elif action == "update_a_record":
        result = infoblox.update_a_record(name, address, current, comment, ttl, extattrs)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()
    elif action == "get_srv_record":
        result = infoblox.get_srv_record(name)
        if result:
            module.exit_json(result=result)
        else:
            raise Exception()
    elif action == "create_srv_record":
        result = infoblox.create_srv_record(name, srv_attr, comment, ttl, extattrs)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()
    elif action == "update_srv_record":
        result = infoblox.update_srv_record(name, srv_attr, current, comment, ttl, extattrs)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()
    elif action == "delete_srv_record":
        result = infoblox.delete_srv_record(name)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()
    elif action == "get_txt_record":
        result = infoblox.get_txt_record(name)
        if result:
            module.exit_json(result=result)
        else:
            raise Exception()
    elif action == "create_txt_record":
        result = infoblox.create_txt_record(name, txt, comment, ttl, extattrs)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()
    elif action == "update_txt_record":
        result = infoblox.update_txt_record(name, txt, current, comment, ttl, extattrs)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()
    elif action == "update_host_record":
        result = infoblox.update_host_record(host, address, current, comment, ttl, extattrs)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()
    elif action == "create_network":
        result = infoblox.create_network(network, comment, ttl, extattrs)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()
    elif action == "get_network_container":
        result = infoblox.get_network_container(network)
        if result:
            module.exit_json(result=result)
        else:
            raise Exception()
    elif action == "create_network_container":
        result = infoblox.create_network_container(network, comment, ttl, extattrs)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()
    elif action == "update_network_container":
        result = infoblox.update_network_container(network, comment, ttl, extattrs)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()
    elif action == "get_auth_zone":
        result = infoblox.get_auth_zone(fqdn)
        if result:
            module.exit_json(result=result)
        else:
            raise Exception()
    elif action == "create_auth_zone":
        result = infoblox.create_auth_zone(fqdn, comment, ttl, extattrs)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()
    elif action == "update_auth_zone":
        result = infoblox.update_auth_zone(fqdn, comment, ttl, extattrs)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()
    elif action == "get_forward_zone":
        result = infoblox.get_forward_zone(fqdn)
        if result:
            module.exit_json(result=result)
        else:
            raise Exception()
    elif action == "create_forward_zone":
        result = infoblox.create_forward_zone(fqdn, name, address, comment, ttl, extattrs)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()
    elif action == "update_forward_zone":
        result = infoblox.update_forward_zone(fqdn, name, address, comment, ttl, extattrs)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()
    elif action == "get_delegated_zone":
        result = infoblox.get_delegated_zone(fqdn)
        if result:
            module.exit_json(result=result)
        else:
            raise Exception()
    elif action == "create_delegated_zone":
        result = infoblox.create_delegated_zone(fqdn, delegate_to, comment, ttl, extattrs)
        if result:
            module.exit_json(changed=True, result=result)
        else:
            raise Exception()


if __name__ == "__main__":
    main()
