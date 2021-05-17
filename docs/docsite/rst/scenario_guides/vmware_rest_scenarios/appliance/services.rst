.. _vmware-rest-appliance-services:


Services managment
******************


Handle your VCSA services with Ansible
======================================

You can use Ansible to control the VCSA services. To get a view of all
the known services, you can use the appliance_services_info module:

::

   - name: List all the services
     vmware.vmware_rest.appliance_services_info:

response

::

   {
       "changed": false,
       "value": {
           "appliance-shutdown": {
               "description": "/etc/rc.local.shutdown Compatibility",
               "state": "STOPPED"
           },
           "atftpd": {
               "description": "The tftp server serves files using the trivial file transfer protocol.",
               "state": "STOPPED"
           },
           "auditd": {
               "description": "Security Auditing Service",
               "state": "STOPPED"
           },
           "cloud-config": {
               "description": "Apply the settings specified in cloud-config",
               "state": "STARTED"
           },
           "cloud-init": {
               "description": "Initial cloud-init job (metadata service crawler)",
               "state": "STARTED"
           },
           "cloud-init-local": {
               "description": "Initial cloud-init job (pre-networking)",
               "state": "STARTED"
           },
           "crond": {
               "description": "Command Scheduler",
               "state": "STARTED"
           },
           "dbus": {
               "description": "D-Bus System Message Bus",
               "state": "STARTED"
           },
           "dm-event": {
               "description": "Device-mapper event daemon",
               "state": "STOPPED"
           },
           "dnsmasq": {
               "description": "A lightweight, caching DNS proxy",
               "state": "STARTED"
           },
           "dracut-cmdline": {
               "description": "dracut cmdline hook",
               "state": "STOPPED"
           },
           "dracut-initqueue": {
               "description": "dracut initqueue hook",
               "state": "STOPPED"
           },
           "dracut-mount": {
               "description": "dracut mount hook",
               "state": "STOPPED"
           },
           "dracut-pre-mount": {
               "description": "dracut pre-mount hook",
               "state": "STOPPED"
           },
           "dracut-pre-pivot": {
               "description": "dracut pre-pivot and cleanup hook",
               "state": "STOPPED"
           },
           "dracut-pre-trigger": {
               "description": "dracut pre-trigger hook",
               "state": "STOPPED"
           },
           "dracut-pre-udev": {
               "description": "dracut pre-udev hook",
               "state": "STOPPED"
           },
           "dracut-shutdown": {
               "description": "Restore /run/initramfs on shutdown",
               "state": "STARTED"
           },
           "emergency": {
               "description": "Emergency Shell",
               "state": "STOPPED"
           },
           "getty@tty1": {
               "description": "Getty on tty1",
               "state": "STARTED"
           },
           "getty@tty2": {
               "description": "DCUI",
               "state": "STARTED"
           },
           "haveged": {
               "description": "Entropy Daemon based on the HAVEGE algorithm",
               "state": "STARTED"
           },
           "initrd-cleanup": {
               "description": "Cleaning Up and Shutting Down Daemons",
               "state": "STOPPED"
           },
           "initrd-parse-etc": {
               "description": "Reload Configuration from the Real Root",
               "state": "STOPPED"
           },
           "initrd-switch-root": {
               "description": "Switch Root",
               "state": "STOPPED"
           },
           "initrd-udevadm-cleanup-db": {
               "description": "Cleanup udevd DB",
               "state": "STOPPED"
           },
           "irqbalance": {
               "description": "irqbalance daemon",
               "state": "STARTED"
           },
           "kmod-static-nodes": {
               "description": "Create list of required static device nodes for the current kernel",
               "state": "STARTED"
           },
           "lsassd": {
               "description": "Likewise Security and Authentication Subsystem",
               "state": "STARTED"
           },
           "lvm2-activate": {
               "description": "LVM2 activate volume groups",
               "state": "STARTED"
           },
           "lvm2-lvmetad": {
               "description": "LVM2 metadata daemon",
               "state": "STARTED"
           },
           "lvm2-pvscan@253:2": {
               "description": "LVM2 PV scan on device 253:2",
               "state": "STARTED"
           },
           "lvm2-pvscan@253:4": {
               "description": "LVM2 PV scan on device 253:4",
               "state": "STARTED"
           },
           "lwsmd": {
               "description": "Likewise Service Control Manager Service",
               "state": "STARTED"
           },
           "ntpd": {
               "description": "Network Time Service",
               "state": "STARTED"
           },
           "observability": {
               "description": "VMware Observability Service",
               "state": "STARTED"
           },
           "rc-local": {
               "description": "/etc/rc.d/rc.local Compatibility",
               "state": "STARTED"
           },
           "rescue": {
               "description": "Rescue Shell",
               "state": "STOPPED"
           },
           "rsyslog": {
               "description": "System Logging Service",
               "state": "STARTED"
           },
           "sendmail": {
               "description": "Sendmail Mail Transport Agent",
               "state": "STARTED"
           },
           "sshd": {
               "description": "OpenSSH Daemon",
               "state": "STARTED"
           },
           "sshd-keygen": {
               "description": "Generate sshd host keys",
               "state": "STOPPED"
           },
           "syslog-ng": {
               "description": "System Logger Daemon",
               "state": "STOPPED"
           },
           "sysstat": {
               "description": "Resets System Activity Logs",
               "state": "STARTED"
           },
           "sysstat-collect": {
               "description": "system activity accounting tool",
               "state": "STOPPED"
           },
           "sysstat-summary": {
               "description": "Generate a daily summary of process accounting",
               "state": "STOPPED"
           },
           "systemd-ask-password-console": {
               "description": "Dispatch Password Requests to Console",
               "state": "STOPPED"
           },
           "systemd-ask-password-wall": {
               "description": "Forward Password Requests to Wall",
               "state": "STOPPED"
           },
           "systemd-binfmt": {
               "description": "Set Up Additional Binary Formats",
               "state": "STOPPED"
           },
           "systemd-fsck-root": {
               "description": "File System Check on Root Device",
               "state": "STARTED"
           },
           "systemd-hostnamed": {
               "description": "Hostname Service",
               "state": "STARTED"
           },
           "systemd-hwdb-update": {
               "description": "Rebuild Hardware Database",
               "state": "STARTED"
           },
           "systemd-initctl": {
               "description": "initctl Compatibility Daemon",
               "state": "STOPPED"
           },
           "systemd-journal-catalog-update": {
               "description": "Rebuild Journal Catalog",
               "state": "STARTED"
           },
           "systemd-journal-flush": {
               "description": "Flush Journal to Persistent Storage",
               "state": "STARTED"
           },
           "systemd-journald": {
               "description": "Journal Service",
               "state": "STARTED"
           },
           "systemd-logind": {
               "description": "Login Service",
               "state": "STARTED"
           },
           "systemd-machine-id-commit": {
               "description": "Commit a transient machine-id on disk",
               "state": "STOPPED"
           },
           "systemd-modules-load": {
               "description": "Load Kernel Modules",
               "state": "STARTED"
           },
           "systemd-networkd": {
               "description": "Network Service",
               "state": "STARTED"
           },
           "systemd-networkd-wait-online": {
               "description": "Wait for Network to be Configured",
               "state": "STARTED"
           },
           "systemd-quotacheck": {
               "description": "File System Quota Check",
               "state": "STOPPED"
           },
           "systemd-random-seed": {
               "description": "Load/Save Random Seed",
               "state": "STARTED"
           },
           "systemd-remount-fs": {
               "description": "Remount Root and Kernel File Systems",
               "state": "STARTED"
           },
           "systemd-resolved": {
               "description": "Network Name Resolution",
               "state": "STARTED"
           },
           "systemd-sysctl": {
               "description": "Apply Kernel Variables",
               "state": "STARTED"
           },
           "systemd-tmpfiles-clean": {
               "description": "Cleanup of Temporary Directories",
               "state": "STOPPED"
           },
           "systemd-tmpfiles-setup": {
               "description": "Create Volatile Files and Directories",
               "state": "STARTED"
           },
           "systemd-tmpfiles-setup-dev": {
               "description": "Create Static Device Nodes in /dev",
               "state": "STARTED"
           },
           "systemd-udev-trigger": {
               "description": "udev Coldplug all Devices",
               "state": "STARTED"
           },
           "systemd-udevd": {
               "description": "udev Kernel Device Manager",
               "state": "STARTED"
           },
           "systemd-update-done": {
               "description": "Update is Completed",
               "state": "STARTED"
           },
           "systemd-update-utmp": {
               "description": "Update UTMP about System Boot/Shutdown",
               "state": "STARTED"
           },
           "systemd-update-utmp-runlevel": {
               "description": "Update UTMP about System Runlevel Changes",
               "state": "STOPPED"
           },
           "systemd-user-sessions": {
               "description": "Permit User Sessions",
               "state": "STARTED"
           },
           "systemd-vconsole-setup": {
               "description": "Setup Virtual Console",
               "state": "STOPPED"
           },
           "vami-lighttp": {
               "description": "vami-lighttp.service",
               "state": "STARTED"
           },
           "vgauthd": {
               "description": "VGAuth Service for open-vm-tools",
               "state": "STOPPED"
           },
           "vmafdd": {
               "description": "LSB: Authentication Framework Daemon",
               "state": "STARTED"
           },
           "vmcad": {
               "description": "LSB: Start and Stop vmca",
               "state": "STARTED"
           },
           "vmdird": {
               "description": "LSB: Start and Stop vmdir",
               "state": "STARTED"
           },
           "vmtoolsd": {
               "description": "Service for virtual machines hosted on VMware",
               "state": "STOPPED"
           },
           "vmware-firewall": {
               "description": "VMware Firewall service",
               "state": "STARTED"
           },
           "vmware-pod": {
               "description": "VMware Pod Service.",
               "state": "STARTED"
           },
           "vmware-vdtc": {
               "description": "VMware vSphere Distrubuted Tracing Collector",
               "state": "STARTED"
           },
           "vmware-vmon": {
               "description": "VMware Service Lifecycle Manager",
               "state": "STARTED"
           }
       }
   }

