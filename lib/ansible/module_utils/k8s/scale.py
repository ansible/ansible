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
import math
import time

from ansible.module_utils.six import iteritems
from ansible.module_utils.k8s.common import KubernetesAnsibleModule, OpenShiftAnsibleModuleHelper
from ansible.module_utils.k8s.helper import AUTH_ARG_SPEC, COMMON_ARG_SPEC

try:
    from openshift.helper.exceptions import KubernetesException
except ImportError as exc:
    class KubernetesException(Exception):
        pass


SCALE_ARG_SPEC = {
    'replicas': {'type': 'int', 'required': True},
    'current_replicas': {'type': 'int'},
    'resource_version': {},
    'wait': {'type': 'bool', 'default': True},
    'wait_time': {'type': 'int', 'default': 30}
}


class KubernetesAnsibleScaleModule(KubernetesAnsibleModule):

    def execute_scale(self):
        if self.resource_definition:
            resource_params = self.resource_to_parameters(self.resource_definition)
            self.params.update(resource_params)

        self._authenticate()

        name = self.params.get('name')
        namespace = self.params.get('namespace')
        current_replicas = self.params.get('current_replicas')
        replicas = self.params.get('replicas')
        resource_version = self.params.get('resource_version')
        wait = self.params.get('wait')
        wait_time = self.params.get('wait_time')
        replica_attribute = None
        existing = None
        return_attributes = dict(changed=False, result=dict())

        try:
            existing = self.helper.get_object(name, namespace)
        except KubernetesException as exc:
            self.fail_json(msg='Failed to retrieve requested object: {0}'.format(exc.message),
                           error=exc.value.get('status'))

        existing_count = None
        if hasattr(existing.status, 'available_replicas'):
            replica_attribute = 'available_replicas'
            existing_count = existing.status.available_replicas
        elif hasattr(existing.status, 'active'):
            replica_attribute = 'active'
            existing_count = existing.status.active
        elif hasattr(existing.status, 'availableReplicas'):
            replica_attribute = 'availableReplicas'
            existing_count = existing.status.availableReplicas

        if existing_count is None:
            self.fail_json(msg='Failed to retrieve the available count for the requested object.')

        existing_version = None
        if hasattr(existing.status, 'latest_version'):
            existing_version = existing.status.latest_version
        if existing_version is None and resource_version is not None:
            self.fail_json(
                msg="Existing {0}, {1}, does not have a 'latest_version' attribute. Cannot honor 'latest_version' "
                    "option.".format(self.kind, name)
            )
        if resource_version and resource_version != existing_version:
            self.exit_json(**return_attributes)

        if existing_count != replicas:
            if (current_replicas is None) or (current_replicas is not None and existing_count == current_replicas):
                k8s_obj = self._scale(existing, replicas, wait, wait_time, replica_attribute)
                return_attributes['result'] = k8s_obj.to_dict()
                return_attributes['changed'] = True

        self.exit_json(**return_attributes)

    def resource_to_parameters(self, resource):
        """ Converts a resource definition to module parameters """
        parameters = {}
        for key, value in iteritems(resource):
            if key in ('apiVersion', 'kind', 'status'):
                continue
            elif key == 'metadata' and isinstance(value, dict):
                for meta_key, meta_value in iteritems(value):
                    if meta_key in ('name', 'namespace'):
                        parameters[meta_key] = meta_value
        return parameters

    @property
    def _argspec(self):
        args = copy.deepcopy(COMMON_ARG_SPEC)
        args.pop('state')
        args.pop('force')
        args.update(AUTH_ARG_SPEC)
        args.update(SCALE_ARG_SPEC)
        return args

    def _scale(self, existing_object, replicas, wait, wait_time, replica_attribute):
        name = existing_object.metadata.name
        namespace = existing_object.metadata.namespace
        method_name = 'patch_namespaced_{0}_scale'.format(self.kind)
        method = None
        model = None

        try:
            method = self.helper.lookup_method(method_name=method_name)
        except KubernetesException:
            self.fail_json(
                msg="Failed to get method {0}. Is 'scale' a valid operation for {1}?".format(method_name,
                                                                                             self.kind)
            )

        try:
            model = self.helper.get_model(self.api_version, 'scale')
        except KubernetesException:
            self.fail_json(
                msg="Failed to fetch the 'Scale' model for API version {0}. Are you using the correct "
                    "API?".format(self.api_version)
            )

        scale_obj = model()
        scale_obj.kind = 'scale'
        scale_obj.api_version = self.api_version.lower()
        scale_obj.metadata = self.helper.get_model(
            self.api_version,
            self.helper.get_base_model_name(scale_obj.swagger_types['metadata'])
        )()
        scale_obj.metadata.name = name
        scale_obj.metadata.namespace = namespace
        scale_obj.spec = self.helper.get_model(
            self.api_version,
            self.helper.get_base_model_name(scale_obj.swagger_types['spec'])
        )()
        scale_obj.spec.replicas = replicas

        try:
            method(name, namespace, scale_obj)
        except Exception as exc:
            self.fail_json(
                msg="Scale request failed: {0}".format(exc)
            )

        return_obj = self.helper._wait_for_response(name, namespace, 'patch')
        if wait:
            limit_cnt = math.ceil(wait_time / 2)
            cnt = 0
            while getattr(return_obj.status, replica_attribute) != replicas and cnt < limit_cnt:
                time.sleep(2)
                cnt += 1
                return_obj = self.helper._wait_for_response(name, namespace, 'patch')

            if getattr(return_obj.status, replica_attribute) != replicas:
                self.fail_json(msg="The scaling operation failed to complete within the allotted wait time.")

        return self.helper.fix_serialization(return_obj)


class OpenShiftAnsibleScaleModule(KubernetesAnsibleScaleModule):

    def _get_helper(self, api_version, kind):
        helper = None
        try:
            helper = OpenShiftAnsibleModuleHelper(api_version=api_version, kind=kind, debug=False)
            helper.get_model(api_version, kind)
        except KubernetesException as exc:
            self.exit_json(msg="Error initializing module helper {}".format(exc.message))
        return helper
