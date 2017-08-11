#!/usr/bin/python
from copy import copy

from ansible.module_utils.basic import AnsibleModule 

try:
    import requests
    requests.packages.urllib3.disable_warnings()
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
module: infoblox
author:
  - "Joan Miquel Luque (@xoanmi)"
short_description: Manage Infoblox via Web API
description:
  - Manage Infoblox IPAM and DNS via Web API
version_added: "2.3"
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
    choices: ["get_host", "get_network", "get_range", "get_ipv6network", "get_next_available_ip", "add_host", "add_ipv6host", "delete_host", "set_extattr"]
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

RETURN = """
hostname:
  description: Hostname of the object
  returned: success
  type: str
  sample: test1.local
result:
  description: result returned by the infoblox web API
  returned: success
  type: json
  samble:
    {
      "_ref": "record:host/DSFRerZfeSDRFWEC2RzLm5hZ2lvcw:test1.local/Private",
      "extattrs": {},
      "ipv4addrs": [
        {
          "_ref": "record:host_ipv4addr/ZG5zLmhvc3RdsDFSAfwRCwrcBNyamniMIOtMOMRNsdEwLjE2Mi4yMzguMjMyLg:192.168.1.1002/test1.local/Private",
          "configure_for_dhcp": false,
          "host": "test1.local",
          "ipv4addr": "192.168.1.100"
        }
      ],
      "name": "test1.local",
      "view": "Private"
    }
"""

