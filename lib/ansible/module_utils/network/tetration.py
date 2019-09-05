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

from __future__ import (absolute_import, division, print_function)
import os
import json
from functools import partial
from ansible.module_utils._text import to_native
from ansible.module_utils.six import iteritems, iterkeys
from ansible.module_utils._text import to_text

try:
    from tetpyclient import RestClient
    HAS_TETRATION_CLIENT = True
except ImportError:
    HAS_TETRATION_CLIENT = False
try:
    import urllib3
    # Disable SSL Warnings
    urllib3.disable_warnings()
except ImportError:
    pass

# defining tetration constants
TETRATION_API_INVENTORY_TAG = '/inventory/tags'
TETRATION_API_ROLE = '/roles'
TETRATION_API_TENANT = '/vrfs'
TETRATION_API_USER = '/users'
TETRATION_API_SENSORS = '/sensors'
TETRATION_API_INVENTORY_FILTER = '/filters/inventories'
TETRATION_API_SCOPES = '/app_scopes'
TETRATION_API_INTERFACE_INTENTS = '/inventory_config/interface_intents'
TETRATION_API_AGENT_NAT_CONFIG = '/agentnatconfig'
TETRATION_API_APPLICATIONS = '/applications'
TETRATION_API_APPLICATION_POLICIES = '/policies'
TETRATION_API_AGENT_CONFIG_PROFILES = '/inventory_config/profiles'
TETRATION_API_AGENT_CONFIG_INTENTS = '/inventory_config/intents'
TETRATION_COLUMN_NAMES = '/assets/cmdb/attributenames'
TETRATION_API_EXT_ORCHESTRATORS = '/orchestrator'

TETRATION_PROVIDER_SPEC = {
    'server_endpoint': dict(type='str', required=True, aliases=['endpoint', 'host']),
    'api_key': dict(type='str', required=True),
    'api_secret': dict(type='str', required=True, no_log=True),
    'verify': dict(type='bool', default=False),
    'silent_ssl_warnings': dict(type='bool', default=True),
    'timeout': dict(type='int', default=10),
    'max_retries': dict(type='int', default=3),
    'api_version': dict(type='str', default='v1')
}


class TetrationApiBase(object):
    ''' Base class for implementing Tetration API '''
    provider_spec = {'provider': dict(type='dict',
                                      options=TETRATION_PROVIDER_SPEC)}

    def __init__(self, provider, module):
        if not HAS_TETRATION_CLIENT:
            raise Exception('tetpyclient is required but does not appear '
                            'to be installed.  It can be installed using the '
                            'command `pip install tetpyclient`')
        if len(provider.keys()) > 0:
            for key in provider.keys():
                if key not in TETRATION_PROVIDER_SPEC.keys():
                    del provider[key]
        for key, value in iteritems(TETRATION_PROVIDER_SPEC):
            if key not in provider:
                # apply default values from NIOS_PROVIDER_SPEC since we cannot just
                # assume the provider values are coming from AnsibleModule
                if 'default' in value:
                    provider[key] = value['default']
                # override any values with env variables unless they were
                # explicitly set
                env = ('TETRATION_%s' % key).upper()
                if env in os.environ:
                    provider[key] = os.environ.get(env)
                # if key is required but still not defined raise Exception
                if key not in provider and 'required' in value and value['required']:
                    raise ValueError('option: %s is required' % key)
        self.rc = RestClient(**provider)


