.. _vmware-rest-vm-tool-information:


How to get information from a running virtual machine
*****************************************************

*  Introduction

*  Scenario requirements

*  How to collect information

   *  Filesystem

   *  Guest identity

   *  Network

   *  Network interfaces

   *  Network routes


Introduction
============

This section shows you how to collection information from a running
virtual machine.


Scenario requirements
=====================

You've already followed `How to run a virtual machine
<6_run_a_vm.rst#vmware-rest-run-a-vm>`_ and your virtual machine runs
VMware Tools.


How to collect information
==========================

In this example, we use the ``vcenter_vm_guest_*`` module to collect
information about the associated resources.


Filesystem
----------

Here we use ``vcenter_vm_guest_localfilesystem_info`` to retrieve the
details about the filesystem of the guest. In this example we also use
a ``retries`` loop. The VMware Tools may take a bit of time to start
and by doing so, we give the VM a bit more time.

::

   - name: Get guest filesystem information
     vmware.vmware_rest.vcenter_vm_guest_localfilesystem_info:
       vm: '{{ test_vm1_info.id }}'
     register: _result
     until:
     - _result is not failed
     retries: 60
     delay: 5

response

::

   {
       "attempts": 1,
       "changed": false,
       "value": {
           "error_type": "SERVICE_UNAVAILABLE",
           "messages": [
               {
                   "args": [
                       "vm-1104:059dd233-dedf-4960-bba8-ab6710e6aeb4"
                   ],
                   "default_message": "VMware Tools in the virtual machine with identifier 'vm-1104:059dd233-dedf-4960-bba8-ab6710e6aeb4' provided no information.",
                   "id": "com.vmware.api.vcenter.vm.guest.information_not_available"
               }
           ]
       }
   }


Guest identity
--------------

You can use ``vcenter_vm_guest_identity_info`` to get details like the
OS family or the hostname of the running VM.

::

   - name: Get guest identity information
     vmware.vmware_rest.vcenter_vm_guest_identity_info:
       vm: '{{ test_vm1_info.id }}'
     register: _result

response

::

   {
       "changed": false,
       "value": {
           "error_type": "SERVICE_UNAVAILABLE",
           "messages": [
               {
                   "args": [
                       "vm-1104:059dd233-dedf-4960-bba8-ab6710e6aeb4"
                   ],
                   "default_message": "VMware Tools in the virtual machine with identifier 'vm-1104:059dd233-dedf-4960-bba8-ab6710e6aeb4' provided no information.",
                   "id": "com.vmware.api.vcenter.vm.guest.information_not_available"
               }
           ]
       }
   }


Network
-------

``vcenter_vm_guest_networking_info`` will return the OS network
configuration.

::

   - name: Get guest networking information
     vmware.vmware_rest.vcenter_vm_guest_networking_info:
       vm: '{{ test_vm1_info.id }}'
     register: _result

response

::

   {
       "changed": false,
       "value": {}
   }


Network interfaces
------------------

``vcenter_vm_guest_networking_interfaces_info`` will return a list of
NIC configurations.

See also `How to attach a VM to a network
<5_vm_hardware_tuning.rst#vmware-rest-attach-a-network>`_.

::

   - name: Get guest network interfaces information
     vmware.vmware_rest.vcenter_vm_guest_networking_interfaces_info:
       vm: '{{ test_vm1_info.id }}'
     register: _result

response

::

   {
       "changed": false,
       "value": []
   }


Network routes
--------------

Use ``vcenter_vm_guest_networking_routes_info`` to explore the route
table of your vitual machine.

::

   - name: Get guest network routes information
     vmware.vmware_rest.vcenter_vm_guest_networking_routes_info:
       vm: '{{ test_vm1_info.id }}'
     register: _result

response

::

   {
       "changed": false,
       "value": []
   }