EXAMPLES = """
---
 - hosts: localhost
    connection: local
       gather_facts: False

  tasks:
  - name: Add host
    infoblox:
      server=192.168.1.1
      username=admin
      password=admin
      action=add_host
      network=192.168.1.0/24
      host={{ item }}
    with_items:
      - test01.local
      - test02.local
    register: infoblox

  - name: Do awesome stuff with the result
    debug: msg="Get crazy!"
"""

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
_IPV4_ADDRS_PROPERTY = "ipv4addr"
_IPV6_ADDRS_PROPERTY = "ipv6addr"
_FQDN_PROPERTY = "fqdn"
_FORWARD_TO_PROPERTY = "forward_to"
_NETWORK_PROPERTY = "network"


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
                           _NETWORK_PROPERTY]

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
            if model_dict.get(model):
                return_model[model] = model_dict.get(model)
        return return_model

    # ---------------------------------------------------------------------------
    # get_network()
    # ---------------------------------------------------------------------------
    def get_network(self, network):
        """
        Search network in infoblox by using rest api
        Network format supported:
            - 192.168.1.0
            - 192.168.1.0/24
        """
        if not network:
            self.module.exit_json(msg="You must specify the option 'network'.")
        params = {"network": network, "network_view": self.net_view}
        return self.invoke("get", "network", params=params)

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
            self.module.exit_json(
                msg="You must specify the option 'start_addr.")
        if not end_addr:
            self.module.exit_json(msg="You must specify the option 'end_addr.")
        params = {"start_addr": start_addr,
                  "end_addr": end_addr, "network_view": self.net_view}
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
            self.module.exit_json(msg="You must specify the option 'network'.")
        params = {"network": network, "network_view": self.net_view}
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
    # reserve_next_available_ip()
    # ---------------------------------------------------------------------------
    def reserve_next_available_ip(self, network, mac_addr=None,
                                  comment=None, extattrs=None):
        """
        Reserve ip address via fixedaddress in infoblox by using rest api
        """
        if comment is None:
            comment = "IP reserved via ansible infoblox module"
        if extattrs is not None:
            extattrs = add_attr(extattrs)

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
    # get_cname()
    # ---------------------------------------------------------------------------
    def get_cname(self, cname):
        """
        Search CNAME by FQDN in infoblox by using rest api
        """
        if not cname:
            self.module.exit_json(msg="You must specify the option 'cname'.")

        params = {_NAME_PROPERTY: name, _VIEW_PROPERTY: self.dns_view}
        return self.invoke("get", "record:cname", params=params)

    # ---------------------------------------------------------------------------
    # create_cname()
    # ---------------------------------------------------------------------------
    def create_cname(self, cname, canonical, comment=None, extattrs=None):
        """
        Add CNAME in infoblox by using rest api
        """
        if cname is None or canonical is None:
            self.module.exit_json(
                msg="You must specify the option 'name' and 'canonical'.")
        if extattrs is not None:
            extattrs = add_attr(extattrs)

        model = {_NAME_PROPERTY: name, _CANONICAL_PROPERTY: canonical,
                 _VIEW_PROPERTY: self.dns_view, _COMMENT_PROPERTY: comment,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("post", "record:cname", ok_codes=(200, 201, 400), json=model)

    # ---------------------------------------------------------------------------
    # update_cname_record()
    # ---------------------------------------------------------------------------
    def update_cname_record(self, current_cname, current_canonical, desired_cname,
                            desired_canonical, comment=None, extattrs=None):
        """
        Update alias for a cname entry
        """
        object_ref = None
        cnames = self.get_cname(current_cname)

        for cname in cnames:
            if cname.get('name') == current_cname:
                key_out = cname.get('_ref')
                object_ref = key_out.split(
                    ':')[0] + ':' + key_out.split(':')[1]
                comment = cname.get('comment')
                ttl = cname.get('ttl')
                break

        if not object_ref:
            msg = "IP {} and ptrdname {} pair was not found.".format(
                current_ip, current_name)
            self.module.exit_json(msg=msg)

        if object_ref is None:
            self.module.exit_json(
                msg="Name {} was not found.".format(current_name))

        model = {_NAME_PROPERTY: desired_name, _CANONICAL_PROPERTY: desired_canonical,
                 _VIEW_PROPERTY: self.dns_view, _COMMENT_PROPERTY: comment,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("put", object_ref, json=model)

    # ---------------------------------------------------------------------------
    # get_a_record()
    # ---------------------------------------------------------------------------
    def get_a_record(self, name):
        """
        Retrieves information about the A record with the given name.
        """
        if not name:
            self.module.exit_json(msg="You must specify the option 'name'.")

        property_list = [_IPV4_ADDRESS_PROPERTY]
        my_property = self._return_property(True, property_list)
        params = {_NAME_PROPERTY: name, _VIEW_PROPERTY: self.dns_view,
                  _RETURN_FIELDS_PROPERTY: my_property}
        return self.invoke("get", "record:a", params=params)

    # ---------------------------------------------------------------------------
    # create_a_record()
    # ---------------------------------------------------------------------------
    def create_a_record(self, name, address, comment, ttl=None, extattrs=None):
        """
        Creates an A record with the given name that points to the given IP address.

        For documentation on how to use the related part of the InfoBlox WAPI, refer to:
        https://ipam.illinois.edu/wapidoc/objects/record.a.html
        """
        if not name or not address:
            self.module.exit_json(
                msg="You must specify the option 'name' and 'address'.")
        if extattrs is not None:
            extattrs = add_attr(extattrs)

        model = {_NAME_PROPERTY: name, _IPV4_ADDRESS_PROPERTY: address,
                 _VIEW_PROPERTY: self.dns_view, _COMMENT_PROPERTY: comment,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("post", "record:a", ok_codes=(200, 201, 400), json=model)

    # ---------------------------------------------------------------------------
    # get_ptr_record()
    # ---------------------------------------------------------------------------
    def get_ptr_record(self, address):
        """
        Retrieves information about the PTR record with the given address.
        """
        if not address:
            self.module.exit_json(msg="You must specify the option 'address'.")

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
            extattrs = add_attr(extattrs)

        model = {_PTRDNAME_PROPERTY: name, _NAME_PROPERTY: name, _IPV4_ADDRESS_PROPERTY: address,
                 _VIEW_PROPERTY: self.dns_view, _COMMENT_PROPERTY: comment,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("post", "record:ptr", ok_codes=(200, 201, 400), json=model)

    # ---------------------------------------------------------------------------
    # update_ptr_record()
    # ---------------------------------------------------------------------------
    def update_ptr_record(self, current_address, current_name, desired_address, desired_name, extattrs=None):
        """
        Update alias for a ptr record
        """
        object_ref = None
        ptrs = self.get_ptr_record(current_address)
        for current_ptr in ptrs:
            if current_ptr.get('ptrdname') == current_name:
                key_out = current_ptr.get('_ref')
                object_ref = key_out.split(
                    ':')[0] + ':' + key_out.split(':')[1]
                comment = current_ptr.get('comment')
                ttl = current_ptr.get('ttl')
                break

        if object_ref is None:
            self.module.exit_json(msg="IP {} and ptrdname {} pair was not found.".format(
                current_ip, current_name))
        if extattrs is not None:
            extattrs = add_attr(extattrs)

        model = {_PTRDNAME_PROPERTY: desired_name, _NAME_PROPERTY: desired_name,
                 _IPV4_ADDRESS_PROPERTY: desired_address,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("put", object_ref, json=model)

    # ---------------------------------------------------------------------------
    # get_srv_record()
    # ---------------------------------------------------------------------------
    def get_srv_record(self, name):
        """
        Retrieves information about the SRV record with the given name.
        """
        if not name:
            self.module.exit_json(msg="You must specify the option 'address'.")

        property_list = [_IPV4_ADDRESS_PROPERTY, _PTRDNAME_PROPERTY, _WEIGHT_PROPERTY,
                         _PORT_PROPERTY, _PRIORITY_PROPERTY, _TARGET_PROPERTY]
        my_property = self._return_property(True, property_list)
        params = {_NAME_PROPERTY: name, _VIEW_PROPERTY: self.dns_view,
                  _RETURN_FIELDS_PROPERTY: my_property}
        return self.invoke("get", "record:srv", params=params)

    # ---------------------------------------------------------------------------
    # create_srv_record()
    # ---------------------------------------------------------------------------
    def create_srv_record(self, name, port, priority, dns_target, weight, comment=None, ttl=None, extattrs=None):
        """
        Creates an SRV record with the name and .
        For documentation on how to use the related part of the InfoBlox WAPI, refer to:
        https://ipam.illinois.edu/wapidoc/objects/record.srv.html
        """
        if extattrs is not None:
            extattrs = add_attr(extattrs)

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
    def update_srv_record(self, current_name, desired_name, port, priority, dns_target, weight, comment=None, ttl=None, extattrs=None):
        """
        Update svr record for a named entry
        """
        object_ref = None
        srvs = self.get_srv_record(current_name)

        for srv in srvs:
            if srv.get('name') == current_name:
                key_out = srv.get('_ref')
                object_ref = key_out.split(
                    ':')[0] + ':' + key_out.split(':')[1]
                comment = srv.get('comment')
                break

        if object_ref is None:
            self.module.exit_json(
                msg="Name {} was not found.".format(current_name))

        model = {_NAME_PROPERTY: name, _PORT_PROPERTY: port,
                 _PRIORITY_PROPERTY: priority, _TARGET_PROPERTY: dns_target,
                 _WEIGHT_PROPERTY: weight, _COMMENT_PROPERTY: comment,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("put", object_ref, json=model)

    # ---------------------------------------------------------------------------
    # get_txt_record()
    # ---------------------------------------------------------------------------
    def get_txt_record(self, name):
        """
        Retrieves information about the PTR record with the given name.
        """
        if not name:
            self.module.exit_json(msg="You must specify the option 'name'.")

        property_list = [_IPV4_ADDRESS_PROPERTY,
                         _COMMENT_PROPERTY, _TXT_PROPERTY]
        my_property = self._return_property(True, property_list)
        params = {_NAME_PROPERTY: name, _VIEW_PROPERTY: self.dns_view,
                  _RETURN_FIELDS_PROPERTY: my_property}
        return self.invoke("get", "record:txt", params=params)

    # ---------------------------------------------------------------------------
    # create_txt_record()
    # ---------------------------------------------------------------------------
    def create_txt_record(self, name, text, comment=None, ttl=None, extattrs=None):
        """
        Creates an PTR record with the given name that points to the given IP address.
        For documentation on how to use the related part of the InfoBlox WAPI, refer to:
        https://ipam.illinois.edu/wapidoc/objects/record.txt.html
        """
        if not name or not txt:
            self.module.exit_json(
                msg="You must specify the option 'name' and 'txt'.")
        if extattrs is not None:
            extattrs = add_attr(extattrs)

        model = {_NAME_PROPERTY: name, _TXT_PROPERTY: text,
                 _VIEW_PROPERTY: self.dns_view,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
                 _COMMENT_PROPERTY: comment, _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("post", "record:txt", ok_codes=(200, 201, 400), json=model)

    # ---------------------------------------------------------------------------
    # update_txt_record()
    # ---------------------------------------------------------------------------
    def update_txt_record(self, current_name, desired_name, desired_text, **kwargs):
        """
        Update alias for a txt record
        """
        object_ref = None
        if kwargs is not None:
            current_text = kwargs.get('current_text')
            first_found = kwargs.get('first_found')
            comment = kwargs.get('comment')
            extattrs = kwargs.get('current_text')

        if first_found is not None and current_text is not None:
            self.module.exit_json(
                msg="Please Specify either current_text or first_found, but not both.")

        txts = self.get_txt_record(current_name)
        if current_text:
            for index, current_txt in entxts:
                if current_txt.get('name') == current_name and current_txt.get('text') == current_text:
                    my_entry = index
        else:
            my_entry = 0

        used_txt = txts[my_entry]
        key_out = used_txt.get('_ref')
        object_ref = key_out.split(':')[0] + ':' + key_out.split(':')[1]
        comment = used_txt.get('comment')
        ttl = used_txt.get('ttl')

        if object_ref is None:
            self.module.exit_json(
                msg="Name {} was not found.".format(current_name))
        if extattrs is not None:
            extattrs = add_attr(extattrs)

        model = {_NAME_PROPERTY: desired_name, _TXT_PROPERTY: desired_text,
                 _VIEW_PROPERTY: self.dns_view,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
                 _COMMENT_PROPERTY: comment, _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("put", object_ref, json=model)

    # ---------------------------------------------------------------------------
    # get_aliases()
    # ---------------------------------------------------------------------------
    def get_aliases(self, host):
        """
        Get all the aliases on a host
        """
        if not host:
            self.module.exit_json(msg="You must specify the option 'host'.")
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
            self.module.exit_json(msg="Object _ref required!")
        if extattrs is not None:
            extattrs = add_attr(extattrs)
        return self.invoke("put", object_ref, json=alias)

    # ---------------------------------------------------------------------------
    # get_host_by_name()
    # ---------------------------------------------------------------------------
    def get_host_by_name(self, host):
        """
        Search host by FQDN in infoblox by using rest api
        """
        if not host:
            self.module.exit_json(msg="You must specify the option 'host'.")
        params = {"name": host, "_return_fields+": "comment,extattrs",
                  "view": self.dns_view}
        return self.invoke("get", "record:host", params=params)

    # ---------------------------------------------------------------------------
    # create_host_record()
    # ---------------------------------------------------------------------------
    def create_host_record(self, host, network_ref, address, comment=None, ttl=None, extattrs=None):
        """
        Add host in infoblox by using rest api
        """
        if not host:
            self.module.exit_json(
                msg="You must specify the hostname parameter 'host'.")

        if extattrs is not None:
            extattrs = add_attr(extattrs)
            payload[_EXT_ATTR_PROPERTY] = extattrs

        if network_ref:
            address = "func:nextavailableip:" + network_ref
        elif address:
            pass
        else:
            raise Exception("Function options missing!")

        model = {_NAME_PROPERTY: host, _IPV4ADDRS_PROPERTY: [{"ipv4addr": address}],
                 _VIEW_PROPERTY: self.dns_view,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
                 _COMMENT_PROPERTY: comment, _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)

        return self.invoke("post", "record:host?_return_fields=ipv4addrs", ok_codes=(200, 201, 400), json=model)

    # ---------------------------------------------------------------------------
    # update_host_record()
    # ---------------------------------------------------------------------------
    def update_host_record(self, current_name, current_address, desired_name, desired_address, comment=None, ttl=None, extattrs=None):
        """
        Update a host record
        """
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
            extattrs = add_attr(extattrs)

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
            self.module.exit_json(msg="You must specify the option 'host'.")

        if network:
            address = "func:nextavailableip:" + network
        elif address:
            pass
        else:
            raise Exception("Function options missing!")

        if extattrs is not None:
            extattrs = add_attr(extattrs)

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
            self.module.exit_json(msg="You must specify the option 'name'.")

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
            self.module.exit_json(msg="You must specify the option 'name'.")

        if extattrs is not None:
            extattrs = add_attr(extattrs)

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
        fqdns = self.get_cname(current_fqdn)

        for fqdn in fqdns:
            if fqdn.get('name') == current_fqdn:
                key_out = fqdn.get('_ref')
                object_ref = key_out.split(':')[0]
                break

        if not object_ref:
            msg = "IP {} and ptrdname {} pair was not found.".format(
                current_ip, current_name)
            self.module.exit_json(msg=msg)

        if object_ref is None:
            self.module.exit_json(
                msg="Name {} was not found.".format(current_name))

        model = {_FQDN_PROPERTY: desired_name,
                 _VIEW_PROPERTY: self.dns_view, _COMMENT_PROPERTY: comment,
                 _USE_TTL_PROPERTY: ttl is not None, _TTL_PROPERTY: ttl,
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
            self.module.exit_json(msg="You must specify the option 'fqdn'.")

        params = {_FQDN_PROPERTY: fqdn, _VIEW_PROPERTY: self.dns_view}
        return self.invoke("get", "zone_forward", params=params)

    # ---------------------------------------------------------------------------
    # create_auth_zone()
    # ---------------------------------------------------------------------------
    def create_forward_zone(self, fqdn, name, address,
                            comment=None, ttl=None, extattrs=None):
        """
        Add FQDN in infoblox by using rest api
        """
        if fqdn is None:
            self.module.exit_json(msg="You must specify the option 'fqdn'.")

        if extattrs is not None:
            extattrs = add_attr(extattrs)
        if name != "dns-server":
            self.module.exit_json(msg="Currently only support dns-server.")

        forward_to = [{_NAME_PROPERTY: name, "address": address}]
        model = {_FQDN_PROPERTY: fqdn, _FORWARD_TO_PROPERTY: forward_to,
                 _VIEW_PROPERTY: self.dns_view, _COMMENT_PROPERTY: comment,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        print model
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
            self.module.exit_json(msg=msg)

        if object_ref is None:
            self.module.exit_json(
                msg="FQDN {} was not found.".format(current_fqdn))

        forward_to = [
            {_NAME_PROPERTY: desired_name, "address": desired_address}]
        model = {_FORWARD_TO_PROPERTY: forward_to,
                 _VIEW_PROPERTY: self.dns_view, _COMMENT_PROPERTY: comment,
                 _EXT_ATTR_PROPERTY: extattrs}
        model = self._make_model(model)
        return self.invoke("put", object_ref, json=model)

    # ---------------------------------------------------------------------------
    # get_ipam_network()
    # ---------------------------------------------------------------------------
    def get_ipam_network_container(self, network):
        """
        Search for IPAM network in infoblox by network
        """
        if network is None:
            self.module.exit_json(msg="You must specify the option 'network'.")

        property_list = ['network_container',
                         'network_view', _NETWORK_PROPERTY]
        my_property = self._return_property(False, property_list)
        params = {_NETWORK_PROPERTY: network,
                  _RETURN_FIELDS_PROPERTY: my_property}
        return self.invoke("get", "networkcontainer", params=params)

    # ---------------------------------------------------------------------------
    # delete_object()
    # ---------------------------------------------------------------------------
    def delete_object(self, obj_ref):
        """
        Delete object in infoblox by using rest api
        """
        if not obj_ref:
            self.module.exit_json(msg="Object _ref required!")
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
            self.module.exit_json(
                msg="You must specify the option 'object_ref''.")
        payload = {"extattrs": {attr_name: {"value": attr_value}}}
        return self.invoke("put", object_ref, json=payload)

    # ---------------------------------------------------------------------------
    # add_attr()
    # ---------------------------------------------------------------------------
    def add_attr(attributes):
        if isinstance(attributes, dict) and len(attributes.keys()) > 1:
            self.module.exit_json(
                msg="A dict was sent with more then one key/val pair. Please use {key:val } only .")
        elif isinstance(attributes, dict):
            attributes = [{attributes.keys()[0]: attributes.values()[0]}]

        attr = {}
        for item in attributes:
            if len(item.keys()) == 1 and len(item.values()) == 1:
                attr[item.keys()[0]] = {'value': item.values()[0]}
            else:
                self.module.exit_json(
                    msg="A dict was sent with more then one key/val pair. Please use {key:val } only .")
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
                "get_aliases", "get_cname", "get_a_record", "get_host", "get_network", "get_range", "get_next_available_ip",
                "get_fixedaddress", "get_ipv6network", "get_ptr_record"
                "add_alias", "add_cname", "add_host", "add_ipv6_host", "create_ptr_record",
                "set_a_record", "set_name", "set_extattr",
                "delete_alias", "delete_cname", "delete_a_record", "delete_fixedaddress", "delete_host",
                "reserve_next_available_ip"
            ]),
            host=dict(required=False),
            network=dict(required=False),
            start_addr=dict(required=False),
            end_addr=dict(required=False),
            object_ref=dict(required=False),
            name=dict(required=False),
            address=dict(required=False),
            addresses=dict(required=False, type="list"),
            alias=dict(required=False),
            attr_name=dict(required=False),
            attr_value=dict(required=False),
            cname=dict(required=False),
            canonical=dict(required=False),
            comment=dict(required=False,
                         default="Object managed by ansible-infoblox module"),
            api_version=dict(required=False, default="1.7.1"),
            dns_view=dict(required=False, default="default"),
            net_view=dict(required=False, default="default"),
            extattrs=dict(required=False, default=None),
            ttl=dict(required=False)
        ),
        mutually_exclusive=[
            ["network", "address"],
            ["addresses", "address"],
            ["host", "cname"]
        ],
        required_together=[
            ["attr_name", "attr_value"],
            # ["object_ref","name"]
        ],
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
    api_version = module.params["api_version"]
    dns_view = module.params["dns_view"]
    net_view = module.params["net_view"]
    ttl = module.params["ttl"]

    infoblox = Infoblox(module, server, username, password,
                        api_version, dns_view, net_view)

    if action == "get_network":
        if network:
            result = infoblox.get_network(network)
            if result:
                module.exit_json(result=result)
            else:
                module.exit_json(msg="Network %s not found" % network)
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
        else:
            module.exit_json(msg="You must specify the option 'network'.")

    elif start_addr and end_addr:
        result = infoblox.get_range(start_addr, end_addr)
        if result:
            network_ref = result[0]["_ref"]
            result = infoblox.get_next_available_ip(network_ref)
            if result:
                ip = result["ips"][0]
                module.exit_json(result=ip)
            else:
                module.fail_json(
                    msg="No available IPs in network: %s" % network)

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
        if network:
            network_ref = infoblox.get_network(network)

        elif start_addr and end_addr:
            network_ref = infoblox.get_range(start_addr, end_addr)
        else:
            raise Exception("No network or range start/end address specified")
        if network_ref:
            network_ref = network_ref[0]["_ref"]  # Break ref out of dict
        else:
            raise Exception("No network/range found for specified parameters")
        result = infoblox.create_host_record(
            host, network_ref, address, comment)
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


if __name__ == "__main__":
    main()
