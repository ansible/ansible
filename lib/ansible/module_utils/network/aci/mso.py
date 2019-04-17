# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Dag Wieers (@dagwieers) <dag@wieers.com>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from copy import deepcopy
from ansible.module_utils.basic import AnsibleModule, json
from ansible.module_utils.six import PY3
from ansible.module_utils.six.moves.urllib.parse import urlencode, urljoin
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_bytes, to_native


if PY3:
    def cmp(a, b):
        return (a > b) - (a < b)


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
        # Ignore empty values
        if value is None:
            return True

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
            try:
                # NOTE: Fails for lists of dicts
                if not set(value) <= set(superset[key]):
                    return False
            except TypeError:
                # Fall back to exact comparison for lists of dicts
                if not cmp(value, superset[key]):
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
    accepted_params = dict((k, v) for (k, v) in params.items() if v is not None)
    return '?' + urlencode(accepted_params)


def mso_argument_spec():
    return dict(
        host=dict(type='str', required=True, aliases=['hostname']),
        port=dict(type='int', required=False),
        username=dict(type='str', default='admin'),
        password=dict(type='str', required=True, no_log=True),
        output_level=dict(type='str', default='normal', choices=['debug', 'info', 'normal']),
        timeout=dict(type='int', default=30),
        use_proxy=dict(type='bool', default=True),
        use_ssl=dict(type='bool', default=True),
        validate_certs=dict(type='bool', default=True),
    )


def mso_reference_spec():
    return dict(
        name=dict(type='str', required=True),
        schema=dict(type='str'),
        template=dict(type='str'),
    )


def mso_subnet_spec():
    return dict(
        subnet=dict(type='str', required=True, aliases=['ip']),
        description=dict(type='str'),
        scope=dict(type='str', choices=['private', 'public']),
        shared=dict(type='bool'),
        no_default_gateway=dict(type='bool'),
    )


def mso_contractref_spec():
    return dict(
        name=dict(type='str', required=True),
        schema=dict(type='str'),
        template=dict(type='str'),
        type=dict(type='str', required=True, choices=['consumer', 'provider']),
    )


