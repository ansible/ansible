# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Mikhail Yohman (@fragmentedpacket) <mikhail.yohman@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

__metaclass__ = type

# Import necessary packages
import traceback
from ansible.module_utils.compat import ipaddress
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.net_tools.netbox.netbox_utils import (
    NetboxModule,
    ENDPOINT_NAME_MAPPING,
)


NB_IP_ADDRESSES = "ip_addresses"
NB_PREFIXES = "prefixes"

class NetboxIpamModule(NetboxModule):
    def __init__(self, module, endpoint):
        super().__init__(module, endpoint)

    def _handle_state_new_present(self, nb_app, nb_endpoint, endpoint_name, name, data):
        if data.get("address"):
            if self.state == "present":
                    self._ensure_object_exists(nb_endpoint, endpoint_name, name, data)
            elif self.state == "new":
                    self._create_netbox_object(nb_endpoint, data)
        else:
            if self.state == "present":
                    self._ensure_ip_in_prefix_present_on_netif(
                        nb_app, nb_endpoint, data
                    )
            elif self.state == "new":
                    self._get_new_available_ip_address(nb_app, data)

    def _ensure_ip_in_prefix_present_on_netif(self, nb_app, nb_endpoint, data):
        """
        """
        if not data.get("interface") or not data.get("prefix"):
            self._handle_errors("A prefix and interface are required")
    
        query_params = {
            "interface_id": data["interface"], "parent": data["prefix"],
        }
        if data.get("vrf"):
            query_params["vrf_id"] = data["vrf"]

        attached_ips = nb_endpoint.filter(**query_params)
        if attached_ips:
            self.nb_object = attached_ips[-1].serialize()
            self.result["changed"] = False
            self.result["msg"] = "IP Address %s already attached" % (self.nb_object["address"])
        else:
            self._get_new_available_ip_address(nb_app, data)
    
    def _get_new_available_ip_address(self, nb_app, data):
        prefix_query = self._build_query_params("prefix", data)
        prefix = nb_app.prefixes.get(**prefix_query)
        if not prefix:
            self.result["changed"] = False
            self.result["msg"] = "%s does not exist - please create first" % (data["prefix"])
        elif prefix.available_ips.list():
            self.nb_object, diff = self._create_netbox_object(prefix.available_ips, data)
            self.result["changed"] = True
            self.result["msg"] = "IP Address %s created" % (self.nb_object["address"])
            self.result["diff"] = diff
        else:
            self.result["changed"] = False
            self.result["msg"] = "No available IPs available within %s" % (data['prefix'])

    def _get_new_available_prefix(self, data):
        if not self.nb_object:
            self.result["changed"] = False
            self.result["msg"] = "Parent prefix does not exist: %s" % (data["parent"])
        elif self.nb_object.available_prefixes.list():
            self.nb_object, diff = self._create_netbox_object(self.nb_object.available_prefixes, data)
            self.result["changed"] = True
            self.result["msg"] = "Prefix %s created" % (self.nb_object["prefix"])
            self.result["diff"] = diff
        else:
            self.result["changed"] = False
            self.result["msg"] = "No available prefixes within %s" % (data["parent"])

    def run(self):
        """
        This function should have all necessary code for endpoints within the application
        to create/update/delete the endpoint objects
        Supported endpoints:
        - ip_addresses 
        - prefixes
        """
        # Used to dynamically set key when returning results
        endpoint_name = ENDPOINT_NAME_MAPPING[self.endpoint]

        self.result = {
            "changed": False,
        }

        application = self._find_app(self.endpoint)
        nb_app = getattr(self.nb, application)
        nb_endpoint = getattr(nb_app, self.endpoint)

        data = self.data

        if self.endpoint == "ip_addresses":
            name = data.get("address")
        elif self.endpoint == "prefixes":
            name = data.get("prefix")

        if self.module.params.get("first_available"):
            first_available = True
        else:
            first_available = False

        object_query_params = self._build_query_params(endpoint_name, data)
        if data.get("prefix") and self.endpoint == "ip_addresses":
            object_query_params = self._build_query_params("prefix", data)
            try:
                self.nb_object = nb_app.prefixes.get(**object_query_params)
            except ValueError:
                self._handle_errors(msg="More than one result returned for %s"
                    % (name)
                )
        else:
            try:
                self.nb_object = nb_endpoint.get(**object_query_params)
            except ValueError:
                self._handle_errors(msg="More than one result returned for %s"
                    % (name)
                )

        if self.state in ("new", "present") and endpoint_name == "ip_address":
            self._handle_state_new_present(nb_app, nb_endpoint, endpoint_name, name, data)
        elif self.state == "present" and first_available and data.get("parent"):
            self._get_new_available_prefix(data)
        elif self.state == "present":
            self._ensure_object_exists(nb_endpoint, endpoint_name, name, data)
        elif self.state == "absent":
            self._ensure_object_absent(endpoint_name, name)

        try:
            serialized_object = self.nb_object.serialize()
        except AttributeError:
            serialized_object = self.nb_object

        self.result.update({endpoint_name: serialized_object})

        self.module.exit_json(**self.result)
