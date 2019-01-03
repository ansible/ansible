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

try:
    from skydive.graph import Node, Edge
    from skydive.rest.client import RESTClient
    from skydive.websocket.client import WSClient
    from skydive.websocket.client import WSClientDebugProtocol
    from skydive.websocket.client import WSMessage
    from skydive.websocket.client import NodeAddedMsgType, EdgeAddedMsgType
    HAS_SKYDIVE_CLIENT = True
except ImportError:
    HAS_SKYDIVE_CLIENT = False

# defining skydive constants
SKYDIVE_LOOKUP_QUERY = 'G.V().Has'


class skydive_base(object):
    ''' Base class for implementing Skydive Rest API '''

    def __init__(self, host="localhost:8082", user="admin", password="password"):
        try:
            self.restclient_object = RESTClient(host, username=user, password=password)
            self.websocketclient_object = WSClient(host, username=user, password=password)
        except TypeError as err:
            raise err


class skydive_lookup(skydive_base):

    def __init__(self):
        super(skydive_lookup, self).__init__()
        self.query_str = ""

    def lookup_query(self, arg_val):
        query_key = arg_val.keys()[0]
        self.query_str = SKYDIVE_LOOKUP_QUERY + "('" + query_key + "' ,'" + arg_val[query_key] + "' )"
        nodes = self.restclient_object.lookup_nodes(self.query_str)
        return nodes[0].__dict__


class skydive_flow_topology(skydive_base):
    ''' Implements Skydive Flow capture modules '''
    def __init__(self, module):
        self.module = module
        super(skydive_flow_topology, self).__init__()

    def run(self, ib_spec):
        state = self.module.params['state']
        if state not in ('present', 'absent'):
            self.module.fail_json(msg='state must be one of `present`, `absent`, got `%s`' % state)

        result = {'changed': False}
        obj_filter = dict([(k, self.module.params[k]) for k, v in iteritems(ib_spec) if v.get('ib_req')])

        proposed_object = {}
        for key, value in iteritems(ib_spec):
            if self.module.params[key] is not None:
                proposed_object[key] = self.module.params[key]

        if state == 'present':
            name = obj_filter.keys()[0]
            type = obj_filter.keys()[1]
            flow_str = SKYDIVE_LOOKUP_QUERY + "(" + name + ', ' + obj_filter[name] + ' ' + type + ', ' + obj_filter[
                type] + " )"
            self.restclient_object.capture_create(flow_str)
            result['changed'] = True
        if state == 'absent':
            name = obj_filter.keys()[0]
            type = obj_filter.keys()[1]
            flow_str = SKYDIVE_LOOKUP_QUERY + "(" + name + ', ' + obj_filter[name] + ' ' + type + ', ' + obj_filter[
                type] + " )"
            self.restclient_object.capture_delete(flow_str)
            result['changed'] = True

        return result


class skydive_graph_engine(skydive_base):
    ''' Implements Skydive Graph event bus modules '''
    def __init__(self, module):
        self.module = module
        super(skydive_graph_engine, self).__init__()

    def run(self, ib_spec):
        state = self.module.params['state']
        if state not in ('present', 'absent'):
            self.module.fail_json(msg='state must be one of `present`, `absent`, got `%s`' % state)

        result = {'changed': False}
        obj_filter = dict([(k, self.module.params[k]) for k, v in iteritems(ib_spec) if v.get('ib_req')])

        proposed_object = {}
        for key, value in iteritems(ib_spec):
            if self.module.params[key] is not None:
                proposed_object[key] = self.module.params[key]

        if state == 'present':
            name = obj_filter.keys()[0]
            capture_type = obj_filter.keys()[1]
            flow_str = SKYDIVE_LOOKUP_QUERY + "('" + name + "' , '" + obj_filter[
                name] + "' '" + capture_type + "', '" + obj_filter[capture_type] + "' )"
            self.restclient_object.capture_create(flow_str)
            result['changed'] = True

        return result
