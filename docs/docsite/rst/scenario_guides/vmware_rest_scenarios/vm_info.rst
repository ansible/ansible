.. _vmware_rest_vm_info:

***************************************
Retrieve information from a specific VM
***************************************

.. contents::
  :local:


Introduction
============

This section shows you how to use Ansible to retrieve information about a specific virtual machine.

Scenario requirements
=====================

You've already followed :ref:`vmware_rest_create_vm` and you've got create a new VM called ``test_vm1``.

How to collect virtual machine information
==========================================

List the VM
___________

In this example, we use the ``vcenter_vm_info`` module to collect information about our new VM.

In this example, we start by asking for a list of VMs. We use a filter to limit the results to just the VM called ``test_vm1``. So we are in a list context, with one single entry in the ``value`` key.

.. literalinclude:: task_outputs/Look_up_the_VM_called_test_vm1_in_the_inventory.task.yaml

Result
______

As expected, we get a list. And thanks to our filter, we just get one entry.

.. literalinclude:: task_outputs/Look_up_the_VM_called_test_vm1_in_the_inventory.result.json

Collect the details about a specific VM
_______________________________________

For the next steps, we pass the ID of the VM through the ``vm`` parameter. This allow us to collect more details about this specific VM.

.. literalinclude:: task_outputs/Collect_information_about_a_specific_VM.task.yaml

Result
______

The result is a structure with all the details about our VM. You will note this is actually the same information that we get when we created the VM.

.. literalinclude:: task_outputs/Collect_information_about_a_specific_VM.result.json


Get the hardware version of a specific VM
_________________________________________

We can also use all the ``vcenter_vm_*_info`` modules to retrieve a smaller amount
of information. Here we use ``vcenter_vm_hardware_info`` to know the hardware version of
the VM.

.. literalinclude:: task_outputs/Collect_the_hardware_information.task.yaml

Result
______

.. literalinclude:: task_outputs/Collect_the_hardware_information.result.json

List the SCSI adapter(s) of a specific VM
_________________________________________

Here for instance, we list the SCSI adapter(s) of the VM:

.. literalinclude:: task_outputs/List_the_SCSI_adapter_of_a_given_VM.task.yaml

You can do the same for the SATA controllers with ``vcenter_vm_adapter_sata_info``. 

Result
______

.. literalinclude:: task_outputs/List_the_SCSI_adapter_of_a_given_VM.result.json

List the CDROM drive(s) of a specific VM
________________________________________

And we list its CDROM drives.

.. literalinclude:: task_outputs/List_the_cdrom_devices_on_the_guest.task.yaml

Result
______

.. literalinclude:: task_outputs/List_the_cdrom_devices_on_the_guest.result.json

Get the memory information of the VM
____________________________________

Here we collect the memory information of the VM:

.. literalinclude:: task_outputs/Retrieve_the_memory_information_from_the_VM.task.yaml

Result
______

.. literalinclude:: task_outputs/Retrieve_the_memory_information_from_the_VM.result.json

Get the storage policy of the VM
--------------------------------

We use the ``vcenter_vm_storage_policy_info`` module for that:

.. literalinclude:: task_outputs/Get_VM_storage_policy.task.yaml

Result
______

.. literalinclude:: task_outputs/Get_VM_storage_policy.result.json

Get the disk information of the VM
----------------------------------

We use the ``vcenter_vm_hardware_disk_info`` for this operation:

.. literalinclude:: task_outputs/Retrieve_the_disk_information_from_the_VM.task.yaml

Result
______

.. literalinclude:: task_outputs/Retrieve_the_disk_information_from_the_VM.result.json
