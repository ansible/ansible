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
from datetime import datetime
from distutils.version import LooseVersion
import time
import sys
import traceback

from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.k8s.common import AUTH_ARG_SPEC, COMMON_ARG_SPEC
from ansible.module_utils.six import string_types
from ansible.module_utils.k8s.common import KubernetesAnsibleModule
from ansible.module_utils.common.dict_transformations import dict_merge


try:
    import yaml
    from openshift.dynamic.exceptions import DynamicApiError, NotFoundError, ConflictError, ForbiddenError, KubernetesValidateMissing
    import urllib3
except ImportError:
    # Exceptions handled in common
    pass

try:
    import kubernetes_validate
    HAS_KUBERNETES_VALIDATE = True
except ImportError:
    HAS_KUBERNETES_VALIDATE = False

K8S_CONFIG_HASH_IMP_ERR = None
try:
    from openshift.helper.hashes import generate_hash
    HAS_K8S_CONFIG_HASH = True
except ImportError:
    K8S_CONFIG_HASH_IMP_ERR = traceback.format_exc()
    HAS_K8S_CONFIG_HASH = False

HAS_K8S_APPLY = None
try:
    from openshift.dynamic.apply import apply_object
    HAS_K8S_APPLY = True
except ImportError:
    HAS_K8S_APPLY = False


