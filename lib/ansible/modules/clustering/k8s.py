#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Chris Houseknecht <@chouseknecht>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''

module: k8s

short_description: Perform CRUD operations on all K8s and OpenShift objects

version_added: "2.5"

author: "Chris Houseknecht (@chouseknecht)"

description:
  - Uses the Python openshift module to perform CRUD operations on all K8s and OpenShift objects.
  - Supports authentication using either a k8s config file, parameters, or ENV variables.

options:
  state:
    description:
    - Determines if an object should be created, patched, or deleted. When set to
      C(present), the object will be created, if it does not exist, or patched, if
      parameter values differ from the existing object's attributes, and deleted,
      if set to C(absent). A patch operation results in merging lists and updating
      dictionaries, with lists being merged into a unique set of values. If a list
      contains a dictionary with a I(name) or I(type) attribute, a strategic merge
      is performed, where individual elements with a matching I(name_) or I(type)
      are merged. To force the replacement of lists, set the I(force) option to C(True).
    default: present
    choices:
    - present
    - absent
  force:
    description:
    - If set to C(True), and I(state) is C(present), an existing object will be updated,
      and lists will be replaced, rather than merged.
    default: false
    type: bool
  resource_definition:
    description:
    - "Provide a valid YAML definition for an object when creating or updating. NOTE: I(kind), I(api_version), I(name),
      and I(namespace) will be overwritten by corresponding values found in the provided I(resource_definition)."
    aliases:
    - definition
    - inline
  src:
    description:
    - "Provide a path to a file containing a valid YAML definition of an object to be created or updated. Mutually
      exclusive with I(resource_definition). NOTE: I(kind), I(api_version), I(name), and I(namespace) will be
      overwritten by corresponding values found in the configuration read in from the I(src) file."
  api_version:
    description:
    - Use to specify the API version when deleting an object, or when creating an object, such as namespace or
      project, that only requires a I(name) attribute.
    aliases:
    - api
    - version
  kind:
    description:
    - Use to specify the object kind when deleting an object, or when creating an object, such as namespace or
      project, that only requires a I(name) attribute.
  name:
    description:
    - Use to specify an object name when deleting an object, or when creating an object, such as namespace or
      project, that only requires a name attribute.
  namespace:
    description:
    - Use to specify the namespace or project when deleting an object, or when creating an object, such as namespace
      or project, that only requires a I(name) attribute.
  host:
    description:
    - Provide a URL for acessing the Kubernetes API.
  api_key:
    description:
    - Token used to authenticate with the API.
  kubeconfig:
    description:
    - Path to an existing Kubernetes config file. If not provided, and no other connection
      options are provided, the openshift client will attempt to load the default
      configuration file from I(~/.kube/config.json).
  context:
    description:
    - The name of a context found in the Kubernetes config file.
  username:
    description:
    - Provide a username for connecting to the API.
  password:
    description:
    - Provide a password for connecting to the API. Use in conjunction with I(username).
  cert_file:
    description:
    - Path to a certificate used to authenticate with the API.
  key_file:
    description:
    - Path to a key file used to authenticate with the API.
  ssl_ca_cert:
    description:
    - Path to a CA certificate used to authenticate with the API.
  verify_ssl:
    description:
    - Whether or not to verify the API server's SSL certificates.
    type: bool

requirements:
    - "python >= 2.7"
    - "openshift >= 0.3"
    - "PyYAML >= 3.11"
'''

EXAMPLES = '''
- name: Create a k8s namespace
  k8s:
    name: testing
    api_version: v1
    kind: namespace
    state: present

- name: Create an OpenShift project
  k8s:
    name: testing
    api_version: v1
    kind: project
    state: present

- name: Create a Service object from an inline definition
  k8s:
    state: present
    definition:
      apiVersion: v1
      kind: Service
      metadata:
        name: web
        namespace: testing
        labels:
          app: galaxy
          service: web
      spec:
        selector:
          app: galaxy
          service: web
        ports:
        - protocol: TCP
          targetPort: 8000
          name: port-8000-tcp
          port: 8000

