.. _vmware-rest-vm-info:


Retrieve information from a specific VM
***************************************

*  Introduction

*  Scenario requirements

*  How to collect virtual machine information

   *  List the VM

   *  Collect the details about a specific VM

   *  Get the hardware version of a specific VM

   *  List the SCSI adapter(s) of a specific VM

   *  List the CDROM drive(s) of a specific VM

   *  Get the memory information of the VM

      *  Get the storage policy of the VM

      *  Get the disk information of the VM


Introduction
============

This section shows you how to use Ansible to retrieve information
about a specific virtual machine.


Scenario requirements
=====================

You've already followed `How to create a Virtual Machine
<3_create_vm.rst#vmware-rest-create-vm>`_ and you've got create a new
VM called ``test_vm1``.


How to collect virtual machine information
==========================================


List the VM
-----------

In this example, we use the ``vcenter_vm_info`` module to collect
information about our new VM.

In this example, we start by asking for a list of VMs. We use a filter
to limit the results to just the VM called ``test_vm1``. So we are in
a list context, with one single entry in the ``value`` key.

::

   - name: Look up the VM called test_vm1 in the inventory
     vmware.vmware_rest.vcenter_vm_info:
       filter_names:
         - test_vm1
     register: search_result

response

::

   {
       "changed": false,
       "value": [
           {
               "cpu_count": 1,
               "memory_size_MiB": 1024,
               "name": "test_vm1",
               "power_state": "POWERED_OFF",
               "vm": "vm-1104"
           }
       ]
   }

As expected, we get a list. And thanks to our filter, we just get one
entry.


Collect the details about a specific VM
---------------------------------------

For the next steps, we pass the ID of the VM through the ``vm``
parameter. This allow us to collect more details about this specific
VM.

::

   - name: Collect information about a specific VM
     vmware.vmware_rest.vcenter_vm_info:
       vm: '{{ search_result.value[0].vm }}'
     register: test_vm1_info

response

::

   {
       "changed": false,
       "id": "vm-1104",
       "value": {
           "boot": {
               "delay": 0,
               "enter_setup_mode": false,
               "retry": false,
               "retry_delay": 10000,
               "type": "BIOS"
           },
           "boot_devices": [],
           "cdroms": {},
           "cpu": {
               "cores_per_socket": 1,
               "count": 1,
               "hot_add_enabled": false,
               "hot_remove_enabled": false
           },
           "disks": {
               "2000": {
                   "backing": {
                       "type": "VMDK_FILE",
                       "vmdk_file": "[rw_datastore] test_vm1/test_vm1.vmdk"
                   },
                   "capacity": 17179869184,
                   "label": "Hard disk 1",
                   "scsi": {
                       "bus": 0,
                       "unit": 0
                   },
                   "type": "SCSI"
               }
           },
           "floppies": {},
           "guest_OS": "DEBIAN_8_64",
           "hardware": {
               "upgrade_policy": "NEVER",
               "upgrade_status": "NONE",
               "version": "VMX_11"
           },
           "identity": {
               "bios_uuid": "422675cc-b9c3-1350-80bb-12e6237823fe",
               "instance_uuid": "50266be8-5d4f-06f4-67e9-b4402867aa15",
               "name": "test_vm1"
           },
           "instant_clone_frozen": false,
           "memory": {
               "hot_add_enabled": true,
               "size_MiB": 1024
           },
           "name": "test_vm1",
           "nics": {},
           "nvme_adapters": {},
           "parallel_ports": {},
           "power_state": "POWERED_OFF",
           "sata_adapters": {},
           "scsi_adapters": {
               "1000": {
                   "label": "SCSI controller 0",
                   "scsi": {
                       "bus": 0,
                       "unit": 7
                   },
                   "sharing": "NONE",
                   "type": "PVSCSI"
               }
           },
           "serial_ports": {}
       }
   }

The result is a structure with all the details about our VM. You will
note this is actually the same information that we get when we created
the VM.


Get the hardware version of a specific VM
-----------------------------------------

We can also use all the ``vcenter_vm_*_info`` modules to retrieve a
smaller amount of information. Here we use
``vcenter_vm_hardware_info`` to know the hardware version of the VM.

::

   - name: Collect the hardware information
     vmware.vmware_rest.vcenter_vm_hardware_info:
       vm: '{{ search_result.value[0].vm }}'
     register: my_vm1_hardware_info

response

::

   {
       "changed": false,
       "value": {
           "upgrade_policy": "NEVER",
           "upgrade_status": "NONE",
           "version": "VMX_11"
       }
   }


List the SCSI adapter(s) of a specific VM
-----------------------------------------

Here for instance, we list the SCSI adapter(s) of the VM:

::

   - name: List the SCSI adapter of a given VM
     vmware.vmware_rest.vcenter_vm_hardware_adapter_scsi_info:
       vm: '{{ test_vm1_info.id }}'
     register: _result

response

::

   {
       "changed": false,
       "value": [
           {
               "label": "SCSI controller 0",
               "scsi": {
                   "bus": 0,
                   "unit": 7
               },
               "sharing": "NONE",
               "type": "PVSCSI"
           }
       ]
   }

You can do the same for the SATA controllers with
``vcenter_vm_adapter_sata_info``.


List the CDROM drive(s) of a specific VM
----------------------------------------

And we list its CDROM drives.

::

   - name: List the cdrom devices on the guest
     vmware.vmware_rest.vcenter_vm_hardware_cdrom_info:
       vm: '{{ test_vm1_info.id }}'
     register: _result

response

::

   {
       "changed": false,
       "value": []
   }


Get the memory information of the VM
------------------------------------

Here we collect the memory information of the VM:

::

   - name: Retrieve the memory information from the VM
     vmware.vmware_rest.vcenter_vm_hardware_memory_info:
       vm: '{{ test_vm1_info.id }}'
     register: _result

response

::

   {
       "changed": false,
       "value": {
           "hot_add_enabled": true,
           "size_MiB": 1024
       }
   }


Get the storage policy of the VM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We use the ``vcenter_vm_storage_policy_info`` module for that:

::

   - name: Get VM storage policy
     vmware.vmware_rest.vcenter_vm_storage_policy_info:
       vm: '{{ test_vm1_info.id }}'
     register: _result

response

::

   {
       "changed": false,
       "value": {
           "disks": {}
       }
   }


Get the disk information of the VM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We use the ``vcenter_vm_hardware_disk_info`` for this operation:

::

   - name: Retrieve the disk information from the VM
     vmware.vmware_rest.vcenter_vm_hardware_disk_info:
       vm: '{{ test_vm1_info.id }}'
     register: _result

response

::

   {
       "changed": false,
       "value": [
           {
               "backing": {
                   "type": "VMDK_FILE",
                   "vmdk_file": "[rw_datastore] test_vm1/test_vm1.vmdk"
               },
               "capacity": 17179869184,
               "label": "Hard disk 1",
               "scsi": {
                   "bus": 0,
                   "unit": 0
               },
               "type": "SCSI"
           }
       ]
   }
