# -*- coding: utf-8 -*-
#

# Copyright (c) 2018, KubeVirt Team <@kubevirt>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from collections import defaultdict
from distutils.version import Version

from ansible.module_utils.common import dict_transformations
from ansible.module_utils.common._collections_compat import Sequence
from ansible.module_utils.k8s.common import list_dict_str
from ansible.module_utils.k8s.raw import KubernetesRawModule

import copy
import re

MAX_SUPPORTED_API_VERSION = 'v1alpha3'
API_GROUP = 'kubevirt.io'


# Put all args that (can) modify 'spec:' here:
VM_SPEC_DEF_ARG_SPEC = {
    'resource_definition': {
        'type': 'dict',
        'aliases': ['definition', 'inline']
    },
    'memory': {'type': 'str'},
    'memory_limit': {'type': 'str'},
    'cpu_cores': {'type': 'int'},
    'disks': {'type': 'list'},
    'labels': {'type': 'dict'},
    'interfaces': {'type': 'list'},
    'machine_type': {'type': 'str'},
    'cloud_init_nocloud': {'type': 'dict'},
    'bootloader': {'type': 'str'},
    'smbios_uuid': {'type': 'str'},
    'cpu_model': {'type': 'str'},
    'headless': {'type': 'str'},
    'hugepage_size': {'type': 'str'},
    'tablets': {'type': 'list'},
    'cpu_limit': {'type': 'int'},
    'cpu_shares': {'type': 'int'},
    'cpu_features': {'type': 'list'},
}
# And other common args go here:
VM_COMMON_ARG_SPEC = {
    'name': {'required': True},
    'namespace': {'required': True},
    'state': {
        'default': 'present',
        'choices': ['present', 'absent'],
    },
    'force': {
        'type': 'bool',
        'default': False,
    },
    'merge_type': {'type': 'list', 'choices': ['json', 'merge', 'strategic-merge']},
    'wait': {'type': 'bool', 'default': True},
    'wait_timeout': {'type': 'int', 'default': 120},
}
VM_COMMON_ARG_SPEC.update(VM_SPEC_DEF_ARG_SPEC)


def virtdict():
    """
    This function create dictionary, with defaults to dictionary.
    """
    return defaultdict(virtdict)


class KubeAPIVersion(Version):
    component_re = re.compile(r'(\d+ | [a-z]+)', re.VERBOSE)

    def __init__(self, vstring=None):
        if vstring:
            self.parse(vstring)

    def parse(self, vstring):
        self.vstring = vstring
        components = [x for x in self.component_re.split(vstring) if x]
        for i, obj in enumerate(components):
            try:
                components[i] = int(obj)
            except ValueError:
                pass

        errmsg = "version '{0}' does not conform to kubernetes api versioning guidelines".format(vstring)
        c = components

        if len(c) not in (2, 4) or c[0] != 'v' or not isinstance(c[1], int):
            raise ValueError(errmsg)
        if len(c) == 4 and (c[2] not in ('alpha', 'beta') or not isinstance(c[3], int)):
            raise ValueError(errmsg)

        self.version = components

    def __str__(self):
        return self.vstring

    def __repr__(self):
        return "KubeAPIVersion ('{0}')".format(str(self))

    def _cmp(self, other):
        if isinstance(other, str):
            other = KubeAPIVersion(other)

        myver = self.version
        otherver = other.version

        for ver in myver, otherver:
            if len(ver) == 2:
                ver.extend(['zeta', 9999])

        if myver == otherver:
            return 0
        if myver < otherver:
            return -1
        if myver > otherver:
            return 1

    # python2 compatibility
    def __cmp__(self, other):
        return self._cmp(other)


