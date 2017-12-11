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
from copy import deepcopy

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

'''
URL_MAPPING = dict(
    action_rule=dict(aci_class='rtctrlAttrP', mo='attr-', key='name'),
    aep=dict(aci_class='infraAttEntityP', mo='infra/attentp-', key='name'),
    ap=dict(aci_class='fvAp', mo='ap-', key='name'),
    bd=dict(aci_class='fvBD', mo='BD-', key='name'),
    bd_l3out=dict(aci_class='fvRsBDToOut', mo='rsBDToOut-', key='tnL3extOutName'),
    contract=dict(aci_class='vzBrCP', mo='brc-', key='name'),
    entry=dict(aci_class='vzEntry', mo='e-', key='name'),
    epg=dict(aci_class='fvAEPg', mo='epg-', key='name'),
    epg_consumer=dict(aci_class='fvRsCons', mo='rscons-', key='tnVzBrCPName'),
    epg_domain=dict(aci_class='fvRsDomAtt', mo='rsdomAtt-', key='tDn'),
    epg_provider=dict(aci_class='fvRsProv', mo='rsprov-', key='tnVzBrCPName'),
    epr_policy=dict(aci_class='fvEpRetPol', mo='epRPol-', key='name'),
    export_policy=dict(aci_class='configExportP', mo='fabric/configexp-', key='name'),
    fc_policy=dict(aci_class='fcIfPol', mo='infra/fcIfPol-', key='name'),
    filter=dict(aci_class='vzFilter', mo='flt-', key='name'),
    gateway_addr=dict(aci_class='fvSubnet', mo='subnet-', key='ip'),
    import_policy=dict(aci_class='configImportP', mo='fabric/configimp-', key='name'),
    l2_policy=dict(aci_class='l2IfPol', mo='infra/l2IfP-', key='name'),
    lldp_policy=dict(aci_class='lldpIfPol', mo='infra/lldpIfP-', key='name'),
    mcp=dict(aci_class='mcpIfPol', mo='infra/mcpIfP-', key='name'),
    monitoring_policy=dict(aci_class='monEPGPol', mo='monepg-', key='name'),
    port_channel=dict(aci_class='lacpLagPol', mo='infra/lacplagp-', key='name'),
    port_security=dict(aci_class='l2PortSecurityPol', mo='infra/portsecurityP-', key='name'),
    rtp=dict(aci_class='l3extRouteTagPol', mo='rttag-', key='name'),
    snapshot=dict(aci_class='configSnapshot', mo='snapshot-', key='name'),
    snapshot_container=dict(aci_class='configSnapshotCont', mo='backupst/snapshots-', key='name'),
    subject=dict(aci_class='vzSubj', mo='subj-', key='name'),
    subject_filter=dict(aci_class='vzRsSubjFiltAtt', mo='rssubjFiltAtt-', key='tnVzFilterName'),
    taboo_contract=dict(aci_class='vzTaboo', mo='taboo-', key='name'),
    tenant=dict(aci_class='fvTenant', mo='tn-', key='name'),
    tenant_span_dst_grp=dict(aci_class='spanDestGrp', mo='destgrp-', key='name'),
    tenant_span_src_grp=dict(aci_class='spanSrcGrp', mo='srcgrp-', key='name'),
    tenant_span_src_grp_dst_grp=dict(aci_class='spanSpanLbl', mo='spanlbl-', key='name'),
    vrf=dict(aci_class='fvCtx', mo='ctx-', key='name'),
)
'''


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
            if 'state' in self.module.argument_spec:
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

    def construct_url(self, root_class, subclass_1=None, subclass_2=None, subclass_3=None, child_classes=None):
        """
        This method is used to retrieve the appropriate URL path and filter_string to make the request to the APIC.

        :param root_class: The top-level class dictionary containing aci_class, aci_rn, filter_target, and module_object keys.
        :param sublass_1: The second-level class dictionary containing aci_class, aci_rn, filter_target, and module_object keys.
        :param sublass_2: The third-level class dictionary containing aci_class, aci_rn, filter_target, and module_object keys.
        :param sublass_3: The fourth-level class dictionary containing aci_class, aci_rn, filter_target, and module_object keys.
        :param child_classes: The list of child classes that the module supports along with the object.
        :type root_class: dict
        :type subclass_1: dict
        :type subclass_2: dict
        :type subclass_3: dict
        :type child_classes: list
        :return: The path and filter_string needed to build the full URL.
        """
        if child_classes is None:
            child_includes = ''
        else:
            child_includes = ','.join(child_classes)
            child_includes = '&rsp-subtree=full&rsp-subtree-class=' + child_includes

        if subclass_3 is not None:
            path, filter_string = self._construct_url_4(root_class, subclass_1, subclass_2, subclass_3, child_includes)
        elif subclass_2 is not None:
            path, filter_string = self._construct_url_3(root_class, subclass_1, subclass_2, child_includes)
        elif subclass_1 is not None:
            path, filter_string = self._construct_url_2(root_class, subclass_1, child_includes)
        else:
            path, filter_string = self._construct_url_1(root_class, child_includes)

        self.result['url'] = '{}://{}/{}'.format(self.module.params['protocol'], self.module.params['hostname'], path)
        self.result['filter_string'] = filter_string

    def _construct_url_1(self, obj, child_includes):
        """
        This method is used by get_url when the object is the top-level class.
        """
        obj_class = obj['aci_class']
        obj_rn = obj['aci_rn']
        mo = obj['module_object']

        # State is present or absent
        if self.module.params['state'] != 'query':
            path = 'api/mo/uni/{}.json'.format(obj_rn)
            filter_string = '?rsp-prop-include=config-only' + child_includes
        # Query for all objects of the module's class
        elif mo is None:
            path = 'api/class/{}.json'.format(obj_class)
            filter_string = ''
        # Query for a specific object in the module's class
        else:
            path = 'api/mo/uni/{}.json'.format(obj_rn)
            filter_string = ''

        # Append child_includes to filter_string if filter string is empty
        if child_includes is not None and filter_string == '':
            filter_string = child_includes.replace('&', '?', 1)

        return path, filter_string

    def _construct_url_2(self, parent, obj, child_includes):
        """
        This method is used by get_url when the object is the second-level class.
        """
        parent_rn = parent['aci_rn']
        parent_obj = parent['module_object']
        obj_class = obj['aci_class']
        obj_rn = obj['aci_rn']
        obj_filter = obj['filter_target']
        mo = obj['module_object']

        if not child_includes:
            self_child_includes = '?rsp-subtree=full&rsp-subtree-class=' + obj_class
        else:
            self_child_includes = child_includes.replace('&', '?', 1) + ',' + obj_class

        # State is present or absent
        if self.module.params['state'] != 'query':
            path = 'api/mo/uni/{}/{}.json'.format(parent_rn, obj_rn)
            filter_string = '?rsp-prop-include=config-only' + child_includes
        # Query for all objects of the module's class
        elif mo is None and parent_obj is None:
            path = 'api/class/{}.json'.format(obj_class)
            filter_string = ''
        # Queries when parent object is provided
        elif parent_obj is not None:
            # Query for specific object in the module's class
            if mo is not None:
                path = 'api/mo/uni/{}/{}.json'.format(parent_rn, obj_rn)
                filter_string = ''
            # Query for all object's of the module's class that belong to a specific parent object
            else:
                path = 'api/mo/uni/{}.json'.format(parent_rn)
                filter_string = self_child_includes
        # Query for all objects of the module's class that match the provided ID value
        else:
            path = 'api/class/{}.json'.format(obj_class)
            filter_string = '?query-target-filter={}'.format(obj_filter) + child_includes

        # Append child_includes to filter_string if filter string is empty
        if child_includes is not None and filter_string == '':
            filter_string = child_includes.replace('&', '?', 1)

        return path, filter_string

    def _construct_url_3(self, root, parent, obj, child_includes):
        """
        This method is used by get_url when the object is the third-level class.
        """
        root_rn = root['aci_rn']
        root_obj = root['module_object']
        parent_class = parent['aci_class']
        parent_rn = parent['aci_rn']
        parent_filter = parent['filter_target']
        parent_obj = parent['module_object']
        obj_class = obj['aci_class']
        obj_rn = obj['aci_rn']
        obj_filter = obj['filter_target']
        mo = obj['module_object']

        if not child_includes:
            self_child_includes = '&rsp-subtree=full&rsp-subtree-class=' + obj_class
        else:
            self_child_includes = '{},{}'.format(child_includes, obj_class)

        if not child_includes:
            parent_self_child_includes = '&rsp-subtree=full&rsp-subtree-class={},{}'.format(parent_class, obj_class)
        else:
            parent_self_child_includes = '{},{},{}'.format(child_includes, parent_class, obj_class)

        # State is ablsent or present
        if self.module.params['state'] != 'query':
            path = 'api/mo/uni/{}/{}/{}.json'.format(root_rn, parent_rn, obj_rn)
            filter_string = '?rsp-prop-include=config-only' + child_includes
        # Query for all objects of the module's class
        elif mo is None and parent_obj is None and root_obj is None:
            path = 'api/class/{}.json'.format(obj_class)
            filter_string = ''
        # Queries when root object is provided
        elif root_obj is not None:
            # Queries when parent object is provided
            if parent_obj is not None:
                # Query for a specific object of the module's class
                if mo is not None:
                    path = 'api/mo/uni/{}/{}/{}.json'.format(root_rn, parent_rn, obj_rn)
                    filter_string = ''
                # Query for all objects of the module's class that belong to a specific parent object
                else:
                    path = 'api/mo/uni/{}/{}.json'.format(root_rn, parent_rn)
                    filter_string = self_child_includes.replace('&', '?', 1)
            # Query for all objects of the module's class that match the provided ID value and belong to a specefic root object
            elif mo is not None:
                path = 'api/mo/uni/{}.json'.format(root_rn)
                filter_string = '?rsp-subtree-filter={}{}'.format(obj_filter, self_child_includes)
            # Query for all objects of the module's class that belong to a specific root object
            else:
                path = 'api/mo/uni/{}.json'.format(root_rn)
                filter_string = '?' + parent_self_child_includes
        # Queries when parent object is provided but root object is not provided
        elif parent_obj is not None:
            # Query for all objects of the module's class that belong to any parent class
            # matching the provided ID values for both object and parent object
            if mo is not None:
                path = 'api/class/{}.json'.format(parent_class)
                filter_string = '?query-target-filter={}{}&rsp-subtree-filter={}'.format(
                    parent_filter, self_child_includes, obj_filter)
            # Query for all objects of the module's class that belong to any parent class
            # matching the provided ID value for the parent object
            else:
                path = 'api/class/{}.json'.format(parent_class)
                filter_string = '?query-target-filter={}{}'.format(parent_filter, self_child_includes)
        # Query for all objects of the module's class matching the provided ID value of the object
        else:
            path = 'api/class/{}.json'.format(obj_class)
            filter_string = '?query-target-filter={}'.format(obj_filter) + child_includes

        # append child_includes to filter_string if filter string is empty
        if child_includes is not None and filter_string == '':
            filter_string = child_includes.replace('&', '?', 1)

        return path, filter_string

    def _construct_url_4(self, root, sec, parent, obj, child_includes):
        """
        This method is used by get_url when the object is the third-level class.
        """
        # root_class = root['aci_class']
        root_rn = root['aci_rn']
        # root_filter = root['filter_target']
        # root_obj = root['module_object']
        # sec_class = sec['aci_class']
        sec_rn = sec['aci_rn']
        # sec_filter = sec['filter_target']
        # sec_obj = sec['module_object']
        # parent_class = parent['aci_class']
        parent_rn = parent['aci_rn']
        # parent_filter = parent['filter_target']
        # parent_obj = parent['module_object']
        obj_class = obj['aci_class']
        obj_rn = obj['aci_rn']
        # obj_filter = obj['filter_target']
        # mo = obj['module_object']

        # State is ablsent or present
        if self.module.params['state'] != 'query':
            path = 'api/mo/uni/{}/{}/{}/{}.json'.format(root_rn, sec_rn, parent_rn, obj_rn)
            filter_string = '?rsp-prop-include=config-only' + child_includes
        else:
            path = 'api/class/{}.json'.format(obj_class)
            filter_string = child_includes

        return path, filter_string

    def delete_config(self):
        """
        This method is used to handle the logic when the modules state is equal to absent. The method only pushes a change if
        the object exists, and if check_mode is False. A successful change will mark the module as changed.
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
                # TODO: If URLs are built with the object's name, then we should be able to leave off adding the name back
                # config["name"] = proposed_config["name"]
                config = {aci_class: {'attributes': config}}

            # check for updates to child configs and update new config dictionary
            children = self.get_diff_children(aci_class)
            if children and config:
                config[aci_class].update({'children': children})
            elif children:
                config = {aci_class: {'attributes': {}, 'children': children}}

        else:
            config = self.result['proposed']

        self.result['config'] = config

    @staticmethod
    def get_diff_child(child_class, proposed_child, existing_child):
        """
        This method is used to get the difference between a proposed and existing child configs. The get_nested_config()
        method should be used to return the proposed and existing config portions of child.

        :param child_class: Type str.
                            The root class (dict key) for the child dictionary.
        :param proposed_child: Type dict.
                               The config portion of the proposed child dictionary.
        :param existing_child: Type dict.
                               The config portion of the existing child dictionary.
        :return: The child config with only values that are updated. If the proposed dictionary has no updates to make
                 to what exists on the APIC, then None is returned.
        """
        update_config = {child_class: {'attributes': {}}}
        for key, value in proposed_child.items():
            if value != existing_child[key]:
                update_config[child_class]['attributes'][key] = value

        if not update_config[child_class]['attributes']:
            return None

        return update_config

    def get_diff_children(self, aci_class):
        """
        This method is used to retrieve the updated child configs by comparing the proposed children configs
        agains the objects existing children configs.

        :param aci_class: Type str.
                          This is the root dictionary key for the MO's configuration body, or the ACI class of the MO.
        :return: The list of updated child config dictionaries. None is returned if there are no changes to the child
                 configurations.
        """
        proposed_children = self.result['proposed'][aci_class].get('children')
        if proposed_children:
            child_updates = []
            existing_children = self.result['existing'][0][aci_class].get('children', [])

            # Loop through proposed child configs and compare against existing child configuration
            for child in proposed_children:
                child_class, proposed_child, existing_child = self.get_nested_config(child, existing_children)

                if existing_child is None:
                    child_update = child
                else:
                    child_update = self.get_diff_child(child_class, proposed_child, existing_child)

                # Update list of updated child configs only if the child config is different than what exists
                if child_update:
                    child_updates.append(child_update)
        else:
            return None

        return child_updates

    def get_existing(self):
        """
        This method is used to get the existing object(s) based on the path specified in the module. Each module should
        build the URL so that if the object's name is supplied, then it will retrieve the configuration for that particular
        object, but if no name is supplied, then it will retrieve all MOs for the class. Following this method will ensure
        that this method can be used to supply the existing configuration when using the get_diff method. The response, status,
        and existing configuration will be added to the self.result dictionary.
        """
        uri = self.result['url'] + self.result['filter_string']

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

    @staticmethod
    def get_nested_config(proposed_child, existing_children):
        """
        This method is used for stiping off the outer layers of the child dictionaries so only the configuration
        key, value pairs are returned.

        :param proposed_child: Type dict.
                               The dictionary that represents the child config.
        :param existing_children: Type list.
                                  The list of existing child config dictionaries.
        :return: The child's class as str (root config dict key), the child's proposed config dict, and the child's
                 existing configuration dict.
        """
        for key in proposed_child.keys():
            child_class = key
            proposed_config = proposed_child[key]['attributes']
            existing_config = None

            # get existing dictionary from the list of existing to use for comparison
            for child in existing_children:
                if child.get(child_class):
                    existing_config = child[key]['attributes']
                    break

        return child_class, proposed_config, existing_config

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
        proposed = dict((k, str(v)) for k, v in class_config.items() if v is not None)
        self.result['proposed'] = {aci_class: {'attributes': proposed}}

        # add child objects to proposed
        if child_configs:
            children = []
            for child in child_configs:
                child_copy = deepcopy(child)
                has_value = False
                for root_key in child_copy.keys():
                    for final_keys, values in child_copy[root_key]['attributes'].items():
                        if values is None:
                            child[root_key]['attributes'].pop(final_keys)
                        else:
                            child[root_key]['attributes'][final_keys] = str(values)
                            has_value = True
                if has_value:
                    children.append(child)

            if children:
                self.result['proposed'][aci_class].update(dict(children=children))

    def post_config(self):
        """
        This method is used to handle the logic when the modules state is equal to present. The method only pushes a change if
        the object has differences than what exists on the APIC, and if check_mode is False. A successful change will mark the
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
