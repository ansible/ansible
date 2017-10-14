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

import copy
import json
import os

from ansible.module_utils.basic import AnsibleModule

try:
    from openshift.helper.ansible import KubernetesAnsibleModuleHelper, ARG_ATTRIBUTES_BLACKLIST
    from openshift.helper.exceptions import KubernetesException
    HAS_K8S_MODULE_HELPER = True
except ImportError as exc:
    HAS_K8S_MODULE_HELPER = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class KubernetesAnsibleException(Exception):
    pass


class KubernetesAnsibleModule(AnsibleModule):
    @staticmethod
    def get_helper(api_version, kind):
        return KubernetesAnsibleModuleHelper(api_version, kind)

    def __init__(self, kind, api_version):
        self.api_version = api_version
        self.kind = kind
        self.argspec_cache = None

        if not HAS_K8S_MODULE_HELPER:
            raise KubernetesAnsibleException(
                "This module requires the OpenShift Python client. Try `pip install openshift`"
            )

        if not HAS_YAML:
            raise KubernetesAnsibleException(
                "This module requires PyYAML. Try `pip install PyYAML`"
            )

        try:
            self.helper = self.get_helper(api_version, kind)
        except Exception as exc:
            raise KubernetesAnsibleException(
                "Error initializing AnsibleModuleHelper: {}".format(exc)
            )

        mutually_exclusive = (
            ('resource_definition', 'src'),
        )

        AnsibleModule.__init__(self,
                               argument_spec=self.argspec,
                               supports_check_mode=True,
                               mutually_exclusive=mutually_exclusive)

    @property
    def argspec(self):
        """
        Build the module argument spec from the helper.argspec, removing any extra attributes not needed by
        Ansible.

        :return: dict: a valid Ansible argument spec
        """
        if not self.argspec_cache:
            spec = {
                'dry_run': {
                    'type': 'bool',
                    'default': False,
                    'description': [
                        "If set to C(True) the module will exit without executing any action."
                        "Useful to only generate YAML file definitions for the resources in the tasks."
                    ]
                }
            }

            for arg_name, arg_properties in self.helper.argspec.items():
                spec[arg_name] = {}
                for option, option_value in arg_properties.items():
                    if option not in ARG_ATTRIBUTES_BLACKLIST:
                        if option == 'choices':
                            if isinstance(option_value, dict):
                                spec[arg_name]['choices'] = [value for key, value in option_value.items()]
                            else:
                                spec[arg_name]['choices'] = option_value
                        else:
                            spec[arg_name][option] = option_value

            self.argspec_cache = spec
        return self.argspec_cache

    def execute_module(self):
        """
        Performs basic CRUD operations on the model object. Ends by calling
        AnsibleModule.fail_json(), if an error is encountered, otherwise
        AnsibleModule.exit_json() with a dict containing:
          changed: boolean
          api_version: the API version
          <kind>: a dict representing the object's state
        :return: None
        """

        if self.params.get('debug'):
            self.helper.enable_debug(reset_logfile=False)
            self.helper.log_argspec()

        resource_definition = self.params.get('resource_definition')
        if self.params.get('src'):
            resource_definition = self.load_resource_definition(self.params['src'])
        if resource_definition:
            resource_params = self.resource_to_parameters(resource_definition)
            self.params.update(resource_params)

        state = self.params.get('state', None)
        force = self.params.get('force', False)
        dry_run = self.params.pop('dry_run', False)
        name = self.params.get('name')
        namespace = self.params.get('namespace', None)
        existing = None

        return_attributes = dict(changed=False,
                                 api_version=self.api_version,
                                 request=self.helper.request_body_from_params(self.params))
        return_attributes[self.helper.base_model_name_snake] = {}

        if dry_run:
            self.exit_json(**return_attributes)

        try:
            auth_options = {}
            for key, value in self.helper.argspec.items():
                if value.get('auth_option') and self.params.get(key) is not None:
                    auth_options[key] = self.params[key]
            self.helper.set_client_config(**auth_options)
        except KubernetesException as e:
            self.fail_json(msg='Error loading config', error=str(e))

        if state is None:
            # This is a list, rollback or ? module with no 'state' param
            if self.helper.base_model_name_snake.endswith('list'):
                # For list modules, execute a GET, and exit
                k8s_obj = self._read(name, namespace)
                return_attributes[self.kind] = k8s_obj.to_dict()
                self.exit_json(**return_attributes)
            elif self.helper.has_method('create'):
                # For a rollback, execute a POST, and exit
                k8s_obj = self._create(namespace)
                return_attributes[self.kind] = k8s_obj.to_dict()
                return_attributes['changed'] = True
                self.exit_json(**return_attributes)
            else:
                self.fail_json(msg="Missing state parameter. Expected one of: present, absent")

        # CRUD modules
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
                return_attributes[self.kind] = k8s_obj.to_dict()
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
                return_attributes[self.kind] = k8s_obj.to_dict()
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
                return_attributes[self.kind] = existing.to_dict()
                self.exit_json(**return_attributes)
            else:
                self.helper.log('Existing:')
                self.helper.log(existing.to_str())
                self.helper.log('\nDifferences:')
                self.helper.log(json.dumps(diff, indent=4))
            # Differences exist between the existing obj and requested params
            if not self.check_mode:
                try:
                    k8s_obj = self.helper.patch_object(name, namespace, k8s_obj)
                except KubernetesException as exc:
                    self.fail_json(msg="Failed to patch object: {}".format(exc.message))
            return_attributes[self.kind] = k8s_obj.to_dict()
            return_attributes['changed'] = True
            self.exit_json(**return_attributes)

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
        self.helper.log("Reading definition from {}".format(path))
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
        for key, value in resource.items():
            if key in ('apiVersion', 'kind', 'status'):
                continue
            elif key == 'metadata' and isinstance(value, dict):
                for meta_key, meta_value in value.items():
                    if meta_key in ('name', 'namespace', 'labels', 'annotations'):
                        parameters[meta_key] = meta_value
            elif key in self.helper.argspec and value is not None:
                    parameters[key] = value
            elif isinstance(value, dict):
                self._add_parameter(value, [key], parameters)
        self.helper.log("Request to parameters: {}".format(json.dumps(parameters)))
        return parameters

    def _add_parameter(self, request, path, parameters):
        for key, value in request.items():
            if path:
                param_name = '_'.join(path + [self.helper.attribute_to_snake(key)])
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
                    msg=("Error parsing resource definition. Encountered {}, which does not map to a module "
                         "parameter. If this looks like a problem with the module, please open an issue at "
                         "github.com/openshift/openshift-restclient-python/issues").format(param_name)
                )
