# -*- coding: utf-8 -*-

# This code is part of Ansible, but is an independent component

# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.

# Copyright: (c) 2018, Kevin Breit <kevin.breit@kevinbreit.net>
# Copyright: (c) 2017, Dag Wieers <dag@wieers.com>
# Copyright: (c) 2017, Jacob McGill (@jmcgill298)
# Copyright: (c) 2017, Swetha Chunduri (@schunduri)
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

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native, to_bytes, to_text


def meraki_argument_spec():
    return dict(auth_key=dict(type='str', no_log=True, fallback=(env_fallback, ['MERAKI_KEY'])),
                host=dict(type='str', default='api.meraki.com'),
                name=dict(type='str'),
                username=dict(type='str'),
                state=dict(type='str', choices=['present', 'absent', 'query'], required=True),
                use_proxy=dict(type='bool', default=True),
                use_ssl=dict(type='bool', default=True),
                validate_certs=dict(type='bool', default=True),
                output_level=dict(type='str', default='normal', choices=['normal', 'debug']),
                timeout=dict(type='int', default=30),
                org_name=dict(type='str'),
                org_id=dict(type='str'),
                net_name=dict(type='str'),
                )


class MerakiModule(object):

    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.result = dict(changed=False)
        self.headers = dict()
        self.function = None

        if module.params['auth_key'] is None:
            module.fail_json(msg='Meraki API key not specified')
        else:
            self.headers = {'Content-Type': 'application/json',
                            'X-Cisco-Meraki-API-Key': module.params['auth_key'],
                            }

        # error output
        self.error = dict(code=None, text=None)

        # normal output
        self.existing = None

        # info output
        self.config = dict()
        self.original = None
        self.proposed = dict()
        self.merged = None

        # debug output
        self.filter_string = ''
        self.method = None
        self.path = None
        self.response = None
        self.status = None
        self.url = None
#        self.url_list = {'org_get_all': '/organizations/',
#                         'org_get_one': '/organizations/replace_org_id',
#                         'org_post': '/organizations/',
#                         'org_put': '/organizations/replace_org_id',
#                         'net_get_all': '/organizations/replace_org_id/networks',
#                         'net_get_one': '/networks/replace_net_id',
#                         'net_post': '/organizations/replace_org_id/networks',
#                         'net_put': '/networks/replace_net_id',
#                         }

        self.get_urls = {'organizations': '/organizations',
                         'networks': '/organizations/replace_org_id/networks',
                         }

        self.get_one_urls = {'organizations': '/organizations/replace_org_id',
                             'networks': 'networks/replace_net_id',
                             }

