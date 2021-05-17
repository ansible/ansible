.. _vmware-rest-vm-hardware-tuning:


How to modify a virtual machine
*******************************

*  Introduction

*  Scenario requirements

*  How to add a CDROM drive to a virtual machine

   *  Add a new SATA adapter

   *  Add a CDROM drive

*  How to attach a VM to a network

   *  Attach a new NIC

   *  Adjust the configuration of the NIC

*  Increase the memory of the VM

*  Upgrade the hardware version of the VM

*  Adjust the number of CPUs of the VM

*  Remove a SATA controller

*  Attach a floppy drive

*  Attach a new disk


Introduction
============

This section shows you how to use Ansible to modify an existing
virtual machine.


Scenario requirements
=====================

You've already followed `How to create a Virtual Machine
<3_create_vm.rst#vmware-rest-create-vm>`_ and created a VM.


How to add a CDROM drive to a virtual machine
=============================================

In this example, we use the ``vcenter_vm_hardware_*`` modules to add a
new CDROM to an existing VM.


Add a new SATA adapter
----------------------

First we create a new SATA adapter. We specify the
``pci_slot_number``. This way if we run the task again it won't do
anything if there is already an adapter there.

::

   - name: Create a SATA adapter at PCI slot 34
     vmware.vmware_rest.vcenter_vm_hardware_adapter_sata:
       vm: '{{ test_vm1_info.id }}'
       pci_slot_number: 34
     register: _sata_adapter_result_1

response

::

   {
       "changed": true,
       "id": "15000",
       "value": {
           "bus": 0,
           "label": "SATA controller 0",
           "pci_slot_number": 34,
           "type": "AHCI"
       }
   }


Add a CDROM drive
-----------------

Now we can create the CDROM drive:

::

   - name: Attach an ISO image to a guest VM
     vmware.vmware_rest.vcenter_vm_hardware_cdrom:
       vm: '{{ test_vm1_info.id }}'
       type: SATA
       sata:
         bus: 0
         unit: 2
       start_connected: true
       backing:
         iso_file: '[ro_datastore] fedora.iso'
         type: ISO_FILE
     register: _result

response

::

   {
       "changed": true,
       "id": "16002",
       "value": {
           "allow_guest_control": false,
           "backing": {
               "iso_file": "[ro_datastore] fedora.iso",
               "type": "ISO_FILE"
           },
           "label": "CD/DVD drive 1",
           "sata": {
               "bus": 0,
               "unit": 2
           },
           "start_connected": true,
           "state": "NOT_CONNECTED",
           "type": "SATA"
       }
   }

.. _vmware-rest-attach-a-network:


How to attach a VM to a network
===============================


Attach a new NIC
----------------

Here we attach the VM to the network (through the portgroup). We
specify a ``pci_slot_number`` for the same reason.

The second task adjusts the NIC configuration.

::

   - name: Attach a VM to a dvswitch
     vmware.vmware_rest.vcenter_vm_hardware_ethernet:
       vm: '{{ test_vm1_info.id }}'
       pci_slot_number: 4
       backing:
         type: DISTRIBUTED_PORTGROUP
         network: "{{ my_portgroup_info.dvs_portgroup_info.dvswitch1[0].key }}"
       start_connected: false
     register: vm_hardware_ethernet_1

response

::

   {
       "changed": true,
       "id": "4000",
       "value": {
           "allow_guest_control": false,
           "backing": {
               "connection_cookie": 198451354,
               "distributed_port": "2",
               "distributed_switch_uuid": "50 26 0b 69 9f 31 e5 f0-5d 16 33 39 c1 d6 73 3f",
               "network": "dvportgroup-1103",
               "type": "DISTRIBUTED_PORTGROUP"
           },
           "label": "Network adapter 1",
           "mac_address": "00:50:56:a6:b5:5c",
           "mac_type": "ASSIGNED",
           "pci_slot_number": 4,
           "start_connected": false,
           "state": "NOT_CONNECTED",
           "type": "VMXNET3",
           "upt_compatibility_enabled": false,
           "wake_on_lan_enabled": false
       }
   }


