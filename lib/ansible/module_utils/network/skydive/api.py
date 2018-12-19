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

import os
from functools import partial
from ansible.module_utils._text import to_native
from ansible.module_utils.six import iteritems
from ansible.module_utils._text import to_text

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
SKYDIVE_LOOKUP_BY_NAME = 'Name'


class skydive_base(object):
    ''' Base class for implementing Infoblox WAPI API '''

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
        self.query_str = SKYDIVE_LOOKUP_QUERY + "('" + SKYDIVE_LOOKUP_BY_NAME + "' ,'" + arg_val + "' )"
        nodes = self.restclient_object.lookup_nodes(self.query_str)

        return nodes[0].__dict__

class skydive_flow_topology(skydive_base):
    pass

class skydive_graph_engine(skydive_base):
    pass