#        self.create_urls = dict()

        # Module should add URLs which are required by the module
        self.url_catalog = {'get_all': self.get_urls,
                            'get_one': self.get_one_urls,
                            'create': None,
                            'delete': None,
                            'Misc': None,
                            }

        if self.module._debug or self.params['output_level'] == 'debug':
            self.module.warn('Enable debug output because ANSIBLE_DEBUG was set or output_level is set to debug.')

        # TODO: This needs to be tested
        self.module.required_if = [('state', 'present', ['name']),
                                   ('state', 'absent', ['name']),
                                   ]

        # Validate whether parameters are compatible
        if self.params['state'] == 'absent':
            if self.params['org_name'] or self.params['org_id']:
                module.fail_json('State cannot be absent if specifying org_name or org_id.')

        self.modifiable_methods = ['POST', 'PUT', 'DELETE']

    def define_protocol(self):
        ''' Set protocol based on use_ssl parameters '''
        if self.params['use_ssl'] is True:
            self.params['protocol'] = 'https'
        else:
            self.params['protocol'] = 'http'

    def define_method(self):
        ''' Set method. May not need to stay. '''
        if self.params['state'] == 'query':
            self.method = 'GET'
        elif self.params['state'] == 'absent':
            self.method = 'DELETE'
        elif self.params['state'] == 'present':
            if self.function == 'organizations':
                self.method = 'POST'
            elif self.is_new() is True:
                self.method = 'POST'
            elif self.is_update_required() is True:
                self.method = 'PUT'
            else:
                return -1

    def response_json(self, rawoutput):
        ''' Handle Dashboard API response output '''
        try:
            return json.loads(rawoutput)
        except Exception as e:
            self.error = dict(code=-1, text="Unable to parse output as JSON, see 'raw' output. {0}".format(e))
            self.result['raw'] = rawoutput
            return

    def is_update_required(self):
        ''' Check original and proposed data to see if an update is needed '''
        self.merged = self.original
        is_changed = False
        for k, v in original.items():
            try:
                if v != proposed[k]:
                    is_changed = True
                    merged[k] = proposed[k]
            except KeyError:
                merged[k] = ''
                if v != '':
                    is_changed = True
        return is_changed

    def is_new(self):
        ''' Check whether an object is new and should be created '''
        r = self.get_existing(self.path)
        for i in r:
            if self.module.params['name'] == i['name']:
                # self.fail_json(msg='False')
                return False
        # self.fail_json(msg='True')
        return True

    def get_existing(self, path):
        ''' Query existing objects associated to path. May not need to stay. '''
        self.define_protocol()
        self.path = path

        self.url = '{0}://{1}/api/v0/{2}'.format(self.params['protocol'], self.params['host'], self.path.lstrip('/'))

        resp, info = fetch_url(self.module, self.url,
                               headers=self.headers,
                               method='GET',
                               timeout=self.params['timeout'],
                               use_proxy=self.params['use_proxy'],
                               )
        self.response = info['msg']
        self.status = info['status']
        response = json.loads(to_native(resp.read()))

        if self.status >= 300:
            try:
                self.error['text'] = self.response_json(info['body'])
                self.error['code'] = info['status']
                self.fail_json(msg='Dashboard API error %(code)s: %(text)s' % self.error)
            except KeyError:
                self.fail_json(msg='Connection failed for %(url)s. %(msg)s' % info)
        return response

    def get_orgs(self):
        ''' Downloads all organizations '''
        return self.response_json(self.request('GET', '/organizations'))

    def is_org(self, org_id):
        ''' Checks whether an organization exists based on its id '''
        orgs = get_orgs()
        for o in orgs:
            if o['id'] == org_id:
                return True
        self.fail_json(msg='No organization found with ID {0}'.format(org_id))

    def is_org_dupe(self, org_name, data):
        ''' Checks whether multiple organizations exist with the same name '''
        dupe_orgs = list()
        for o in data:
            if o['name'] == org_name:
                dupe_orgs.append(o)
        if len(dupe_orgs) == 0:
            self.fail_json(msg="Found no organizations matching name {0}".format(org_name))
        elif len(dupe_orgs) == 1:
            return dupe_orgs[0]
        elif len(dupe_orgs) > 1:
            # TODO: Output organization info for each matching org
            # TODO: Output networks associated for each matching org
            self.fail_json(msg="Multiple organizations found with the name {0}".format(org_name))

    def get_org_id(self, org_name):
        ''' Returns an organization id based on organization name, only if unique
            If org_id is specified, return that instead of a lookup
        '''
        if self.params['org_id'] is not None:
            if self.is_org(self.params['org_id']) is True:
                return self.params['org_id']
        org = is_org_dupe(self.params['org_name'], self.get_orgs())
        return org['id']

    def get_net(self, org_name, net_name):
        ''' Return network information '''
        org_id = get_org_id(org_name)
        path = '/organizations/{0}/networks'.format(org_id)
        return self.response_json(self.request('GET', path))

    def get_net_id(self, org_name=None, net_name=None, data=None):
        ''' Returne network id from lookup or existing data '''
        if data is not None:
            return net['id']
        else:
            if org_name is not None and net_name is not None:
                net = self.get_net(org_name, net_name)
                return net['id']

    def construct_path(self, action):
        built_path = self.url_catalog[action][self.function]
        if 'replace_org_id' in built_path:
            built_path.replace('replace_org_id', self.get_org_id(module.params['org_name']))
        if 'replace_net_id' in built_path:
            built_path.replace('replace_net_id', self.get_net_id(module.params['net_name']))
        return built_path

    def create_object(self, payload):
        create_path = self.construct_path('create')
        return self.response_json(self.request('POST', create_path, payload=payload))

    def delete_object(self, payload):
        delete_path = self.construct_path('delete')
        return self.response_json(self.request('DELETE', delete_path, payload=payload))

    def request(self, method, path, payload=None):
        ''' Generic HTTP method for Meraki requests '''
        self.path = path
        self.define_protocol()
        if self.define_method() is -1:  # No changes are needed to existing object
            return

        self.url = '{0}://{1}/api/v0/{2}'.format(self.params['protocol'], self.params['host'], self.path.lstrip('/'))

        if payload is None:
            resp, info = fetch_url(self.module, self.url,
                                   headers=self.headers,
                                   method=self.method,
                                   timeout=self.params['timeout'],
                                   use_proxy=self.params['use_proxy'],
                                   )
        elif payload:
            resp, info = fetch_url(self.module, self.url,
                                   headers=self.headers,
                                   data=payload,
                                   method=self.method,
                                   timeout=self.params['timeout'],
                                   use_proxy=self.params['use_proxy'],
                                   )
        self.response = info['msg']
        self.status = info['status']
        response = json.loads(to_native(resp.read()))

        if self.status >= 300:
            try:
                self.error['text'] = self.response_json(info['body'])
                self.error['code'] = info['status']
                self.fail_json(msg='Dashboard API error %(code)s: %(text)s' % self.error)
            except KeyError:
                self.fail_json(msg='Connection failed for %(url)s. %(msg)s' % info)
        if self.status >= 201 and self.status <= 299 and method in self.modifiable_methods:
            self.result['changed'] = True
        return response

    def exit_json(self, **kwargs):
        if 'state' in self.params:
            if self.params['state'] in ('absent', 'present'):
                if self.params['output_level'] in ('debug', 'info'):
                    self.result['previous'] = self.existing

        # Return the gory details when we need it
        if self.params['output_level'] == 'debug':
            if 'state' in self.params:
                self.result['filter_string'] = self.filter_string
            self.result['method'] = self.method
            # self.result['path'] = self.path  # Adding 'path' in result causes state: absent in output
            self.result['response'] = self.response
            self.result['status'] = self.status
            self.result['url'] = self.url

        # if 'state' in self.params:
        #     self.original = self.existing
        #     if self.params['state'] in ('absent', 'present'):
        #         self.get_existing()

        #     self.result['current'] = self.existing

        #     if self.params['output_level'] in ('debug', 'info'):
        #         self.result['sent'] = self.config
        #         self.result['proposed'] = self.proposed

        self.result.update(**kwargs)
        self.module.exit_json(**self.result)

    def fail_json(self, msg, **kwargs):

        # Return error information, if we have it
        if self.error['code'] is not None and self.error['text'] is not None:
            self.result['error'] = self.error

        if 'state' in self.params:
            if self.params['state'] in ('absent', 'present'):
                if self.params['output_level'] in ('debug', 'info'):
                    self.result['previous'] = self.existing

            # Return the gory details when we need it
            # if self.params['output_level'] == 'debug':
            #     if self.imdata is not None:
            #         self.result['imdata'] = self.imdata
            #         self.result['totalCount'] = self.totalCount

        if self.params['output_level'] == 'debug':
            if self.url is not None:
                if 'state' in self.params:
                    self.result['filter_string'] = self.filter_string
                self.result['method'] = self.method
                # self.result['path'] = self.path  # Adding 'path' in result causes state: absent in output
                self.result['response'] = self.response
                self.result['status'] = self.status
                self.result['url'] = self.url

        if 'state' in self.params:
            if self.params['output_level'] in ('debug', 'info'):
                self.result['sent'] = self.config
                self.result['proposed'] = self.proposed

        self.result.update(**kwargs)
        self.module.fail_json(msg=msg, **self.result)
