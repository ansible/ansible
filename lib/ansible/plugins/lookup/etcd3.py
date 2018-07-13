from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    author:
        - Caio Tedim <caiotedim(at)gmail(dot)com>
    lookup: etcd3
    short_description: get on etcd3 server
    description:
        - Retrieves data from etcd3 server
    options:
        url:
            description:
                - URL for etcd3 server
            default: 127.0.0.1:2379
            type: string
            required: True
        key:
            description:
                - Key to lookup on etcd3 server
            type: string
            required: True
    response:
        - Return value in a json format
        - If key not found the return comes on stdout attribute
'''

EXAMPLES = '''
    - name: "Get key from etcd3 server"
      debug: msg="{{ lookup('etcd3', key='test',url='127.0.0.1:2379').foo }}"
    - name: "Get key from etcd3 server, this key is not-found"
      debug: msg="{{ lookup('etcd3', key='testt',url='127.0.0.1:2379').stdout }}"
'''

RETURN = '''
    _raw:
        description: field data requested
'''
import json

from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleError

try:
    import etcd3
    HAS_ETCD3 = True
except ImportError as e:
    HAS_ETCD3 = False


class Etcd3:

    def __init__(self):
        if not HAS_ETCD3:
            raise AnsibleError('python-etcd3 is required for etcd3 lookup, '
                               'take a look on https://pypi.org/project/etcd3/')

    def run(self, terms, variables=None, **kwargs):
        self.params = kwargs

        url = kwargs.get('url')
        key = kwargs.get('key')

        if url is None:
            url = "127.0.0.1:2379"

        address = url.split(':')
        isValid, host, port = self.validAddress(address)

        if not isValid:
            raise AnsibleError("Please check if your url param is defined follow documentation "
                               "url=<host:port>")

        resp = self.get(key, host, port)
        return resp

    def get(self, key, host, port):
        try:
            client = etcd3.client(host, port)
            resp = []
            for value, i in client.get_prefix(key):
                if value is not None:
                    resp.append(json.loads(value))
            if len(resp) < 1:
                resp = [{"stdout": "key not-found"}]
            return resp
        except Exception:
            raise

    def validAddress(self, address):
        if address[0] == '' or address[1] == '':
            return False, None, None

        if len(address) < 2 or len(address) > 2:
            if address[0] == 'http' or address[0] == 'https':
                return True, address[1].split('/')[2], address[2]
            return False, None, None
        else:
            return True, address[0], address[1]


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        return Etcd3().run(terms, variables=variables, **kwargs)
