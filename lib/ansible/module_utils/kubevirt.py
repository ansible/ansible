# -*- coding: utf-8 -*-
#

# Copyright (c) 2018, KubeVirt Team <@kubevirt>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from collections import defaultdict

from ansible.module_utils.k8s.common import list_dict_str
from ansible.module_utils.k8s.raw import KubernetesRawModule

try:
    from openshift import watch
    from openshift.helper.exceptions import KubernetesException
except ImportError:
    # Handled in k8s common:
    pass


API_VERSION = 'kubevirt.io/v1alpha3'


VM_COMMON_ARG_SPEC = {
    'name': {},
    'force': {
        'type': 'bool',
        'default': False,
    },
    'resource_definition': {
        'type': list_dict_str,
        'aliases': ['definition', 'inline']
    },
    'src': {
        'type': 'path',
    },
    'namespace': {},
    'api_version': {'type': 'str', 'default': API_VERSION, 'aliases': ['api', 'version']},
    'merge_type': {'type': 'list', 'choices': ['json', 'merge', 'strategic-merge']},
    'wait': {'type': 'bool', 'default': True},
    'wait_timeout': {'type': 'int', 'default': 120},
    'memory': {'type': 'str'},
    'disks': {'type': 'list'},
    'labels': {'type': 'dict'},
    'interfaces': {'type': 'list'},
    'machine_type': {'type': 'str'},
    'cloud_init_nocloud': {'type': 'dict'},
}


def virtdict():
    """
    This function create dictionary, with defaults to dictionary.
    """
    return defaultdict(virtdict)


class KubeVirtRawModule(KubernetesRawModule):
    def __init__(self, *args, **kwargs):
        self.api_version = API_VERSION
        super(KubeVirtRawModule, self).__init__(*args, **kwargs)

    @staticmethod
    def merge_dicts(x, y):
        """
        This function merge two dictionaries, where the first dict has
        higher priority in merging two same keys.
        """
        for k in set(x.keys()).union(y.keys()):
            if k in x and k in y:
                if isinstance(x[k], dict) and isinstance(y[k], dict):
                    yield (k, dict(KubeVirtRawModule.merge_dicts(x[k], y[k])))
                else:
                    yield (k, y[k])
            elif k in x:
                yield (k, x[k])
            else:
                yield (k, y[k])

    def _create_stream(self, resource, namespace, wait_timeout):
        """ Create a stream of events for the object """
        w = None
        stream = None
        try:
            w = watch.Watch()
            w._api_client = self.client.client
            stream = w.stream(resource.get, serialize=False, namespace=namespace, timeout_seconds=wait_timeout)
        except KubernetesException as exc:
            self.fail_json(msg='Failed to initialize watch: {0}'.format(exc.message))
        return w, stream

    def get_resource(self, resource):
        try:
            existing = resource.get(name=self.name, namespace=self.namespace)
        except Exception:
            existing = None

        return existing

    def _define_cloud_init(self, cloud_init_nocloud, template_spec):
        """
        Takes the user's cloud_init_nocloud parameter and fill it in kubevirt
        API strucuture. The name of the volume is hardcoded to ansiblecloudinitvolume
        and the name for disk is hardcoded to ansiblecloudinitdisk.
        """
        if cloud_init_nocloud:
            if not template_spec['volumes']:
                template_spec['volumes'] = []
            if not template_spec['domain']['devices']['disks']:
                template_spec['domain']['devices']['disks'] = []

            template_spec['volumes'].append({'name': 'ansiblecloudinitvolume', 'cloudInitNoCloud': cloud_init_nocloud})
            template_spec['domain']['devices']['disks'].append({
                'name': 'ansiblecloudinitdisk',
                'volumeName': 'ansiblecloudinitvolume',
                'disk': {'bus': 'virtio'},
            })

    def _define_interfaces(self, interfaces, template_spec):
        """
        Takes interfaces parameter of Ansible and create kubevirt API interfaces
        and networks strucutre out from it.
        """
        if interfaces:
            # Extract interfaces k8s specification from interfaces list passed to Ansible:
            spec_interfaces = []
            for i in interfaces:
                spec_interfaces.append(dict((k, v) for k, v in i.items() if k != 'network'))
            template_spec['domain']['devices']['interfaces'] = spec_interfaces

            # Extract networks k8s specification from interfaces list passed to Ansible:
            spec_networks = []
            for i in interfaces:
                net = i['network']
                net['name'] = i['name']
                spec_networks.append(net)
            template_spec['networks'] = spec_networks

    def _define_disks(self, disks, template_spec):
        """
        Takes disks parameter of Ansible and create kubevirt API disks and
        volumes strucutre out from it.
        """
        if disks:
            # Extract k8s specification from disks list passed to Ansible:
            spec_disks = []
            for d in disks:
                spec_disks.append(dict((k, v) for k, v in d.items() if k != 'volume'))
            template_spec['domain']['devices']['disks'] = spec_disks

            # Extract volumes k8s specification from disks list passed to Ansible:
            spec_volumes = []
            for d in disks:
                volume = d['volume']
                volume['name'] = d['name']
                spec_volumes.append(volume)
            template_spec['volumes'] = spec_volumes

    def execute_crud(self, kind, definition, template):
        """ Module execution """
        self.client = self.get_api_client()

        disks = self.params.get('disks', [])
        memory = self.params.get('memory')
        labels = self.params.get('labels')
        interfaces = self.params.get('interfaces')
        cloud_init_nocloud = self.params.get('cloud_init_nocloud')
        machine_type = self.params.get('machine_type')
        template_spec = template['spec']

        # Merge additional flat parameters:
        if memory:
            template_spec['domain']['resources']['requests']['memory'] = memory

        if labels:
            template['metadata']['labels'] = labels

        if machine_type:
            template_spec['domain']['machine']['type'] = machine_type

        # Define cloud init disk if defined:
        self._define_cloud_init(cloud_init_nocloud, template_spec)

        # Define disks
        self._define_disks(disks, template_spec)

        # Define interfaces:
        self._define_interfaces(interfaces, template_spec)

        # Perform create/absent action:
        definition = dict(self.merge_dicts(self.resource_definitions[0], definition))
        resource = self.find_resource(kind, self.api_version, fail=True)
        definition = self.set_defaults(resource, definition)
        return self.perform_action(resource, definition)
