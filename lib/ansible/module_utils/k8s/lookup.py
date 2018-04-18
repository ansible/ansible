#
#  Copyright 2018 Red Hat | Ansible
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function

import json
import os

from ansible.module_utils.k8s.common import OpenShiftAnsibleModuleMixin, DateTimeEncoder, remove_secret_data, to_snake
from ansible.module_utils.k8s.helper import AUTH_ARG_SPEC

try:
    from openshift.helper.kubernetes import KubernetesObjectHelper
    from openshift.helper.exceptions import KubernetesException
    HAS_K8S_MODULE_HELPER = True
except ImportError as exc:
    HAS_K8S_MODULE_HELPER = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class KubernetesLookup(object):

    def __init__(self):

        if not HAS_K8S_MODULE_HELPER:
            raise Exception(
                "Requires the OpenShift Python client. Try `pip install openshift`"
            )

        if not HAS_YAML:
            raise Exception(
                "Requires PyYAML. Try `pip install PyYAML`"
            )

        self.kind = None
        self.name = None
        self.namespace = None
        self.api_version = None
        self.label_selector = None
        self.field_selector = None
        self.include_uninitialized = None
        self.resource_definition = None
        self.helper = None
        self.connection = {}

    def run(self, terms, variables=None, **kwargs):
        self.kind = kwargs.get('kind')
        self.name = kwargs.get('resource_name')
        self.namespace = kwargs.get('namespace')
        self.api_version = kwargs.get('api_version', 'v1')
        self.label_selector = kwargs.get('label_selector')
        self.field_selector = kwargs.get('field_selector')
        self.include_uninitialized = kwargs.get('include_uninitialized', False)

        resource_definition = kwargs.get('resource_definition')
        src = kwargs.get('src')
        if src:
            resource_definition = self.load_resource_definition(src)
        if resource_definition:
            self.params_from_resource_definition(resource_definition)

        if not self.kind:
            raise Exception(
                "Error: no Kind specified. Use the 'kind' parameter, or provide an object YAML configuration "
                "using the 'resource_definition' parameter."
            )

        self.kind = to_snake(self.kind)
        self.helper = self.get_helper(self.api_version, self.kind)

        auth_args = ('host', 'api_key', 'kubeconfig', 'context', 'username', 'password',
                     'cert_file', 'key_file', 'ssl_ca_cert', 'verify_ssl')

        for arg in AUTH_ARG_SPEC:
            if arg in auth_args and kwargs.get(arg) is not None:
                self.connection[arg] = kwargs.get(arg)

        try:
            self.helper.set_client_config(**self.connection)
        except Exception as exc:
            raise Exception(
                "Client authentication failed: {0}".format(exc.message)
            )

        if self.name:
            return self.get_object()

        return self.list_objects()

    def get_helper(self, api_version, kind):
        try:
            helper = KubernetesObjectHelper(api_version=api_version, kind=kind, debug=False)
            helper.get_model(api_version, kind)
            return helper
        except KubernetesException as exc:
            raise Exception("Error initializing helper: {0}".format(exc.message))

    def load_resource_definition(self, src):
        """ Load the requested src path """
        path = os.path.normpath(src)
        if not os.path.exists(path):
            raise Exception("Error accessing {0}. Does the file exist?".format(path))
        try:
            result = yaml.safe_load(open(path, 'r'))
        except (IOError, yaml.YAMLError) as exc:
            raise Exception("Error loading resource_definition: {0}".format(exc))
        return result

    def params_from_resource_definition(self, defn):
        if defn.get('apiVersion'):
            self.api_version = defn['apiVersion']
        if defn.get('kind'):
            self.kind = defn['kind']
        if defn.get('metadata', {}).get('name'):
            self.name = defn['metadata']['name']
        if defn.get('metadata', {}).get('namespace'):
            self.namespace = defn['metadata']['namespace']

    def get_object(self):
        """ Fetch a named object """
        try:
            result = self.helper.get_object(self.name, self.namespace)
        except KubernetesException as exc:
            raise Exception('Failed to retrieve requested object: {0}'.format(exc.message))
        response = []
        if result is not None:
            # Convert Datetime objects to ISO format
            result_json = json.loads(json.dumps(result.to_dict(), cls=DateTimeEncoder))
            if self.kind == 'secret':
                remove_secret_data(result_json)
            response.append(result_json)

        return response

    def list_objects(self):
        """ Query for a set of objects """
        if self.namespace:
            method_name = 'list_namespaced_{0}'.format(self.kind)
            try:
                method = self.helper.lookup_method(method_name=method_name)
            except KubernetesException:
                raise Exception(
                    "Failed to find method {0} for API {1}".format(method_name, self.api_version)
                )
        else:
            method_name = 'list_{0}_for_all_namespaces'.format(self.kind)
            try:
                method = self.helper.lookup_method(method_name=method_name)
            except KubernetesException:
                method_name = 'list_{0}'.format(self.kind)
                try:
                    method = self.helper.lookup_method(method_name=method_name)
                except KubernetesException:
                    raise Exception(
                        "Failed to find method for API {0} and Kind {1}".format(self.api_version, self.kind)
                    )

        params = {}
        if self.field_selector:
            params['field_selector'] = self.field_selector
        if self.label_selector:
            params['label_selector'] = self.label_selector
        params['include_uninitialized'] = self.include_uninitialized

        if self.namespace:
            try:
                result = method(self.namespace, **params)
            except KubernetesException as exc:
                raise Exception(exc.message)
        else:
            try:
                result = method(**params)
            except KubernetesException as exc:
                raise Exception(exc.message)

        response = []
        if result is not None:
            # Convert Datetime objects to ISO format
            result_json = json.loads(json.dumps(result.to_dict(), cls=DateTimeEncoder))
            response = result_json.get('items', [])
            if self.kind == 'secret':
                for item in response:
                    remove_secret_data(item)
        return response


class OpenShiftLookup(OpenShiftAnsibleModuleMixin, KubernetesLookup):
    pass
