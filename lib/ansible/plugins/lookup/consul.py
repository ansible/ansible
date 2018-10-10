from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import string
from ansible.errors import AnsibleError

from ansible.plugins.lookup import LookupBase

try:
    import consul

    HAS_CONSUL = True
except ImportError as importError:
    HAS_CONSUL = False


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        if not HAS_CONSUL:
            raise AnsibleError(
                'python-consul is required for consul lookup. See https://python-consul.readthedocs.io/en/latest/#installation')
        key = next(iter(terms), None)
        api = kwargs.get('api', 'kv')
        port = kwargs.get('port', '8500')
        host = kwargs.get('host', 'localhost')
        scheme = kwargs.get('scheme', 'http')
        validate_certs = kwargs.get('validate_certs', True)
        client_cert = kwargs.get('client_cert', None)
        short_keys = kwargs.get('short_keys', False)

        try:
            consul_api = consul.Consul(host=host, port=port, scheme=scheme, verify=validate_certs, cert=client_cert)
            results = None
            if api is 'kv':
                index, results = consul_api.kv.get(key, token=kwargs.get('token', None),
                                                   index=kwargs.get('index', None),
                                                   recurse=kwargs.get('recurse', False))
            if results is not None:
                if isinstance(results, list) and short_keys:
                    for result in results:
                        result['Key'] = string.replace(result['Key'], key + '/', '')

            return results
        except Exception as e:
            raise AnsibleError("Error looking up '%s' in consul '%s'. Error was %s" % (key, api, e))