- name: Create a Service object by reading the definition from a file
  k8s:
    state: present
    src: /testing/service.yml

- name: Remove an existing Service object
  k8s:
    state: absent
    api_version: v1
    kind: service
    namespace: testing
    name: web
'''

RETURN = '''
result:
  description:
  - A JSON representation of the created, patched, or otherwise present object. In the case of a deletion, will be
    empty.
  returned: success
  type: dict
request:
  description:
  - The JSON request sent to the API. Useful for troubleshooting unexpected differences and 404 errors.
  returned: when diff is true
  type: dict
diff:
  description:
  - List of differences found when determining if an existing object will be patched. A copy of the existing object
    is updated with the requested options, and the updated object is then compared to the original. If there are
    differences, they will appear here when the --diff option is passed to ansible-playbook.
  returned: when diff is true
  type: list
'''

import copy
import json
import os
import re

from ansible.module_utils.six import iteritems
from ansible.module_utils.basic import AnsibleModule

try:
    from openshift.helper.ansible import KubernetesAnsibleModuleHelper, OpenShiftAnsibleModuleHelper
    from openshift.helper.exceptions import KubernetesException
    HAS_K8S_MODULE_HELPER = True
except ImportError as exc:
    HAS_K8S_MODULE_HELPER = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class K8sException(Exception):
    pass


class K8sModule(AnsibleModule):

    def __init__(self, argspec=None, mutually_exclusive=None, supports_check_mode=False):

        self.argspec = argspec

        if not HAS_K8S_MODULE_HELPER:
            raise K8sException(
                "This module requires the OpenShift Python client. Try `pip install openshift`"
            )

        if not HAS_YAML:
            raise K8sException(
                "This module requires PyYAML. Try `pip install PyYAML`"
            )

        AnsibleModule.__init__(self,
                               argument_spec=argspec,
                               supports_check_mode=supports_check_mode,
                               mutually_exclusive=mutually_exclusive)

        self.kind = self.params.pop('kind')
        self.api_version = self.params.pop('api_version')
        self.resource_definition = self.params.pop('resource_definition')
        self.src = self.params.pop('src')
        if self.src:
            self.resource_definition = self.load_resource_definition(self.src)

        if self.resource_definition:
            self.api_version = self.resource_definition.get('apiVersion')
            self.kind = self.resource_definition.get('kind')

        self.api_version = self.api_version.lower()
        self.kind = self._to_snake(self.kind)

        try:
            self.helper = self._get_helper(self.api_version, self.kind)
        except Exception as exc:
            raise K8sException(
                "Error initializing AnsibleModuleHelper: {}".format(str(exc))
            )

    def _get_helper(self, api_version, kind):
        if not api_version:
            self.fail_json(
                msg=("Error: no api_version specified. Use the api_version parameter, or provide it as part of a ",
                     "resource_definition.")
            )
        if not kind:
            self.fail_json(
                msg="Error: no kind specified. Use the kind parameter, or provide it as part of a resource_definition"
            )
        try:
            helper = KubernetesAnsibleModuleHelper(api_version=api_version, kind=kind, debug=False)
            helper.get_model(api_version, kind)
        except:
            try:
                helper = OpenShiftAnsibleModuleHelper(api_version=api_version, kind=kind, debug=False)
                helper.get_model(api_version, kind)
            except:
                raise
        return helper

    def execute_module(self):
        if self.resource_definition:
            resource_params = self.resource_to_parameters(self.resource_definition)
            self.params.update(resource_params)

        self._authenticate()

        state = self.params.pop('state', None)
        force = self.params.pop('force', False)
        dry_run = self.params.pop('dry_run', False)
        name = self.params.get('name')
        namespace = self.params.get('namespace')
        existing = None

        self._remove_aliases()

        return_attributes = dict(changed=False, result=dict())

        if dry_run:
            self.exit_json(**return_attributes)

        if self._diff:
            return_attributes['request'] = self.helper.request_body_from_params(self.params)

        try:
            existing = self.helper.get_object(name, namespace)
        except KubernetesException as exc:
            self.fail_json(msg='Failed to retrieve requested object: {}'.format(exc.message),
                           error=exc.value.get('status'))

        if state == 'absent':
            if not existing:
                # The object already does not exist
                self.exit_json(**return_attributes)
            else:
                # Delete the object
                if not self.check_mode:
                    try:
                        self.helper.delete_object(name, namespace)
                    except KubernetesException as exc:
                        self.fail_json(msg="Failed to delete object: {}".format(exc.message),
                                       error=exc.value.get('status'))
                return_attributes['changed'] = True
                self.exit_json(**return_attributes)
        else:
            if not existing:
                k8s_obj = self._create(namespace)
                return_attributes['result'] = k8s_obj.to_dict()
                return_attributes['changed'] = True
                self.exit_json(**return_attributes)

            if existing and force:
                k8s_obj = None
                request_body = self.helper.request_body_from_params(self.params)
                if not self.check_mode:
                    try:
                        k8s_obj = self.helper.replace_object(name, namespace, body=request_body)
                    except KubernetesException as exc:
                        self.fail_json(msg="Failed to replace object: {}".format(exc.message),
                                       error=exc.value.get('status'))
                return_attributes['result'] = k8s_obj.to_dict()
                return_attributes['changed'] = True
                self.exit_json(**return_attributes)

            # Check if existing object should be patched
            k8s_obj = copy.deepcopy(existing)
            try:
                self.helper.object_from_params(self.params, obj=k8s_obj)
            except KubernetesException as exc:
                self.fail_json(msg="Failed to patch object: {}".format(exc.message))
            match, diff = self.helper.objects_match(existing, k8s_obj)
            if match:
                return_attributes['result'] = existing.to_dict()
                self.exit_json(**return_attributes)
            elif self._diff:
                return_attributes['differences'] = diff
            # Differences exist between the existing obj and requested params
            if not self.check_mode:
                try:
                    k8s_obj = self.helper.patch_object(name, namespace, k8s_obj)
                except KubernetesException as exc:
                    self.fail_json(msg="Failed to patch object: {}".format(exc.message))
            return_attributes['result'] = k8s_obj.to_dict()
            return_attributes['changed'] = True
            self.exit_json(**return_attributes)

    def _authenticate(self):
        try:
            auth_options = {}
            auth_args = ('host', 'api_key', 'kubeconfig', 'context', 'username', 'password',
                         'cert_file', 'key_file', 'ssl_ca_cert', 'verify_ssl')
            for key, value in iteritems(self.params):
                if key in auth_args and value is not None:
                    auth_options[key] = value
            self.helper.set_client_config(**auth_options)
        except KubernetesException as e:
            self.fail_json(msg='Error loading config', error=str(e))

    def _remove_aliases(self):
        """
        The helper doesn't know what to do with aliased keys
        """
        for k, v in iteritems(self.argspec):
            if 'aliases' in v:
                for alias in v['aliases']:
                    if alias in self.params:
                        self.params.pop(alias)

    def _create(self, namespace):

        if self.kind.lower() == 'project':
            return self._create_project()

        request_body = None
        k8s_obj = None
        try:
            request_body = self.helper.request_body_from_params(self.params)
        except KubernetesException as exc:
            self.fail_json(msg="Failed to create object: {}".format(exc.message))
        if not self.check_mode:
            try:
                k8s_obj = self.helper.create_object(namespace, body=request_body)
            except KubernetesException as exc:
                self.fail_json(msg="Failed to create object: {}".format(exc.message),
                               error=exc.value.get('status'))
        return k8s_obj

    def _create_project(self):
        new_obj = None
        k8s_obj = None
        try:
            new_obj = self.helper.object_from_params(self.params)
        except KubernetesException as exc:
            self.fail_json(msg="Failed to create object: {}".format(exc.message))
        try:
            k8s_obj = self.helper.create_project(metadata=new_obj.metadata,
                                                 display_name=self.params.get('display_name'),
                                                 description=self.params.get('description'))
        except KubernetesException as exc:
            self.fail_json(msg='Failed to retrieve requested object',
                           error=exc.value.get('status'))
        return k8s_obj

    def _read(self, name, namespace):
        k8s_obj = None
        try:
            k8s_obj = self.helper.get_object(name, namespace)
        except KubernetesException as exc:
            self.fail_json(msg='Failed to retrieve requested object',
                           error=exc.value.get('status'))
        return k8s_obj

    def load_resource_definition(self, src):
        """ Load the requested src path """
        result = None
        path = os.path.normpath(src)
        self.log("Reading definition from {}".format(path))
        if not os.path.exists(path):
            self.fail_json(msg="Error accessing {}. Does the file exist?".format(path))
        try:
            result = yaml.safe_load(open(path, 'r'))
        except (IOError, yaml.YAMLError) as exc:
            self.fail_json(msg="Error loading resource_definition: {}".format(exc))
        return result

    def resource_to_parameters(self, resource):
        """ Converts a resource definition to module parameters """
        parameters = {}
        for key, value in iteritems(resource):
            if key in ('apiVersion', 'kind', 'status'):
                continue
            elif key == 'metadata' and isinstance(value, dict):
                for meta_key, meta_value in iteritems(value):
                    if meta_key in ('name', 'namespace', 'labels', 'annotations'):
                        parameters[meta_key] = meta_value
            elif key in self.helper.argspec and value is not None:
                    parameters[key] = value
            elif isinstance(value, dict):
                self._add_parameter(value, [key], parameters)
        self.log("Request to parameters: {}".format(json.dumps(parameters)))
        return parameters

    def _add_parameter(self, request, path, parameters):
        for key, value in iteritems(request):
            if path:
                param_name = '_'.join(path + [self._to_snake(key)])
            else:
                param_name = self.helper.attribute_to_snake(key)
            if param_name in self.helper.argspec and value is not None:
                parameters[param_name] = value
            elif isinstance(value, dict):
                continue_path = copy.copy(path) if path else []
                continue_path.append(self.helper.attribute_to_snake(key))
                self._add_parameter(value, continue_path, parameters)
            else:
                self.fail_json(
                    msg=("Error parsing resource definition. Encountered {}, which does not map to a parameter "
                         "expected by the openshift Python module.".format(param_name))
                )

    @staticmethod
    def _to_snake(name):
        """
        Convert a string from camel to snake
        :param name: string to convert
        :return: string
        """
        if not name:
            return name

        def replace(m):
            m = m.group(0)
            return m[0] + '_' + m[1:]

        p = r'[a-z][A-Z]|' \
            r'[A-Z]{2}[a-z]'
        result = re.sub(p, replace, name)
        return result.lower()


def main():
    argument_spec = {
        'state': {
            'default': 'present',
            'choices': ['present', 'absent'],
        },
        'force': {
            'type': 'bool',
            'default': False,
        },
        'resource_definition': {
            'type': 'dict',
            'aliases': ['definition', 'inline']
        },
        'src': {
            'type': 'path',
        },
        'kind': {},
        'name': {},
        'namespace': {},
        'api_version': {
            'aliases': ['api', 'version']
        },
        'kubeconfig': {
            'type': 'path',
        },
        'context': {},
        'host': {},
        'api_key': {
            'no_log': True,
        },
        'username': {},
        'password': {
            'no_log': True,
        },
        'verify_ssl': {
            'type': 'bool',
        },
        'ssl_ca_cert': {
            'type': 'path',
        },
        'cert_file': {
            'type': 'path',
        },
        'key_file': {
            'type': 'path',
        },
    }

    mutually_exclusive = [
        ('resource_definition', 'src'),
    ]

    K8sModule(argspec=argument_spec,
              mutually_exclusive=mutually_exclusive,
              supports_check_mode=True).execute_module()


if __name__ == '__main__':
    main()
