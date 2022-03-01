.. _vmware_rest_vm_tool_configuration:

**************************************************************
How to configure the VMware tools of a running virtual machine 
**************************************************************

.. contents::
  :local:


Introduction
============

This section show you how to collection information from a running virtual machine.

Scenario requirements
=====================

You've already followed :ref:`vmware_rest_run_a_vm` and your virtual machine runs VMware Tools.

How to change the upgrade policy
================================

Change the upgrade policy to MANUAL
---------------------------------------------------

You can adjust the VMware Tools upgrade policy with the ``vcenter_vm_tools`` module.

.. literalinclude:: task_outputs/Change_vm-tools_upgrade_policy_to_MANUAL.task.yaml

Result
______

.. literalinclude:: task_outputs/Change_vm-tools_upgrade_policy_to_MANUAL.result.json


Change the upgrade policy to UPGRADE_AT_POWER_CYCLE 
------------------------------------------------------------------------------------------

.. literalinclude:: task_outputs/Change_vm-tools_upgrade_policy_to_UPGRADE_AT_POWER_CYCLE.task.yaml

Result
______

.. literalinclude:: task_outputs/Change_vm-tools_upgrade_policy_to_UPGRADE_AT_POWER_CYCLE.result.json