class KubernetesRawModule(KubernetesAnsibleModule):

    @property
    def validate_spec(self):
        return dict(
            fail_on_error=dict(type='bool'),
            version=dict(),
            strict=dict(type='bool', default=True)
        )

    @property
    def condition_spec(self):
        return dict(
            type=dict(),
            status=dict(default=True, choices=[True, False, "Unknown"]),
            reason=dict()
        )

    @property
    def argspec(self):
        argument_spec = copy.deepcopy(COMMON_ARG_SPEC)
        argument_spec.update(copy.deepcopy(AUTH_ARG_SPEC))
        argument_spec['merge_type'] = dict(type='list', choices=['json', 'merge', 'strategic-merge'])
        argument_spec['wait'] = dict(type='bool', default=False)
        argument_spec['wait_sleep'] = dict(type='int', default=5)
        argument_spec['wait_timeout'] = dict(type='int', default=120)
        argument_spec['wait_condition'] = dict(type='dict', default=None, options=self.condition_spec)
        argument_spec['validate'] = dict(type='dict', default=None, options=self.validate_spec)
        argument_spec['append_hash'] = dict(type='bool', default=False)
        argument_spec['apply'] = dict(type='bool', default=False)
        return argument_spec

    def __init__(self, k8s_kind=None, *args, **kwargs):
        self.client = None
        self.warnings = []

        mutually_exclusive = [
            ('resource_definition', 'src'),
            ('merge_type', 'apply'),
        ]

        KubernetesAnsibleModule.__init__(self, *args,
                                         mutually_exclusive=mutually_exclusive,
                                         supports_check_mode=True,
                                         **kwargs)
        self.kind = k8s_kind or self.params.get('kind')
        self.api_version = self.params.get('api_version')
        self.name = self.params.get('name')
        self.namespace = self.params.get('namespace')
        resource_definition = self.params.get('resource_definition')
        validate = self.params.get('validate')
        if validate:
            if LooseVersion(self.openshift_version) < LooseVersion("0.8.0"):
                self.fail_json(msg="openshift >= 0.8.0 is required for validate")
        self.append_hash = self.params.get('append_hash')
        if self.append_hash:
            if not HAS_K8S_CONFIG_HASH:
                self.fail_json(msg=missing_required_lib("openshift >= 0.7.2", reason="for append_hash"),
                               exception=K8S_CONFIG_HASH_IMP_ERR)
        if self.params['merge_type']:
            if LooseVersion(self.openshift_version) < LooseVersion("0.6.2"):
                self.fail_json(msg=missing_required_lib("openshift >= 0.6.2", reason="for merge_type"))
        self.apply = self.params.get('apply', False)
        if self.apply:
            if not HAS_K8S_APPLY:
                self.fail_json(msg=missing_required_lib("openshift >= 0.9.2", reason="for apply"))

        if resource_definition:
            if isinstance(resource_definition, string_types):
                try:
                    self.resource_definitions = yaml.safe_load_all(resource_definition)
                except (IOError, yaml.YAMLError) as exc:
                    self.fail(msg="Error loading resource_definition: {0}".format(exc))
            elif isinstance(resource_definition, list):
                self.resource_definitions = resource_definition
            else:
                self.resource_definitions = [resource_definition]
        src = self.params.get('src')
        if src:
            self.resource_definitions = self.load_resource_definitions(src)
        try:
            self.resource_definitions = [item for item in self.resource_definitions if item]
        except AttributeError:
            pass

        if not resource_definition and not src:
            implicit_definition = dict(
                kind=self.kind,
                apiVersion=self.api_version,
                metadata=dict(name=self.name)
            )
            if self.namespace:
                implicit_definition['metadata']['namespace'] = self.namespace
            self.resource_definitions = [implicit_definition]

    def flatten_list_kind(self, list_resource, definitions):
        flattened = []
        parent_api_version = list_resource.group_version if list_resource else None
        parent_kind = list_resource.kind[:-4] if list_resource else None
        for definition in definitions.get('items', []):
            resource = self.find_resource(definition.get('kind', parent_kind), definition.get('apiVersion', parent_api_version), fail=True)
            flattened.append((resource, self.set_defaults(resource, definition)))
        return flattened

    def execute_module(self):
        changed = False
        results = []
        try:
            self.client = self.get_api_client()
        # Hopefully the kubernetes client will provide its own exception class one day
        except (urllib3.exceptions.RequestError) as e:
            self.fail_json(msg="Couldn't connect to Kubernetes: %s" % str(e))

        flattened_definitions = []
        for definition in self.resource_definitions:
            kind = definition.get('kind', self.kind)
            api_version = definition.get('apiVersion', self.api_version)
            if kind.endswith('List'):
                resource = self.find_resource(kind, api_version, fail=False)
                flattened_definitions.extend(self.flatten_list_kind(resource, definition))
            else:
                resource = self.find_resource(kind, api_version, fail=True)
                flattened_definitions.append((resource, definition))

        for (resource, definition) in flattened_definitions:
            kind = definition.get('kind', self.kind)
            api_version = definition.get('apiVersion', self.api_version)
            definition = self.set_defaults(resource, definition)
            self.warnings = []
            if self.params['validate'] is not None:
                self.warnings = self.validate(definition)
            result = self.perform_action(resource, definition)
            result['warnings'] = self.warnings
            changed = changed or result['changed']
            results.append(result)

        if len(results) == 1:
            self.exit_json(**results[0])

        self.exit_json(**{
            'changed': changed,
            'result': {
                'results': results
            }
        })

    def validate(self, resource):
        def _prepend_resource_info(resource, msg):
            return "%s %s: %s" % (resource['kind'], resource['metadata']['name'], msg)

        try:
            warnings, errors = self.client.validate(resource, self.params['validate'].get('version'), self.params['validate'].get('strict'))
        except KubernetesValidateMissing:
            self.fail_json(msg="kubernetes-validate python library is required to validate resources")

        if errors and self.params['validate']['fail_on_error']:
            self.fail_json(msg="\n".join([_prepend_resource_info(resource, error) for error in errors]))
        else:
            return [_prepend_resource_info(resource, msg) for msg in warnings + errors]

    def set_defaults(self, resource, definition):
        definition['kind'] = resource.kind
        definition['apiVersion'] = resource.group_version
        metadata = definition.get('metadata', {})
        if self.name and not metadata.get('name'):
            metadata['name'] = self.name
        if resource.namespaced and self.namespace and not metadata.get('namespace'):
            metadata['namespace'] = self.namespace
        definition['metadata'] = metadata
        return definition

    def perform_action(self, resource, definition):
        result = {'changed': False, 'result': {}}
        state = self.params.get('state', None)
        force = self.params.get('force', False)
        name = definition['metadata'].get('name')
        namespace = definition['metadata'].get('namespace')
        existing = None
        wait = self.params.get('wait')
        wait_sleep = self.params.get('wait_sleep')
        wait_timeout = self.params.get('wait_timeout')
        wait_condition = None
        if self.params.get('wait_condition') and self.params['wait_condition'].get('type'):
            wait_condition = self.params['wait_condition']

        self.remove_aliases()

        try:
            # ignore append_hash for resources other than ConfigMap and Secret
            if self.append_hash and definition['kind'] in ['ConfigMap', 'Secret']:
                name = '%s-%s' % (name, generate_hash(definition))
                definition['metadata']['name'] = name
            params = dict(name=name)
            if namespace:
                params['namespace'] = namespace
            existing = resource.get(**params)
        except NotFoundError:
            # Remove traceback so that it doesn't show up in later failures
            try:
                sys.exc_clear()
            except AttributeError:
                # no sys.exc_clear on python3
                pass
        except ForbiddenError as exc:
            if definition['kind'] in ['Project', 'ProjectRequest'] and state != 'absent':
                return self.create_project_request(definition)
            self.fail_json(msg='Failed to retrieve requested object: {0}'.format(exc.body),
                           error=exc.status, status=exc.status, reason=exc.reason)
        except DynamicApiError as exc:
            self.fail_json(msg='Failed to retrieve requested object: {0}'.format(exc.body),
                           error=exc.status, status=exc.status, reason=exc.reason)

        if state == 'absent':
            result['method'] = "delete"
            if not existing:
                # The object already does not exist
                return result
            else:
                # Delete the object
                result['changed'] = True
                if not self.check_mode:
                    try:
                        k8s_obj = resource.delete(**params)
                        result['result'] = k8s_obj.to_dict()
                    except DynamicApiError as exc:
                        self.fail_json(msg="Failed to delete object: {0}".format(exc.body),
                                       error=exc.status, status=exc.status, reason=exc.reason)
                    if wait:
                        success, resource, duration = self.wait(resource, definition, wait_sleep, wait_timeout, 'absent')
                        result['duration'] = duration
                        if not success:
                            self.fail_json(msg="Resource deletion timed out", **result)
                return result
        else:
            if self.apply:
                if self.check_mode:
                    ignored, k8s_obj = apply_object(resource, definition)
                else:
                    try:
                        k8s_obj = resource.apply(definition, namespace=namespace).to_dict()
                    except DynamicApiError as exc:
                        msg = "Failed to apply object: {0}".format(exc.body)
                        if self.warnings:
                            msg += "\n" + "\n    ".join(self.warnings)
                        self.fail_json(msg=msg, error=exc.status, status=exc.status, reason=exc.reason)
                success = True
                result['result'] = k8s_obj
                if wait:
                    success, result['result'], result['duration'] = self.wait(resource, definition, wait_sleep, wait_timeout, condition=wait_condition)
                if existing:
                    existing = existing.to_dict()
                else:
                    existing = {}
                match, diffs = self.diff_objects(existing, result['result'])
                result['changed'] = not match
                result['diff'] = diffs
                result['method'] = 'apply'
                if not success:
                    self.fail_json(msg="Resource apply timed out", **result)
                return result

            if not existing:
                if self.check_mode:
                    k8s_obj = definition
                else:
                    try:
                        k8s_obj = resource.create(definition, namespace=namespace).to_dict()
                    except ConflictError:
                        # Some resources, like ProjectRequests, can't be created multiple times,
                        # because the resources that they create don't match their kind
                        # In this case we'll mark it as unchanged and warn the user
                        self.warn("{0} was not found, but creating it returned a 409 Conflict error. This can happen \
                                  if the resource you are creating does not directly create a resource of the same kind.".format(name))
                        return result
                    except DynamicApiError as exc:
                        msg = "Failed to create object: {0}".format(exc.body)
                        if self.warnings:
                            msg += "\n" + "\n    ".join(self.warnings)
                        self.fail_json(msg=msg, error=exc.status, status=exc.status, reason=exc.reason)
                success = True
                result['result'] = k8s_obj
                if wait and not self.check_mode:
                    success, result['result'], result['duration'] = self.wait(resource, definition, wait_sleep, wait_timeout, condition=wait_condition)
                result['changed'] = True
                result['method'] = 'create'
                if not success:
                    self.fail_json(msg="Resource creation timed out", **result)
                return result

            match = False
            diffs = []

            if existing and force:
                if self.check_mode:
                    k8s_obj = definition
                else:
                    try:
                        k8s_obj = resource.replace(definition, name=name, namespace=namespace, append_hash=self.append_hash).to_dict()
                    except DynamicApiError as exc:
                        msg = "Failed to replace object: {0}".format(exc.body)
                        if self.warnings:
                            msg += "\n" + "\n    ".join(self.warnings)
                        self.fail_json(msg=msg, error=exc.status, status=exc.status, reason=exc.reason)
                match, diffs = self.diff_objects(existing.to_dict(), k8s_obj)
                success = True
                result['result'] = k8s_obj
                if wait:
                    success, result['result'], result['duration'] = self.wait(resource, definition, wait_sleep, wait_timeout, condition=wait_condition)
                match, diffs = self.diff_objects(existing.to_dict(), result['result'])
                result['changed'] = not match
                result['method'] = 'replace'
                result['diff'] = diffs
                if not success:
                    self.fail_json(msg="Resource replacement timed out", **result)
                return result

            # Differences exist between the existing obj and requested params
            if self.check_mode:
                k8s_obj = dict_merge(existing.to_dict(), definition)
            else:
                if LooseVersion(self.openshift_version) < LooseVersion("0.6.2"):
                    k8s_obj, error = self.patch_resource(resource, definition, existing, name,
                                                         namespace)
                else:
                    for merge_type in self.params['merge_type'] or ['strategic-merge', 'merge']:
                        k8s_obj, error = self.patch_resource(resource, definition, existing, name,
                                                             namespace, merge_type=merge_type)
                        if not error:
                            break
                if error:
                    self.fail_json(**error)

            success = True
            result['result'] = k8s_obj
            if wait:
                success, result['result'], result['duration'] = self.wait(resource, definition, wait_sleep, wait_timeout, condition=wait_condition)
            match, diffs = self.diff_objects(existing.to_dict(), result['result'])
            result['changed'] = not match
            result['method'] = 'patch'
            result['diff'] = diffs

            if not success:
                self.fail_json(msg="Resource update timed out", **result)
            return result

    def patch_resource(self, resource, definition, existing, name, namespace, merge_type=None):
        try:
            params = dict(name=name, namespace=namespace)
            if merge_type:
                params['content_type'] = 'application/{0}-patch+json'.format(merge_type)
            k8s_obj = resource.patch(definition, **params).to_dict()
            match, diffs = self.diff_objects(existing.to_dict(), k8s_obj)
            error = {}
            return k8s_obj, {}
        except DynamicApiError as exc:
            msg = "Failed to patch object: {0}".format(exc.body)
            if self.warnings:
                msg += "\n" + "\n    ".join(self.warnings)
            error = dict(msg=msg, error=exc.status, status=exc.status, reason=exc.reason, warnings=self.warnings)
            return None, error

    def create_project_request(self, definition):
        definition['kind'] = 'ProjectRequest'
        result = {'changed': False, 'result': {}}
        resource = self.find_resource('ProjectRequest', definition['apiVersion'], fail=True)
        if not self.check_mode:
            try:
                k8s_obj = resource.create(definition)
                result['result'] = k8s_obj.to_dict()
            except DynamicApiError as exc:
                self.fail_json(msg="Failed to create object: {0}".format(exc.body),
                               error=exc.status, status=exc.status, reason=exc.reason)
        result['changed'] = True
        result['method'] = 'create'
        return result

    def _wait_for(self, resource, name, namespace, predicate, sleep, timeout, state):
        start = datetime.now()

        def _wait_for_elapsed():
            return (datetime.now() - start).seconds

        response = None
        while _wait_for_elapsed() < timeout:
            try:
                response = resource.get(name=name, namespace=namespace)
                if predicate(response):
                    if response:
                        return True, response.to_dict(), _wait_for_elapsed()
                    else:
                        return True, {}, _wait_for_elapsed()
                time.sleep(sleep)
            except NotFoundError:
                if state == 'absent':
                    return True, {}, _wait_for_elapsed()
        if response:
            response = response.to_dict()
        return False, response, _wait_for_elapsed()

    def wait(self, resource, definition, sleep, timeout, state='present', condition=None):

        def _deployment_ready(deployment):
            # FIXME: frustratingly bool(deployment.status) is True even if status is empty
            # Furthermore deployment.status.availableReplicas == deployment.status.replicas == None if status is empty
            return (deployment.status and deployment.status.replicas is not None and
                    deployment.status.availableReplicas == deployment.status.replicas and
                    deployment.status.observedGeneration == deployment.metadata.generation)

        def _pod_ready(pod):
            return (pod.status and pod.status.containerStatuses is not None and
                    all([container.ready for container in pod.status.containerStatuses]))

        def _daemonset_ready(daemonset):
            return (daemonset.status and daemonset.status.desiredNumberScheduled is not None and
                    daemonset.status.numberReady == daemonset.status.desiredNumberScheduled and
                    daemonset.status.observedGeneration == daemonset.metadata.generation)

        def _custom_condition(resource):
            if not resource.status or not resource.status.conditions:
                return False
            match = [x for x in resource.status.conditions if x.type == condition['type']]
            if not match:
                return False
            # There should never be more than one condition of a specific type
            match = match[0]
            if match.status == 'Unknown':
                if match.status == condition['status']:
                    if 'reason' not in condition:
                        return True
                    if condition['reason']:
                        return match.reason == condition['reason']
                return False
            status = True if match.status == 'True' else False
            if status == condition['status']:
                if condition.get('reason'):
                    return match.reason == condition['reason']
                return True
            return False

        def _resource_absent(resource):
            return not resource

        waiter = dict(
            Deployment=_deployment_ready,
            DaemonSet=_daemonset_ready,
            Pod=_pod_ready
        )
        kind = definition['kind']
        if state == 'present' and not condition:
            predicate = waiter.get(kind, lambda x: x)
        elif state == 'present' and condition:
            predicate = _custom_condition
        else:
            predicate = _resource_absent
        return self._wait_for(resource, definition['metadata']['name'], definition['metadata'].get('namespace'), predicate, sleep, timeout, state)
