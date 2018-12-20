# -*- coding: utf-8 -*-

# This code is part of Ansible, but is an independent component

# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.

# Copyright: (c) 2018, Dag Wieers <dag@wieers.com>
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

from copy import deepcopy
from ansible.module_utils.basic import AnsibleModule, json
from ansible.module_utils.six.moves.urllib.parse import urljoin
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native, to_bytes


def issubset(subset, superset):
    ''' Recurse through nested dictionary and compare entries '''

    # Both objects are the same object
    if subset is superset:
        return True

    # Both objects are identical
    if subset == superset:
        return True

    # Both objects have a different type
    if type(subset) != type(superset):
        return False

    for key, value in subset.items():
        # Item from subset is missing from superset
        if key not in superset:
            return False

        # Item has different types in subset and superset
        if type(superset[key]) != type(value):
            return False

        # Compare if item values are subset
        if isinstance(value, dict):
            if not issubset(superset[key], value):
                return False
        elif isinstance(value, list):
            if not set(value) <= set(superset[key]):
                return False
        elif isinstance(value, set):
            if not value <= superset[key]:
                return False
        else:
            if not value == superset[key]:
                return False

    return True


def update_qs(params):
    ''' Append key-value pairs to self.filter_string '''
    accepted_params = dict((k, v) for (k, v) in params.items() if v)
    return '?' + '&'.join(['%s=%s' % (k, v) for (k, v) in accepted_params.items()])


def msc_argument_spec():
    return dict(
        host=dict(type='str', required=True, aliases=['hostname']),
        port=dict(type='int', required=False),
        username=dict(type='str', default='admin'),
        password=dict(type='str', required=True, no_log=True),
        output_level=dict(type='str', default='normal', choices=['normal', 'info', 'debug']),
        timeout=dict(type='int', default=30),
        use_proxy=dict(type='bool', default=True),
        use_ssl=dict(type='bool', default=True),
        validate_certs=dict(type='bool', default=True),
    )


class MSCModule(object):

    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.result = dict(changed=False)
        self.headers = {'Content-Type': 'text/json'}

        # normal output
        self.existing = dict()

        # info output
        self.previous = dict()
        self.proposed = dict()
        self.sent = dict()

        # debug output
        self.filter_string = ''
        self.method = None
        self.path = None
        self.response = None
        self.status = None
        self.url = None

        # Ensure protocol is set
        self.params['protocol'] = 'https' if self.params.get('use_ssl', True) else 'http'

        # Set base_uri
        if 'port' in self.params and self.params['port'] is not None:
            self.baseuri = '{protocol}://{host}:{port}/api/v1/'.format(**self.params)
        else:
            self.baseuri = '{protocol}://{host}/api/v1/'.format(**self.params)

        if self.module._debug:
            self.module.warn('Enable debug output because ANSIBLE_DEBUG was set.')
            self.params['output_level'] = 'debug'

        if self.params['password']:
            # Perform password-based authentication, log on using password
            self.login()
        else:
            self.module.fail_json(msg="Parameter 'password' is required for authentication")

    def login(self):
        ''' Log in to MSC '''

        # Perform login request
        self.url = urljoin(self.baseuri, 'auth/login')
        payload = {'username': self.params['username'], 'password': self.params['password']}
        resp, auth = fetch_url(self.module,
                               self.url,
                               data=json.dumps(payload),
                               method='POST',
                               headers=self.headers,
                               timeout=self.params['timeout'],
                               use_proxy=self.params['use_proxy'])

        # Handle MSC response
        if auth['status'] != 201:
            self.response = auth['msg']
            self.status = auth['status']
            self.fail_json(msg='Authentication failed: {msg}'.format(**auth))

        payload = json.loads(resp.read())

        self.headers['Authorization'] = 'Bearer {token}'.format(**payload)

    def request(self, path, method=None, data=None, qs=None):
        ''' Generic HTTP method for MSC requests. '''
        self.path = path

        if method is not None:
            self.method = method

        self.url = urljoin(self.baseuri, path)

        if qs is not None:
            self.url = self.url + update_qs(qs)

        resp, info = fetch_url(self.module,
                               self.url,
                               headers=self.headers,
                               data=json.dumps(data),
                               method=self.method,
                               timeout=self.params['timeout'],
                               use_proxy=self.params['use_proxy'],
                               )
        self.response = info['msg']
        self.status = info['status']

        # 200: OK, 201: Created, 202: Accepted, 204: No Content
        if self.status in (200, 201, 202, 204):
            output = resp.read()
