.. _vmware-rest-appliance-health:


Get the health state of the VCSA components
*******************************************


Introduction
============

The collection provides several modules that you can use to know the
state of the different components of the VCSA.


Scenario requirements
=====================

You've got an up and running vCenter Server Appliance.


Health state per component
--------------------------

The database:

::

   - name: Get the database heath status
     vmware.vmware_rest.appliance_health_database_info:

response

::

   {
       "changed": false,
       "value": {
           "messages": [
               {
                   "message": {
                       "args": [],
                       "default_message": "DB state is Degraded",
                       "id": "desc"
                   },
                   "severity": "WARNING"
               }
           ],
           "status": "DEGRADED"
       }
   }

The database storage:

::

   - name: Get the database storage heath status
     vmware.vmware_rest.appliance_health_databasestorage_info:

response

::

   {
       "changed": false,
       "value": "gray"
   }

The system load:

::

   - name: Get the system load status
     vmware.vmware_rest.appliance_health_load_info:

response

::

   {
       "changed": false,
       "value": "gray"
   }

The memory usage:

::

   - name: Get the system mem status
     vmware.vmware_rest.appliance_health_mem_info:

response

::

   {
       "changed": false,
       "value": "gray"
   }

The system status:

::

   - name: Get the system health status
     vmware.vmware_rest.appliance_health_system_info:

response

::

   {
       "changed": false,
       "value": "gray"
   }

The package manager:

::

   - name: Get the health of the software package manager
     vmware.vmware_rest.appliance_health_softwarepackages_info:

response

::

   {
       "changed": false,
       "value": "gray"
   }

The storage system:

::

   - name: Get the health of the storage system
     vmware.vmware_rest.appliance_health_storage_info:

response

::

   {
       "changed": false,
       "value": "gray"
   }

The swap usage:

::

   - name: Get the health of the swap
     vmware.vmware_rest.appliance_health_swap_info:

response

::

   {
       "changed": false,
       "value": "gray"
   }


Monitoring
----------

You can also retrieve information from the VCSA monitoring backend.
First you need the name of the item. To get a full list of these
items, run:

::

   - name: Get the list of the monitored items
     vmware.vmware_rest.appliance_monitoring_info:
     register: result

response

