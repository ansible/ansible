#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''

module: kubevirt_pvc

short_description: Manage PVCs on Kubernetes

version_added: "2.8"

author: KubeVirt Team (@kubevirt)

description:
  - Use Openshift Python SDK to manage PVCs on Kubernetes
  - Support Containerized Data Importer out of the box

options:
  resource_definition:
    description:
    - "A partial YAML definition of the PVC object being created/updated. Here you can define Kubernetes
      PVC Resource parameters not covered by this module's parameters."
    - "NOTE: I(resource_definition) has lower priority than module parameters. If you try to define e.g.
      I(metadata.namespace) here, that value will be ignored and I(namespace) used instead."
    aliases:
    - definition
    - inline
    type: dict
  state:
    description:
    - "Determines if an object should be created, patched, or deleted. When set to C(present), an object will be
      created, if it does not already exist. If set to C(absent), an existing object will be deleted. If set to
      C(present), an existing object will be patched, if its attributes differ from those specified using
      module options and I(resource_definition)."
    default: present
    choices:
    - present
    - absent
  force:
    description:
    - If set to C(True), and I(state) is C(present), an existing object will be replaced.
    default: false
    type: bool
  merge_type:
    description:
    - Whether to override the default patch merge approach with a specific type.
    - "This defaults to C(['strategic-merge', 'merge']), which is ideal for using the same parameters
      on resource kinds that combine Custom Resources and built-in resources."
    - See U(https://kubernetes.io/docs/tasks/run-application/update-api-object-kubectl-patch/#use-a-json-merge-patch-to-update-a-deployment)
    - If more than one merge_type is given, the merge_types will be tried in order
    choices:
    - json
    - merge
    - strategic-merge
    type: list
  name:
    description:
      - Use to specify a PVC object name.
    required: true
    type: str
  namespace:
    description:
      - Use to specify a PVC object namespace.
    required: true
    type: str
  annotations:
    description:
      - Annotations attached to this object.
      - U(https://kubernetes.io/docs/concepts/overview/working-with-objects/annotations/)
    type: dict
  labels:
    description:
      - Labels attached to this object.
      - U(https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)
    type: dict
  selector:
    description:
      - A label query over volumes to consider for binding.
      - U(https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)
    type: dict
  access_modes:
    description:
      - Contains the desired access modes the volume should have.
      - "More info: U(https://kubernetes.io/docs/concepts/storage/persistent-volumes#access-modes)"
    type: list
  size:
    description:
      - How much storage to allocate to the PVC.
    type: str
    aliases:
    - storage
  storage_class_name:
    description:
      - Name of the StorageClass required by the claim.
      - "More info: U(https://kubernetes.io/docs/concepts/storage/persistent-volumes#class-1)"
    type: str
  volume_mode:
    description:
      - "This defines what type of volume is required by the claim. Value of Filesystem is implied when not
        included in claim spec. This is an alpha feature of kubernetes and may change in the future."
    type: str
  volume_name:
    description:
      - This is the binding reference to the PersistentVolume backing this claim.
    type: str
  cdi_source:
    description:
      - "If data is to be copied onto the PVC using the Containerized Data Importer you can specify the source of
        the data (along with any additional configuration) as well as it's format."
      - "Valid source types are: blank, http, s3, registry, pvc and upload. The last one requires using the
        M(kubevirt_cdi_upload) module to actually perform an upload."
      - "Source data format is specified using the optional I(content_type). Valid options are C(kubevirt)
        (default; raw image) and C(archive) (tar.gz)."
      - "This uses the DataVolume source syntax:
        U(https://github.com/kubevirt/containerized-data-importer/blob/master/doc/datavolumes.md#https3registry-source)"
    type: dict
  wait:
    description:
      - "If set, this module will wait for the PVC to become bound and CDI (if enabled) to finish its operation
        before returning."
      - "Used only if I(state) set to C(present)."
      - "Unless used in conjuction with I(cdi_source), this might result in a timeout, as clusters may be configured
        to not bind PVCs until first usage."
    default: false
    type: bool
  wait_timeout:
    description:
      - Specifies how much time in seconds to wait for PVC creation to complete if I(wait) option is enabled.
      - Default value is reasonably high due to an expectation that CDI might take a while to finish its operation.
    type: int
    default: 300

extends_documentation_fragment:
  - k8s_auth_options

requirements:
  - python >= 2.7
  - openshift >= 0.8.2
'''

EXAMPLES = '''
- name: Create a PVC and import data from an external source
  kubevirt_pvc:
    name: pvc1
    namespace: default
    size: 100Mi
    access_modes:
      - ReadWriteOnce
    cdi_source:
      http:
        url: https://www.source.example/path/of/data/vm.img
      # If the URL points to a tar.gz containing the disk image, ucomment the line below:
      #content_type: archive

- name: Create a PVC as a clone from a different PVC
  kubevirt_pvc:
    name: pvc2
    namespace: default
    size: 100Mi
    access_modes:
      - ReadWriteOnce
    cdi_source:
      pvc:
        namespace: source-ns
        name: source-pvc

- name: Create a PVC ready for data upload
  kubevirt_pvc:
    name: pvc3
    namespace: default
    size: 100Mi
    access_modes:
      - ReadWriteOnce
    cdi_source:
      upload: yes
    # You need the kubevirt_cdi_upload module to actually upload something

- name: Create a PVC with a blank raw image
  kubevirt_pvc:
    name: pvc4
    namespace: default
    size: 100Mi
    access_modes:
      - ReadWriteOnce
    cdi_source:
      blank: yes

- name: Create a PVC and fill it with data from a container
  kubevirt_pvc:
    name: pvc5
    namespace: default
    size: 100Mi
    access_modes:
      - ReadWriteOnce
    cdi_source:
      registry:
        url: "docker://kubevirt/fedora-cloud-registry-disk-demo"

'''

RETURN = '''
result:
  description:
  - The created, patched, or otherwise present object. Will be empty in the case of a deletion.
  returned: success
  type: complex
  contains:
     api_version:
       description: The versioned schema of this representation of an object.
       returned: success
       type: str
     kind:
       description: Represents the REST resource this object represents.
       returned: success
       type: str
     metadata:
       description: Standard object metadata. Includes name, namespace, annotations, labels, etc.
       returned: success
       type: complex
     spec:
       description: Specific attributes of the object. Will vary based on the I(api_version) and I(kind).
       returned: success
       type: complex
     status:
       description: Current status details for the object.
       returned: success
       type: complex
     items:
       description: Returned only when multiple yaml documents are passed to src or resource_definition
       returned: when resource_definition or src contains list of objects
       type: list
     duration:
       description: elapsed time of task in seconds
       returned: when C(wait) is true
       type: int
       sample: 48
'''


import copy
import traceback

from collections import defaultdict

from ansible.module_utils.k8s.common import AUTH_ARG_SPEC
from ansible.module_utils.k8s.raw import KubernetesRawModule
from ansible.module_utils.kubevirt import virtdict, KubeVirtRawModule


PVC_ARG_SPEC = {
    'name': {'required': True},
    'namespace': {'required': True},
    'state': {
        'type': 'str',
        'choices': [
            'present', 'absent'
        ],
        'default': 'present'
    },
    'force': {
        'type': 'bool',
        'default': False,
    },
    'merge_type': {
        'type': 'list',
        'choices': ['json', 'merge', 'strategic-merge']
    },
    'resource_definition': {
        'type': 'dict',
        'aliases': ['definition', 'inline']
    },
    'labels': {'type': 'dict'},
    'annotations': {'type': 'dict'},
    'selector': {'type': 'dict'},
    'access_modes': {'type': 'list'},
    'size': {
        'type': 'str',
        'aliases': ['storage']
    },
    'storage_class_name': {'type': 'str'},
    'volume_mode': {'type': 'str'},
    'volume_name': {'type': 'str'},
    'cdi_source': {'type': 'dict'},
    'wait': {
        'type': 'bool',
        'default': False
    },
    'wait_timeout': {
        'type': 'int',
        'default': 300
    }
}


class CreatePVCFailed(Exception):
    pass


class KubevirtPVC(KubernetesRawModule):
    def __init__(self):
        super(KubevirtPVC, self).__init__()

    @property
    def argspec(self):
        argument_spec = copy.deepcopy(AUTH_ARG_SPEC)
        argument_spec.update(PVC_ARG_SPEC)
        return argument_spec

    @staticmethod
    def fix_serialization(obj):
        if obj and hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return obj

    def _parse_cdi_source(self, _cdi_src, metadata):
        cdi_src = copy.deepcopy(_cdi_src)
        annotations = metadata['annotations']
        labels = metadata['labels']

        valid_content_types = ('kubevirt', 'archive')
        valid_sources = ('http', 's3', 'pvc', 'upload', 'blank', 'registry')

        if 'content_type' in cdi_src:
            content_type = cdi_src.pop('content_type')
            if content_type not in valid_content_types:
                raise ValueError("cdi_source.content_type must be one of {0}, not: '{1}'".format(
                    valid_content_types, content_type))
            annotations['cdi.kubevirt.io/storage.contentType'] = content_type

        if len(cdi_src) != 1:
            raise ValueError("You must specify exactly one valid CDI source, not {0}: {1}".format(len(cdi_src), tuple(cdi_src.keys())))

        src_type = tuple(cdi_src.keys())[0]
        src_spec = cdi_src[src_type]

        if src_type not in valid_sources:
            raise ValueError("Got an invalid CDI source type: '{0}', must be one of {1}".format(src_type, valid_sources))

        # True for all cases save one
        labels['app'] = 'containerized-data-importer'

        if src_type == 'upload':
            annotations['cdi.kubevirt.io/storage.upload.target'] = ''
        elif src_type == 'blank':
            annotations['cdi.kubevirt.io/storage.import.source'] = 'none'
        elif src_type == 'pvc':
            if not isinstance(src_spec, dict) or sorted(src_spec.keys()) != ['name', 'namespace']:
                raise ValueError("CDI Source 'pvc' requires specifying 'name' and 'namespace' (and nothing else)")
            labels['app'] = 'host-assisted-cloning'
            annotations['k8s.io/CloneRequest'] = '{0}/{1}'.format(src_spec['namespace'], src_spec['name'])
        elif src_type in ('http', 's3', 'registry'):
            if not isinstance(src_spec, dict) or 'url' not in src_spec:
                raise ValueError("CDI Source '{0}' requires specifying 'url'".format(src_type))
            unknown_params = set(src_spec.keys()).difference(set(('url', 'secretRef', 'certConfigMap')))
            if unknown_params:
                raise ValueError("CDI Source '{0}' does not know recognize params: {1}".format(src_type, tuple(unknown_params)))
            annotations['cdi.kubevirt.io/storage.import.source'] = src_type
            annotations['cdi.kubevirt.io/storage.import.endpoint'] = src_spec['url']
            if 'secretRef' in src_spec:
                annotations['cdi.kubevirt.io/storage.import.secretName'] = src_spec['secretRef']
            if 'certConfigMap' in src_spec:
                annotations['cdi.kubevirt.io/storage.import.certConfigMap'] = src_spec['certConfigMap']

    def _wait_for_creation(self, resource, uid):
        return_obj = None
        desired_cdi_status = 'Succeeded'
        use_cdi = True if self.params.get('cdi_source') else False
        if use_cdi and 'upload' in self.params['cdi_source']:
            desired_cdi_status = 'Running'

        for event in resource.watch(namespace=self.namespace, timeout=self.params.get('wait_timeout')):
            entity = event['object']
            metadata = entity.metadata
            if not hasattr(metadata, 'uid') or metadata.uid != uid:
                continue
            if entity.status.phase == 'Bound':
                if use_cdi and hasattr(metadata, 'annotations'):
                    import_status = metadata.annotations.get('cdi.kubevirt.io/storage.pod.phase')
                    if import_status == desired_cdi_status:
                        return_obj = entity
                        break
                else:
                    return_obj = entity
                    break
            elif entity.status.phase == 'Failed':
                raise CreatePVCFailed("PVC creation failed")

        if not return_obj:
            raise CreatePVCFailed("PVC creation timed out")

        return self.fix_serialization(return_obj)

    def execute_module(self):
        KIND = 'PersistentVolumeClaim'
        API = 'v1'

        definition = virtdict()
        definition['kind'] = KIND
        definition['apiVersion'] = API

        metadata = definition['metadata']
        metadata['name'] = self.params.get('name')
        metadata['namespace'] = self.params.get('namespace')
        if self.params.get('annotations'):
            metadata['annotations'] = self.params.get('annotations')
        if self.params.get('labels'):
            metadata['labels'] = self.params.get('labels')
        if self.params.get('cdi_source'):
            self._parse_cdi_source(self.params.get('cdi_source'), metadata)

        spec = definition['spec']
        if self.params.get('access_modes'):
            spec['accessModes'] = self.params.get('access_modes')
        if self.params.get('size'):
            spec['resources']['requests']['storage'] = self.params.get('size')
        if self.params.get('storage_class_name'):
            spec['storageClassName'] = self.params.get('storage_class_name')
        if self.params.get('selector'):
            spec['selector'] = self.params.get('selector')
        if self.params.get('volume_mode'):
            spec['volumeMode'] = self.params.get('volume_mode')
        if self.params.get('volume_name'):
            spec['volumeName'] = self.params.get('volume_name')

        # 'resource_definition:' has lower priority than module parameters
        definition = dict(KubeVirtRawModule.merge_dicts(self.resource_definitions[0], definition))

        self.client = self.get_api_client()
        resource = self.find_resource(KIND, API, fail=True)
        definition = self.set_defaults(resource, definition)
        result = self.perform_action(resource, definition)
        if self.params.get('wait') and self.params.get('state') == 'present':
            result['result'] = self._wait_for_creation(resource, result['result']['metadata']['uid'])

        self.exit_json(**result)


def main():
    module = KubevirtPVC()
    try:
        module.execute_module()
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
