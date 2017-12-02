#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017, Kenneth D. Evensen <kevensen@redhat.com>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = """
author:
  - "Kenneth D. Evensen (@kevensen)"
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
      - "The OpenShift service account token with which to authenticate against the OpenShift cluster."
    required: false
  kube_config:
    description:
      - "A path to the Kubernetes configuration file containing the cluster login credentials.  If the 'token'
         option isn't defined this is taken as the default login mechanism.  The 'kube_config' is mutually
         exclusive with 'token'."
    required: false
    default: ~/.kube/config
    version_added: 2.5
  kube_context:
    description:
      - "The login context to use when accessing the OpenShift cluster.  The last login credentials are indicated
         by 'current-context' which is the default context for the option."
    required: false
    default: current-context
    version_added: 2.5
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
  type: string
url:
  description: The URL to the requested resource.
  returned: success
  type: string
method:
  description: The HTTP method that was used to take action upon the resource
  returned: success
  type: string
...
'''

import base64
import os
import tempfile
import sys
try:
    import yaml
except ImportError:
    pass
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils import urls
from ansible.module_utils._text import to_text
from ansible.module_utils._text import to_native


class ApiEndpoint(object):
    def __init__(self, host, port, api, version):
        self.host = host
        self.port = port
        self.api = api
        self.version = version

    def __str__(self):
        url = "https://{0}:{1}/{2}/{3}".format(self.host, self.port, self.api, self.version)
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
        url = [str(self.resource_endpoint)]

        if self.resource_endpoint.namespaced:
            url.append('namespaces')
            url.append(self.namespace())
        url.append(self.resource_endpoint.name)
        if not create:
            url.append(self.name())
        return '/'.join(url)

    def __dict__(self):
        return self.definition

    def __str__(self):
        return self.module.jsonify(self.definition)


class OC(object):
    def __init__(self, module, host, port,
                 apis=None, token=None):
        apis = ['api', 'oapi'] if apis is None else apis

        self.apis = apis
        self.version = 'v1'
        self.token = token
        self.module = module
        self.host = host
        self.port = port
        self.kinds = {}

        # If the authentication mechanism is a token, we set the appropriate header
        if self.token:
            self.bearer = "Bearer " + self.token
            self.headers = {"Authorization": self.bearer,
                            "Content-type": "application/json"}
        # Otherwise, just set the content-type.
        else:
            self.headers = {"Content-type": "application/json"}

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
        _, code = self.connect(named_resource.url(), 'get')
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

        existing_definition, _ = self.get(named_resource)

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
            body = to_text(response.read(), errors='surrogate_or_strict')
        if info['status'] >= 300:
            body = to_native(info['body'])
        elif info['status'] == -1:
            body = str(info)

        message = "The URL, method, and code for connect is {0}, {1}, {2}: {3}".format(url, method, info['status'], body)
        if info['status'] == 401:
            self.module.fail_json(msg="{0}  Unauthorized.  Check that you have a valid serivce account and token.".format(message))

        self.module.log(msg=message)

        try:
            json_body = self.module.from_json(body)
        except TypeError:
            self.module.fail_json(msg="Response from {0} expected to be a expected string or buffer.  Instead was {1}".format(url, str(type(body))))
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
                    _, changed = self.merge(value, node, changed)

            elif isinstance(value, list) and key in destination.keys():
                if destination[key] != source[key]:
                    destination[key] = source[key]
                    changed = True

            elif (key not in destination.keys() or
                  destination[key] != source[key]):
                destination[key] = value
                changed = True
        return destination, changed


class KubeConfig(object):
    def __init__(self, module, config_file, context):
        self.module = module
        with open(config_file, 'r') as kube_file:
            kube_data = yaml.load(kube_file)
            # By default we will use the 'current-context' from the .kube/config file.  We also allow
            # for the user to specify the context to use.  While this is an unlikely scenario, it's
            # still possible.
            if context == 'current-context':
                self.context = kube_data['current-context']
            else:
                self.context = context
            self.context_info = [context['context'] for context in kube_data['contexts'] if context['name'] == self.context]

            if not self.context_info:
                raise self.module.fail_json(msg="Could not find context info from context {0} in kube config file {1}.".format(module.params['kube_context'],
                                                                                                                               module.params['kube_confg']))

            self.login_info = [user['user'] for user in kube_data['users'] if user['name'] in self.context_info[0]['user']]

            self.cluster_info = [cluster['cluster'] for cluster in kube_data['clusters'] if cluster['name'] == self.context_info[0]['cluster']]

            self.cert_file_name = None
            self.cert_file = None
            self.key_file_name = None
            self.key_file = None

    # The user authenticaion mechanism in the kubeconfig file may very well be a token.  If so, we will use it.
    def user_token(self):
        try:
            return self.login_info[0]['token']
        except KeyError:
            pass
        return None

    # The client certificate in the kube/config file is Base64 encoded.  We have to decode it.
    def user_client_cert(self):
        try:
            return base64.b64decode(self.login_info[0]['client-certificate-data'])
        except KeyError:
            pass
        return None

    # The client key in the kube/config file is Base64 encoded.  We have to decode it.
    def user_client_key(self):
        try:
            return base64.b64decode(self.login_info[0]['client-key-data'])
        except KeyError:
            pass
        return None

    # Because Python requests doesn't take a certificate as a string, but rather a file,
    # we will have to create a temporary file for the client certificate.
    def user_client_cert_file(self):
        if self.user_client_cert():
            self.cert_file, self.cert_file_name = tempfile.mkstemp()
            os.write(self.cert_file, self.user_client_cert())
            self.module.log('cert file name {0}'.format(self.cert_file_name))
            return self.cert_file_name
        return None

    # Because Python requests doesn't take a certificate as a string, but rather a file,
    # we will have to create a temporary file for the client key.
    def user_client_key_file(self):
        if self.user_client_key():
            self.key_file, self.key_file_name = tempfile.mkstemp()
            os.write(self.key_file, self.user_client_key())
            self.module.log('key file name {0}'.format(self.key_file_name))
            return self.key_file_name
        return None

    def clean(self):
        if os.path.isfile(self.cert_file_name):
            os.remove(self.cert_file_name)
        if os.path.isfile(self.key_file_name):
            os.remove(self.key_file_name)


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
            token=dict(required=False, type='str', no_log=True),
            kube_config=dict(required=False, type='path', default='~/.kube/config'),
            kube_context=dict(required=False, type='str', default='current-context'),
            state=dict(required=True,
                       choices=['present', 'absent']),
            validate_certs=dict(type='bool', default='yes')
        ),
        mutually_exclusive=(['kind', 'definition'],
                            ['name', 'definition'],
                            ['namespace', 'definition'],
                            ['kube_config', 'token'],
                            ['kube_context', 'token']),
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
    token = None
    kube_config = None

    # If the token is set in the module arguments, that takes priority.  Otherwise, the default
    # is to use the credentials in the kube/config.
    if module.params['token']:
        token = module.params['token']
        module.log("Using token specified in module args.")
    elif 'yaml' in sys.modules:
        kube_config = KubeConfig(module, module.params['kube_config'], module.params['kube_context'])
        if kube_config.user_token():
            token = kube_config.user_token()
            module.log("Using token from config file {0}".format(module.params['kube_config']))

        elif kube_config.user_client_cert():
            # By setting the client_cert and client_key module params, the values get passed down
            # to the Ansible urls module.
            module.params['client_cert'] = kube_config.user_client_cert_file()
            module.params['client_key'] = kube_config.user_client_key_file()
            module.log("Using client cert and key from config file {0}".format(module.params['kube_config']))
    # If a token isn't specified in the module arguments, we expect to use .kube/config.  However, this
    # requires PyYAML.  If it isn't found, we will raise an error.
    else:
        module.fail_json(msg="Attempted to read configuration file {0} but PyYAML isn't found on this host.  Install PyYAML or consider using the \'token\' module argument.".format(module.params['kube_config']))

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

    oc = OC(module, host, port, token=token)
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

    # Remove the temporary files if they exist.
    if kube_config:
        kube_config.clean()

    module.exit_json(changed=changed, ansible_facts=facts)


if __name__ == '__main__':
    main()
