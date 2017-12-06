#
#  Copyright 2017 Red Hat | Ansible
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

import copy
import json
import os
import re

from ansible.module_utils.six import iteritems
from ansible.module_utils.basic import AnsibleModule

try:
    from openshift.helper.ansible import KubernetesAnsibleModuleHelper
    from openshift.helper.exceptions import KubernetesException

    HAS_K8S_MODULE_HELPER = True
except ImportError as exc:
    HAS_K8S_MODULE_HELPER = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class KubernetesAnsibleModule(AnsibleModule):

    def __init__(self):

        if not HAS_K8S_MODULE_HELPER:
            raise Exception(
                "This module requires the OpenShift Python client. Try `pip install openshift`"
            )

        if not HAS_YAML:
            raise Exception(
                "This module requires PyYAML. Try `pip install PyYAML`"
            )

        mutually_exclusive = [
            ('resource_definition', 'src'),
        ]

        AnsibleModule.__init__(self,
                               argument_spec=self._argspec,
                               supports_check_mode=True,
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

        if not self.api_version:
            self.fail_json(
                msg=("Error: no api_version specified. Use the api_version parameter, or provide it as part of a ",
                     "resource_definition.")
            )
        if not self.kind:
            self.fail_json(
                msg="Error: no kind specified. Use the kind parameter, or provide it as part of a resource_definition"
            )

        self.helper = self._get_helper(self.api_version, self.kind)

    @property
    def _argspec(self):
        return {
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

    def _get_helper(self, api_version, kind):
        try:
            helper = KubernetesAnsibleModuleHelper(api_version=api_version, kind=kind, debug=False)
            helper.get_model(api_version, kind)
            return helper
        except KubernetesException as exc:
            self.exit_json(msg="Error initializing module helper {}".format(str(exc)))

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
        for k, v in iteritems(self._argspec):
            if 'aliases' in v:
                for alias in v['aliases']:
                    if alias in self.params:
                        self.params.pop(alias)

    def _create(self, namespace):
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
