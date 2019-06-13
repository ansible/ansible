# -*- coding: utf-8 -*-

# Copyright: (c) 2018, KubeVirt Team <@kubevirt>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


class ModuleDocFragment(object):

    # Standard oVirt documentation fragment
    DOCUMENTATION = r'''
options:
    disks:
        description:
            - List of dictionaries which specify disks of the virtual machine.
            - "A disk can be made accessible via four different types: I(disk), I(lun), I(cdrom), I(floppy)."
            - "All possible configuration options are available in U(https://kubevirt.io/api-reference/master/definitions.html#_v1_disk)"
            - Each disk must have specified a I(volume) that declares which volume type of the disk
              All possible configuration options of volume are available in U(https://kubevirt.io/api-reference/master/definitions.html#_v1_volume).
        type: list
    labels:
        description:
            - Labels are key/value pairs that are attached to virtual machines. Labels are intended to be used to
              specify identifying attributes of virtual machines that are meaningful and relevant to users, but do not directly
              imply semantics to the core system. Labels can be used to organize and to select subsets of virtual machines.
              Labels can be attached to virtual machines at creation time and subsequently added and modified at any time.
            - More on labels that are used for internal implementation U(https://kubevirt.io/user-guide/#/misc/annotations_and_labels)
        type: dict
    interfaces:
        description:
            - An interface defines a virtual network interface of a virtual machine (also called a frontend).
            - All possible configuration options interfaces are available in U(https://kubevirt.io/api-reference/master/definitions.html#_v1_interface)
            - Each interface must have specified a I(network) that declares which logical or physical device it is connected to (also called as backend).
              All possible configuration options of network are available in U(https://kubevirt.io/api-reference/master/definitions.html#_v1_network).
        type: list
    cloud_init_nocloud:
        description:
            - "Represents a cloud-init NoCloud user-data source. The NoCloud data will be added
               as a disk to the virtual machine. A proper cloud-init installation is required inside the guest.
               More information U(https://kubevirt.io/api-reference/master/definitions.html#_v1_cloudinitnocloudsource)"
        type: dict
    affinity:
        description:
            - "Describes node affinity scheduling rules for the vm."
        type: dict
        version_added: 2.9
        suboptions:
            soft:
                description:
                    - "The scheduler will prefer to schedule vms to nodes that satisfy the affinity expressions specified by this field, but it may choose a
                    node that violates one or more of the expressions. The node that is most preferred is the one with the greatest sum of weights, i.e. for
                    each node that meets all of the scheduling requirements (resource request, requiredDuringScheduling affinity expressions, etc.), compute
                    a sum by iterating through the elements of this field and adding C(weight) to the sum if the node has vms which matches the corresponding
                    C(term); the nodes with the highest sum are the most preferred."
                type: dict
            hard:
                description:
                    - "If the affinity requirements specified by this field are not met at scheduling time, the vm will not be scheduled onto the node. If
                    the affinity requirements specified by this field cease to be met at some point during vm execution (e.g. due to a vm label update), the
                    system may or may not try to eventually evict the vm from its node. When there are multiple elements, the lists of nodes corresponding to
                    each C(term) are intersected, i.e. all terms must be satisfied."
                type: dict
    node_affinity:
        description:
            - "Describes vm affinity scheduling rules e.g. co-locate this vm in the same node, zone, etc. as some other vms"
        type: dict
        version_added: 2.9
        suboptions:
            soft:
                description:
                    - "The scheduler will prefer to schedule vms to nodes that satisfy the affinity expressions specified by this field, but it may choose
                    a node that violates one or more of the expressions. The node that is most preferred is the one with the greatest sum of weights, i.e.
                    for each node that meets all of the scheduling requirements (resource request, requiredDuringScheduling affinity expressions, etc.),
                    compute a sum by iterating through the elements of this field and adding C(weight) to the sum if the node matches the corresponding
                    match_expressions; the nodes with the highest sum are the most preferred."
                type: dict
            hard:
                description:
                    - "If the affinity requirements specified by this field are not met at scheduling time, the vm will not be scheduled onto the node. If
                    the affinity requirements specified by this field cease to be met at some point during vm execution (e.g. due to an update), the system
                    may or may not try to eventually evict the vm from its node."
                type: dict
    anti_affinity:
        description:
            - "Describes vm anti-affinity scheduling rules e.g. avoid putting this vm in the same node, zone, etc. as some other vms."
        type: dict
        version_added: 2.9
        suboptions:
            soft:
                description:
                    - "The scheduler will prefer to schedule vms to nodes that satisfy the anti-affinity expressions specified by this field, but it may
                    choose a node that violates one or more of the expressions. The node that is most preferred is the one with the greatest sum of weights,
                    i.e. for each node that meets all of the scheduling requirements (resource request, requiredDuringScheduling anti-affinity expressions,
                    etc.), compute a sum by iterating through the elements of this field and adding C(weight) to the sum if the node has vms which matches
                    the corresponding C(term); the nodes with the highest sum are the most preferred."
                type: dict
            hard:
                description:
                    - "If the anti-affinity requirements specified by this field are not met at scheduling time, the vm will not be scheduled onto the node.
                    If the anti-affinity requirements specified by this field cease to be met at some point during vm execution (e.g. due to a vm label
                    update), the system may or may not try to eventually evict the vm from its node. When there are multiple elements, the lists of nodes
                    corresponding to each C(term) are intersected, i.e. all terms must be satisfied."
                type: dict
'''