class TetrationApiModule(TetrationApiBase):
    ''' Implements Tetration OpenAPI for executing a tetration module '''
    def __init__(self, module):
        self.module = module
        provider = module.params.get('provider') if module.params.get('provider') else dict()
        try:
            super(TetrationApiModule, self).__init__(provider, module)
        except Exception as exc:
            self.module.fail_json(msg=to_text(exc))

    def handle_exception(self, method_name, exc):
        ''' Handles any exceptions raised
        This method is called when an unexpected response
        code is returned from a Tetration OpenAPI call
        '''
        self.module.fail_json(
            msg=exc.text,
            code=exc.status_code,
            operation=method_name
        )

    def get_object(self, filter, target=None, params=None, sub_element=None, allow_multiple=False, search_array=None):
        '''Returns a single object from Tetration that exactly matches every
        value specified in filter.
        '''
        result_array = []
        while True:
            if search_array:
                query_result = search_array
            else:
                query_result = self.get(target=target, params=params, req_payload=None)
            search_objects = query_result[sub_element] if sub_element and sub_element in query_result else query_result
            for obj in search_objects:
                match = True
                for k, v in iteritems(filter):
                    if obj[k] != v:
                        match = False
                if match:
                    if allow_multiple:
                        result_array.append(obj)
                    else:
                        return obj
            if 'offset' in query_result and not search_array:
                params['offset'] = query_result['offset']
            else:
                return result_array if result_array else None

    def run_method(self, method_name, target, **kwargs):
        methods = {
            'get': self.get,
            'post': self.post,
            'put': self.put,
            'delete': self.delete
        }
        if 'req_payload' in kwargs:
            kwargs['json_body'] = json.dumps(kwargs['req_payload'])
            del kwargs['req_payload']
        return methods[method_name.lower()](target, **kwargs)

    def get(self, target, **kwargs):
        resp = self.rc.get(target, **kwargs)
        # import pdb; pdb.set_trace()
        if resp.status_code == 400:
            return None
        elif resp.status_code == 200:
            return resp.json()
        else:
            self.handle_exception('get', resp)

    def post(self, target, **kwargs):
        resp = self.rc.post(target, **kwargs)
        if resp.status_code/100 == 2:
            try:
                return resp.json()
            except ValueError:
                return None
        else:
            self.handle_exception('post', resp)

    def put(self, target, **kwargs):
        resp = self.rc.put(target, **kwargs)
        if resp.status_code/100 == 2:
            try:
                return resp.json()
            except ValueError:
                return None
        else:
            self.handle_exception('put', resp)

    def delete(self, target, **kwargs):
        resp = self.rc.delete(target, **kwargs)
        if resp.status_code/100 == 2:
            try:
                return resp.json()
            except ValueError:
                return None
        else:
            self.handle_exception('delete', resp)

    def filter_object(self, obj1, obj2, check_only=False):
        changed_flag = False
        try:
            for k in list(iterkeys(obj1)):
                if k in list(iterkeys(obj2)):
                    if type(obj1[k]) is dict:
                        if (lambda a, b: (a > b)-(a < b))(obj1[k], obj2[k]) != 0:
                            changed_flag = True
                    elif obj1[k] != obj2[k]:
                        changed_flag = True
                    if not changed_flag and not check_only:
                        del obj1[k]
                else:
                    changed_flag = True
            return changed_flag
        except AttributeError:
            changed_flag = True
            return changed_flag

    def compare_keys(self, obj1, obj2):
        unknown_keys = []
        for k in list(iterkeys(obj1)):
            if k not in list(iterkeys(obj2)):
                unknown_keys.append(k)
        return unknown_keys

    def clear_values(self, obj):
        for k in list(iterkeys(obj)):
            obj[k] = ''

