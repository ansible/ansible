# -*- coding: utf-8 -*-

# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright: (c) 2019, Rubén del Campo Gómez <yo@rubendelcampo.es>
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import json
import xml.etree.cElementTree as ET
import ansible.module_utils.six.moves.urllib.parse as urllib

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.errors import AnsibleError, AnsibleConnectionFailure

try:
    import xmltodict
    HAS_XMLTODICT = True
except ImportError as e:
    HAS_XMLTODICT = False
    XMLTODICT_IMPORT_ERR = e


class SFOSModuleConfigurationError(Exception):

    def __init__(self, msg, **args):
        super(SFOSModuleConfigurationError, self).__init__(self, msg)
        self.msg = msg
        self.module_fail_args = args

    def do_fail(self, module):
        module.fail_json(msg=self.msg, other=self.module_fail_args)


class SFOSModule(AnsibleModule):
    """
    This is a helper class to construct any SFOS Module. This will automatically add the endpoint host, port, username,
    password, protocol, validate_certs and state field to the module. If you want to implement your own sophos xg module
    just initialize this SFOSModule class and define the Payload fields that are needed for your module.
    See the other modules like sfos_iphost for example.
    """

    def __init__(self, argument_spec, bypass_checks=False, no_log=False, check_invalid_arguments=None,
                 mutually_exclusive=None, required_together=None, required_one_of=None, add_file_common_args=False,
                 supports_check_mode=False, required_if=None):
        default_specs = dict(
            sfos_host=dict(type='str', required=True, fallback=(env_fallback, ['SFOS_HOST'])),
            sfos_port=dict(type='int', default=4444, fallback=(env_fallback, ['SFOS_PORT'])),
            sfos_username=dict(type='str', required=True, no_log=True, fallback=(env_fallback, ['SFOS_USERNAME'])),
            sfos_password=dict(type='str', required=True, no_log=True, fallback=(env_fallback, ['SFOS_PASSWORD'])),
            sfos_protocol=dict(type='str', required=False, default="https", choices=["https", "http"], fallback=(env_fallback, ['SFOS_PROTOCOL'])),
            validate_certs=dict(type='bool', required=False, default=True, fallback=(env_fallback, ['SFOS_VALIDATECERTS'])),
            state=dict(type='str', required=False, default='present', choices=['present', 'absent'])
        )
        super(SFOSModule, self).__init__(self._merge_specs(default_specs, argument_spec), bypass_checks, no_log,
                                         check_invalid_arguments, mutually_exclusive, required_together, required_one_of,
                                         add_file_common_args, supports_check_mode, required_if)

    def _merge_specs(self, default_specs, custom_specs):
        result = default_specs.copy()
        result.update(custom_specs)
        return result