#            if self.method in ('DELETE', 'PATCH', 'POST', 'PUT') and self.status in (200, 201, 204):
#                self.result['changed'] = True
            if output:
                return json.loads(output)

        # 404: Not Found
        elif self.method == 'DELETE' and self.status == 404:
            return {}

        # 400: Bad Request, 401: Unauthorized, 403: Forbidden,
        # 405: Method Not Allowed, 406: Not Acceptable
        # 500: Internal Server Error, 501: Not Implemented
        elif self.status >= 400:
            try:
                payload = json.loads(resp.read())
            except Exception:
                payload = json.loads(info['body'])
            if 'code' in payload:
                self.fail_json(msg='MSC Error {code}: {message}'.format(**payload), data=data, info=info, payload=payload)
            else:
                self.fail_json(msg='MSC Error:'.format(**payload), data=data, info=info, payload=payload)

        return {}

    def query_objs(self, path, key=None, **kwargs):
        ''' Query the MSC REST API for objects in a path '''
        found = []
        objs = self.request(path, method='GET')

        if key is None:
            key = path

        for obj in objs[key]:
            for kw_key, kw_value in kwargs.items():
                if kw_value is None:
                    continue
                if obj[kw_key] != kw_value:
                    break
            else:
                found.append(obj)
        return found

    def get_obj(self, path, **kwargs):
        ''' Get a specific object from a set of MSC REST objects '''
        objs = self.query_objs(path, **kwargs)
        if len(objs) == 0:
            return {}
        if len(objs) > 1:
            self.fail_json(msg='More than one object matches unique filter: {0}'.format(kwargs))
        return objs[0]

    def lookup_domain(self, domain):
        ''' Look up a domain and return its id '''
        if domain is None:
            return domain

        d = self.get_obj('auth/domains', key='domains', name=domain)
        if not d:
            self.module.fail_json(msg="Domain '%s' is not valid." % domain)
        if 'id' not in d:
                self.module.fail_json(msg="Domain lookup failed for '%s': %s" % (domain, d))
        return d['id']

    def lookup_roles(self, roles):
        ''' Look up roles and return their ids '''
        if roles is None:
            return roles

        ids = []
        for role in roles:
            r = self.get_obj('roles', name=role)
            if not r:
                self.module.fail_json(msg="Role '%s' is not valid." % role)
            if 'id' not in r:
                self.module.fail_json(msg="Role lookup failed for '%s': %s" % (role, r))
            ids.append(dict(roleId=r['id']))
        return ids

    def create_label(self, label, label_type):
        ''' Create a new label '''
        return self.request('labels', method='POST', data=dict(displayName=label, type=label_type))

    def lookup_labels(self, labels, label_type):
        ''' Look up labels and return their ids (create if necessary) '''
        if labels is None:
            return None

        ids = []
        for label in labels:
            l = self.get_obj('labels', displayName=label)
            if not l:
                l = self.create_label(label, label_type)
            if 'id' not in l:
                self.module.fail_json(msg="Label lookup failed for '%s': %s" % (label, l))
            ids.append(l['id'])
        return ids

    def sanitize(self, updates, collate=False, required_keys=None):
        ''' Clean up unset keys from a request payload '''
        if required_keys is None:
            required_keys = []
        self.proposed = deepcopy(self.existing)
        self.sent = deepcopy(self.existing)

        # Clean up self.sent
        for key in updates:
            # Always retain 'id'
            if key in required_keys:
                pass

            # Remove unspecified values
            elif not collate and updates[key] is None:
                if key in self.existing:
                    del(self.sent[key])
                continue

            # Remove identical values
            elif not collate and key in self.existing and updates[key] == self.existing[key]:
                del(self.sent[key])
                continue

            # Add everything else
            if updates[key] is not None:
                self.sent[key] = updates[key]

        # Update self.proposed
        self.proposed.update(self.sent)

    def exit_json(self, **kwargs):
        ''' Custom written method to exit from module. '''

        if self.params['state'] in ('absent', 'present'):
            if self.params['output_level'] in ('debug', 'info'):
                self.result['previous'] = self.previous
            if self.previous != self.existing:
                self.result['changed'] = True

        # Return the gory details when we need it
        if self.params['output_level'] == 'debug':
            self.result['method'] = self.method
            self.result['response'] = self.response
            self.result['status'] = self.status
            self.result['url'] = self.url

            if self.params['state'] in ('absent', 'present'):
                self.result['sent'] = self.sent
                self.result['proposed'] = self.proposed

        self.result['current'] = self.existing

        if self.module._diff:
            self.result['diff'] = dict(
                before=self.previous,
                after=self.existing,
            )

        self.result.update(**kwargs)
        self.module.exit_json(**self.result)

    def fail_json(self, msg, **kwargs):
        ''' Custom written method to return info on failure. '''

        if self.params['state'] in ('absent', 'present'):
            if self.params['output_level'] in ('debug', 'info'):
                self.result['previous'] = self.previous
            if self.previous != self.existing:
                self.result['changed'] = True

        # Return the gory details when we need it
        if self.params['output_level'] == 'debug':
            if self.url is not None:
                self.result['method'] = self.method
                self.result['response'] = self.response
                self.result['status'] = self.status
                self.result['url'] = self.url

            if self.params['state'] in ('absent', 'present'):
                self.result['sent'] = self.sent
                self.result['proposed'] = self.proposed

        self.result['current'] = self.existing

        self.result.update(**kwargs)
        self.module.fail_json(msg=msg, **self.result)