Adjust the configuration of the NIC
-----------------------------------

::

   - name: Turn the NIC's start_connected flag on
     vmware.vmware_rest.vcenter_vm_hardware_ethernet:
       nic: '{{ vm_hardware_ethernet_1.id }}'
       start_connected: true
       vm: '{{ test_vm1_info.id }}'

response

::

   {
       "changed": true,
       "id": "4000",
       "value": {}
   }


Increase the memory of the VM
=============================

We can also adjust the amount of memory that we dedicate to our VM.

::

   - name: Increase the memory of a VM
     vmware.vmware_rest.vcenter_vm_hardware_memory:
       vm: '{{ test_vm1_info.id }}'
       size_MiB: 1080
     register: _result

response

::

   {
       "changed": true,
       "id": null,
       "value": {}
   }


Upgrade the hardware version of the VM
======================================

Here we use the ``vcenter_vm_hardware`` module to upgrade the version
of the hardware:

::

   - name: Upgrade the VM hardware version
     vmware.vmware_rest.vcenter_vm_hardware:
       upgrade_policy: AFTER_CLEAN_SHUTDOWN
       upgrade_version: VMX_13
       vm: '{{ test_vm1_info.id }}'
     register: _result

response

::

   {
       "changed": true,
       "id": null,
       "value": {}
   }


Adjust the number of CPUs of the VM
===================================

You can use ``vcenter_vm_hardware_cpu`` for that:

::

   - name: Dedicate one core to the VM
     vmware.vmware_rest.vcenter_vm_hardware_cpu:
       vm: '{{ test_vm1_info.id }}'
       count: 1
     register: _result

response

::

   {
       "changed": false,
       "id": null,
       "value": {
           "cores_per_socket": 1,
           "count": 1,
           "hot_add_enabled": false,
           "hot_remove_enabled": false
       }
   }


Remove a SATA controller
========================

In this example, we remove the SATA controller of the PCI slot 34.

::

   - name: Dedicate one core to the VM
     vmware.vmware_rest.vcenter_vm_hardware_cpu:
       vm: '{{ test_vm1_info.id }}'
       count: 1
     register: _result

response

::

   {
       "changed": false,
       "id": null,
       "value": {
           "cores_per_socket": 1,
           "count": 1,
           "hot_add_enabled": false,
           "hot_remove_enabled": false
       }
   }


Attach a floppy drive
=====================

Here we attach a floppy drive to a VM.

::

   - name: Add a floppy disk drive
     vmware.vmware_rest.vcenter_vm_hardware_floppy:
       vm: '{{ test_vm1_info.id }}'
       allow_guest_control: true
     register: my_floppy_drive

response

::

   {
       "changed": true,
       "id": "8000",
       "value": {
           "allow_guest_control": true,
           "backing": {
               "auto_detect": true,
               "host_device": "",
               "type": "HOST_DEVICE"
           },
           "label": "Floppy drive 1",
           "start_connected": false,
           "state": "NOT_CONNECTED"
       }
   }


Attach a new disk
=================

Here we attach a tiny disk to the VM. The ``capacity`` is in bytes.

::

   - name: Create a new disk
     vmware.vmware_rest.vcenter_vm_hardware_disk:
       vm: '{{ test_vm1_info.id }}'
       type: SATA
       new_vmdk:
         capacity: 320000
     register: my_new_disk

response

::

   {
       "changed": true,
       "id": "16000",
       "value": {
           "backing": {
               "type": "VMDK_FILE",
               "vmdk_file": "[rw_datastore] test_vm1/test_vm1_1.vmdk"
           },
           "capacity": 320000,
           "label": "Hard disk 2",
           "sata": {
               "bus": 0,
               "unit": 0
           },
           "type": "SATA"
       }
   }
