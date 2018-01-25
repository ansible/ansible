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

import os
import re
import copy
import json

from datetime import datetime

from ansible.module_utils.six import iteritems
from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.k8s.helper import\
    AnsibleMixin,\
    HAS_STRING_UTILS

try:
    from openshift.helper.kubernetes import KubernetesObjectHelper
    from openshift.helper.openshift import OpenShiftObjectHelper
    from openshift.helper.exceptions import KubernetesException
    HAS_K8S_MODULE_HELPER = True
except ImportError as exc:
    class KubernetesObjectHelper(object):
        pass

    class OpenShiftObjectHelper(object):
        pass

    HAS_K8S_MODULE_HELPER = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def remove_secret_data(obj_dict):
    """ Remove any sensitive data from a K8s dict"""
    if obj_dict.get('data'):
        # Secret data
        obj_dict.pop('data')
    if obj_dict.get('string_data'):
        # The API should not return sting_data in Secrets, but just in case
        obj_dict.pop('string_data')
    if obj_dict['metadata'].get('annotations'):
        # Remove things like 'openshift.io/token-secret' from metadata
        for key in [k for k in obj_dict['metadata']['annotations'] if 'secret' in k]:
            obj_dict['metadata']['annotations'].pop(key)


def to_snake(name):
    """ Convert a string from camel to snake """
    if not name:
        return name

    def _replace(m):
        m = m.group(0)
        return m[0] + '_' + m[1:]

    p = r'[a-z][A-Z]|' \
        r'[A-Z]{2}[a-z]'
    return re.sub(p, _replace, name).lower()


class DateTimeEncoder(json.JSONEncoder):
    # When using json.dumps() with K8s object, pass cls=DateTimeEncoder to handle any datetime objects
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


class KubernetesAnsibleModuleHelper(AnsibleMixin, KubernetesObjectHelper):
    pass


class KubernetesAnsibleModule(AnsibleModule):
    resource_definition = None
    api_version = None
    kind = None
    helper = None

    def __init__(self, *args, **kwargs):

        if not HAS_K8S_MODULE_HELPER:
            raise Exception(
                "This module requires the OpenShift Python client. Try `pip install openshift`"
            )

        if not HAS_YAML:
            raise Exception(
                "This module requires PyYAML. Try `pip install PyYAML`"
            )

        if not HAS_STRING_UTILS:
            raise Exception(
                "This module requires Python string utils. Try `pip install python-string-utils`"
            )

        kwargs['argument_spec'] = self.argspec
        AnsibleModule.__init__(self, *args, **kwargs)

    @property
    def argspec(self):
        raise NotImplementedError()

    def get_helper(self, api_version, kind):
        try:
            helper = KubernetesAnsibleModuleHelper(api_version=api_version, kind=kind, debug=False)
            helper.get_model(api_version, kind)
            return helper
        except KubernetesException as exc:
            self.fail_json(msg="Error initializing module helper: {0}".format(exc.message))

    def execute_module(self):
        raise NotImplementedError()

    def exit_json(self, **return_attributes):
        """ Filter any sensitive data that we don't want logged """
        if return_attributes.get('result') and \
           return_attributes['result'].get('kind') in ('Secret', 'SecretList'):
            if return_attributes['result'].get('data'):
                remove_secret_data(return_attributes['result'])
            elif return_attributes['result'].get('items'):
                for item in return_attributes['result']['items']:
                    remove_secret_data(item)
        super(KubernetesAnsibleModule, self).exit_json(**return_attributes)

    def authenticate(self):
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

    def remove_aliases(self):
        """
        The helper doesn't know what to do with aliased keys
        """
        for k, v in iteritems(self.argspec):
            if 'aliases' in v:
                for alias in v['aliases']:
                    if alias in self.params:
                        self.params.pop(alias)

    def load_resource_definition(self, src):
        """ Load the requested src path """
        result = None
        path = os.path.normpath(src)
        if not os.path.exists(path):
            self.fail_json(msg="Error accessing {0}. Does the file exist?".format(path))
        try:
            result = yaml.safe_load(open(path, 'r'))
        except (IOError, yaml.YAMLError) as exc:
            self.fail_json(msg="Error loading resource_definition: {0}".format(exc))
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
        return parameters

    def _add_parameter(self, request, path, parameters):
        for key, value in iteritems(request):
            if path:
                param_name = '_'.join(path + [to_snake(key)])
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
                    msg=("Error parsing resource definition. Encountered {0}, which does not map to a parameter "
                         "expected by the OpenShift Python module.".format(param_name))
                )


class OpenShiftAnsibleModuleHelper(AnsibleMixin, OpenShiftObjectHelper):
    pass


class OpenShiftAnsibleModuleMixin(object):

    def get_helper(self, api_version, kind):
        try:
            helper = OpenShiftAnsibleModuleHelper(api_version=api_version, kind=kind, debug=False)
            helper.get_model(api_version, kind)
            return helper
        except KubernetesException as exc:
            self.fail_json(msg="Error initializing module helper: {0}".format(exc.message))