If you need to target a specific service, you can pass its name
through the ``service`` parameter.

::

   - name: Get information about ntpd
     vmware.vmware_rest.appliance_services_info:
       service: ntpd

response

::

   {
       "changed": false,
       "id": "ntpd",
       "value": {
           "description": "ntpd.service",
           "state": "STARTED"
       }
   }

Use the appliance_services module to stop a service:

::

   - name: Stop the ntpd service
     vmware.vmware_rest.appliance_services:
       service: ntpd
       state: stop

response

::

   {
       "changed": false,
       "value": {}
   }

or to start a service:

::

   - name: Start the ntpd service
     vmware.vmware_rest.appliance_services:
       service: ntpd
       state: start

response

::

   {
       "changed": false,
       "value": {}
   }


VMON services
=============

The VMON services can also be managed from Ansible. For instance to
get the state of the ``vpxd`` service:

::

   - name: Get information about a VMON service
     vmware.vmware_rest.appliance_vmon_service_info:
       service: vpxd

response

::

   {
       "changed": false,
       "value": [
           {
               "key": "analytics",
               "value": {
                   "description_key": "cis.analytics.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [],
                   "name_key": "cis.analytics.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "applmgmt",
               "value": {
                   "description_key": "cis.applmgmt.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [],
                   "name_key": "cis.applmgmt.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "certificateauthority",
               "value": {
                   "description_key": "cis.certificateauthority.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [
                       {
                           "args": [
                               "GREEN"
                           ],
                           "default_message": "Health is GREEN",
                           "id": "certificateathority.health.statuscode"
                       }
                   ],
                   "name_key": "cis.certificateauthority.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "certificatemanagement",
               "value": {
                   "description_key": "cis.certificatemanagement.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [
                       {
                           "args": [
                               "GREEN"
                           ],
                           "default_message": "Health is GREEN",
                           "id": "certificatemanagement.health.statuscode"
                       }
                   ],
                   "name_key": "cis.certificatemanagement.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "cis-license",
               "value": {
                   "description_key": "cis.cis-license.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [
                       {
                           "args": [],
                           "default_message": "The License Service is operational.",
                           "id": "cis.license.health.ok"
                       }
                   ],
                   "name_key": "cis.cis-license.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "content-library",
               "value": {
                   "description_key": "cis.content-library.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [
                       {
                           "args": [],
                           "default_message": "Database server connection is GREEN.",
                           "id": "com.vmware.vdcs.vsphere-cs-lib.db_health_green"
                       }
                   ],
                   "name_key": "cis.content-library.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "eam",
               "value": {
                   "description_key": "cis.eam.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [
                       {
                           "args": [],
                           "default_message": "",
                           "id": "cis.eam.statusOK"
                       }
                   ],
                   "name_key": "cis.eam.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "envoy",
               "value": {
                   "description_key": "cis.envoy.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [],
                   "name_key": "cis.envoy.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "hvc",
               "value": {
                   "description_key": "cis.hvc.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [
                       {
                           "args": [
                               "GREEN"
                           ],
                           "default_message": "Health is GREEN",
                           "id": "hvc.health.statuscode"
                       }
                   ],
                   "name_key": "cis.hvc.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "imagebuilder",
               "value": {
                   "description_key": "cis.imagebuilder.ServiceDescription",
                   "name_key": "cis.imagebuilder.ServiceName",
                   "startup_type": "MANUAL",
                   "state": "STOPPED"
               }
           },
           {
               "key": "infraprofile",
               "value": {
                   "description_key": "cis.infraprofile.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [
                       {
                           "args": [
                               "GREEN"
                           ],
                           "default_message": "Health is GREEN",
                           "id": "infraprofile.health.statuscode"
                       }
                   ],
                   "name_key": "cis.infraprofile.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "lookupsvc",
               "value": {
                   "description_key": "cis.lookupsvc.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [],
                   "name_key": "cis.lookupsvc.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "netdumper",
               "value": {
                   "description_key": "cis.netdumper.ServiceDescription",
                   "name_key": "cis.netdumper.ServiceName",
                   "startup_type": "MANUAL",
                   "state": "STOPPED"
               }
           },
           {
               "key": "observability-vapi",
               "value": {
                   "description_key": "cis.observability-vapi.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [
                       {
                           "args": [
                               "GREEN"
                           ],
                           "default_message": "Health is GREEN",
                           "id": "observability.health.statuscode"
                       }
                   ],
                   "name_key": "cis.observability-vapi.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "perfcharts",
               "value": {
                   "description_key": "cis.perfcharts.ServiceDescription",
                   "health": "DEGRADED",
                   "health_messages": [
                       {
                           "args": [],
                           "default_message": "health.statsReoptInitalizer.illegalStateEx",
                           "id": "health.statsReoptInitalizer.illegalStateEx"
                       }
                   ],
                   "name_key": "cis.perfcharts.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "pschealth",
               "value": {
                   "description_key": "cis.pschealth.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [],
                   "name_key": "cis.pschealth.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "rbd",
               "value": {
                   "description_key": "cis.rbd.ServiceDescription",
                   "name_key": "cis.rbd.ServiceName",
                   "startup_type": "MANUAL",
                   "state": "STOPPED"
               }
           },
           {
               "key": "rhttpproxy",
               "value": {
                   "description_key": "cis.rhttpproxy.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [],
                   "name_key": "cis.rhttpproxy.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "sca",
               "value": {
                   "description_key": "cis.sca.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [],
                   "name_key": "cis.sca.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "sps",
               "value": {
                   "description_key": "cis.sps.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [],
                   "name_key": "cis.sps.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "statsmonitor",
               "value": {
                   "description_key": "cis.statsmonitor.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [
                       {
                           "args": [],
                           "default_message": "Appliance monitoring service is healthy.",
                           "id": "com.vmware.applmgmt.mon.health.healthy"
                       }
                   ],
                   "name_key": "cis.statsmonitor.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "sts",
               "value": {
                   "description_key": "cis.sts.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [],
                   "name_key": "cis.sts.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "topologysvc",
               "value": {
                   "description_key": "cis.topologysvc.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [
                       {
                           "args": [
                               "GREEN"
                           ],
                           "default_message": "Health is GREEN",
                           "id": "topologysvc.health.statuscode"
                       }
                   ],
                   "name_key": "cis.topologysvc.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "trustmanagement",
               "value": {
                   "description_key": "cis.trustmanagement.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [
                       {
                           "args": [
                               "GREEN"
                           ],
                           "default_message": "Health is GREEN",
                           "id": "trustmanagement.health.statuscode"
                       }
                   ],
                   "name_key": "cis.trustmanagement.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "updatemgr",
               "value": {
                   "description_key": "cis.updatemgr.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [],
                   "name_key": "cis.updatemgr.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "vapi-endpoint",
               "value": {
                   "description_key": "cis.vapi-endpoint.ServiceDescription",
                   "health": "HEALTHY_WITH_WARNINGS",
                   "health_messages": [
                       {
                           "args": [
                               "498abd68-65d4-4272-ad63-1918298aafc8\\com.vmware.cis.ds"
                           ],
                           "default_message": "Failed to connect to 498abd68-65d4-4272-ad63-1918298aafc8\\com.vmware.cis.ds vAPI provider.",
                           "id": "com.vmware.vapi.endpoint.failedToConnectToVApiProvider"
                       },
                       {
                           "args": [
                               "2021-05-17T14:33:57UTC",
                               "2021-05-17T14:33:58UTC"
                           ],
                           "default_message": "Configuration health status is created between 2021-05-17T14:33:57UTC and 2021-05-17T14:33:58UTC.",
                           "id": "com.vmware.vapi.endpoint.healthStatusProducedTimes"
                       }
                   ],
                   "name_key": "cis.vapi-endpoint.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "vcha",
               "value": {
                   "description_key": "cis.vcha.ServiceDescription",
                   "name_key": "cis.vcha.ServiceName",
                   "startup_type": "DISABLED",
                   "state": "STOPPED"
               }
           },
           {
               "key": "vlcm",
               "value": {
                   "description_key": "cis.vlcm.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [],
                   "name_key": "cis.vlcm.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "vmcam",
               "value": {
                   "description_key": "cis.vmcam.ServiceDescription",
                   "name_key": "cis.vmcam.ServiceName",
                   "startup_type": "MANUAL",
                   "state": "STOPPED"
               }
           },
           {
               "key": "vmonapi",
               "value": {
                   "description_key": "cis.vmonapi.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [],
                   "name_key": "cis.vmonapi.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "vmware-postgres-archiver",
               "value": {
                   "description_key": "cis.vmware-postgres-archiver.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [
                       {
                           "args": [],
                           "default_message": "VMware Archiver service is healthy.",
                           "id": "cis.vmware-postgres-archiver.health.healthy"
                       }
                   ],
                   "name_key": "cis.vmware-postgres-archiver.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "vmware-vpostgres",
               "value": {
                   "description_key": "cis.vmware-vpostgres.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [
                       {
                           "args": [],
                           "default_message": "Service vmware-vpostgres is healthy.",
                           "id": "cis.vmware-vpostgres.health.healthy"
                       }
                   ],
                   "name_key": "cis.vmware-vpostgres.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "vpxd",
               "value": {
                   "description_key": "cis.vpxd.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [
                       {
                           "args": [
                               "vCenter Server",
                               "GREEN"
                           ],
                           "default_message": "{0} health is {1}",
                           "id": "vc.health.statuscode"
                       },
                       {
                           "args": [
                               "VirtualCenter Database",
                               "GREEN"
                           ],
                           "default_message": "{0} health is {1}",
                           "id": "vc.health.statuscode"
                       }
                   ],
                   "name_key": "cis.vpxd.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "vpxd-svcs",
               "value": {
                   "description_key": "cis.vpxd-svcs.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [
                       {
                           "args": [],
                           "default_message": "Tagging service is in a healthy state",
                           "id": "cis.tagging.health.status"
                       }
                   ],
                   "name_key": "cis.vpxd-svcs.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "vsan-health",
               "value": {
                   "description_key": "cis.vsan-health.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [],
                   "name_key": "cis.vsan-health.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "vsm",
               "value": {
                   "description_key": "cis.vsm.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [],
                   "name_key": "cis.vsm.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "vsphere-ui",
               "value": {
                   "description_key": "cis.vsphere-ui.ServiceDescription",
                   "name_key": "cis.vsphere-ui.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STOPPED"
               }
           },
           {
               "key": "vstats",
               "value": {
                   "description_key": "cis.vstats.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [],
                   "name_key": "cis.vstats.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "vtsdb",
               "value": {
                   "description_key": "cis.vtsdb.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [
                       {
                           "args": [],
                           "default_message": "Service vtsdb is healthy.",
                           "id": "cis.vtsdb.health.healthy"
                       }
                   ],
                   "name_key": "cis.vtsdb.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           },
           {
               "key": "wcp",
               "value": {
                   "description_key": "cis.wcp.ServiceDescription",
                   "health": "HEALTHY",
                   "health_messages": [],
                   "name_key": "cis.wcp.ServiceName",
                   "startup_type": "AUTOMATIC",
                   "state": "STARTED"
               }
           }
       ]
   }

And to ensure it starts ``automatically``:

::

   - name: Adjust vpxd configuration
     vmware.vmware_rest.appliance_vmon_service:
       service: vpxd
       startup_type: AUTOMATIC

response

::

   {
       "changed": false,
       "id": "vpxd",
       "value": {
           "description_key": "cis.vpxd.ServiceDescription",
           "health": "HEALTHY",
           "health_messages": [
               {
                   "args": [
                       "vCenter Server",
                       "GREEN"
                   ],
                   "default_message": "{0} health is {1}",
                   "id": "vc.health.statuscode"
               },
               {
                   "args": [
                       "VirtualCenter Database",
                       "GREEN"
                   ],
                   "default_message": "{0} health is {1}",
                   "id": "vc.health.statuscode"
               }
           ],
           "name_key": "cis.vpxd.ServiceName",
           "startup_type": "AUTOMATIC",
           "state": "STARTED"
       }
   }
