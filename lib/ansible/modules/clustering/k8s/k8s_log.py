#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Fabian von Feilitzsch <@fabianvf>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: k8s_log

short_description: Fetch logs from Kubernetes resources

version_added: "2.8"

author:
    - "Fabian von Feilitzsch (@fabianvf)"

description:
  - Use the OpenShift Python client to perform read operations on K8s log endpoints.
  - Authenticate using either a config file, certificates, password or token.
  - Supports check mode.
  - Analogous to `kubectl log` or `oc log`

options:
  api_version:
    description:
    - Use to specify the API version. in conjunction with I(kind), I(name), and I(namespace) to identify a
      specific object.
    default: v1
    aliases:
    - api
    - version
  kind:
    description:
    - Use to specify an object model. Use in conjunction with I(api_version), I(name), and I(namespace) to identify a
      specific object.
    required: no
    default: Pod
  name:
    description:
    - Use to specify an object name.  Use in conjunction with I(api_version), I(kind) and I(namespace) to identify a
      specific object.
  namespace:
    description:
    - Use to specify an object namespace. Use in conjunction with I(api_version), I(kind), and I(name)
      to identify a specfic object.
  container:
    description:
    - Use to specify the container within a pod to grab the log from.
    - If there is only one container, this will default to that container.
    - If there is more than one container, this option is required.
    required: no
  label_selectors:
    description: List of label selectors to use to filter results

extends_documentation_fragment:
  - k8s_auth_options

requirements:
  - "python >= 2.7"
  - "openshift >= 0.6"
  - "PyYAML >= 3.11"
'''

EXAMPLES = '''
- name: Get a log from a Pod
  k8s_log:
    api_version: v1
    kind: Pod
    name: web-1
    namespace: testing
  register: web_log
'''

RETURN = '''
log:
  type: str
  description:
  - The text log of the object
  returned: success
'''


from ansible.module_utils.k8s.common import KubernetesAnsibleModule, AUTH_ARG_SPEC
import copy


class KubernetesLogModule(KubernetesAnsibleModule):

    def __init__(self, *args, **kwargs):
        KubernetesAnsibleModule.__init__(self, *args,
                                         supports_check_mode=True,
                                         **kwargs)

    @property
    def argspec(self):
        args = copy.deepcopy(AUTH_ARG_SPEC)
        args.update(
            dict(
                kind=dict(default='Pod'),
                api_version=dict(default='v1', aliases=['api', 'version']),
                name=dict(),
                namespace=dict(),
                container=dict(),
                label_selectors=dict(type='list', default=[]),
            )
        )
        return args

    def execute_module(self):
        name = self.params.get('name')
        label_selector = ','.join(self.params.get('label_selectors', {}))
        if name and label_selector:
            self.fail(msg='Only one of name or label_selectors can be provided')

        self.client = self.get_api_client()
        resource = self.find_resource(self.params['kind'], self.params['api_version'], fail=True)
        if 'log' not in resource.subresources:
            if not self.params.get('name'):
                self.fail(msg='name must be provided for resources that do not support the log subresource')
            instance = resource.get(name=self.params['name'], namespace=self.params.get('namespace'))
            label_selector = ','.join(self.extract_selectors(instance))
            resource = self.find_resource('Pod', 'v1', fail=True)

        if label_selector:
            v1_pods = self.find_resource('Pod', 'v1', fail=True)
            instances = v1_pods.get(namespace=self.params['namespace'], label_selector=label_selector)
            if not instances.items:
                self.fail(msg='No pods in namespace {0} matched selector {1}'.format(self.params['namespace'], label_selector))
            # This matches the behavior of kubectl when logging pods via a selector
            name = instances.items[0].metadata.name

        kwargs = {}
        if self.params.get('container'):
            kwargs['query_params'] = dict(containter=self.params['container'])

        self.exit_json(changed=False, log=resource.log.get(
            name=name,
            namespace=self.params.get('namespace'),
            **kwargs
        ))

    def extract_selectors(self, instance):
        # Parses selectors on an object based on the specifications documented here:
        # https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/#label-selectors
        selectors = []
        if not instance.spec.selector:
            self.fail(msg='{0} {1} does not support the log subresource directly, and no Pod selector was found on the object'.format(
                      '/'.join(instance.group, instance.apiVersion), instance.kind))

        if not (instance.spec.selector.matchLabels or instance.spec.selector.matchExpressions):
            # A few resources (like DeploymentConfigs) just use a simple key:value style instead of supporting expressions
            for k, v in dict(instance.spec.selector).items():
                selectors.append('{0}={1}'.format(k, v))
            return selectors

        if instance.spec.selector.matchLabels:
            for k, v in dict(instance.spec.selector.matchLabels).items():
                selectors.append('{0}={1}'.format(k, v))

        if instance.spec.selector.matchExpressions:
            for expression in instance.spec.selector.matchExpressions:
                operator = expression.operator

                if operator == 'Exists':
                    selectors.append(expression.key)
                elif operator == 'DoesNotExist':
                    selectors.append('!{0}'.format(expression.key))
                elif operator in ['In', 'NotIn']:
                    selectors.append('{key} {operator} {values}'.format(
                        key=expression.key,
                        operator=operator.lower(),
                        values='({0})'.format(
                            ', '.join(expression.values)
                        )
                    ))
                else:
                    self.fail(msg='The k8s_log module does not support the {0} matchExpression operator'.format(operator.lower()))

        return selectors


def main():
    KubernetesLogModule().execute_module()


if __name__ == '__main__':
    main()
