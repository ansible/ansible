# -*- coding: utf-8 -*-

# This code is part of Ansible, but is an independent component

# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.

# Copyright 2017 Dag Wieers <dag@wieers.com>
# Copyright 2017 Swetha Chunduri (@schunduri)
# All rights reserved.

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

import json

from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_bytes

# Optional, only used for XML payload
try:
    import lxml.etree
    HAS_LXML_ETREE = True
except ImportError:
    HAS_LXML_ETREE = False

# Optional, only used for XML payload
try:
    from xmljson import cobra
    HAS_XMLJSON_COBRA = True
except ImportError:
    HAS_XMLJSON_COBRA = False


aci_argument_spec = dict(
    hostname=dict(type='str', required=True, aliases=['host']),
    username=dict(type='str', default='admin', aliases=['user']),
    password=dict(type='str', required=True, no_log=True),
    protocol=dict(type='str', removed_in_version='2.6'),  # Deprecated in v2.6
    timeout=dict(type='int', default=30),
    use_proxy=dict(type='bool', default=True),
    use_ssl=dict(type='bool', default=True),
    validate_certs=dict(type='bool', default=True),
)


def aci_response_error(result):
    ''' Set error information when found '''
    result['error_code'] = 0
    result['error_text'] = 'Success'
    # Handle possible APIC error information
    if result['totalCount'] != '0':
        try:
            result['error_code'] = result['imdata'][0]['error']['attributes']['code']
            result['error_text'] = result['imdata'][0]['error']['attributes']['text']
        except (KeyError, IndexError):
            pass


def aci_response_json(result, rawoutput):
    ''' Handle APIC JSON response output '''
    try:
        result.update(json.loads(rawoutput))
    except Exception as e:
        # Expose RAW output for troubleshooting
        result.update(raw=rawoutput, error_code=-1, error_text="Unable to parse output as JSON, see 'raw' output. %s" % e)
        return

    # Handle possible APIC error information
    aci_response_error(result)


def aci_response_xml(result, rawoutput):
    ''' Handle APIC XML response output '''

    # NOTE: The XML-to-JSON conversion is using the "Cobra" convention
    try:
        xml = lxml.etree.fromstring(to_bytes(rawoutput))
        xmldata = cobra.data(xml)
    except Exception as e:
        # Expose RAW output for troubleshooting
        result.update(raw=rawoutput, error_code=-1, error_text="Unable to parse output as XML, see 'raw' output. %s" % e)
        return

    # Reformat as ACI does for JSON API output
    try:
        result.update(imdata=xmldata['imdata']['children'])
    except KeyError:
        result['imdata'] = dict()
    result['totalCount'] = xmldata['imdata']['attributes']['totalCount']

    # Handle possible APIC error information
    aci_response_error(result)