class MSOModule(object):

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
        self.has_modified = False
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
        ''' Log in to MSO '''

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

        # Handle MSO response
        if auth['status'] != 201:
            self.response = auth['msg']
            self.status = auth['status']
            self.fail_json(msg='Authentication failed: {msg}'.format(**auth))

        payload = json.loads(resp.read())

        self.headers['Authorization'] = 'Bearer {token}'.format(**payload)

    def request(self, path, method=None, data=None, qs=None):
        ''' Generic HTTP method for MSO requests. '''
        self.path = path

        if method is not None:
            self.method = method

        # If we PATCH with empty operations, return
        if method == 'PATCH' and not data:
            return {}

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

        # self.result['info'] = info

        # Get change status from HTTP headers
        if 'modified' in info:
            self.has_modified = True
            if info['modified'] == 'false':
                self.result['changed'] = False
            elif info['modified'] == 'true':
                self.result['changed'] = True

        # 200: OK, 201: Created, 202: Accepted, 204: No Content
        if self.status in (200, 201, 202, 204):
            output = resp.read()
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
                output = resp.read()
                payload = json.loads(output)
            except (ValueError, AttributeError):
                try:
                    payload = json.loads(info['body'])
                except Exception:
                    self.fail_json(msg='MSO Error:', data=data, info=info)
            if 'code' in payload:
                self.fail_json(msg='MSO Error {code}: {message}'.format(**payload), data=data, info=info, payload=payload)
            else:
                self.fail_json(msg='MSO Error:'.format(**payload), data=data, info=info, payload=payload)

        return {}

    def query_objs(self, path, key=None, **kwargs):
        ''' Query the MSO REST API for objects in a path '''
        found = []
        objs = self.request(path, method='GET')

        if objs == {}:
            return found

        if key is None:
            key = path

        if key not in objs:
            self.fail_json(msg="Key '%s' missing from data", data=objs)

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
        ''' Get a specific object from a set of MSO REST objects '''
        objs = self.query_objs(path, **kwargs)
        if len(objs) == 0:
            return {}
        if len(objs) > 1:
            self.fail_json(msg='More than one object matches unique filter: {0}'.format(kwargs))
        return objs[0]

    def lookup_schema(self, schema):
        ''' Look up schema and return its id '''
        if schema is None:
            return schema

        s = self.get_obj('schemas', displayName=schema)
        if not s:
            self.module.fail_json(msg="Schema '%s' is not a valid schema name." % schema)
        if 'id' not in s:
            self.module.fail_json(msg="Schema lookup failed for schema '%s': %s" % (schema, s))
        return s['id']

    def lookup_domain(self, domain):
        ''' Look up a domain and return its id '''
        if domain is None:
            return domain

        d = self.get_obj('auth/domains', key='domains', name=domain)
        if not d:
            self.module.fail_json(msg="Domain '%s' is not a valid domain name." % domain)
        if 'id' not in d:
            self.module.fail_json(msg="Domain lookup failed for domain '%s': %s" % (domain, d))
        return d['id']

    def lookup_roles(self, roles):
        ''' Look up roles and return their ids '''
        if roles is None:
            return roles

        ids = []
        for role in roles:
            r = self.get_obj('roles', name=role)
            if not r:
                self.module.fail_json(msg="Role '%s' is not a valid role name." % role)
            if 'id' not in r:
                self.module.fail_json(msg="Role lookup failed for role '%s': %s" % (role, r))
            ids.append(dict(roleId=r['id']))
        return ids

    def lookup_site(self, site):
        ''' Look up a site and return its id '''
        if site is None:
            return site

        s = self.get_obj('sites', name=site)
        if not s:
            self.module.fail_json(msg="Site '%s' is not a valid site name." % site)
        if 'id' not in s:
            self.module.fail_json(msg="Site lookup failed for site '%s': %s" % (site, s))
        return s['id']

    def lookup_sites(self, sites):
        ''' Look up sites and return their ids '''
        if sites is None:
            return sites

        ids = []
        for site in sites:
            s = self.get_obj('sites', name=site)
            if not s:
                self.module.fail_json(msg="Site '%s' is not a valid site name." % site)
            if 'id' not in s:
                self.module.fail_json(msg="Site lookup failed for site '%s': %s" % (site, s))
            ids.append(dict(siteId=s['id'], securityDomains=[]))
        return ids

    def lookup_tenant(self, tenant):
        ''' Look up a tenant and return its id '''
        if tenant is None:
            return tenant

        t = self.get_obj('tenants', key='tenants', name=tenant)
        if not t:
            self.module.fail_json(msg="Tenant '%s' is not valid tenant name." % tenant)
        if 'id' not in t:
            self.module.fail_json(msg="Tenant lookup failed for tenant '%s': %s" % (tenant, t))
        return t['id']

    def lookup_users(self, users):
        ''' Look up users and return their ids '''
        if users is None:
            return users

        ids = []
        for user in users:
            u = self.get_obj('users', username=user)
            if not u:
                self.module.fail_json(msg="User '%s' is not a valid user name." % user)
            if 'id' not in u:
                self.module.fail_json(msg="User lookup failed for user '%s': %s" % (user, u))
            ids.append(dict(userId=u['id']))
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
                self.module.fail_json(msg="Label lookup failed for label '%s': %s" % (label, l))
            ids.append(l['id'])
        return ids

    def anp_ref(self, **data):
        ''' Create anpRef string '''
        return '/schemas/{schema_id}/templates/{template}/anps/{anp}'.format(**data)

    def epg_ref(self, **data):
        ''' Create epgRef string '''
        return '/schemas/{schema_id}/templates/{template}/anps/{anp}/epgs/{epg}'.format(**data)

    def bd_ref(self, **data):
        ''' Create bdRef string '''
        return '/schemas/{schema_id}/templates/{template}/bds/{bd}'.format(**data)

    def contract_ref(self, **data):
        ''' Create contractRef string '''
        # Support the contract argspec
        if 'name' in data:
            data['contract'] = data['name']
        return '/schemas/{schema_id}/templates/{template}/contracts/{contract}'.format(**data)

    def filter_ref(self, **data):
        ''' Create a filterRef string '''
        return '/schemas/{schema_id}/templates/{template}/filters/{filter}'.format(**data)

    def vrf_ref(self, **data):
        ''' Create vrfRef string '''
        return '/schemas/{schema_id}/templates/{template}/vrfs/{vrf}'.format(**data)

    def make_reference(self, data, reftype, schema_id, template):
        ''' Create a reference from a dictionary '''
        # Removes entry from payload
        if data is None:
            return None

        if data.get('schema') is not None:
            schema_obj = self.get_obj('schemas', displayName=data['schema'])
            if not schema_obj:
                self.fail_json(msg="Referenced schema '{schema}' in {reftype}ref does not exist".format(reftype=reftype, **data))
            schema_id = schema_obj['id']

        if data.get('template') is not None:
            template = data['template']

        refname = '%sName' % reftype

        return {
            refname: data['name'],
            'schemaId': schema_id,
            'templateName': template,
        }

    def make_subnets(self, data):
        ''' Create a subnets list from input '''
        if data is None:
            return None

        subnets = []
        for subnet in data:
            subnets.append(dict(
                ip=subnet['ip'],
                description=subnet.get('description', subnet['ip']),
                scope=subnet.get('scope', 'private'),
                shared=subnet.get('shared', False),
                noDefaultGateway=subnet.get('no_default_gateway', False),
            ))

        return subnets

    def sanitize(self, updates, collate=False, required=None, unwanted=None):
        ''' Clean up unset keys from a request payload '''
        if required is None:
            required = []
        if unwanted is None:
            unwanted = []
        self.proposed = deepcopy(self.existing)
        self.sent = deepcopy(self.existing)

        for key in self.existing:
            # Remove References
            if key.endswith('Ref'):
                del(self.proposed[key])
                del(self.sent[key])
                continue

            # Removed unwanted keys
            elif key in unwanted:
                del(self.proposed[key])
                del(self.sent[key])
                continue

        # Clean up self.sent
        for key in updates:
            # Always retain 'id'
            if key in required:
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
            # FIXME: Modified header only works for PATCH
            if not self.has_modified and self.previous != self.existing:
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

        if self.module._diff and self.result['changed'] is True:
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
            # FIXME: Modified header only works for PATCH
            if not self.has_modified and self.previous != self.existing:
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
