# -*- coding: utf-8 -*-

# Copyright: (c) 2018, KubeVirt Team <@kubevirt>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard oVirt documentation fragment
    DOCUMENTATION = r'''
options:
    wait:
        description:
            - "I(True) if the module should wait for the resource to get into desired state."
        type: bool
        default: yes
    kind:
        description:
            - Use to specify an object model. Use to create, delete, or discover an object without providing a full
              resource definition. Use in conjunction with I(api_version), I(name), and I(namespace) to identify a
              specific object. If I(resource definition) is provided, the I(kind) from the I(resource_definition)
              will override this option.
    force:
       description:
            - If set to C(no), and I(state) is C(present), an existing object will be replaced.
       type: bool
       default: no
    wait_timeout:
        description:
            - The amount of time in seconds the module should wait for the resource to get into desired state.
        type: int
        default: 120
    api_version:
        description:
            - "Specify the API version to be used."
        type: str
        default: kubevirt.io/v1alpha3
        aliases:
            - api
            - version
    memory:
        description:
            - The amount of memory to be requested by virtual machine.
            - For example 1024Mi.
        type: str
    machine_type:
        description:
            - QEMU machine type is the actual chipset of the virtual machine.
        type: str
    merge_type:
        description:
            - Whether to override the default patch merge approach with a specific type. By default, the strategic
              merge will typically be used.
            - For example, Custom Resource Definitions typically aren't updatable by the usual strategic merge. You may
              want to use C(merge) if you see "strategic merge patch format is not supported"
            - See U(https://kubernetes.io/docs/tasks/run-application/update-api-object-kubectl-patch/#use-a-json-merge-patch-to-update-a-deployment)
            - Requires openshift >= 0.6.2
            - If more than one merge_type is given, the merge_types will be tried in order
            - If openshift >= 0.6.2, this defaults to C(['strategic-merge', 'merge']), which is ideal for using the same parameters
              on resource kinds that combine Custom Resources and built-in resources. For openshift < 0.6.2, the default
              is simply C(strategic-merge).
        type: list
        choices: [ json, merge, strategic-merge ]
    cpu_cores:
        description:
            - "Number of CPU cores."
requirements:
    - python >= 2.7
    - openshift >= 0.8.2
notes:
  - "In order to use this module you have to install Openshift Python SDK.
     To ensure it's installed with correct version you can create the following task:
     I(pip: name=openshift version=0.8.2)"
'''
