.. _vmware-rest-appliance-shutdown:


System managment
****************


How to reboot or shutdown the VCSA
==================================

You can use Ansible to trigger or cancel a shutdown. The
appliance_shutdown_info module is useful to know if a shutdown is
already scheduled.

::

   - name: Check if there is a shutdown scheduled
     vmware.vmware_rest.appliance_shutdown_info:

response

::

   {
       "changed": false,
       "value": {
           "action": "",
           "reason": ""
       }
   }

When you trigger a shutdown, you can also specify a ``reason``. The
information will be exposed to the other users:

::

   - name: Shutdown the appliance
     vmware.vmware_rest.appliance_shutdown:
       state: poweroff
       reason: this is an example
       delay: 600

response

::

   {
       "changed": false,
       "value": {}
   }

To cancel a shutdown, you must set the ``state`` to ``cancel``:

::

   - name: Abort the shutdown of the appliance
     vmware.vmware_rest.appliance_shutdown:
       state: cancel

response

::

   {
       "changed": false,
       "value": {}
   }


FIPS mode
*********


Federal Information Processing Standards (FIPS)
===============================================

The appliance_system_globalfips_info module will tell you if FIPS is
enabled.

::

   - name: "Get the status of the Federal Information Processing Standard mode"
     vmware.vmware_rest.appliance_system_globalfips_info:

response

::

   {
       "changed": false,
       "value": {
           "enabled": false
       }
   }

You can turn the option on or off with appliance_system_globalfips:

Warning: The VCSA will silently reboot itself if you change the FIPS
   configuration.

::

   - name: Turn off the FIPS mode and reboot
     vmware.vmware_rest.appliance_system_globalfips:
       enabled: false

response

::

   {
       "changed": false,
       "id": null,
       "value": {
           "enabled": false
       }
   }


Time and Timezone configuration
*******************************


Timezone
========

The appliance_system_time_timezone and
ppliance_system_time_timezone_info modules handle the Timezone
configuration. You can get the current configuration with:

::

   - name: Get the timezone configuration
     vmware.vmware_rest.appliance_system_time_timezone_info:

response

::

   {
       "changed": false,
       "value": "UTC"
   }

And to adjust the system's timezone, just do:

::

   - name: Use the UTC timezone
     vmware.vmware_rest.appliance_system_time_timezone:
       name: UTC

response

::

   {
       "changed": false,
       "value": "UTC"
   }

In this example we set the ``UTC`` timezone, you can also pass a
timezone in the ``Europe/Paris`` format.


Current time
============

If you want to get the current time, use appliance_system_time_info:

::

   - name: Get the current time
     vmware.vmware_rest.appliance_system_time_info:

response

::

   {
       "changed": false,
       "value": {
           "date": "Mon 05-17-2021",
           "seconds_since_epoch": 1621262229.576272,
           "time": "02:37:09 PM",
           "timezone": "UTC"
       }
   }


Time Service (NTP)
==================

The VCSA can get the time from a NTP server:

::

   - name: Get the NTP configuration
     vmware.vmware_rest.appliance_ntp_info:

response

::

   {
       "changed": false,
       "value": [
           "time.google.com"
       ]
   }

You can use the appliance_ntp module to adjust the system NTP servers.
The module accepts one or more NTP servers:

::

   - name: Adjust the NTP configuration
     vmware.vmware_rest.appliance_ntp:
       servers:
         - time.google.com

response

::

   {
       "changed": false,
       "value": [
           "time.google.com"
       ]
   }

If you set ``state=test``, the module will validate the servers are
rechable.

::

   - name: Test the NTP configuration
     vmware.vmware_rest.appliance_ntp:
       state: test
       servers:
         - time.google.com

response

::

   {
       "changed": false,
       "value": [
           {
               "message": {
                   "args": [],
                   "default_message": "NTP Server is reachable.",
                   "id": "com.vmware.appliance.ntp_sync.success"
               },
               "server": "time.google.com",
               "status": "SERVER_REACHABLE"
           }
       ]
   }

You can check the clock synchronization with appliance_timesync_info:

::

   - name: Get information regarding the clock synchronization
     vmware.vmware_rest.appliance_timesync_info:

response

::

   {
       "changed": false,
       "value": "NTP"
   }

Or also validate the system use NTP with:

::

   - name: Ensure we use NTP
     vmware.vmware_rest.appliance_timesync:
       mode: NTP

response

::

   {
       "changed": false,
       "value": "NTP"
   }


Storage system
**************

The collection also provides modules to manage the storage system.
appliance_system_storage_info will list the storage partitions:

::

   - name: Get the appliance storage information
     vmware.vmware_rest.appliance_system_storage_info:

response

::

   {
       "changed": false,
       "value": []
   }

You can use the ``state=resize_ex`` option to extend an existing
partition:

::

   - name: Resize the first partition and return the state of the partition before and after the operation
     vmware.vmware_rest.appliance_system_storage:
       state: resize_ex

response

::

   {
       "changed": false,
       "value": {}
   }

Note: ``state=resize`` also works, but you won't get as much information
   as with ``resize_ex``.