class ACIModule(object):

    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.result = dict(changed=False)
        self.headers = None

        self.login()

    def define_protocol(self):
        ''' Set protocol based on use_ssl parameter '''

        # Set protocol for further use
        if self.params['protocol'] in ('http', 'https'):
            self.module.deprecate("Parameter 'protocol' is deprecated, please use 'use_ssl' instead.", '2.6')
        elif self.params['protocol'] is None:
            self.params['protocol'] = 'https' if self.params.get('use_ssl', True) else 'http'
        else:
            self.module.fail_json(msg="Parameter 'protocol' needs to be one of ( http, https )")

    def define_method(self):
        ''' Set method based on state parameter '''

        # Handle deprecated method/action parameter
        if self.params['method']:
            # Deprecate only if state was a valid option (not for aci_rest)
            if self.module.argument_spec('state', False):
                self.module.deprecate("Parameter 'method' or 'action' is deprecated, please use 'state' instead", '2.6')
            method_map = dict(delete='absent', get='query', post='present')
            self.params['state'] = method_map[self.params['method']]
        else:
            state_map = dict(absent='delete', present='post', query='get')
            self.params['method'] = state_map[self.params['state']]

    def login(self):
        ''' Log in to APIC '''

        # Ensure protocol is set (only do this once)
        self.define_protocol()

        # Perform login request
        url = '%(protocol)s://%(hostname)s/api/aaaLogin.json' % self.params
        payload = {'aaaUser': {'attributes': {'name': self.params['username'], 'pwd': self.params['password']}}}
        resp, auth = fetch_url(self.module, url,
                               data=json.dumps(payload),
                               method='POST',
                               timeout=self.params['timeout'],
                               use_proxy=self.params['use_proxy'])

        # Handle APIC response
        if auth['status'] != 200:
            self.result['response'] = auth['msg']
            self.result['status'] = auth['status']
            try:
                # APIC error
                aci_response_json(self.result, auth['body'])
                self.module.fail_json(msg='Authentication failed: %(error_code)s %(error_text)s' % self.result, **self.result)
            except KeyError:
                # Connection error
                self.module.fail_json(msg='Authentication failed for %(url)s. %(msg)s' % auth)

        # Retain cookie for later use
        self.headers = dict(Cookie=resp.headers['Set-Cookie'])

    def request(self, path, payload=None):
        ''' Perform a REST request '''

        # Ensure method is set (only do this once)
        self.define_method()

        # Perform request
        self.result['url'] = '%(protocol)s://%(hostname)s/' % self.params + path.lstrip('/')
        resp, info = fetch_url(self.module, self.result['url'],
                               data=payload,
                               headers=self.headers,
                               method=self.params['method'].upper(),
                               timeout=self.params['timeout'],
                               use_proxy=self.params['use_proxy'])

        self.result['response'] = info['msg']
        self.result['status'] = info['status']

        # Handle APIC response
        if info['status'] != 200:
            try:
                # APIC error
                aci_response_json(self.result, info['body'])
                self.module.fail_json(msg='Request failed: %(error_code)s %(error_text)s' % self.result, **self.result)
            except KeyError:
                # Connection error
                self.module.fail_json(msg='Request failed for %(url)s. %(msg)s' % info)

        aci_response_json(self.result, resp.read())

    def query(self, path):
        ''' Perform a query with no payload '''
        url = '%(protocol)s://%(hostname)s/' % self.params + path.lstrip('/')
        resp, query = fetch_url(self.module, url,
                                data=None,
                                headers=self.headers,
                                method='GET',
                                timeout=self.params['timeout'],
                                use_proxy=self.params['use_proxy'])

        # Handle APIC response
        if query['status'] != 200:
            self.result['response'] = query['msg']
            self.result['status'] = query['status']
            try:
                # APIC error
                aci_response_json(self.result, query['body'])
                self.module.fail_json(msg='Query failed: %(error_code)s %(error_text)s' % self.result, **self.result)
            except KeyError:
                # Connection error
                self.module.fail_json(msg='Query failed for %(url)s. %(msg)s' % query)

        query = json.loads(resp.read())

        return json.dumps(query['imdata'], sort_keys=True, indent=2) + '\n'

    def request_diff(self, path, payload=None):
        ''' Perform a request, including a proper diff output '''
        self.result['diff'] = dict()
        self.result['diff']['before'] = self.query(path)
        self.request(path, payload=payload)
        # TODO: Check if we can use the request output for the 'after' diff
        self.result['diff']['after'] = self.query(path)

        if self.result['diff']['before'] != self.result['diff']['after']:
            self.result['changed'] = True

    def delete_config(self):
        """
        This method is used to handle the logic when the modules state is equal to absent. The method only pushes a change if
        the object exists, and if check_mode is Fasle. A successful change will mark the module as changed.
        """
        self.result['proposed'] = {}

        if not self.result['existing']:
            return

        elif not self.module.check_mode:
            resp, info = fetch_url(self.module, self.result['url'],
                                   headers=self.headers,
                                   method='DELETE',
                                   timeout=self.params['timeout'],
                                   use_proxy=self.params['use_proxy'])

            self.result['response'] = info['msg']
            self.result['status'] = info['status']
            self.result['method'] = 'DELETE'

            # Handle APIC response
            if info['status'] == 200:
                self.result['changed'] = True
                aci_response_json(self.result, resp.read())
            else:
                try:
                    # APIC error
                    aci_response_json(self.result, info['body'])
                    self.module.fail_json(msg='Request failed: %(error_code)s %(error_text)s' % self.result, **self.result)
                except KeyError:
                    # Connection error
                    self.module.fail_json(msg='Request failed for %(url)s. %(msg)s' % info)
        else:
            self.result['changed'] = True
            self.result['method'] = 'DELETE'

    def get_diff(self, aci_class):
        """
        This method is used to get the difference between the proposed and existing configurations. Each module
        should call the get_existing method before this method, and add the proposed config to the module results
        using the module's config parameters. The new config will added to the self.result dictionary.

        :param aci_class: Type str.
                          This is the root dictionary key for the MO's configuration body, or the ACI class of the MO.
        """
        proposed_config = self.result['proposed'][aci_class]['attributes']
        proposed_children = self.result['proposed'][aci_class].get('children')
        if self.result['existing']:
            existing_config = self.result['existing'][0][aci_class]['attributes']
            config = {}

            # values are strings, so any diff between proposed and existing can be a straight replace
            for key, value in proposed_config.items():
                existing_field = existing_config.get(key)
                if value != existing_field:
                    config[key] = value

            # add name back to config only if the configs do not match
            if config:
                config["name"] = proposed_config["name"]
                config = {aci_class: {'attributes': config}}

            # compare existing child dictionaries with what is in existing
            if proposed_children:
                existing_children = self.result['existing'][0][aci_class].get('children', [])
                children = [relation for relation in proposed_children if relation not in existing_children]

                if children and config:
                    config[aci_class].update({'children': children})
                elif children:
                    config = {aci_class: {'attributes': {'name': proposed_config['name']}, 'children': children}}

        else:
            config = self.result['proposed']

        self.result['config'] = config

    def get_existing(self, filter_string=""):
        """
        This method is used to get the existing object(s) based on the path specified in the module. Each module should
        build the URL so that if the object's name is supplied, then it will retrieve the configuration for that particular
        object, but if no name is supplied, then it will retrieve all MOs for the class. Following this method will ensure
        that this method can be used to supply the existing configuration when using the get_diff method. The response, status,
        and existing configuration will be added to the self.result dictionary.

        :param filter_string: Type str.
                             The filter to use in order to retrieve the filtered configuration.
        """
        uri = self.result['url'] + filter_string
        resp, info = fetch_url(self.module, uri,
                               headers=self.headers,
                               method='GET',
                               timeout=self.params['timeout'],
                               use_proxy=self.params['use_proxy'])
        self.result['response'] = info['msg']
        self.result['status'] = info['status']
        self.result['method'] = 'GET'

        # Handle APIC response
        if info['status'] == 200:
            self.result['existing'] = json.loads(resp.read())['imdata']
        else:
            try:
                # APIC error
                aci_response_json(self.result, info['body'])
                self.module.fail_json(msg='Request failed: %(error_code)s %(error_text)s' % self.result, **self.result)
            except KeyError:
                # Connection error
                self.module.fail_json(msg='Request failed for %(url)s. %(msg)s' % info)

    def payload(self, aci_class, class_config, child_configs=None):
        """
        This method is used to dynamically build the proposed configuration dictionary from the config related parameters
        passed into the module. All values that were not passed values from the playbook task will be removed so as to not
        inadvertently change configurations.

        :param aci_class: Type str
                          This is the root dictionary key for the MO's configuration body, or the ACI class of the MO.
        :param class_config: Type dict
                             This is the configuration of the MO using the dictionary keys expected by the API
        :param child_configs: Type list
                              This is a list of child dictionaries associated with the MOs config. The list should only
                              include child objects that are used to associate two MOs together. Children that represent
                              MOs should have their own module.
        """
        proposed = dict((k, v) for k, v in class_config.items() if v)
        self.result['proposed'] = {aci_class: {'attributes': proposed}}

        # add child objects to proposed
        if child_configs:
            children = []
            for child in child_configs:
                for root_key in child.keys():
                    for final_keys, values in child[root_key]['attributes'].items():
                        if values is not None:
                            children.append(child)
                            break

            if children:
                self.result['proposed'][aci_class].update(dict(children=children))

    def post_config(self):
        """
        This method is used to handle the logic when the modules state is equal to present. The method only pushes a change if
        the object has differences than what exists on the APIC, and if check_mode is Fasle. A successful change will mark the
        module as changed.
        """
        if not self.result['config']:
            return
        elif not self.module.check_mode:
            resp, info = fetch_url(self.module, self.result['url'],
                                   data=json.dumps(self.result['config']),
                                   headers=self.headers,
                                   method='POST',
                                   timeout=self.params['timeout'],
                                   use_proxy=self.params['use_proxy'])

            self.result['response'] = info['msg']
            self.result['status'] = info['status']
            self.result['method'] = 'POST'

            # Handle APIC response
            if info['status'] == 200:
                self.result['changed'] = True
                aci_response_json(self.result, resp.read())
            else:
                try:
                    # APIC error
                    aci_response_json(self.result, info['body'])
                    self.module.fail_json(msg='Request failed: %(error_code)s %(error_text)s' % self.result, **self.result)
                except KeyError:
                    # Connection error
                    self.module.fail_json(msg='Request failed for %(url)s. %(msg)s' % info)
        else:
            self.result['changed'] = True
            self.result['method'] = 'POST'
