import json
import re
import sys

from ansible.module_utils.basic import env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.six.moves.urllib.parse import urlencode


def scaleway_argument_spec():
    return dict(
        api_token=dict(required=True, fallback=(env_fallback, ['SCW_TOKEN', 'SCW_API_KEY', 'SCW_OAUTH_TOKEN', 'SCW_API_TOKEN']),
                       no_log=True, aliases=['oauth_token']),
        api_url=dict(fallback=(env_fallback, ['SCW_API_URL']), default='https://api.scaleway.com', aliases=['base_url']),
        api_timeout=dict(type='int', default=30, aliases=['timeout']),
        query_parameters=dict(type='dict', default={}),
        validate_certs=dict(default=True, type='bool'),
    )


def payload_from_object(scw_object):
    return dict(
        (k, v)
        for k, v in scw_object.items()
        if k != 'id' and v is not None
    )


class ScalewayException(Exception):

    def __init__(self, message):
        self.message = message


# Specify a complete Link header, for validation purposes
R_LINK_HEADER = r'''<[^>]+>;\srel="(first|previous|next|last)"
    (,<[^>]+>;\srel="(first|previous|next|last)")*'''
# Specify a single relation, for iteration and string extraction purposes
R_RELATION = r'<(?P<target_IRI>[^>]+)>; rel="(?P<relation>first|previous|next|last)"'


def parse_pagination_link(header):
    if not re.match(R_LINK_HEADER, header, re.VERBOSE):
        raise ScalewayException('Scaleway API answered with an invalid Link pagination header')
    else:
        relations = header.split(',')
        parsed_relations = {}
        rc_relation = re.compile(R_RELATION)
        for relation in relations:
            match = rc_relation.match(relation)
            if not match:
                raise ScalewayException('Scaleway API answered with an invalid relation in the Link pagination header')
            data = match.groupdict()
            parsed_relations[data['relation']] = data['target_IRI']
        return parsed_relations


class Response(object):

    def __init__(self, resp, info):
        self.body = None
        if resp:
            self.body = resp.read()
        self.info = info

    @property
    def json(self):
        if not self.body:
            if "body" in self.info:
                return json.loads(self.info["body"])
            return None
        try:
            return json.loads(self.body)
        except ValueError:
            return None

    @property
    def status_code(self):
        return self.info["status"]

    @property
    def ok(self):
        return self.status_code in (200, 201, 202, 204)


class Scaleway(object):

    def __init__(self, module):
        self.module = module
        self.headers = {
            'X-Auth-Token': self.module.params.get('api_token'),
            'User-Agent': self.get_user_agent_string(module),
            'Content-type': 'application/json',
        }
        self.name = None

    def get_resources(self):
        results = self.get('/%s' % self.name)

        if not results.ok:
            raise ScalewayException('Error fetching {0} ({1}) [{2}: {3}]'.format(
                self.name, '%s/%s' % (self.module.params.get('api_url'), self.name),
                results.status_code, results.json['message']
            ))

        return results.json.get(self.name)

    def _url_builder(self, path, params):
        d = self.module.params.get('query_parameters')
        if params is not None:
            d.update(params)
        query_string = urlencode(d, doseq=True)

        if path[0] == '/':
            path = path[1:]
        return '%s/%s?%s' % (self.module.params.get('api_url'), path, query_string)

    def send(self, method, path, data=None, headers=None, params=None):
        url = self._url_builder(path=path, params=params)
        self.warn(url)
        data = self.module.jsonify(data)

        if headers is not None:
            self.headers.update(headers)

        resp, info = fetch_url(
            self.module, url, data=data, headers=self.headers, method=method,
            timeout=self.module.params.get('api_timeout')
        )

        # Exceptions in fetch_url may result in a status -1, the ensures a proper error to the user in all cases
        if info['status'] == -1:
            self.module.fail_json(msg=info['msg'])

        return Response(resp, info)

    @staticmethod
    def get_user_agent_string(module):
        return "ansible %s Python %s" % (module.ansible_version, sys.version.split(' ')[0])

    def get(self, path, data=None, headers=None, params=None):
        return self.send(method='GET', path=path, data=data, headers=headers, params=params)

    def put(self, path, data=None, headers=None, params=None):
        return self.send(method='PUT', path=path, data=data, headers=headers, params=params)

    def post(self, path, data=None, headers=None, params=None):
        return self.send(method='POST', path=path, data=data, headers=headers, params=params)

    def delete(self, path, data=None, headers=None, params=None):
        return self.send(method='DELETE', path=path, data=data, headers=headers, params=params)

    def patch(self, path, data=None, headers=None, params=None):
        return self.send(method="PATCH", path=path, data=data, headers=headers, params=params)

    def update(self, path, data=None, headers=None, params=None):
        return self.send(method="UPDATE", path=path, data=data, headers=headers, params=params)

    def warn(self, x):
        self.module.warn(str(x))


SCALEWAY_LOCATION = {
    'par1': {'name': 'Paris 1', 'country': 'FR', "api_endpoint": 'https://cp-par1.scaleway.com'},
    'EMEA-FR-PAR1': {'name': 'Paris 1', 'country': 'FR', "api_endpoint": 'https://cp-par1.scaleway.com'},

    'ams1': {'name': 'Amsterdam 1', 'country': 'NL', "api_endpoint": 'https://cp-ams1.scaleway.com'},
    'EMEA-NL-EVS': {'name': 'Amsterdam 1', 'country': 'NL', "api_endpoint": 'https://cp-ams1.scaleway.com'}
}

SCALEWAY_ENDPOINT = "https://api-world.scaleway.com"

SCALEWAY_REGIONS = [
    "fr-par",
    "nl-ams",
]

SCALEWAY_ZONES = [
    "fr-par-1",
    "nl-ams-1",
]
