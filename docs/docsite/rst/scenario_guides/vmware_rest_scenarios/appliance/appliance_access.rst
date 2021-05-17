.. _vmware-rest-appliance-access:


Configure the console and SSH access
************************************


Introduction
============

This section show you how to manage the console and SSH access of the
vCenter Server Appliance (VCSA).


Scenario requirements
=====================

You've got an up and running vCenter Server Appliance.


Manage the shell access
-----------------------

Detect if the Shell is enabled.

::

   - name: Check if the Shell is enabled
     vmware.vmware_rest.appliance_access_shell_info:

response

::

   {
       "changed": false,
       "value": {
           "enabled": false,
           "timeout": 0
       }
   }

Or turn on the Shell access with a timeout:

::

   - name: Disable the Shell
     vmware.vmware_rest.appliance_access_shell:
       enabled: False
       timeout: 600

response

::

   {
       "changed": false,
       "value": {
           "enabled": false,
           "timeout": 0
       }
   }


Manage the Direct Console User Interface (DCUI)
-----------------------------------------------

You can use `vmware.vmware_rest.appliance_access_dcui_info
<../../docs/vmware.vmware_rest.appliance_access_dcui_info_module.rst#vmware-vmware-rest-appliance-access-dcui-info-module>`_
to get the current state of the configuration:

::

   - name: Check if the Direct Console User Interface is enabled
     vmware.vmware_rest.appliance_access_dcui_info:

response

::

   {
       "changed": false,
       "value": false
   }

You can enable or disable the interface with appliance_access_dcui:

::

   - name: Disable the Direct Console User Interface
     vmware.vmware_rest.appliance_access_dcui:
       enabled: False

response

::

   {
       "changed": false,
       "value": false
   }


Manage the SSH interface
------------------------

You can also get the status of the SSH interface with
appliance_access_ssh_info:

::

   - name: Check is the SSH access is enabled
     vmware.vmware_rest.appliance_access_ssh_info:

response

::

   {
       "changed": false,
       "value": true
   }

And to enable the SSH interface:

::

   - name: Ensure the SSH access ie enabled
     vmware.vmware_rest.appliance_access_ssh:
       enabled: true

response

::

   {
       "changed": false,
       "value": true
   }