class KubeVirtRawModule(KubernetesRawModule):
    def __init__(self, *args, **kwargs):
        super(KubeVirtRawModule, self).__init__(*args, **kwargs)

    @staticmethod
    def merge_dicts(base_dict, merging_dicts):
        """This function merges a base dictionary with one or more other dictionaries.
        The base dictionary takes precedence when there is a key collision.
        merging_dicts can be a dict or a list or tuple of dicts.  In the latter case, the
        dictionaries at the front of the list have higher precedence over the ones at the end.
        """
        if not merging_dicts:
            merging_dicts = ({},)

        if not isinstance(merging_dicts, Sequence):
            merging_dicts = (merging_dicts,)

        new_dict = {}
        for d in reversed(merging_dicts):
            new_dict = dict_transformations.dict_merge(new_dict, d)

        new_dict = dict_transformations.dict_merge(new_dict, base_dict)

        return new_dict

    def get_resource(self, resource):
        try:
            existing = resource.get(name=self.name, namespace=self.namespace)
        except Exception:
            existing = None

        return existing

    def _define_datavolumes(self, datavolumes, spec):
        """
        Takes datavoulmes parameter of Ansible and create kubevirt API datavolumesTemplateSpec
        structure from it
        """
        if not datavolumes:
            return

        spec['dataVolumeTemplates'] = []
        for dv in datavolumes:
            # Add datavolume to datavolumetemplates spec:
            dvt = virtdict()
            dvt['metadata']['name'] = dv.get('name')
            dvt['spec']['pvc'] = {
                'accessModes': dv.get('pvc').get('accessModes'),
                'resources': {
                    'requests': {
                        'storage': dv.get('pvc').get('storage'),
                    }
                }
            }
            dvt['spec']['source'] = dv.get('source')
            spec['dataVolumeTemplates'].append(dvt)

            # Add datavolume to disks spec:
            if not spec['template']['spec']['domain']['devices']['disks']:
                spec['template']['spec']['domain']['devices']['disks'] = []

            spec['template']['spec']['domain']['devices']['disks'].append(
                {
                    'name': dv.get('name'),
                    'disk': dv.get('disk', {'bus': 'virtio'}),
                }
            )

            # Add datavolume to volumes spec:
            if not spec['template']['spec']['volumes']:
                spec['template']['spec']['volumes'] = []

            spec['template']['spec']['volumes'].append(
                {
                    'dataVolume': {
                        'name': dv.get('name')
                    },
                    'name': dv.get('name'),
                }
            )

    def _define_cloud_init(self, cloud_init_nocloud, template_spec):
        """
        Takes the user's cloud_init_nocloud parameter and fill it in kubevirt
        API strucuture. The name for disk is hardcoded to ansiblecloudinitdisk.
        """
        if cloud_init_nocloud:
            if not template_spec['volumes']:
                template_spec['volumes'] = []
            if not template_spec['domain']['devices']['disks']:
                template_spec['domain']['devices']['disks'] = []

            template_spec['volumes'].append({'name': 'ansiblecloudinitdisk', 'cloudInitNoCloud': cloud_init_nocloud})
            template_spec['domain']['devices']['disks'].append({
                'name': 'ansiblecloudinitdisk',
                'disk': {'bus': 'virtio'},
            })

    def _define_interfaces(self, interfaces, template_spec, defaults):
        """
        Takes interfaces parameter of Ansible and create kubevirt API interfaces
        and networks strucutre out from it.
        """
        if not interfaces and defaults and 'interfaces' in defaults:
            interfaces = copy.deepcopy(defaults['interfaces'])
            for d in interfaces:
                d['network'] = defaults['networks'][0]

        if interfaces:
            # Extract interfaces k8s specification from interfaces list passed to Ansible:
            spec_interfaces = []
            for i in interfaces:
                spec_interfaces.append(
                    self.merge_dicts(dict((k, v) for k, v in i.items() if k != 'network'), defaults['interfaces'])
                )
            if 'interfaces' not in template_spec['domain']['devices']:
                template_spec['domain']['devices']['interfaces'] = []
            template_spec['domain']['devices']['interfaces'].extend(spec_interfaces)

            # Extract networks k8s specification from interfaces list passed to Ansible:
            spec_networks = []
            for i in interfaces:
                net = i['network']
                net['name'] = i['name']
                spec_networks.append(self.merge_dicts(net, defaults['networks']))
            if 'networks' not in template_spec:
                template_spec['networks'] = []
            template_spec['networks'].extend(spec_networks)

    def _define_disks(self, disks, template_spec, defaults):
        """
        Takes disks parameter of Ansible and create kubevirt API disks and
        volumes strucutre out from it.
        """
        if not disks and defaults and 'disks' in defaults:
            disks = copy.deepcopy(defaults['disks'])
            for d in disks:
                d['volume'] = defaults['volumes'][0]

        if disks:
            # Extract k8s specification from disks list passed to Ansible:
            spec_disks = []
            for d in disks:
                spec_disks.append(
                    self.merge_dicts(dict((k, v) for k, v in d.items() if k != 'volume'), defaults['disks'])
                )
            if 'disks' not in template_spec['domain']['devices']:
                template_spec['domain']['devices']['disks'] = []
            template_spec['domain']['devices']['disks'].extend(spec_disks)

            # Extract volumes k8s specification from disks list passed to Ansible:
            spec_volumes = []
            for d in disks:
                volume = d['volume']
                volume['name'] = d['name']
                spec_volumes.append(self.merge_dicts(volume, defaults['volumes']))
            if 'volumes' not in template_spec:
                template_spec['volumes'] = []
            template_spec['volumes'].extend(spec_volumes)

    def find_supported_resource(self, kind):
        results = self.client.resources.search(kind=kind, group=API_GROUP)
        if not results:
            self.fail('Failed to find resource {0} in {1}'.format(kind, API_GROUP))
        sr = sorted(results, key=lambda r: KubeAPIVersion(r.api_version), reverse=True)
        for r in sr:
            if KubeAPIVersion(r.api_version) <= KubeAPIVersion(MAX_SUPPORTED_API_VERSION):
                return r
        self.fail("API versions {0} are too recent. Max supported is {1}/{2}.".format(
            str([r.api_version for r in sr]), API_GROUP, MAX_SUPPORTED_API_VERSION))

    def _construct_vm_definition(self, kind, definition, template, params, defaults=None):
        self.client = self.get_api_client()

        disks = params.get('disks', [])
        memory = params.get('memory')
        memory_limit = params.get('memory_limit')
        cpu_cores = params.get('cpu_cores')
        cpu_model = params.get('cpu_model')
        cpu_features = params.get('cpu_features')
        labels = params.get('labels')
        datavolumes = params.get('datavolumes')
        interfaces = params.get('interfaces')
        bootloader = params.get('bootloader')
        cloud_init_nocloud = params.get('cloud_init_nocloud')
        machine_type = params.get('machine_type')
        headless = params.get('headless')
        smbios_uuid = params.get('smbios_uuid')
        hugepage_size = params.get('hugepage_size')
        tablets = params.get('tablets')
        cpu_shares = params.get('cpu_shares')
        cpu_limit = params.get('cpu_limit')
        template_spec = template['spec']

        # Merge additional flat parameters:
        if memory:
            template_spec['domain']['resources']['requests']['memory'] = memory

        if cpu_shares:
            template_spec['domain']['resources']['requests']['cpu'] = cpu_shares

        if cpu_limit:
            template_spec['domain']['resources']['limits']['cpu'] = cpu_limit

        if tablets:
            for tablet in tablets:
                tablet['type'] = 'tablet'
            template_spec['domain']['devices']['inputs'] = tablets

        if memory_limit:
            template_spec['domain']['resources']['limits']['memory'] = memory_limit

        if hugepage_size is not None:
            template_spec['domain']['memory']['hugepages']['pageSize'] = hugepage_size

        if cpu_features is not None:
            template_spec['domain']['cpu']['features'] = cpu_features

        if cpu_cores is not None:
            template_spec['domain']['cpu']['cores'] = cpu_cores

        if cpu_model:
            template_spec['domain']['cpu']['model'] = cpu_model

        if labels:
            template['metadata']['labels'] = self.merge_dicts(labels, template['metadata']['labels'])

        if machine_type:
            template_spec['domain']['machine']['type'] = machine_type

        if bootloader:
            template_spec['domain']['firmware']['bootloader'] = {bootloader: {}}

        if smbios_uuid:
            template_spec['domain']['firmware']['uuid'] = smbios_uuid

        if headless is not None:
            template_spec['domain']['devices']['autoattachGraphicsDevice'] = not headless

        # Define disks
        self._define_disks(disks, template_spec, defaults)

        # Define cloud init disk if defined:
        # Note, that this must be called after _define_disks, so the cloud_init
        # is not first in order and it's not used as boot disk:
        self._define_cloud_init(cloud_init_nocloud, template_spec)

        # Define interfaces:
        self._define_interfaces(interfaces, template_spec, defaults)

        # Define datavolumes:
        self._define_datavolumes(datavolumes, definition['spec'])

        return self.merge_dicts(definition, self.resource_definitions[0])

    def construct_vm_definition(self, kind, definition, template, defaults=None):
        definition = self._construct_vm_definition(kind, definition, template, self.params, defaults)
        resource = self.find_supported_resource(kind)
        definition = self.set_defaults(resource, definition)
        return resource, definition

    def construct_vm_template_definition(self, kind, definition, template, params):
        definition = self._construct_vm_definition(kind, definition, template, params)
        resource = self.find_resource(kind, definition['apiVersion'], fail=True)

        # Set defaults:
        definition['kind'] = kind
        definition['metadata']['name'] = params.get('name')
        definition['metadata']['namespace'] = params.get('namespace')

        return resource, definition

    def execute_crud(self, kind, definition):
        """ Module execution """
        resource = self.find_supported_resource(kind)
        definition = self.set_defaults(resource, definition)
        return self.perform_action(resource, definition)
