#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017, Kenneth D. Evensen <kevensen@redhat.com>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['deprecated'],
    'supported_by': 'community'
}


DOCUMENTATION = """
author:
  - "Kenneth D. Evensen (@kevensen)"
deprecated:
  removed_in: "2.9"
  why: This module used the oc command line tool, where as M(openshift_raw) goes over the REST API.
  alternative: Use M(openshift_raw) instead.
description:
  - This module allows management of resources in an OpenShift cluster. The
    inventory host can be any host with network connectivity to the OpenShift
    cluster; the default port being 8443/TCP.
  - This module relies on a token to authenticate to OpenShift. This can either
    be a user or a service account.
module: oc
options:
  host:
    description:
      - "Hostname or address of the OpenShift API endpoint. By default, this is expected to be the current inventory host."
    required: false
    default: 127.0.0.1
  port:
    description:
      - "The port number of the API endpoint."
    required: false
    default: 8443
  inline:
    description:
      - "The inline definition of the resource. This is mutually exclusive with name, namespace and kind."
    required: false
    aliases: ['def', 'definition']
  kind:
    description: The kind of the resource upon which to take action.
    required: true
  name:
    description:
      - "The name of the resource on which to take action."
    required: false
  namespace:
    description:
      - "The namespace of the resource upon which to take action."
    required: false
  token:
    description:
      - "The token with which to authenticate against the OpenShift cluster."
    required: true
  validate_certs:
    description:
      - If C(no), SSL certificates for the target url will not be validated.
        This should only be used on personally controlled sites using
        self-signed certificates.
    type: bool
    default: yes
  state:
    choices:
      - present
      - absent
    description:
      - "If the state is present, and the resource doesn't exist, it shall be created using the inline definition. If the state is present and the
        resource exists, the definition will be updated, again using an inline definition. If the state is absent, the resource will be deleted if it exists."
    required: true
short_description: Manage OpenShift Resources
version_added: 2.4

"""

EXAMPLES = """
- name: Create project
  oc:
    state: present
    inline:
      kind: ProjectRequest
      metadata:
        name: ansibletestproject
      displayName: Ansible Test Project
      description: This project was created using Ansible
    token: << redacted >>

- name: Delete a service
  oc:
    state: absent
    name: myservice
    namespace: mynamespace
    kind: Service
    token: << redacted >>

- name: Add project role Admin to a user
  oc:
    state: present
    inline:
      kind: RoleBinding
      metadata:
        name: admin
        namespace: mynamespace
      roleRef:
        name: admin
      userNames:
        - "myuser"
      token: << redacted >>

- name: Obtain an object definition
  oc:
   state: present
   name: myroute
   namespace: mynamespace
   kind: Route
   token: << redacted >>
"""

