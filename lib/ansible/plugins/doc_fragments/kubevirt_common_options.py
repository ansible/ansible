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
    memory_limit:
        description:
            - The maximum memory to be used by virtual machine.
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
    cpu_shares:
        description:
            - "Specify CPU shares."
        type: int
    cpu_limit:
        description:
            - "Is converted to its millicore value and multiplied by 100. The resulting value is the total amount of CPU time that a container can use
               every 100ms. A virtual machine cannot use more than its share of CPU time during this interval."
        type: int
    cpu_cores:
        description:
            - "Number of CPU cores."
        type: int
    cpu_model:
        description:
            - "CPU model."
            - "You can check list of available models here: U(https://github.com/libvirt/libvirt/blob/master/src/cpu_map/index.xml)."
            - "I(Note:) User can define default CPU model via as I(default-cpu-model) in I(kubevirt-config) I(ConfigMap), if not set I(host-model) is used."
            - "I(Note:) Be sure that node CPU model where you run a VM, has the same or higher CPU family."
            - "I(Note:) If CPU model wasn't defined, the VM will have CPU model closest to one that used on the node where the VM is running."
        type: str
    bootloader:
        description:
            - "Specify the bootloader of the virtual machine."
            - "All virtual machines use BIOS by default for booting."
        type: str
    smbios_uuid:
        description:
            - "In order to provide a consistent view on the virtualized hardware for the guest OS, the SMBIOS UUID can be set."
        type: str
    cpu_features:
        description:
            - "List of dictionary to fine-tune features provided by the selected CPU model."
            - "I(Note): Policy attribute can either be omitted or contain one of the following policies: force, require, optional, disable, forbid."
            - "I(Note): In case a policy is omitted for a feature, it will default to require."
            - "More information about policies: U(https://libvirt.org/formatdomain.html#elementsCPU)"
        type: list
    headless:
        description:
            - "Specify if the virtual machine should have attached a  minimal Video and Graphics device configuration."
            - "By default a minimal Video and Graphics device configuration will be applied to the VirtualMachineInstance. The video device is vga
               compatible and comes with a memory size of 16 MB."
    hugepage_size:
        description:
            - "Specify huge page size."
        type: str
    tablets:
        description:
            - "Specify tablets to be used as input devices"
        type: list
requirements:
    - python >= 2.7
    - openshift >= 0.8.2
notes:
  - "In order to use this module you have to install Openshift Python SDK.
     To ensure it's installed with correct version you can create the following task:
     I(pip: name=openshift version=0.8.2)"
'''
