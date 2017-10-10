# -*- coding: utf-8 -*-
# (c) 2017, Kenneth D. Evensen <kevensen@redhat.com>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: openshift
    version_added: "2.5"
    short_description: Returns the JSON definition of an object in OpenShift
    description:
        - This lookup plugin provides the ability to query an OpenShift Container
        - platform cluster for information about objects.  This plugin requires
        - a valid user or service account token.
    options:
      kind:
        description:
          - The kind of OpenShift resource to read (e.g. Project, Service, Pod)
        required: True
      host:
        description:
          - The IP address of the host serving the OpenShift API
        required: False
        default: 127.0.0.1
      port:
        description:
          - The port on which to access the OpenShift API
        required: False
        default: 8443
      token:
        description:
          - The token to use for authentication against the OpenShift API.
          - This can be a user or ServiceAccount token.
        required: True
      validate_certs:
        description:
          - Whether or not to validate the TLS certificate of the API.
        required: False
        default: True
      namespace:
        description:
          - The namespace/project where the object resides.
        required: False
      resource_name:
        description:
          - The name of the object to query.
        required: False
      pretty:
        description:
          - Whether or not to prettify the output.  This is useful for debugging.
        required: False
        default: False
      labelSelector:
        description:
          - Additional labels to include in the query.
        required: False
      fieldSelector:
        description:
          - Specific fields on which to query.
        required: False
      resourceVersion:
        description:
          - Query for a specific resource version.
        required: False
"""

EXAMPLES = """
- name: Get Project {{ project_name }}
  set_fact:
    project_fact:  "{{ lookup('openshift',
                       kind='Project',
                       host=inventory_host,
                       token=hostvars[inventory_host]['ansible_sa_token'],
                       resource_name=project_name,
                       validate_certs=validate_certs) }}"
- name: Get All Service Accounts in a Project
  set_fact:
    service_fact: "{{ lookup('openshift',
                      kind='ServiceAccount',
                      host=inventory_host,
                      token=hostvars[inventory_host]['ansible_sa_token'],
                      namespace=project_name,
                      validate_certs=validate_certs) }}"
"""

RETURN = """
  _list:
    description:
      - An object definition or list of objects definitions returned from OpenShift.
    type: dict
"""

import json
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils import urls
from ansible.module_utils.six.moves import urllib
from ansible.module_utils.six.moves import urllib_error
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils._text import to_text
from ansible.module_utils._text import to_native


class OcpQuery(object):
    def __init__(self, host, port, token, validate_certs):
        self.apis = ['api', 'oapi']
        self.token = token
        self.validate_certs = validate_certs
        self.host = host
        self.port = port
        self.kinds = {}
        bearer = "Bearer " + self.token
        self.headers = {"Authorization": bearer}
        self.build_facts()

    def build_facts(self):

        for api in self.apis:
            url = "https://{0}:{1}/{2}/v1".format(self.host, self.port, api)
            try:
                response = urls.open_url(url=url,
                                         headers=self.headers,
                                         validate_certs=self.validate_certs,
                                         method='get')
            except urllib_error.HTTPError as error:
                try:
                    body = to_native(error.read())
                except AttributeError:
                    body = ''
                raise AnsibleError("OC Query raised exception with code {0} and message {1} against url {2}".format(error.code, body, url))

            for resource in json.loads(to_text(response.read(), errors='surrogate_or_strict'))['resources']:
                if 'generated' not in resource['name']:
                    self.kinds[resource['kind']] = \
                        {'kind': resource['kind'],
                         'name': resource['name'].split('/')[0],
                         'namespaced': resource['namespaced'],
                         'api': api,
                         'version': 'v1',
                         'baseurl': url
                         }

    def url(self, kind=None, namespace=None, resource_name=None, pretty=False, labelSelector=None, fieldSelector=None, resourceVersion=None):
        first_param = True

        url = [self.kinds[kind]['baseurl']]
        if self.kinds[kind]['namespaced'] is True:
            url.append('/namespaces/')
            if namespace is None:
                raise AnsibleError('Kind %s requires a namespace.'
                                   ' None provided' % kind)
            url.append(namespace)

        url.append('/' + self.kinds[kind]['name'])

        if resource_name is not None:
            url.append('/' + resource_name)

        if pretty:
            url.append('?pretty')
            first_param = False

        if labelSelector is not None:
            if first_param:
                url.append('?')
            else:
                url.append('&')

            url.append(urlencode({'labelSelector': labelSelector}))
            first_param = False

        if fieldSelector is not None:
            if first_param:
                url.append('?')
            else:
                url.append('&')

            url.append(urlencode({'fieldSelector': fieldSelector}))
            first_param = False

        if resourceVersion is not None:
            if first_param:
                url.append('?')
            else:
                url.append('&')

            url.append(urlencode({'resourceVersion': resourceVersion}))
            first_param = False

        return "".join(url)

    def query(self, kind=None, namespace=None, resource_name=None, pretty=False, labelSelector=None, fieldSelector=None, resourceVersion=None):
        url = self.url(kind=kind,
                       namespace=namespace,
                       resource_name=resource_name,
                       pretty=pretty,
                       labelSelector=labelSelector,
                       fieldSelector=fieldSelector,
                       resourceVersion=resourceVersion)

        try:
            response = urls.open_url(url=url,
                                     headers=self.headers,
                                     validate_certs=self.validate_certs,
                                     method='get')
        except urllib_error.HTTPError as error:
            try:
                body = to_native(error.read())
            except AttributeError:
                body = ''
            raise AnsibleError("OC Query raised exception with code {0} and message {1} against url {2}".format(error.code, body, url))

        return json.loads(to_text(response.read(), errors='surrogate_or_strict'))


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):

        host = kwargs.get('host', '127.0.0.1')
        port = kwargs.get('port', '8443')
        validate_certs = kwargs.get('validate_certs', True)
        token = kwargs.get('token', None)

        namespace = kwargs.get('namespace', None)
        resource_name = kwargs.get('resource_name', None)
        pretty = kwargs.get('pretty', False)
        label_selector = kwargs.get('labelSelector', None)
        field_selector = kwargs.get('fieldSelector', None)
        resource_version = kwargs.get('resourceVersion', None)
        resource_kind = kwargs.get('kind', None)

        ocp = OcpQuery(host, port, token, validate_certs)

        search_response = ocp.query(kind=resource_kind,
                                    namespace=namespace,
                                    resource_name=resource_name,
                                    pretty=pretty,
                                    labelSelector=label_selector,
                                    fieldSelector=field_selector,
                                    resourceVersion=resource_version)
        if search_response is not None and "items" in search_response:
            search_response['item_list'] = search_response.pop('items')

        values = [search_response]

        return values