::

   {
       "changed": false,
       "value": [
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.read.rate.dm-10",
               "id": "disk.read.rate.dm-10",
               "instance": "dm-10",
               "name": "com.vmware.applmgmt.mon.name.disk.read.rate.dm-10",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.read.rate.dm-11",
               "id": "disk.read.rate.dm-11",
               "instance": "dm-11",
               "name": "com.vmware.applmgmt.mon.name.disk.read.rate.dm-11",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.read.rate.dm-12",
               "id": "disk.read.rate.dm-12",
               "instance": "dm-12",
               "name": "com.vmware.applmgmt.mon.name.disk.read.rate.dm-12",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.read.rate.dm-13",
               "id": "disk.read.rate.dm-13",
               "instance": "dm-13",
               "name": "com.vmware.applmgmt.mon.name.disk.read.rate.dm-13",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.read.rate.dm-14",
               "id": "disk.read.rate.dm-14",
               "instance": "dm-14",
               "name": "com.vmware.applmgmt.mon.name.disk.read.rate.dm-14",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.read.rate.dm-2",
               "id": "disk.read.rate.dm-2",
               "instance": "dm-2",
               "name": "com.vmware.applmgmt.mon.name.disk.read.rate.dm-2",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.read.rate.dm-3",
               "id": "disk.read.rate.dm-3",
               "instance": "dm-3",
               "name": "com.vmware.applmgmt.mon.name.disk.read.rate.dm-3",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.read.rate.dm-4",
               "id": "disk.read.rate.dm-4",
               "instance": "dm-4",
               "name": "com.vmware.applmgmt.mon.name.disk.read.rate.dm-4",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.read.rate.dm-5",
               "id": "disk.read.rate.dm-5",
               "instance": "dm-5",
               "name": "com.vmware.applmgmt.mon.name.disk.read.rate.dm-5",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.read.rate.dm-6",
               "id": "disk.read.rate.dm-6",
               "instance": "dm-6",
               "name": "com.vmware.applmgmt.mon.name.disk.read.rate.dm-6",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.read.rate.dm-7",
               "id": "disk.read.rate.dm-7",
               "instance": "dm-7",
               "name": "com.vmware.applmgmt.mon.name.disk.read.rate.dm-7",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.read.rate.dm-8",
               "id": "disk.read.rate.dm-8",
               "instance": "dm-8",
               "name": "com.vmware.applmgmt.mon.name.disk.read.rate.dm-8",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.read.rate.dm-9",
               "id": "disk.read.rate.dm-9",
               "instance": "dm-9",
               "name": "com.vmware.applmgmt.mon.name.disk.read.rate.dm-9",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.write.rate.dm-10",
               "id": "disk.write.rate.dm-10",
               "instance": "dm-10",
               "name": "com.vmware.applmgmt.mon.name.disk.write.rate.dm-10",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.write.rate.dm-11",
               "id": "disk.write.rate.dm-11",
               "instance": "dm-11",
               "name": "com.vmware.applmgmt.mon.name.disk.write.rate.dm-11",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.write.rate.dm-12",
               "id": "disk.write.rate.dm-12",
               "instance": "dm-12",
               "name": "com.vmware.applmgmt.mon.name.disk.write.rate.dm-12",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.write.rate.dm-13",
               "id": "disk.write.rate.dm-13",
               "instance": "dm-13",
               "name": "com.vmware.applmgmt.mon.name.disk.write.rate.dm-13",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.write.rate.dm-14",
               "id": "disk.write.rate.dm-14",
               "instance": "dm-14",
               "name": "com.vmware.applmgmt.mon.name.disk.write.rate.dm-14",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.write.rate.dm-2",
               "id": "disk.write.rate.dm-2",
               "instance": "dm-2",
               "name": "com.vmware.applmgmt.mon.name.disk.write.rate.dm-2",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.write.rate.dm-3",
               "id": "disk.write.rate.dm-3",
               "instance": "dm-3",
               "name": "com.vmware.applmgmt.mon.name.disk.write.rate.dm-3",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.write.rate.dm-4",
               "id": "disk.write.rate.dm-4",
               "instance": "dm-4",
               "name": "com.vmware.applmgmt.mon.name.disk.write.rate.dm-4",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.write.rate.dm-5",
               "id": "disk.write.rate.dm-5",
               "instance": "dm-5",
               "name": "com.vmware.applmgmt.mon.name.disk.write.rate.dm-5",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.write.rate.dm-6",
               "id": "disk.write.rate.dm-6",
               "instance": "dm-6",
               "name": "com.vmware.applmgmt.mon.name.disk.write.rate.dm-6",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.write.rate.dm-7",
               "id": "disk.write.rate.dm-7",
               "instance": "dm-7",
               "name": "com.vmware.applmgmt.mon.name.disk.write.rate.dm-7",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.write.rate.dm-8",
               "id": "disk.write.rate.dm-8",
               "instance": "dm-8",
               "name": "com.vmware.applmgmt.mon.name.disk.write.rate.dm-8",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.write.rate.dm-9",
               "id": "disk.write.rate.dm-9",
               "instance": "dm-9",
               "name": "com.vmware.applmgmt.mon.name.disk.write.rate.dm-9",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.latency.rate.dm-10",
               "id": "disk.latency.rate.dm-10",
               "instance": "dm-10",
               "name": "com.vmware.applmgmt.mon.name.disk.latency.rate.dm-10",
               "units": "com.vmware.applmgmt.mon.unit.msec_per_io"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.latency.rate.dm-11",
               "id": "disk.latency.rate.dm-11",
               "instance": "dm-11",
               "name": "com.vmware.applmgmt.mon.name.disk.latency.rate.dm-11",
               "units": "com.vmware.applmgmt.mon.unit.msec_per_io"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.latency.rate.dm-12",
               "id": "disk.latency.rate.dm-12",
               "instance": "dm-12",
               "name": "com.vmware.applmgmt.mon.name.disk.latency.rate.dm-12",
               "units": "com.vmware.applmgmt.mon.unit.msec_per_io"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.latency.rate.dm-13",
               "id": "disk.latency.rate.dm-13",
               "instance": "dm-13",
               "name": "com.vmware.applmgmt.mon.name.disk.latency.rate.dm-13",
               "units": "com.vmware.applmgmt.mon.unit.msec_per_io"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.latency.rate.dm-14",
               "id": "disk.latency.rate.dm-14",
               "instance": "dm-14",
               "name": "com.vmware.applmgmt.mon.name.disk.latency.rate.dm-14",
               "units": "com.vmware.applmgmt.mon.unit.msec_per_io"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.latency.rate.dm-2",
               "id": "disk.latency.rate.dm-2",
               "instance": "dm-2",
               "name": "com.vmware.applmgmt.mon.name.disk.latency.rate.dm-2",
               "units": "com.vmware.applmgmt.mon.unit.msec_per_io"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.latency.rate.dm-3",
               "id": "disk.latency.rate.dm-3",
               "instance": "dm-3",
               "name": "com.vmware.applmgmt.mon.name.disk.latency.rate.dm-3",
               "units": "com.vmware.applmgmt.mon.unit.msec_per_io"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.latency.rate.dm-4",
               "id": "disk.latency.rate.dm-4",
               "instance": "dm-4",
               "name": "com.vmware.applmgmt.mon.name.disk.latency.rate.dm-4",
               "units": "com.vmware.applmgmt.mon.unit.msec_per_io"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.latency.rate.dm-5",
               "id": "disk.latency.rate.dm-5",
               "instance": "dm-5",
               "name": "com.vmware.applmgmt.mon.name.disk.latency.rate.dm-5",
               "units": "com.vmware.applmgmt.mon.unit.msec_per_io"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.latency.rate.dm-6",
               "id": "disk.latency.rate.dm-6",
               "instance": "dm-6",
               "name": "com.vmware.applmgmt.mon.name.disk.latency.rate.dm-6",
               "units": "com.vmware.applmgmt.mon.unit.msec_per_io"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.latency.rate.dm-7",
               "id": "disk.latency.rate.dm-7",
               "instance": "dm-7",
               "name": "com.vmware.applmgmt.mon.name.disk.latency.rate.dm-7",
               "units": "com.vmware.applmgmt.mon.unit.msec_per_io"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.latency.rate.dm-8",
               "id": "disk.latency.rate.dm-8",
               "instance": "dm-8",
               "name": "com.vmware.applmgmt.mon.name.disk.latency.rate.dm-8",
               "units": "com.vmware.applmgmt.mon.unit.msec_per_io"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.latency.rate.dm-9",
               "id": "disk.latency.rate.dm-9",
               "instance": "dm-9",
               "name": "com.vmware.applmgmt.mon.name.disk.latency.rate.dm-9",
               "units": "com.vmware.applmgmt.mon.unit.msec_per_io"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.swap.util",
               "id": "swap.util",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.swap.util",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.used.filesystem.swap",
               "id": "storage.used.filesystem.swap",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.used.filesystem.swap",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.swap",
               "id": "swap",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.swap",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.filesystem.swap",
               "id": "storage.totalsize.filesystem.swap",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.filesystem.swap",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.util.filesystem.swap",
               "id": "storage.util.filesystem.swap",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.util.filesystem.swap",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.cpu",
               "description": "com.vmware.applmgmt.mon.descr.cpu.totalfrequency",
               "id": "cpu.totalfrequency",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.cpu.totalfrequency",
               "units": "com.vmware.applmgmt.mon.unit.mhz"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.directory.vcdb_hourly_stats",
               "id": "storage.totalsize.directory.vcdb_hourly_stats",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.directory.vcdb_hourly_stats",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.cpu",
               "description": "com.vmware.applmgmt.mon.descr.cpu.systemload",
               "id": "cpu.systemload",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.cpu.systemload",
               "units": "com.vmware.applmgmt.mon.unit.load_per_min"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.directory.vcdb_daily_stats",
               "id": "storage.totalsize.directory.vcdb_daily_stats",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.directory.vcdb_daily_stats",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.memory",
               "description": "com.vmware.applmgmt.mon.descr.mem.util",
               "id": "mem.util",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.mem.util",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.directory.vcdb_monthly_stats",
               "id": "storage.totalsize.directory.vcdb_monthly_stats",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.directory.vcdb_monthly_stats",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.memory",
               "description": "com.vmware.applmgmt.mon.descr.mem.total",
               "id": "mem.total",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.mem.total",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.directory.vcdb_yearly_stats",
               "id": "storage.totalsize.directory.vcdb_yearly_stats",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.directory.vcdb_yearly_stats",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.memory",
               "description": "com.vmware.applmgmt.mon.descr.mem.usage",
               "id": "mem.usage",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.mem.usage",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.directory.vcdb_stats",
               "id": "storage.totalsize.directory.vcdb_stats",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.directory.vcdb_stats",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.network",
               "description": "com.vmware.applmgmt.mon.descr.net.rx.error.eth0",
               "id": "net.rx.error.eth0",
               "instance": "eth0",
               "name": "com.vmware.applmgmt.mon.name.net.rx.error.eth0",
               "units": "com.vmware.applmgmt.mon.unit.errors_per_sample"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.network",
               "description": "com.vmware.applmgmt.mon.descr.net.rx.error.lo",
               "id": "net.rx.error.lo",
               "instance": "lo",
               "name": "com.vmware.applmgmt.mon.name.net.rx.error.lo",
               "units": "com.vmware.applmgmt.mon.unit.errors_per_sample"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.network",
               "description": "com.vmware.applmgmt.mon.descr.net.tx.error.eth0",
               "id": "net.tx.error.eth0",
               "instance": "eth0",
               "name": "com.vmware.applmgmt.mon.name.net.tx.error.eth0",
               "units": "com.vmware.applmgmt.mon.unit.errors_per_sample"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.network",
               "description": "com.vmware.applmgmt.mon.descr.net.tx.error.lo",
               "id": "net.tx.error.lo",
               "instance": "lo",
               "name": "com.vmware.applmgmt.mon.name.net.tx.error.lo",
               "units": "com.vmware.applmgmt.mon.unit.errors_per_sample"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.filesystem.seat",
               "id": "storage.totalsize.filesystem.seat",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.filesystem.seat",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.util.directory.vcdb_stats",
               "id": "storage.util.directory.vcdb_stats",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.util.directory.vcdb_stats",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.directory.vcdb_events",
               "id": "storage.totalsize.directory.vcdb_events",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.directory.vcdb_events",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.util.directory.vcdb_events",
               "id": "storage.util.directory.vcdb_events",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.util.directory.vcdb_events",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.directory.vcdb_alarms",
               "id": "storage.totalsize.directory.vcdb_alarms",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.directory.vcdb_alarms",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.util.directory.vcdb_alarms",
               "id": "storage.util.directory.vcdb_alarms",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.util.directory.vcdb_alarms",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.directory.vcdb_tasks",
               "id": "storage.totalsize.directory.vcdb_tasks",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.directory.vcdb_tasks",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.util.directory.vcdb_tasks",
               "id": "storage.util.directory.vcdb_tasks",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.util.directory.vcdb_tasks",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.used.filesystem.seat",
               "id": "storage.used.filesystem.seat",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.used.filesystem.seat",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.util.filesystem.seat",
               "id": "storage.util.filesystem.seat",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.util.filesystem.seat",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.used.filesystem.db",
               "id": "storage.used.filesystem.db",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.used.filesystem.db",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.filesystem.db",
               "id": "storage.totalsize.filesystem.db",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.filesystem.db",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.util.filesystem.db",
               "id": "storage.util.filesystem.db",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.util.filesystem.db",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.used.filesystem.dblog",
               "id": "storage.used.filesystem.dblog",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.used.filesystem.dblog",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.filesystem.dblog",
               "id": "storage.totalsize.filesystem.dblog",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.filesystem.dblog",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.util.filesystem.dblog",
               "id": "storage.util.filesystem.dblog",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.storage.util.filesystem.dblog",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.filesystem.root",
               "id": "storage.totalsize.filesystem.root",
               "instance": "/",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.filesystem.root",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.util.filesystem.root",
               "id": "storage.util.filesystem.root",
               "instance": "/",
               "name": "com.vmware.applmgmt.mon.name.storage.util.filesystem.root",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.filesystem.boot",
               "id": "storage.totalsize.filesystem.boot",
               "instance": "/boot",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.filesystem.boot",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.util.filesystem.boot",
               "id": "storage.util.filesystem.boot",
               "instance": "/boot",
               "name": "com.vmware.applmgmt.mon.name.storage.util.filesystem.boot",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.filesystem.archive",
               "id": "storage.totalsize.filesystem.archive",
               "instance": "/storage/archive",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.filesystem.archive",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.util.filesystem.archive",
               "id": "storage.util.filesystem.archive",
               "instance": "/storage/archive",
               "name": "com.vmware.applmgmt.mon.name.storage.util.filesystem.archive",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.filesystem.autodeploy",
               "id": "storage.totalsize.filesystem.autodeploy",
               "instance": "/storage/autodeploy",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.filesystem.autodeploy",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.util.filesystem.autodeploy",
               "id": "storage.util.filesystem.autodeploy",
               "instance": "/storage/autodeploy",
               "name": "com.vmware.applmgmt.mon.name.storage.util.filesystem.autodeploy",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.filesystem.core",
               "id": "storage.totalsize.filesystem.core",
               "instance": "/storage/core",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.filesystem.core",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.util.filesystem.core",
               "id": "storage.util.filesystem.core",
               "instance": "/storage/core",
               "name": "com.vmware.applmgmt.mon.name.storage.util.filesystem.core",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.filesystem.imagebuilder",
               "id": "storage.totalsize.filesystem.imagebuilder",
               "instance": "/storage/imagebuilder",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.filesystem.imagebuilder",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.util.filesystem.imagebuilder",
               "id": "storage.util.filesystem.imagebuilder",
               "instance": "/storage/imagebuilder",
               "name": "com.vmware.applmgmt.mon.name.storage.util.filesystem.imagebuilder",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.filesystem.lifecycle",
               "id": "storage.totalsize.filesystem.lifecycle",
               "instance": "/storage/lifecycle",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.filesystem.lifecycle",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.util.filesystem.lifecycle",
               "id": "storage.util.filesystem.lifecycle",
               "instance": "/storage/lifecycle",
               "name": "com.vmware.applmgmt.mon.name.storage.util.filesystem.lifecycle",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.filesystem.log",
               "id": "storage.totalsize.filesystem.log",
               "instance": "/storage/log",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.filesystem.log",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.util.filesystem.log",
               "id": "storage.util.filesystem.log",
               "instance": "/storage/log",
               "name": "com.vmware.applmgmt.mon.name.storage.util.filesystem.log",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.filesystem.netdump",
               "id": "storage.totalsize.filesystem.netdump",
               "instance": "/storage/netdump",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.filesystem.netdump",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.util.filesystem.netdump",
               "id": "storage.util.filesystem.netdump",
               "instance": "/storage/netdump",
               "name": "com.vmware.applmgmt.mon.name.storage.util.filesystem.netdump",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.filesystem.updatemgr",
               "id": "storage.totalsize.filesystem.updatemgr",
               "instance": "/storage/updatemgr",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.filesystem.updatemgr",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.util.filesystem.updatemgr",
               "id": "storage.util.filesystem.updatemgr",
               "instance": "/storage/updatemgr",
               "name": "com.vmware.applmgmt.mon.name.storage.util.filesystem.updatemgr",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.filesystem.vtsdb",
               "id": "storage.totalsize.filesystem.vtsdb",
               "instance": "/storage/vtsdb",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.filesystem.vtsdb",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.util.filesystem.vtsdb",
               "id": "storage.util.filesystem.vtsdb",
               "instance": "/storage/vtsdb",
               "name": "com.vmware.applmgmt.mon.name.storage.util.filesystem.vtsdb",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.totalsize.filesystem.vtsdblog",
               "id": "storage.totalsize.filesystem.vtsdblog",
               "instance": "/storage/vtsdblog",
               "name": "com.vmware.applmgmt.mon.name.storage.totalsize.filesystem.vtsdblog",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.util.filesystem.vtsdblog",
               "id": "storage.util.filesystem.vtsdblog",
               "instance": "/storage/vtsdblog",
               "name": "com.vmware.applmgmt.mon.name.storage.util.filesystem.vtsdblog",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.used.filesystem.root",
               "id": "storage.used.filesystem.root",
               "instance": "/",
               "name": "com.vmware.applmgmt.mon.name.storage.used.filesystem.root",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.used.filesystem.boot",
               "id": "storage.used.filesystem.boot",
               "instance": "/boot",
               "name": "com.vmware.applmgmt.mon.name.storage.used.filesystem.boot",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.used.filesystem.archive",
               "id": "storage.used.filesystem.archive",
               "instance": "/storage/archive",
               "name": "com.vmware.applmgmt.mon.name.storage.used.filesystem.archive",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.used.filesystem.autodeploy",
               "id": "storage.used.filesystem.autodeploy",
               "instance": "/storage/autodeploy",
               "name": "com.vmware.applmgmt.mon.name.storage.used.filesystem.autodeploy",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.used.filesystem.core",
               "id": "storage.used.filesystem.core",
               "instance": "/storage/core",
               "name": "com.vmware.applmgmt.mon.name.storage.used.filesystem.core",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.used.filesystem.imagebuilder",
               "id": "storage.used.filesystem.imagebuilder",
               "instance": "/storage/imagebuilder",
               "name": "com.vmware.applmgmt.mon.name.storage.used.filesystem.imagebuilder",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.used.filesystem.lifecycle",
               "id": "storage.used.filesystem.lifecycle",
               "instance": "/storage/lifecycle",
               "name": "com.vmware.applmgmt.mon.name.storage.used.filesystem.lifecycle",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.used.filesystem.log",
               "id": "storage.used.filesystem.log",
               "instance": "/storage/log",
               "name": "com.vmware.applmgmt.mon.name.storage.used.filesystem.log",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.used.filesystem.netdump",
               "id": "storage.used.filesystem.netdump",
               "instance": "/storage/netdump",
               "name": "com.vmware.applmgmt.mon.name.storage.used.filesystem.netdump",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.used.filesystem.updatemgr",
               "id": "storage.used.filesystem.updatemgr",
               "instance": "/storage/updatemgr",
               "name": "com.vmware.applmgmt.mon.name.storage.used.filesystem.updatemgr",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.used.filesystem.vtsdb",
               "id": "storage.used.filesystem.vtsdb",
               "instance": "/storage/vtsdb",
               "name": "com.vmware.applmgmt.mon.name.storage.used.filesystem.vtsdb",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.storage",
               "description": "com.vmware.applmgmt.mon.descr.storage.used.filesystem.vtsdblog",
               "id": "storage.used.filesystem.vtsdblog",
               "instance": "/storage/vtsdblog",
               "name": "com.vmware.applmgmt.mon.name.storage.used.filesystem.vtsdblog",
               "units": "com.vmware.applmgmt.mon.unit.kb"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.cpu",
               "description": "com.vmware.applmgmt.mon.descr.cpu.util",
               "id": "cpu.util",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.cpu.util",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.cpu",
               "description": "com.vmware.applmgmt.mon.descr.cpu.steal",
               "id": "cpu.steal",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.cpu.steal",
               "units": "com.vmware.applmgmt.mon.unit.percent"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.memory",
               "description": "com.vmware.applmgmt.mon.descr.swap.pageRate",
               "id": "swap.pageRate",
               "instance": "",
               "name": "com.vmware.applmgmt.mon.name.swap.pageRate",
               "units": "com.vmware.applmgmt.mon.unit.pages_per_sec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.read.rate.dm-0",
               "id": "disk.read.rate.dm-0",
               "instance": "dm-0",
               "name": "com.vmware.applmgmt.mon.name.disk.read.rate.dm-0",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.read.rate.dm-1",
               "id": "disk.read.rate.dm-1",
               "instance": "dm-1",
               "name": "com.vmware.applmgmt.mon.name.disk.read.rate.dm-1",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.write.rate.dm-0",
               "id": "disk.write.rate.dm-0",
               "instance": "dm-0",
               "name": "com.vmware.applmgmt.mon.name.disk.write.rate.dm-0",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.write.rate.dm-1",
               "id": "disk.write.rate.dm-1",
               "instance": "dm-1",
               "name": "com.vmware.applmgmt.mon.name.disk.write.rate.dm-1",
               "units": "com.vmware.applmgmt.mon.unit.num_of_io_per_msec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.latency.rate.dm-0",
               "id": "disk.latency.rate.dm-0",
               "instance": "dm-0",
               "name": "com.vmware.applmgmt.mon.name.disk.latency.rate.dm-0",
               "units": "com.vmware.applmgmt.mon.unit.msec_per_io"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.disk",
               "description": "com.vmware.applmgmt.mon.descr.disk.latency.rate.dm-1",
               "id": "disk.latency.rate.dm-1",
               "instance": "dm-1",
               "name": "com.vmware.applmgmt.mon.name.disk.latency.rate.dm-1",
               "units": "com.vmware.applmgmt.mon.unit.msec_per_io"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.network",
               "description": "com.vmware.applmgmt.mon.descr.net.rx.activity.eth0",
               "id": "net.rx.activity.eth0",
               "instance": "eth0",
               "name": "com.vmware.applmgmt.mon.name.net.rx.activity.eth0",
               "units": "com.vmware.applmgmt.mon.unit.kb_per_sec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.network",
               "description": "com.vmware.applmgmt.mon.descr.net.rx.activity.lo",
               "id": "net.rx.activity.lo",
               "instance": "lo",
               "name": "com.vmware.applmgmt.mon.name.net.rx.activity.lo",
               "units": "com.vmware.applmgmt.mon.unit.kb_per_sec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.network",
               "description": "com.vmware.applmgmt.mon.descr.net.rx.packetRate.eth0",
               "id": "net.rx.packetRate.eth0",
               "instance": "eth0",
               "name": "com.vmware.applmgmt.mon.name.net.rx.packetRate.eth0",
               "units": "com.vmware.applmgmt.mon.unit.packets_per_sec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.network",
               "description": "com.vmware.applmgmt.mon.descr.net.rx.packetRate.lo",
               "id": "net.rx.packetRate.lo",
               "instance": "lo",
               "name": "com.vmware.applmgmt.mon.name.net.rx.packetRate.lo",
               "units": "com.vmware.applmgmt.mon.unit.packets_per_sec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.network",
               "description": "com.vmware.applmgmt.mon.descr.net.rx.drop.eth0",
               "id": "net.rx.drop.eth0",
               "instance": "eth0",
               "name": "com.vmware.applmgmt.mon.name.net.rx.drop.eth0",
               "units": "com.vmware.applmgmt.mon.unit.drops_per_sample"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.network",
               "description": "com.vmware.applmgmt.mon.descr.net.rx.drop.lo",
               "id": "net.rx.drop.lo",
               "instance": "lo",
               "name": "com.vmware.applmgmt.mon.name.net.rx.drop.lo",
               "units": "com.vmware.applmgmt.mon.unit.drops_per_sample"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.network",
               "description": "com.vmware.applmgmt.mon.descr.net.tx.activity.eth0",
               "id": "net.tx.activity.eth0",
               "instance": "eth0",
               "name": "com.vmware.applmgmt.mon.name.net.tx.activity.eth0",
               "units": "com.vmware.applmgmt.mon.unit.kb_per_sec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.network",
               "description": "com.vmware.applmgmt.mon.descr.net.tx.activity.lo",
               "id": "net.tx.activity.lo",
               "instance": "lo",
               "name": "com.vmware.applmgmt.mon.name.net.tx.activity.lo",
               "units": "com.vmware.applmgmt.mon.unit.kb_per_sec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.network",
               "description": "com.vmware.applmgmt.mon.descr.net.tx.packetRate.eth0",
               "id": "net.tx.packetRate.eth0",
               "instance": "eth0",
               "name": "com.vmware.applmgmt.mon.name.net.tx.packetRate.eth0",
               "units": "com.vmware.applmgmt.mon.unit.packets_per_sec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.network",
               "description": "com.vmware.applmgmt.mon.descr.net.tx.packetRate.lo",
               "id": "net.tx.packetRate.lo",
               "instance": "lo",
               "name": "com.vmware.applmgmt.mon.name.net.tx.packetRate.lo",
               "units": "com.vmware.applmgmt.mon.unit.packets_per_sec"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.network",
               "description": "com.vmware.applmgmt.mon.descr.net.tx.drop.eth0",
               "id": "net.tx.drop.eth0",
               "instance": "eth0",
               "name": "com.vmware.applmgmt.mon.name.net.tx.drop.eth0",
               "units": "com.vmware.applmgmt.mon.unit.drops_per_sample"
           },
           {
               "category": "com.vmware.applmgmt.mon.cat.network",
               "description": "com.vmware.applmgmt.mon.descr.net.tx.drop.lo",
               "id": "net.tx.drop.lo",
               "instance": "lo",
               "name": "com.vmware.applmgmt.mon.name.net.tx.drop.lo",
               "units": "com.vmware.applmgmt.mon.unit.drops_per_sample"
           }
       ]
   }

With this information, you can access the information for a given time
frame:

::

   - name: Query the monitoring backend
     vmware.vmware_rest.appliance_monitoring_query:
       end_time: 2021-04-14T09:34:56.000Z
       start_time: 2021-04-14T08:34:56.000Z
       names:
         - mem.total
       interval: MINUTES5
       function: AVG
     register: result

response

::

   {
       "changed": false,
       "value": [
           {
               "data": [
                   "",
                   "",
                   "",
                   "",
                   "",
                   "",
                   "",
                   "",
                   "",
                   "",
                   "",
                   "",
                   ""
               ],
               "end_time": "2021-04-14T09:34:56.000Z",
               "function": "AVG",
               "interval": "MINUTES5",
               "name": "mem.total",
               "start_time": "2021-04-14T08:34:56.000Z"
           }
       ]
   }
