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

from ansible.module_utils.six import iteritems
from ansible.module_utils.six import iterkeys
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback

try:
    from skydive.rest.client import RESTClient
    HAS_SKYDIVE_CLIENT = True
except ImportError:
    HAS_SKYDIVE_CLIENT = False

# defining skydive constants
SKYDIVE_LOOKUP_QUERY = 'G.V().Has'

SKYDIVE_PROVIDER_SPEC = {
    'endpoint': dict(fallback=(env_fallback, ['SKYDIVE_HOST'])),
    'username': dict(fallback=(env_fallback, ['SKYDIVE_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['SKYDIVE_PASSWORD']), no_log=True),
    'ssl_verify': dict(type='bool', default=False, fallback=(env_fallback, ['SKYDIVE_SSL_VERIFY']))
}


class skydive_restclient(object):
    ''' Base class for implementing Skydive Rest API '''
    provider_spec = {'provider': dict(type='dict', options=SKYDIVE_PROVIDER_SPEC)}

    def __init__(self, endpoint="localhost:8082", username="admin", password="password"):
        try:
            self.restclient_object = RESTClient(endpoint, username=username, password=password)
        except TypeError as err:
            raise err


class skydive_lookup(skydive_restclient):
    provider_spec = {'provider': dict(type='dict', options=SKYDIVE_PROVIDER_SPEC)}

    def __init__(self, provider):
        endpoint = provider['host']
        username = provider['username']
        password = provider['password']
        super(skydive_lookup, self).__init__(endpoint, username, password)
        self.query_str = ""

    def lookup_query(self, filter_data):
        query_key = filter_data.keys()[0]
        self.query_str = SKYDIVE_LOOKUP_QUERY + "('{0}', '{1}')".format(query_key, filter_data[query_key])
        nodes = self.restclient_object.lookup_nodes(self.query_str)
        return nodes[0].__dict__


class skydive_flow_topology(skydive_restclient):
    ''' Implements Skydive Flow capture modules '''
    def __init__(self, module):
        self.module = module
        provider = module.params['provider']

        endpoint = provider['host']
        username = provider['username']
        password = provider['password']

        super(skydive_flow_topology, self).__init__(endpoint, username, password)

    def run(self, ib_spec):
        state = self.module.params['state']
        if state not in ('present', 'absent'):
            self.module.fail_json(msg='state must be one of `present`, `absent`, got `%s`' % state)

        result = {'changed': False}
        obj_filter = dict([(k, self.module.params[k]) for k, v in iteritems(ib_spec) if v.get('ib_req')])

        proposed_object = {}
        for key in iterkeys(ib_spec):
            if self.module.params[key] is not None:
                proposed_object[key] = self.module.params[key]

        if state == 'present':
            capture_str = SKYDIVE_LOOKUP_QUERY + "('Name', '{0}', 'Type', '{1}', 'extra_tcp_metric', '{2}'\
                                                 ,'ip_defrag', '{3}', 'reassemble_tcp',\
                                                 '{4}')".format(obj_filter['name'],
                                                                obj_filter['capture_type'],
                                                                obj_filter['extra_tcp_metric'],
                                                                obj_filter['ip_defrag'],
                                                                obj_filter['reassemble_tcp'])
            try:
                self.restclient_object.capture_create(capture_str)
            except Exception as e:
                self.module.fail_json(msg=to_text(e))
            result['changed'] = True
        if state == 'absent':
            capture_str = SKYDIVE_LOOKUP_QUERY + "('Name', '{0}', 'Type', '{1}', 'extra_tcp_metric', '{2}'\
                                                 ,'ip_defrag', '{3}', 'reassemble_tcp',\
                                                 '{4}')".format(obj_filter['name'],
                                                                obj_filter['capture_type'],
                                                                obj_filter['extra_tcp_metric'],
                                                                obj_filter['ip_defrag'],
                                                                obj_filter['reassemble_tcp'])
            # iterating over the captured list and get capture uuid
            for each_capture in self.restclient_object.capture_list().keys():
                if capture_str == self.restclient_object.capture_list()[each_capture]['GremlinQuery']:
                    uuid = each_capture
                    break
            try:
                if uuid:
                    self.restclient_object.capture_delete(uuid)
            except Exception:
                self.module.fail_json(msg="Capture UUID for the input Gremlin query is not found!")
            result['changed'] = True

        return result
