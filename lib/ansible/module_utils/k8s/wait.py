import copy

from ansible.module_utils.k8s.common import AUTH_ARG_SPEC, COMMON_ARG_SPEC
from ansible.module_utils.six import string_types
from ansible.module_utils.k8s.common import KubernetesAnsibleModule

try:
    import yaml
except ImportError:
    # Exceptions handled in common
    pass


class KubernetesWaitModule(KubernetesAnsibleModule):

    @property
    def field_spec(self):
        return dict(
            name=dict(),
            operator=dict(choices=['=', '!=', '>', '<', '<=', '>='], default='='),
            value=dict(type='raw')
        )

    @property
    def condition_spec(self):
        return dict(
            type=dict(),
            status=dict(choices=[True, False, "Unknown"], default=True),
            reason=dict()
        )

    @property
    def argspec(self):
        argument_spec = copy.deepcopy(COMMON_ARG_SPEC)
        argument_spec.update(copy.deepcopy(AUTH_ARG_SPEC))
        argument_spec.pop('resource_definition')
        argument_spec.pop('src')
        argument_spec['timeout'] = dict(type='int', default=120)
        argument_spec['field'] = dict(type='dict', default=None, options=self.field_spec)
        argument_spec['condition'] = dict(type='dict', default=None, options=self.condition_spec)
        argument_spec['label_selectors'] = dict(type='list', default=[])
        argument_spec['field_selectors'] = dict(type='list', default=[])
        return argument_spec

    def __init__(self, k8s_kind=None, *args, **kwargs):
        self.client = None

        KubernetesAnsibleModule.__init__(self, *args,
                                         supports_check_mode=True,
                                         **kwargs)
        self.kind = k8s_kind or self.params.get('kind')
        self.api_version = self.params.get('api_version')
        self.name = self.params.get('name')
        self.namespace = self.params.get('namespace')
        self.label_selectors = self.params.get('label_selectors')
        self.field_selectors = self.params.get('field_selectors')
        self.condition = self.params.get('condition')
        self.field = self.params.get('field')

    def predicate(self):
        def _condition_func(resource):
            if not resource.status or not resource.status.conditions:
                return False
            match = [x for x in resource.status.conditions if x.type == self.condition['type']]
            if not match:
                return False
            # There should never be more than one condition of a specific type
            match = match[0]
            if match.status == 'Unknown':
                return False
            status = True if match.status == 'True' else False
            if status == self.condition['status']:
                if self.condition.get('reason'):
                    return match.reason == self.condition['reason']
                return True
            return False

        def _field_func(resource):
            operators = {
                '=': lambda x, y: x == y,
                '!=': lambda x, y: x != y,
                '>': lambda x, y: x > y,
                '<': lambda x, y: x < y,
                '>=': lambda x, y: x >= y,
                '<=': lambda x, y: x <= y
            }
            if not resource.status:
                return False
            current = getattr(resource.status, self.field['name'], None)
            return operators[self.field['operator']](current, self.field['value'])

    def execute_module(self):
        self.client = self.get_api_client()
        resource = self.find_resource(self.kind, self.api_version, fail=True)
        success, resource, duration = self.wait(
            resource,
            predicate=self.predicate(),
            name=self.name,
            namespace=self.namespace,
            label_selectors=self.label_selectors,
            field_selectors=self.field_selectors,
        )
        if success:
            self.exit_json(changed=False, duration=duration, **resource)
        self.fail(msg="Timeout: waited {0}s for Kubernetes resource to match desired state")
