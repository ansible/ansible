# -*- coding: utf-8 -*-

# This code is part of Ansible, but is an independent component

# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.

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

URL_MAPPING = dict(
    organization=dict(path='organization'),
    )

def construct_url(action):
    print('test')

def meraki_argument_spec():
    return dict(auth_key=dict(type='str', no_log=True, fallback=(env_fallback, ['MERAKI_KEY'])),
                host=dict(type='str', default='api.meraki.com'),
                name=dict(type='str'),
                username=dict(type='str'),
                state=dict(type='str', choices=['present', 'absent', 'query',], required=True),
                use_proxy=dict(type='bool', default=True),
                use_ssl=dict(type='bool', default=True),
                validate_certs=dict(type='bool', default=True),
                output_level=dict(type='str', default='normal', choices=['normal', 'debug']),
                timeout=dict(type='int', default=30),
    )

class MerakiModule(object):

    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.result = dict(changed=False)
        self.headers = dict()

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

        # debug output
        self.filter_string = ''
        self.method = None
        self.path = None
        self.response = None
        self.status = None
        self.url = None

        if self.module._debug or self.params['output_level'] == 'debug':
            self.module.warn('Enable debug output because ANSIBLE_DEBUG was set or output_level is set to debug.')

        module.required_if=[
                               ['state', 'present', ['name']],
                               ['state', 'absent', ['name']],
                           ]

    def define_protocol(self):
        ''' Set protocol based on use_ssl parameters '''
        if self.params['use_ssl'] is True:
            self.params['protocol'] = 'https'
        else:
            self.params['protocol'] = 'http'

    def define_method(self):
        if self.params['state'] == 'query':
            self.method = 'GET'
        elif self.params['state'] == 'absent':
            self.method = 'DELETE'
        elif self.params['state'] == 'present':
            self.method = 'POST'

    def response_json(self, rawoutput):
        ''' Handle Dashboard API response output '''
        try:
            return json.loads(rawoutput)
        except Exception as e:
            self.error = dict(code=-1, text="Unable to parse output as JSON, see 'raw' output. {0}".format(e))
            self.result['raw'] = rawoutput
            return

    def get_existing(self, path):
        self.define_protocol()
        self.define_method()
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
        # self.module.fail_json(msg="Error", response=response)
        # self.module

        if self.status >= 300:
            try:
                self.error['text'] = self.response_json(info['body'])
                self.error['code'] = info['status']
                self.fail_json(msg='Dashboard API error %(code)s: %(text)s' % self.error)
            except KeyError:
                self.fail_json(msg='Connection failed for %(url)s. %(msg)s' % info)
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

        if 'state' in self.params:
            self.original = self.existing
            if self.params['state'] in ('absent', 'present'):
                self.get_existing()

            # if self.module._diff and self.original != self.existing:
            #     self.result['diff'] = dict(
            #         before=json.dumps(self.original, sort_keys=True, indent=4),
            #         after=json.dumps(self.existing, sort_keys=True, indent=4),
            #     )
            self.result['current'] = self.existing

            if self.params['output_level'] in ('debug', 'info'):
                self.result['sent'] = self.config
                self.result['proposed'] = self.proposed

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
            if self.params['output_level'] == 'debug':
                if self.imdata is not None:
                    self.result['imdata'] = self.imdata
                    self.result['totalCount'] = self.totalCount

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
