.. _vmware_rest_vm_tool_information:

*****************************************************
How to get information from a running virtual machine 
*****************************************************

.. contents::
  :local:


Introduction
============

This section shows you how to collection information from a running virtual machine.

Scenario requirements
=====================

You've already followed :ref:`vmware_rest_run_a_vm` and your virtual machine runs VMware Tools.

How to collect information
==========================

In this example, we use the ``vcenter_vm_guest_*`` module to collect information about the associated resources.

Filesystem
----------

Here we use ``vcenter_vm_guest_localfilesystem_info`` to retrieve the details
about the filesystem of the guest. In this example we also use a ``retries``
loop. The VMware Tools may take a bit of time to start and by doing so, we give
the VM a bit more time.

.. literalinclude:: task_outputs/Get_guest_filesystem_information.task.yaml

Result
______

.. literalinclude:: task_outputs/Get_guest_filesystem_information.result.json

Guest identity
--------------

You can use ``vcenter_vm_guest_identity_info`` to get details like the OS family or the hostname of the running VM.

.. literalinclude:: task_outputs/Get_guest_identity_information.task.yaml

Result
______

.. literalinclude:: task_outputs/Get_guest_identity_information.result.json

Network
-------

``vcenter_vm_guest_networking_info`` will return the OS network configuration.

.. literalinclude:: task_outputs/Get_guest_networking_information.task.yaml

Result
______

.. literalinclude:: task_outputs/Get_guest_networking_information.result.json

Network interfaces
------------------

``vcenter_vm_guest_networking_interfaces_info`` will return a list of NIC configurations.

See also :ref:`vmware_rest_attach_a_network`.

.. literalinclude:: task_outputs/Get_guest_network_interfaces_information.task.yaml

Result
______

.. literalinclude:: task_outputs/Get_guest_network_interfaces_information.result.json

Network routes
--------------

Use ``vcenter_vm_guest_networking_routes_info`` to explore the route table of your vitual machine.

.. literalinclude:: task_outputs/Get_guest_network_routes_information.task.yaml

Result
______

.. literalinclude:: task_outputs/Get_guest_network_routes_information.result.json

