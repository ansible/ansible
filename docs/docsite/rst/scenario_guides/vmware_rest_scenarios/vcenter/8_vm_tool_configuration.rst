.. _vmware-rest-vm-tool-configuration:


How to configure the VMware tools of a running virtual machine
**************************************************************

*  Introduction

*  Scenario requirements

*  How to change the upgrade policy

   *  Change the upgrade policy to MANUAL

   *  Change the upgrade policy to UPGRADE_AT_POWER_CYCLE


Introduction
============

This section show you how to collection information from a running
virtual machine.


Scenario requirements
=====================

You've already followed `How to run a virtual machine
<6_run_a_vm.rst#vmware-rest-run-a-vm>`_ and your virtual machine runs
VMware Tools.


How to change the upgrade policy
================================


Change the upgrade policy to MANUAL
-----------------------------------

You can adjust the VMware Tools upgrade policy with the
``vcenter_vm_tools`` module.

::

   - name: Change vm-tools upgrade policy to MANUAL
     vmware.vmware_rest.vcenter_vm_tools:
       vm: '{{ test_vm1_info.id }}'
       upgrade_policy: MANUAL
     register: _result

response

::

   {
       "changed": false,
       "id": null,
       "value": {
           "auto_update_supported": false,
           "install_attempt_count": 0,
           "install_type": "OPEN_VM_TOOLS",
           "run_state": "RUNNING",
           "upgrade_policy": "MANUAL",
           "version": "10346",
           "version_number": 10346,
           "version_status": "UNMANAGED"
       }
   }


Change the upgrade policy to UPGRADE_AT_POWER_CYCLE
---------------------------------------------------

::

   - name: Change vm-tools upgrade policy to UPGRADE_AT_POWER_CYCLE
     vmware.vmware_rest.vcenter_vm_tools:
       vm: '{{ test_vm1_info.id }}'
       upgrade_policy: UPGRADE_AT_POWER_CYCLE
     register: _result

response

::

   {
       "changed": true,
       "id": null,
       "value": {}
   }
