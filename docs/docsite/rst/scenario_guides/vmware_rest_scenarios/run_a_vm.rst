.. _vmware_rest_run_a_vm:

****************************
How to run a virtual machine
****************************

.. contents::
  :local:


Introduction
============

This section covers the power management of your virtual machine.

Power information
=================

Use ``vcenter_vm_power_info`` to know the power state of the VM.

.. literalinclude:: task_outputs/Get_guest_power_information.task.yaml

Result
______

.. literalinclude:: task_outputs/Get_guest_power_information.result.json


How to start a virtual machine
==============================

Use the ``vcenter_vm_power`` module to start your VM:

.. literalinclude:: task_outputs/Turn_the_power_of_the_VM_on.task.yaml

Result
______

.. literalinclude:: task_outputs/Turn_the_power_of_the_VM_on.result.json

How to wait until my virtual machine is ready
=============================================

If your virtual machine runs VMware Tools, you can build a loop
around the ``center_vm_tools_info`` module:

.. literalinclude:: task_outputs/Wait_until_my_VM_is_ready.task.yaml

Result
______

.. literalinclude:: task_outputs/Wait_until_my_VM_is_ready.result.json