RETURN = '''
result:
  description:
    The resource that was created, changed, or otherwise determined to be present.
    In the case of a deletion, this is the response from the delete request.
  returned: success
  type: str
url:
  description: The URL to the requested resource.
  returned: success
  type: str
method:
  description: The HTTP method that was used to take action upon the resource
  returned: success
  type: str
...
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils import urls


class ApiEndpoint(object):
    def __init__(self, host, port, api, version):
        self.host = host
        self.port = port
        self.api = api
        self.version = version

    def __str__(self):
        url = "https://"
        url += self.host
        url += ":"
        url += str(self.port)
        url += "/"
        url += self.api
        url += "/"
        url += self.version
        return url


class ResourceEndpoint(ApiEndpoint):
    def __init__(self, name, namespaced, api_endpoint):
        super(ResourceEndpoint, self).__init__(api_endpoint.host,
                                               api_endpoint.port,
                                               api_endpoint.api,
                                               api_endpoint.version)
        self.name = name
        self.namespaced = namespaced


class NamedResource(object):
    def __init__(self, module, definition, resource_endpoint):
        self.module = module
        self.set_definition(definition)
        self.resource_endpoint = resource_endpoint

    def name(self):
        if 'name' in self.definition['metadata'].keys():
            return self.definition['metadata']['name']
        return None

    def namespace(self):
        if 'namespace' in self.definition['metadata'].keys():
            return self.definition['metadata']['namespace']
        return None

    def set_definition(self, definition):
        if isinstance(definition, str):
            self.definition = self.module.from_json(definition)
        else:
            self.definition = definition

    def url(self, create=False):
        url = str(self.resource_endpoint)
        url += '/'
        if self.resource_endpoint.namespaced:
            url += 'namespaces/'
            url += self.namespace()
            url += '/'
        url += self.resource_endpoint.name
        if not create:
            url += '/'
            url += self.name()
        return url

    def __dict__(self):
        return self.definition

    def __str__(self):
        return self.module.jsonify(self.definition)


class OC(object):
    def __init__(self, module, token, host, port,
                 apis=None):
        apis = ['api', 'oapi'] if apis is None else apis

        self.apis = apis
        self.version = 'v1'
        self.token = token
        self.module = module
        self.host = host
        self.port = port
        self.kinds = {}

        self.bearer = "Bearer " + self.token
        self.headers = {"Authorization": self.bearer,
                        "Content-type": "application/json"}
        # Build Endpoints
        for api in self.apis:
            endpoint = ApiEndpoint(self.host,
                                   self.port,
                                   api,
                                   self.version)
            # Create resource facts
            response, code = self.connect(str(endpoint), "get")

            if code < 300:
                self.build_kinds(response['resources'], endpoint)

    def build_kinds(self, resources, endpoint):
        for resource in resources:
            if 'generated' not in resource['name']:
                self.kinds[resource['kind']] = \
                    ResourceEndpoint(resource['name'].split('/')[0],
                                     resource['namespaced'],
                                     endpoint)

    def get(self, named_resource):
        changed = False
        response, code = self.connect(named_resource.url(), 'get')
        return response, changed

    def exists(self, named_resource):
        x, code = self.connect(named_resource.url(), 'get')
        if code == 200:
            return True
        return False

    def delete(self, named_resource):
        changed = False
        response, code = self.connect(named_resource.url(), 'delete')
        if code == 404:
            return None, changed
        elif code >= 300:
            self.module.fail_json(msg='Failed to delete resource %s in \
                                  namespace %s with msg %s'
                                  % (named_resource.name(),
                                     named_resource.namespace(),
                                     response))
        changed = True
        return response, changed

    def create(self, named_resource):
        changed = False
        response, code = self.connect(named_resource.url(create=True),
                                      'post',
                                      data=str(named_resource))
        if code == 404:
            return None, changed
        elif code == 409:
            return self.get(named_resource)
        elif code >= 300:
            self.module.fail_json(
                msg='Failed to create resource %s in \
                namespace %s with msg %s' % (named_resource.name(),
                                             named_resource.namespace(),
                                             response))
        changed = True
        return response, changed

    def replace(self, named_resource, check_mode):
        changed = False

        existing_definition, x = self.get(named_resource)

        new_definition, changed = self.merge(named_resource.definition,
                                             existing_definition,
                                             changed)
        if changed and not check_mode:
            named_resource.set_definition(new_definition)
            response, code = self.connect(named_resource.url(),
                                          'put',
                                          data=str(named_resource))

            return response, changed
        return existing_definition, changed

    def connect(self, url, method, data=None):
        body = None
        json_body = ""
        if data is not None:
            self.module.log(msg="Payload is %s" % data)
        response, info = urls.fetch_url(module=self.module,
                                        url=url,
                                        headers=self.headers,
                                        method=method,
                                        data=data)
        if response is not None:
            body = response.read()
        if info['status'] >= 300:
            body = info['body']

        message = "The URL, method, and code for connect is %s, %s, %d." % (url, method, info['status'])
        if info['status'] == 401:
            self.module.fail_json(msg=message + "  Unauthorized.  Check that you have a valid serivce account and token.")

        self.module.log(msg=message)

        try:
            json_body = self.module.from_json(body)
        except TypeError:
            self.module.fail_json(msg="Response from %s expected to be a " +
                                  "expected string or buffer." % url)
        except ValueError:
            return body, info['status']

        return json_body, info['status']

    def get_resource_endpoint(self, kind):
        return self.kinds[kind]

    # Attempts to 'kindly' merge the dictionaries into a new object definition
    def merge(self, source, destination, changed):

        for key, value in source.items():
            if isinstance(value, dict):
                # get node or create one
                try:
                    node = destination.setdefault(key, {})
                except AttributeError:
                    node = {}
                finally:
                    x, changed = self.merge(value, node, changed)

            elif isinstance(value, list) and key in destination.keys():
                if destination[key] != source[key]:
                    destination[key] = source[key]
                    changed = True

            elif (key not in destination.keys() or
                  destination[key] != source[key]):
                destination[key] = value
                changed = True
        return destination, changed


def main():

    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', default='127.0.0.1'),
            port=dict(type='int', default=8443),
            definition=dict(aliases=['def', 'inline'],
                            type='dict'),
            kind=dict(type='str'),
            name=dict(type='str'),
            namespace=dict(type='str'),
            token=dict(required=True, type='str', no_log=True),
            state=dict(required=True,
                       choices=['present', 'absent']),
            validate_certs=dict(type='bool', default='yes')
        ),
        mutually_exclusive=(['kind', 'definition'],
                            ['name', 'definition'],
                            ['namespace', 'definition']),
        required_if=([['state', 'absent', ['kind']]]),
        required_one_of=([['kind', 'definition']]),
        no_log=False,
        supports_check_mode=True
    )
    kind = None
    definition = None
    name = None
    namespace = None

    host = module.params['host']
    port = module.params['port']
    definition = module.params['definition']
    state = module.params['state']
    kind = module.params['kind']
    name = module.params['name']
    namespace = module.params['namespace']
    token = module.params['token']

    if definition is None:
        definition = {}
        definition['metadata'] = {}
        definition['metadata']['name'] = name
        definition['metadata']['namespace'] = namespace

    if "apiVersion" not in definition.keys():
        definition['apiVersion'] = 'v1'
    if "kind" not in definition.keys():
        definition['kind'] = kind

    result = None
    oc = OC(module, token, host, port)
    resource = NamedResource(module,
                             definition,
                             oc.get_resource_endpoint(definition['kind']))

    changed = False
    method = ''
    exists = oc.exists(resource)
    module.log(msg="URL %s" % resource.url())

    if state == 'present' and exists:
        method = 'put'
        result, changed = oc.replace(resource, module.check_mode)
    elif state == 'present' and not exists and definition is not None:
        method = 'create'
        if not module.check_mode:
            result, changed = oc.create(resource)
        else:
            changed = True
            result = definition
    elif state == 'absent' and exists:
        method = 'delete'
        if not module.check_mode:
            result, changed = oc.delete(resource)
        else:
            changed = True
            result = definition

    facts = {}

    if result is not None and "items" in result:
        result['item_list'] = result.pop('items')
    elif result is None and state == 'present':
        result = 'Resource not present and no inline provided.'
    facts['oc'] = {'definition': result,
                   'url': resource.url(),
                   'method': method}

    module.exit_json(changed=changed, ansible_facts=facts)


if __name__ == '__main__':
    main()
