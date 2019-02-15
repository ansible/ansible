# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2019 Red Hat Inc.
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

import os

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
SKYDIVE_GREMLIN_QUERY = 'G.V().Has'

SKYDIVE_PROVIDER_SPEC = {
    'endpoint': dict(fallback=(env_fallback, ['SKYDIVE_ENDPOINT'])),
    'username': dict(fallback=(env_fallback, ['SKYDIVE_USERNAME'])),
    'password': dict(fallback=(env_fallback, ['SKYDIVE_PASSWORD']), no_log=True),
    'insecure': dict(type='bool', default=False, fallback=(env_fallback, ['SKYDIVE_INSECURE'])),
    'ssl': dict(type='bool', default=False, fallback=(env_fallback, ['SKYDIVE_SSL']))
}


class skydive_restclient(object):
    ''' Base class for implementing Skydive Rest API '''
    provider_spec = {'provider': dict(type='dict', options=SKYDIVE_PROVIDER_SPEC)}

    def __init__(self, **kwargs):
        if not HAS_SKYDIVE_CLIENT:
            raise Exception('skydive-client is required but does not appear '
                            'to be installed.  It can be installed using the '
                            'command `pip install skydive-client`')

        if not set(kwargs.keys()).issubset(SKYDIVE_PROVIDER_SPEC.keys()):
            raise Exception('invalid or unsupported keyword argument for skydive_restclient connection.')
        for key, value in iteritems(SKYDIVE_PROVIDER_SPEC):
            if key not in kwargs:
                # apply default values from SKYDIVE_PROVIDER_SPEC since we cannot just
                # assume the provider values are coming from AnsibleModule
                if 'default' in value:
                    kwargs[key] = value['default']
                # override any values with env variables unless they were
                # explicitly set
                env = ('SKYDIVE_%s' % key).upper()
                if env in os.environ:
                    kwargs[key] = os.environ.get(env)
        kwargs['scheme'] = "http"
        if 'ssl' in kwargs:
            if kwargs['ssl']:
                kwargs['scheme'] = "https"
        if 'insecure' not in kwargs:
            kwargs['insecure'] = False
        self.restclient_object = RESTClient(kwargs['endpoint'],
                                            scheme=kwargs['scheme'],
                                            insecure=kwargs['insecure'],
                                            username=kwargs['username'],
                                            password=kwargs['password'])


class skydive_lookup(skydive_restclient):
    provider_spec = {'provider': dict(type='dict', options=SKYDIVE_PROVIDER_SPEC)}

    def __init__(self, provider):
        super(skydive_lookup, self).__init__(**provider)
        self.query_str = ""

    def lookup_query(self, filter_data):
        query_key = filter_data.keys()[0]
        self.query_str = filter_data[query_key]
        nodes = self.restclient_object.lookup_nodes(self.query_str)
        result = []
        for each in nodes:
            result.append(each.__dict__)
        if len(result) == 0:
            raise Exception("Cannot find any entry for the input Gremlin query!")
        return result


class skydive_flow_capture(skydive_restclient):
    ''' Implements Skydive Flow capture modules '''
    def __init__(self, module):
        self.module = module
        provider = module.params['provider']

        super(skydive_flow_capture, self).__init__(**provider)

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

        if obj_filter['query']:
            cature_query = obj_filter['query']
        elif obj_filter['interface_name'] and obj_filter['type']:
            cature_query = SKYDIVE_GREMLIN_QUERY + "('Name', '{0}', 'Type', '{1}')".format(obj_filter['interface_name'],
                                                                                           obj_filter['type'])
        else:
            raise self.module.fail_json(msg="Interface name and Type is required if gremlin query is not defined!")

        # to check current object ref for idempotency
        captured_list_objs = self.restclient_object.capture_list()
        current_ref_uuid = None
        for each_capture in captured_list_objs:
            if cature_query == each_capture.__dict__['query']:
                current_ref_uuid = each_capture.__dict__['uuid']
                break
        if state == 'present':
            if not current_ref_uuid:
                try:
                    self.restclient_object.capture_create(cature_query, obj_filter['capture_name'],
                                                          obj_filter['description'], obj_filter['extra_tcp_metric'],
                                                          obj_filter['ip_defrag'], obj_filter['reassemble_tcp'],
                                                          obj_filter['layer_key_mode'])
                except Exception as e:
                    self.module.fail_json(msg=to_text(e))
                result['changed'] = True
        if state == 'absent':
            if current_ref_uuid:
                try:
                    self.restclient_object.capture_delete(current_ref_uuid)
                except Exception as e:
                    self.module.fail_json(msg=to_text(e))
                result['changed'] = True

        return result
