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

import copy

from ansible.module_utils.k8s.helper import COMMON_ARG_SPEC, AUTH_ARG_SPEC, OPENSHIFT_ARG_SPEC
from ansible.module_utils.k8s.common import KubernetesAnsibleModule, OpenShiftAnsibleModuleMixin, to_snake

try:
    from openshift.helper.exceptions import KubernetesException
except ImportError:
    # Exception handled in common
    pass


class KubernetesRawModule(KubernetesAnsibleModule):

    def __init__(self, *args, **kwargs):
        mutually_exclusive = [
            ('resource_definition', 'src'),
        ]

        KubernetesAnsibleModule.__init__(self, *args,
                                         mutually_exclusive=mutually_exclusive,
                                         supports_check_mode=True,
                                         **kwargs)

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
        self.kind = to_snake(self.kind)

        if not self.api_version:
            self.fail_json(
                msg=("Error: no api_version specified. Use the api_version parameter, or provide it as part of a ",
                     "resource_definition.")
            )
        if not self.kind:
            self.fail_json(
                msg="Error: no kind specified. Use the kind parameter, or provide it as part of a resource_definition"
            )

        self.helper = self.get_helper(self.api_version, self.kind)

    @property
    def argspec(self):
        argspec = copy.deepcopy(COMMON_ARG_SPEC)
        argspec.update(copy.deepcopy(AUTH_ARG_SPEC))
        return argspec

    def execute_module(self):
        if self.resource_definition:
            resource_params = self.resource_to_parameters(self.resource_definition)
            self.params.update(resource_params)

        self.authenticate()

        state = self.params.pop('state', None)
        force = self.params.pop('force', False)
        name = self.params.get('name')
        namespace = self.params.get('namespace')
        existing = None

        self.remove_aliases()

        return_attributes = dict(changed=False, result=dict())

        if self.helper.base_model_name_snake.endswith('list'):
            k8s_obj = self._read(name, namespace)
            return_attributes['result'] = k8s_obj.to_dict()
            self.exit_json(**return_attributes)

        try:
            existing = self.helper.get_object(name, namespace)
        except KubernetesException as exc:
            self.fail_json(msg='Failed to retrieve requested object: {0}'.format(exc.message),
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
                        self.fail_json(msg="Failed to delete object: {0}".format(exc.message),
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
                        self.fail_json(msg="Failed to replace object: {0}".format(exc.message),
                                       error=exc.value.get('status'))
                return_attributes['result'] = k8s_obj.to_dict()
                return_attributes['changed'] = True
                self.exit_json(**return_attributes)

            # Check if existing object should be patched
            k8s_obj = copy.deepcopy(existing)
            try:
                self.helper.object_from_params(self.params, obj=k8s_obj)
            except KubernetesException as exc:
                self.fail_json(msg="Failed to patch object: {0}".format(exc.message))
            match, diff = self.helper.objects_match(self.helper.fix_serialization(existing), k8s_obj)
            if match:
                return_attributes['result'] = existing.to_dict()
                self.exit_json(**return_attributes)
            # Differences exist between the existing obj and requested params
            if not self.check_mode:
                try:
                    k8s_obj = self.helper.patch_object(name, namespace, k8s_obj)
                except KubernetesException as exc:
                    self.fail_json(msg="Failed to patch object: {0}".format(exc.message))
            return_attributes['result'] = k8s_obj.to_dict()
            return_attributes['changed'] = True
            self.exit_json(**return_attributes)

    def _create(self, namespace):
        request_body = None
        k8s_obj = None
        try:
            request_body = self.helper.request_body_from_params(self.params)
        except KubernetesException as exc:
            self.fail_json(msg="Failed to create object: {0}".format(exc.message))
        if not self.check_mode:
            try:
                k8s_obj = self.helper.create_object(namespace, body=request_body)
            except KubernetesException as exc:
                self.fail_json(msg="Failed to create object: {0}".format(exc.message),
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


class OpenShiftRawModule(OpenShiftAnsibleModuleMixin, KubernetesRawModule):

    @property
    def argspec(self):
        args = super(OpenShiftRawModule, self).argspec
        args.update(copy.deepcopy(OPENSHIFT_ARG_SPEC))
        return args

    def _create(self, namespace):
        if self.kind.lower() == 'project':
            return self._create_project()
        return KubernetesRawModule._create(self, namespace)

    def _create_project(self):
        new_obj = None
        k8s_obj = None
        try:
            new_obj = self.helper.object_from_params(self.params)
        except KubernetesException as exc:
            self.fail_json(msg="Failed to create object: {0}".format(exc.message))
        try:
            k8s_obj = self.helper.create_project(metadata=new_obj.metadata,
                                                 display_name=self.params.get('display_name'),
                                                 description=self.params.get('description'))
        except KubernetesException as exc:
            self.fail_json(msg='Failed to retrieve requested object',
                           error=exc.value.get('status'))
        return k8s_obj
