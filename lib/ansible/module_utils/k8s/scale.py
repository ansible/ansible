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
from ansible.module_utils.k8s.common import OpenShiftAnsibleModuleMixin
from ansible.module_utils.k8s.raw import KubernetesRawModule
from ansible.module_utils.k8s.helper import AUTH_ARG_SPEC, COMMON_ARG_SPEC

try:
    from openshift import watch
    from openshift.helper.exceptions import KubernetesException
except ImportError as exc:
    class KubernetesException(Exception):
        pass


SCALE_ARG_SPEC = {
    'replicas': {'type': 'int', 'required': True},
    'current_replicas': {'type': 'int'},
    'resource_version': {},
    'wait': {'type': 'bool', 'default': True},
    'wait_timeout': {'type': 'int', 'default': 20}
}


class KubernetesAnsibleScaleModule(KubernetesRawModule):

    def execute_module(self):
        if self.resource_definition:
            resource_params = self.resource_to_parameters(self.resource_definition)
            self.params.update(resource_params)

        self.authenticate()

        name = self.params.get('name')
        namespace = self.params.get('namespace')
        current_replicas = self.params.get('current_replicas')
        replicas = self.params.get('replicas')
        resource_version = self.params.get('resource_version')

        wait = self.params.get('wait')
        wait_time = self.params.get('wait_timeout')
        existing = None
        existing_count = None
        return_attributes = dict(changed=False, result=dict())

        try:
            existing = self.helper.get_object(name, namespace)
            return_attributes['result'] = existing.to_dict()
        except KubernetesException as exc:
            self.fail_json(msg='Failed to retrieve requested object: {0}'.format(exc.message),
                           error=exc.value.get('status'))

        if self.kind == 'job':
            existing_count = existing.spec.parallelism
        elif hasattr(existing.spec, 'replicas'):
            existing_count = existing.spec.replicas

        if existing_count is None:
            self.fail_json(msg='Failed to retrieve the available count for the requested object.')

        if resource_version and resource_version != existing.metadata.resource_version:
            self.exit_json(**return_attributes)

        if current_replicas is not None and existing_count != current_replicas:
            self.exit_json(**return_attributes)

        if existing_count != replicas:
            return_attributes['changed'] = True
            if not self.check_mode:
                if self.kind == 'job':
                    existing.spec.parallelism = replicas
                    k8s_obj = self.helper.patch_object(name, namespace, existing)
                else:
                    k8s_obj = self.scale(existing, replicas, wait, wait_time)
                return_attributes['result'] = k8s_obj.to_dict()

        self.exit_json(**return_attributes)

    def resource_to_parameters(self, resource):
        """ Converts a resource definition to module parameters """
        parameters = {}
        for key, value in iteritems(resource):
            if key in ('apiVersion', 'kind', 'status'):
                continue
            elif key == 'metadata' and isinstance(value, dict):
                for meta_key, meta_value in iteritems(value):
                    if meta_key in ('name', 'namespace', 'resourceVersion'):
                        parameters[meta_key] = meta_value
        return parameters

    @property
    def argspec(self):
        args = copy.deepcopy(COMMON_ARG_SPEC)
        args.pop('state')
        args.pop('force')
        args.update(AUTH_ARG_SPEC)
        args.update(SCALE_ARG_SPEC)
        return args

    def scale(self, existing_object, replicas, wait, wait_time):
        name = existing_object.metadata.name
        namespace = existing_object.metadata.namespace
        method_name = 'patch_namespaced_{0}_scale'.format(self.kind)
        method = None
        model = None

        try:
            method = self.helper.lookup_method(method_name=method_name)
        except KubernetesException:
            self.fail_json(
                msg="Failed to get method {0}. Is 'scale' a valid operation for {1}?".format(method_name, self.kind)
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

        return_obj = None
        stream = None

        if wait:
            w, stream = self._create_stream(namespace, wait_time)

        try:
            method(name, namespace, scale_obj)
        except Exception as exc:
            self.fail_json(
                msg="Scale request failed: {0}".format(exc.message)
            )

        if wait and stream is not None:
            return_obj = self._read_stream(w, stream, name, replicas)

        if not return_obj:
            return_obj = self._wait_for_response(name, namespace)

        return return_obj

    def _create_stream(self, namespace, wait_time):
        """ Create a stream of events for the object """
        w = None
        stream = None
        try:
            list_method = self.helper.lookup_method('list', namespace)
            w = watch.Watch()
            w._api_client = self.helper.api_client
            if namespace:
                stream = w.stream(list_method, namespace, timeout_seconds=wait_time)
            else:
                stream = w.stream(list_method, timeout_seconds=wait_time)
        except KubernetesException:
            pass
        except Exception:
            raise
        return w, stream

    def _read_stream(self, watcher, stream, name, replicas):
        """ Wait for ready_replicas to equal the requested number of replicas. """
        return_obj = None
        try:
            for event in stream:
                if event.get('object'):
                    obj = event['object']
                    if obj.metadata.name == name and hasattr(obj, 'status'):
                        if hasattr(obj.status, 'ready_replicas') and obj.status.ready_replicas == replicas:
                            return_obj = obj
                            watcher.stop()
                            break
        except Exception as exc:
            self.fail_json(msg="Exception reading event stream: {0}".format(exc.message))

        if not return_obj:
            self.fail_json(msg="Error fetching the patched object. Try a higher wait_timeout value.")
        if return_obj.status.ready_replicas is None:
            self.fail_json(msg="Failed to fetch the number of ready replicas. Try a higher wait_timeout value.")
        if return_obj.status.ready_replicas != replicas:
            self.fail_json(msg="Number of ready replicas is {0}. Failed to reach {1} ready replicas within "
                               "the wait_timeout period.".format(return_obj.status.ready_replicas, replicas))
        return return_obj

    def _wait_for_response(self, name, namespace):
        """ Wait for an API response """
        tries = 0
        half = math.ceil(20 / 2)
        obj = None

        while tries <= half:
            obj = self.helper.get_object(name, namespace)
            if obj:
                break
            tries += 2
            time.sleep(2)
        return obj


class OpenShiftAnsibleScaleModule(OpenShiftAnsibleModuleMixin, KubernetesAnsibleScaleModule):
    pass