class SFOS:

    def __init__(self, module, endpoint, change_relevant_keys, bool_keys, argument_spec, info_only=False):
        """
        Initialize SFOS Class
        :param module: The Ansible module
        :param endpoint: The corresponding endpoint to the module
        :param change_relevant_keys: The keys of the object to check for changes
        :param info_only: When implementing an info module, set this to true. Will allow access to the info method only
        """
        self.info_only = info_only
        self.module = module
        self.argument_spec = argument_spec
        self.endpoint = endpoint
        self.bool_keys = bool_keys

        if not HAS_XMLTODICT:
            raise Exception("xmltodict is not installed: %s" % to_native(XMLTODICT_IMPORT_ERR))

        self.request_url = module.params.get('sfos_protocol') + "://" + module.params.get('sfos_host') + ":" + to_native(
            module.params.get('sfos_port')) + "/webconsole/APIController?reqxml="

        """
        The change_relevant_keys will be checked for changes to determine whether the object needs to be updated
        """
        self.change_relevant_keys = change_relevant_keys
        self.module.params['sfos_username'] = module.params.get('sfos_username')
        self.module.params['sfos_password'] = module.params.get('sfos_password')
        if all(elem in self.change_relevant_keys for elem in module.params.keys()):
            raise SFOSModuleConfigurationError(
                "The keys " + to_native(
                    self.change_relevant_keys) + " to check are not in the modules keys:\n" + to_native(
                    module.params.keys()))

    def execute(self):
        try:
            if not self.info_only:
                if self.module.params.get('state') == 'present':
                    self._add()
                elif self.module.params.get('state') == 'absent':
                    self._remove()
            else:
                self._info()
        except Exception as e:
            self.module.fail_json(msg=to_native(e))

    def _info(self):
        """
        gathers facts for an object in Sophos XG
        """
        exists, result = self._lookup_entry(self.module, self.request_url)

        if exists:
            if type(result) == list:
                for item in result:
                    for k, v in list(item.items()):
                        if not k.startswith('@'):
                            item[k.lower()] = v  # copy lowercase result keys
                        item.pop(k)  # remove the rest of keys, including xml attributes
            else:
                for k, v in list(result.items()):
                    if not k.startswith('@'):
                        result[k.lower()] = v  # copy lowercase result keys
                    result.pop(k)  # remove the rest of keys, including xml attributes

            self.module.exit_json(result=result, changed=False)
        else:
            self.module.exit_json(changed=False)

    def _construct_xml_request(self, method, operation=""):
        """
        Construct XML request
        :param method:
        :param operation: Operation to perform, can be Get, Set or Remove
        :return:
        """
        Request = ET.Element("Request")
        Login = ET.SubElement(Request, "Login")
        Method = ET.SubElement(Request, method, operation=operation)
        Endpoint = ET.SubElement(Method, self.endpoint)

        if method is "Get":
            if self.info_only:
                if self.module.params.get('name'):
                    Filter = ET.SubElement(Endpoint, "Filter")
                    ET.SubElement(Filter, "key", name="Name", criteria=self.module.params.get('criteria')).text = self.module.params.get('name')
            else:
                Filter = ET.SubElement(Endpoint, "Filter")
                ET.SubElement(Filter, "key", name="Name", criteria="=").text = self.module.params.get('name')
        else:
            for k in list(self.argument_spec.keys()):
                if self.module.params.get(k):
                    if type(self.module.params.get(k)) == list:
                        if "item" not in self.argument_spec[k]:
                            ET.SubElement(Endpoint, k).text = str(','.join(map(str, self.module.params.get(k))))
                        else:
                            List = ET.SubElement(Endpoint, k)
                            for item in list(self.module.params.get(k)):
                                ET.SubElement(List, self.argument_spec[k]["item"]).text = str(item)
                    else:
                        ET.SubElement(Endpoint, k).text = str(self.module.params.get(k))

        ET.SubElement(Login, "Username").text = self.module.params.get('sfos_username')
        ET.SubElement(Login, "Password").text = self.module.params.get('sfos_password')

        reqxml = urllib.quote(ET.tostring(Request).decode('utf-8'), safe="%/:=&?~#+!$,;'@()*[]<>")
        return reqxml

    def _construct_response(self, response):
        """
        Returns status code and text message from a request response
        :param response: The API response received from the request
        :return: The status code and text message
        """
        result = json.loads(json.dumps(xmltodict.parse(response.read())))
        status = int(result['Response'][self.endpoint]['Status']['@code'])

        if status >= 200:
            msg = result['Response'][self.endpoint]['Status']['#text']

        return status, msg

    def _add(self):
        """
        Adds or updates a host object on sfos
        """
        is_changed = False
        exists, results = self._lookup_entry(self.module, self.request_url)

        if exists:
            if self._is_object_changed(self.change_relevant_keys, self.module, results, self.bool_keys):
                reqxml = self._construct_xml_request("Set")
                is_changed = True
        else:
            reqxml = self._construct_xml_request("Set", "add")
            is_changed = True

        if is_changed:
            response, dummy = fetch_url(self.module, self.request_url + reqxml, method="GET")
            status, msg = self._construct_response(response)
            if status >= 500:
                self.module.fail_json(msg=msg)

        result = self._clean_result(self.module.params)
        self.module.exit_json(result=result, changed=is_changed)

    def _remove(self):
        """
        Removes an object from sfos
        """
        is_changed = False
        exists, dummy = self._lookup_entry(self.module, self.request_url)

        if exists:
            is_changed = True
            reqxml = self._construct_xml_request("Remove")
            response, dummy = fetch_url(self.module, self.request_url + reqxml, method="GET")
            status, msg = self._construct_response(response)
            if status >= 500:
                self.module.fail_json(msg=msg)

        self.module.exit_json(changed=is_changed)

    def _lookup_entry(self, module, request_url):
        """
        Lookup for existing entry in sfos
        :param module:
        :param request_url:
        :return:
        """
        response, info = fetch_url(module, request_url + self._construct_xml_request("Get"), method="GET")

        if info['status'] == -1:
            self.module.fail_json(msg=info['msg'])

        if response is not None:
            res = json.loads(json.dumps(xmltodict.parse(response.read())))
            exists = False
            results = dict()

            if self.endpoint in res['Response'].keys():
                if type(res['Response'][self.endpoint]) == list or res['Response'][self.endpoint].get('Name'):
                    exists = True
                    results = res['Response'][self.endpoint]
            else:
                if res['Response']['Login']['status'] == "Authentication Failure":
                    self.module.fail_json(msg="Authentication Failure")
                else:
                    if int(res['Response']['Status']['@code']) >= 200:
                        msg = res['Response']['Status']['#text']
                        self.module.fail_json(msg=msg)

        return exists, results

    def _clean_result(self, result):
        """
        Will clean the result from irrelevant fields
        :param result: The result from the query
        :return: The modified result
        """
        del result['sfos_host']
        del result['sfos_username']
        del result['sfos_password']
        del result['sfos_port']
        del result['validate_certs']
        del result['sfos_protocol']
        del result['state']
        return result

    def _is_object_changed(self, keys, module, result, matchs):
        """
        Check if my object is changed
        :param keys: The keys that will determine if an object is changed
        :param module: The module
        :param result: The result from the query
        :return: True or False if object has changed or not
        """
        for k, v in list(result.items()):
            result[k.lower()] = v

        for key in keys:
            # Format booleans returned as strings into correct boolean values
            if key in matchs:
                if result[key]:
                    result[key] = matchs[key][str(result[key])]

            if module.params.get(key) is None and self.argument_spec[key]["type"] == "list":
                continue  # if key type is list and is not present, skip this check to not wipe current values
            elif type(module.params.get(key)) != list:  # if key type is not list, compare string values
                if str(module.params.get(key)) != str(result[key]):
                    return True
            else:
                if key not in result.keys():  # if result list not exists, assume object has changed
                    return True
                elif type(result[key][self.argument_spec[key]["item"]]) == str:
                    if module.params.get(key) != [result[key][self.argument_spec[key]["item"]]]:
                        return True  # if the result list has only one item, type is string, so lets compare list with list
                elif module.params.get(key) != result[key][self.argument_spec[key]["item"]]:
                    return True

        return False
