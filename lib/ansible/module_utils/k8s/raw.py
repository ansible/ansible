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
from ansible.module_utils.k8s.common import AUTH_ARG_SPEC, COMMON_ARG_SPEC
from ansible.module_utils.six import string_types
from ansible.module_utils.k8s.common import KubernetesAnsibleModule
from ansible.module_utils.common.dict_transformations import dict_merge


try:
    import yaml
    from openshift.dynamic.exceptions import DynamicApiError, NotFoundError, ConflictError, ForbiddenError
except ImportError:
    # Exceptions handled in common
    pass


class KubernetesRawModule(KubernetesAnsibleModule):

    @property
    def argspec(self):
        argument_spec = copy.deepcopy(COMMON_ARG_SPEC)
        argument_spec.update(copy.deepcopy(AUTH_ARG_SPEC))
        argument_spec['merge_type'] = dict(choices=['json', 'merge', 'strategic-merge'])
        return argument_spec

    def __init__(self, *args, **kwargs):
        self.client = None

        mutually_exclusive = [
            ('resource_definition', 'src'),
        ]

        KubernetesAnsibleModule.__init__(self, *args,
                                         mutually_exclusive=mutually_exclusive,
                                         supports_check_mode=True,
                                         **kwargs)

        self.kind = self.params.pop('kind')
        self.api_version = self.params.pop('api_version')
        self.name = self.params.pop('name')
        self.namespace = self.params.pop('namespace')
        resource_definition = self.params.pop('resource_definition')
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
        src = self.params.pop('src')
        if src:
            self.resource_definitions = self.load_resource_definitions(src)

        if not resource_definition and not src:
            self.resource_definitions = [{
                'kind': self.kind,
                'apiVersion': self.api_version,
                'metadata': {
                    'name': self.name,
                    'namespace': self.namespace
                }
            }]

    def execute_module(self):
        changed = False
        results = []
        self.client = self.get_api_client()
        for definition in self.resource_definitions:
            kind = definition.get('kind', self.kind)
            search_kind = kind
            if kind.lower().endswith('list'):
                search_kind = kind[:-4]
            api_version = definition.get('apiVersion', self.api_version)
            resource = self.find_resource(search_kind, api_version, fail=True)
            definition = self.set_defaults(resource, definition)
            result = self.perform_action(resource, definition)
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

    def set_defaults(self, resource, definition):
        definition['kind'] = resource.kind
        definition['apiVersion'] = resource.group_version
        if not definition.get('metadata'):
            definition['metadata'] = {}
        if self.name and not definition['metadata'].get('name'):
            definition['metadata']['name'] = self.name
        if resource.namespaced and self.namespace and not definition['metadata'].get('namespace'):
            definition['metadata']['namespace'] = self.namespace
        return definition

    def perform_action(self, resource, definition):
        result = {'changed': False, 'result': {}}
        state = self.params.get('state', None)
        force = self.params.get('force', False)
        name = definition['metadata'].get('name')
        namespace = definition['metadata'].get('namespace')
        existing = None

        self.remove_aliases()

        if definition['kind'].endswith('List'):
            result['result'] = resource.get(namespace=namespace).to_dict()
            result['changed'] = False
            result['method'] = 'get'
            return result

        try:
            existing = resource.get(name=name, namespace=namespace)
        except NotFoundError:
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
                if not self.check_mode:
                    try:
                        k8s_obj = resource.delete(name, namespace=namespace)
                        result['result'] = k8s_obj.to_dict()
                    except DynamicApiError as exc:
                        self.fail_json(msg="Failed to delete object: {0}".format(exc.body),
                                       error=exc.status, status=exc.status, reason=exc.reason)
                result['changed'] = True
                return result
        else:
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
                        self.fail_json(msg="Failed to create object: {0}".format(exc.body),
                                       error=exc.status, status=exc.status, reason=exc.reason)
                result['result'] = k8s_obj
                result['changed'] = True
                result['method'] = 'create'
                return result

            match = False
            diffs = []

            if existing and force:
                if self.check_mode:
                    k8s_obj = definition
                else:
                    try:
                        k8s_obj = resource.replace(definition, name=name, namespace=namespace).to_dict()
                    except DynamicApiError as exc:
                        self.fail_json(msg="Failed to replace object: {0}".format(exc.body),
                                       error=exc.status, status=exc.status, reason=exc.reason)
                match, diffs = self.diff_objects(existing.to_dict(), k8s_obj)
                result['result'] = k8s_obj
                result['changed'] = not match
                result['method'] = 'replace'
                result['diff'] = diffs
                return result

            # Differences exist between the existing obj and requested params
            if self.check_mode:
                k8s_obj = dict_merge(existing.to_dict(), definition)
            else:
                try:
                    params = dict(name=name, namespace=namespace)
                    if self.params['merge_type']:
                        from distutils.version import LooseVersion
                        if LooseVersion(self.openshift_version) < LooseVersion("0.6.2"):
                            self.fail_json(msg="openshift >= 0.6.2 is required for merge_type")
                        params['content_type'] = 'application/{0}-patch+json'.format(self.params['merge_type'])
                    k8s_obj = resource.patch(definition, **params).to_dict()
                    match, diffs = self.diff_objects(existing.to_dict(), k8s_obj)
                    result['result'] = k8s_obj
                except DynamicApiError as exc:
                    self.fail_json(msg="Failed to patch object: {0}".format(exc.body),
                                   error=exc.status, status=exc.status, reason=exc.reason)
            match, diffs = self.diff_objects(existing.to_dict(), k8s_obj)
            result['result'] = k8s_obj
            result['changed'] = not match
            result['method'] = 'patch'
            result['diff'] = diffs
            return result

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