TETRATION_API_PROTOCOLS = [
    dict(name='ANY', value=""),
    dict(name='TCP', value=6),
    dict(name='UDP', value=17),
    dict(name='ICMP', value=1),
    dict(name='Other', value=0),
    dict(name='A/N', value=107),
    dict(name='AH', value=51),
    dict(name='ARGUS', value=13),
    dict(name='ARIS', value=104),
    dict(name='AX.25', value=93),
    dict(name='BBN-RCC-MON', value=10),
    dict(name='BNA', value=49),
    dict(name='BR-SAT-MON', value=76),
    dict(name='CARP', value=112),
    dict(name='CBT', value=7),
    dict(name='CFTP', value=62),
    dict(name='CHAOS', value=16),
    dict(name='CPHB', value=73),
    dict(name='CPNX', value=72),
    dict(name='CRTP', value=126),
    dict(name='CRUDP', value=127),
    dict(name='Compaq-Peer', value=110),
    dict(name='DCCP', value=33),
    dict(name='DCN-MEAS', value=19),
    dict(name='DDP', value=37),
    dict(name='DDX', value=116),
    dict(name='DGP', value=86),
    dict(name='DIVERT', value=258),
    dict(name='DSR', value=48),
    dict(name='EGP', value=8),
    dict(name='EIGRP', value=88),
    dict(name='EMCON', value=14),
    dict(name='ENCAP', value=98),
    dict(name='ESP', value=50),
    dict(name='ETHERIP', value=97),
    dict(name='FC', value=133),
    dict(name='FIRE', value=125),
    dict(name='GGP', value=3),
    dict(name='GMTP', value=100),
    dict(name='GRE', value=47),
    dict(name='HIP', value=139),
    dict(name='HMP', value=20),
    dict(name='I-NLSP', value=52),
    dict(name='IATP', value=117),
    dict(name='IDPR', value=35),
    dict(name='IDPR-CMTP', value=38),
    dict(name='IDRP', value=45),
    dict(name='IFMP', value=101),
    dict(name='IGMP', value=2),
    dict(name='IGP', value=9),
    dict(name='IL', value=40),
    dict(name='IP-ENCAP', value=4),
    dict(name='IPCV', value=71),
    dict(name='IPComp', value=108),
    dict(name='IPIP', value=94),
    dict(name='IPLT', value=129),
    dict(name='IPPC', value=67),
    dict(name='IPV6', value=41),
    dict(name='IPV6-FRAG', value=44),
    dict(name='IPV6-ICMP', value=58),
    dict(name='IPV6-NONXT', value=59),
    dict(name='IPV6-OPTS', value=60),
    dict(name='IPV6-ROUTE', value=43),
    dict(name='IPX-in-IP', value=111),
    dict(name='IRTP', value=28),
    dict(name='ISIS', value=124),
    dict(name='ISO-IP', value=80),
    dict(name='ISO-TP4', value=29),
    dict(name='KRYPTOLAN', value=65),
    dict(name='L2TP', value=115),
    dict(name='LARP', value=91),
    dict(name='LEAF-1', value=25),
    dict(name='LEAF-2', value=26),
    dict(name='MANET', value=138),
    dict(name='MERIT-INP', value=32),
    dict(name='MFE-NSP', value=31),
    dict(name='MICP', value=95),
    dict(name='MOBILE', value=55),
    dict(name='MPLS-IN-IP', value=137),
    dict(name='MTP', value=92),
    dict(name='MUX', value=18),
    dict(name='Mobility-Header', value=135),
    dict(name='NARP', value=54),
    dict(name='NETBLT', value=30),
    dict(name='NSFNET-IGP', value=85),
    dict(name='NVP-II', value=11),
    dict(name='OSPFIGP', value=89),
    dict(name='PFSYNC', value=240),
    dict(name='PGM', value=113),
    dict(name='PIM', value=103),
    dict(name='PIPE', value=131),
    dict(name='PNNI', value=102),
    dict(name='PRM', value=21),
    dict(name='PTP', value=123),
    dict(name='PUP', value=12),
    dict(name='PVP', value=75),
    dict(name='QNX', value=106),
    dict(name='RDP', value=27),
    dict(name='ROHC', value=142),
    dict(name='RSVP', value=46),
    dict(name='RSVP-E2E-IGNORE', value=134),
    dict(name='RVD', value=66),
    dict(name='SAT-EXPAK', value=64),
    dict(name='SAT-MON', value=69),
    dict(name='SCC-SP', value=96),
    dict(name='SCPS', value=105),
    dict(name='SCTP', value=132),
    dict(name='SDRP', value=42),
    dict(name='SECURE-VMTP', value=82),
    dict(name='SHIM6', value=140),
    dict(name='SKIP', value=57),
    dict(name='SM', value=122),
    dict(name='SMP', value=121),
    dict(name='SNP', value=109),
    dict(name='SPS', value=130),
    dict(name='SRP', value=119),
    dict(name='SSCOPMCE', value=128),
    dict(name='ST2', value=5),
    dict(name='STP', value=118),
    dict(name='SUN-ND', value=77),
    dict(name='SWIPE', value=53),
    dict(name='Sprite-RPC', value=90),
    dict(name='TCF', value=87),
    dict(name='TLSP', value=56),
    dict(name='TP++', value=39),
    dict(name='TRUNK-1', value=23),
    dict(name='TRUNK-2', value=24),
    dict(name='TTP', value=84),
    dict(name='UDPLite', value=136),
    dict(name='UTI', value=120),
    dict(name='VINES', value=83),
    dict(name='VISA', value=70),
    dict(name='VMTP', value=81),
    dict(name='WB-EXPAK', value=79),
    dict(name='WB-MON', value=78),
    dict(name='WESP', value=141),
    dict(name='WSN', value=74),
    dict(name='XNET', value=15),
    dict(name='XNS-IDP', value=22),
    dict(name='XTP', value=36),
]
