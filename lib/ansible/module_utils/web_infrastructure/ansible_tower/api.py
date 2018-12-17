# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2018 Red Hat Inc.
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
#

from ansible.module_utils.urls import Request
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.six.moves.urllib.parse import urlencode

class ApiEndpoint(object):
    def __init__(self, host, api, version):
        self.host = host
        self.api = api
        self.version = version

    def __str__(self):
        url = "https://"
        url += self.host
        url += "/"
        url += self.api
        url += "/"
        url += self.version
        return url

class AnsibleTowerBase(object):

    def __init__(self, provider):
        self.api = 'api'
        self.version = 'v2'
        self.headers = {'Content-Type': 'application/json'}
        self.host = provider['host']
        self.username = provider['username']
        self.password = provider['password']
        self.initial_url = ApiEndpoint(self.host,
                                       self.api,
                                       self.version)
        self.request = Request(headers=self.headers, url_username=self.username, url_password=self.password,
                               validate_certs=False, force_basic_auth=True)

    def construct_query(self, tower_module, filter_data):
        # This function constructs the lookup query
        query_url = ''
        query_url += str(self.initial_url) + tower_module
        query_url += "?" + urlencode(filter_data)
        return query_url


class AnsibleTowerLookup(AnsibleTowerBase):

    def __init__(self, provider, tower_module, filter_data):
        super(AnsibleTowerLookup, self).__init__(provider)
        self.tower_module = tower_module
        self.filter = filter_data

    def request_query(self):
        # This function will fire get request to check for the filter data
        query_url = self.construct_query(self.tower_module, self.filter)
        response = self.request.get(query_url)
        return response


class AnsibleTowerModule(AnsibleTowerBase):
    def __init__(self, module):
        self.module = module
        provider = module.params['provider']
        try:
            super(AnsibleTowerModule, self).__init__(provider)
        except Exception as exc:
            self.module.fail_json(msg=to_text(exc))

    def handle_exception(self, method_name, exc):
        ''' Handles any exceptions raised
            This method will then gracefully fail the module.
        '''
        if ('text' in exc.response):
            self.module.fail_json(
                msg=exc.response['text'],
                type=exc.response['Error'].split(':')[0],
                code=exc.response.get('code'),
                operation=method_name
            )
        else:
            self.module.fail_json(msg=to_native(exc))

    def run(self, module):
        ''' Runs the module and performans configuration tasks
            :args module: the tower module to operate against
            :returns: a results dict
        '''
        result = {'changed': False}
        response = self.get_object_ref(module)
        if response.count != 0:
            pass
        else:
            pass

    def get_object_ref(self, tower_module):
        tower_module = '/' + tower_module + '/'
        query_url = self.construct_query(tower_module, self.filter)
        response = self.request.get(query_url)
        return response
