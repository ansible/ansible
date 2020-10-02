.. _vmware_rest_vm_hardware_tuning:

*******************************
How to modify a Virtual Machine
*******************************

.. contents:: Topics

Introduction
============

This guide will show you how to utilize Ansible to modify an existing virtual machine.

Scenario Requirements
=====================

You've already followed :ref:`vmware_rest_create_vm` and you've already created a VM.

How to add a CDROM drive to Virtual Machine
===========================================

In this examples, we will use the ``vcenter_vm_hardware_*`` modules to add a new CDROM to an existing VM.

Add a new SATA adapter
______________________

First we create a new SATA adapter. We specify the ``pci_slot_number``, this way if we run the task again it won't do anything if there is already an adapter there.

.. literalinclude:: task_outputs/Create_a_SATA_adapter_at_PCI_slot_34.task.yaml

Result
______

.. literalinclude:: task_outputs/Create_a_SATA_adapter_at_PCI_slot_34.result.json

Add a CDROM drive
_________________

Now I can create my CDROM drive:

.. literalinclude:: task_outputs/Attach_an_ISO_image_to_a_guest_VM.task.yaml

Result
______

.. literalinclude:: task_outputs/Attach_an_ISO_image_to_a_guest_VM.result.json


.. _vmware_rest_attach_a_network:

How to attach a VM to a network
===============================

Attach a new NIC
________________

Here we attach the VM to network (via the portgroup). We specifc a ``pci_slot_number`` for the same reason.

The second task adjust the NIC configuration.

.. literalinclude:: task_outputs/Attach_a_VM_to_a_dvswitch.task.yaml

Result
______

.. literalinclude:: task_outputs/Attach_a_VM_to_a_dvswitch.result.json

Adjust the configuration of the NIC
___________________________________

.. literalinclude:: task_outputs/Turn_the_NIC's_start_connected_flag_on.task.yaml

Result
______

.. literalinclude:: task_outputs/Turn_the_NIC's_start_connected_flag_on.result.json

Increase the memory of the VM
=============================

We can also adjust the amount of memory that we dedicate to our VM.

.. literalinclude:: task_outputs/Increase_the_memory_of_a_VM.task.yaml

Result
______

.. literalinclude:: task_outputs/Increase_the_memory_of_a_VM.result.json

Upgrade the hardware version of the VM
======================================

Here we use the ``vcenter_vm_hardware`` to upgrade the version of the hardware: 

.. literalinclude:: task_outputs/Upgrade_the_VM_hardware_version.task.yaml

Result
______

.. literalinclude:: task_outputs/Upgrade_the_VM_hardware_version.result.json

Adjust the number of CPU of the VM
==================================

You can use ``vcenter_vm_hardware_cpu`` for that:

.. literalinclude:: task_outputs/Dedicate_one_core_to_the_VM.task.yaml

Result
______

.. literalinclude:: task_outputs/Dedicate_one_core_to_the_VM.result.json

Remove a SATA controller
========================

In this example, we remove the SATA controller of the PCI slot 34.

.. literalinclude:: task_outputs/Remove_SATA_adapter_at_PCI_slot_34.result.json

Result
______

.. literalinclude:: task_outputs/Remove_SATA_adapter_at_PCI_slot_34.result.json

Attach a floppy drive
=====================

Here we attach a floppy drive to a VM.

.. literalinclude:: task_outputs/Add_a_floppy_disk_drive.task.yaml

Result
______

.. literalinclude:: task_outputs/Add_a_floppy_disk_drive.result.json

Attach a new disk
=================

Here we attach a tiny disk to the VM. The ``capacity`` is in bytes.

.. literalinclude:: task_outputs/Create_a_new_disk.task.yaml

Result
______

.. literalinclude:: task_outputs/Create_a_new_disk.result.json
