.. _vmware_inventory_vm_attributes:

*******************************************************************
Using Virtual machine attributes in VMware dynamic inventory plugin
*******************************************************************

.. contents:: Topics

Virtual machine attributes
==========================

You can use virtual machine properties which can be used to populate ``hostvars`` for the given
virtual machine in a VMware dynamic inventory plugin.

capability
----------

This section describes settings for the runtime capabilities of the virtual machine.

snapshotOperationsSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether or not a virtual machine supports snapshot operations.

multipleSnapshotsSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether or not a virtual machine supports multiple snapshots.
    This value is not set when the virtual machine is unavailable, for instance, when it is being created or deleted.

snapshotConfigSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether or not a virtual machine supports snapshot config.

poweredOffSnapshotsSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether or not a virtual machine supports snapshot operations in ``poweredOff`` state.

memorySnapshotsSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether or not a virtual machine supports memory snapshots.

revertToSnapshotSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether or not a virtual machine supports reverting to a snapshot.

quiescedSnapshotsSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether or not a virtual machine supports quiesced snapshots.

disableSnapshotsSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether or not snapshots can be disabled.

lockSnapshotsSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether or not the snapshot tree can be locked.

consolePreferencesSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether console preferences can be set for the virtual machine.

cpuFeatureMaskSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether CPU feature requirements masks can be set for the virtual machine.

s1AcpiManagementSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether or not a virtual machine supports ACPI S1 settings management.

settingScreenResolutionSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether or not the virtual machine supports setting the screen resolution of the console window.

toolsAutoUpdateSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Supports tools auto-update.

vmNpivWwnSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^

    Supports virtual machine NPIV WWN.

npivWwnOnNonRdmVmSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Supports assigning NPIV WWN to virtual machines that do not have RDM disks.

vmNpivWwnDisableSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether the NPIV disabling operation is supported on the virtual machine.

vmNpivWwnUpdateSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether the update of NPIV WWNs are supported on the virtual machine.

swapPlacementSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Flag indicating whether the virtual machine has a configurable (swapfile placement policy).

toolsSyncTimeSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether asking tools to sync time with the host is supported.

virtualMmuUsageSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether or not the use of nested page table hardware support can be explicitly set.

diskSharesSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether resource settings for disks can be applied to the virtual machine.

bootOptionsSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether boot options can be configured for the virtual machine.

bootRetryOptionsSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether automatic boot retry can be configured for the virtual machine.

settingVideoRamSizeSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Flag indicating whether the video RAM size of the virtual machine can be configured.

settingDisplayTopologySupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether or not the virtual machine supports setting the display topology of the console window.

recordReplaySupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether record and replay functionality is supported on the virtual machine.

changeTrackingSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates that change tracking is supported for virtual disks of the virtual machine.
    However, even if change tracking is supported, it might not be available for all disks of the virtual machine.
    For example, passthru raw disk mappings or disks backed by any Ver1BackingInfo cannot be tracked.

multipleCoresPerSocketSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether multiple virtual cores per socket is supported on the virtual machine.

hostBasedReplicationSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates that host based replication is supported on the virtual machine.
    However, even if host based replication is supported, it might not be available for all disk types.
    For example, passthru raw disk mappings can not be replicated.

guestAutoLockSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether or not guest autolock is supported on the virtual machine.

memoryReservationLockSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether :ref:`memory_reservation_locked_to_max` may be set to true for the virtual machine.

featureRequirementSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether the featureRequirement feature is supported.

poweredOnMonitorTypeChangeSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether a monitor type change is supported while the virtual machine is in the ``poweredOn`` state.

seSparseDiskSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether the virtual machine supports the Flex-SE (space-efficent, sparse) format for virtual disks.

nestedHVSupported (bool)
^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether the virtual machine supports nested hardware-assisted virtualization.

vPMCSupported (bool)
^^^^^^^^^^^^^^^^^^^^

    Indicates whether the virtual machine supports virtualized CPU performance counters.


config
------

This section describes the configuration settings of the virtual machine, including the name and UUID.
This property is set when a virtual machine is created or when the ``reconfigVM`` method is called.
The virtual machine configuration is not guaranteed to be available.
For example, the configuration information would be unavailable if the server is unable to access the virtual machine files on disk, and is often also unavailable during the initial phases of virtual machine creation.

changeVersion (str)
^^^^^^^^^^^^^^^^^^^

    The changeVersion is a unique identifier for a given version of the configuration.
    Each change to the configuration updates this value. This is typically implemented as an ever increasing count or a time-stamp.
    However, a client should always treat this as an opaque string.

modified (datetime)
^^^^^^^^^^^^^^^^^^^

    Last time a virtual machine's configuration was modified.

name (str)
^^^^^^^^^^

    Display name of the virtual machine. Any / (slash), \ (backslash), character used in this name element is escaped. Similarly, any % (percent) character used in this name element is escaped, unless it is used to start an escape sequence. A slash is escaped as %2F or %2f. A backslash is escaped as %5C or %5c, and a percent is escaped as %25.

.. _guest_full_name:

guestFullName (str)
^^^^^^^^^^^^^^^^^^^

    This is the full name of the guest operating system for the virtual machine. For example: Windows 2000 Professional. See :ref:`alternate_guest_name`.

version (str)
^^^^^^^^^^^^^

    The version string for the virtual machine.

uuid (str)
^^^^^^^^^^

    128-bit SMBIOS UUID of a virtual machine represented as a hexadecimal string in "12345678-abcd-1234-cdef-123456789abc" format.

instanceUuid (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    VirtualCenter-specific 128-bit UUID of a virtual machine, represented as a hexademical string. This identifier is used by VirtualCenter to uniquely identify all virtual machine instances, including those that may share the same SMBIOS UUID.

npivNodeWorldWideName (long, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    A 64-bit node WWN (World Wide Name).

npivPortWorldWideName (long, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    A 64-bit port WWN (World Wide Name).

npivWorldWideNameType (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The source that provides/generates the assigned WWNs.

npivDesiredNodeWwns (short, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The NPIV node WWNs to be extended from the original list of WWN numbers.

npivDesiredPortWwns (short, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The NPIV port WWNs to be extended from the original list of WWN numbers.

npivTemporaryDisabled (bool, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    This property is used to enable or disable the NPIV capability on a desired virtual machine on a temporary basis.

npivOnNonRdmDisks (bool, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    This property is used to check whether the NPIV can be enabled on the Virtual machine with non-rdm disks in the configuration, so this is potentially not enabling npiv on vmfs disks.
    Also this property is used to check whether RDM is required to generate WWNs for a virtual machine.

locationId (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^

    Hash incorporating the virtual machine's config file location and the UUID of the host assigned to run the virtual machine.

template (bool)
^^^^^^^^^^^^^^^

    Flag indicating whether or not a virtual machine is a template.

guestId (str)
^^^^^^^^^^^^^

    Guest operating system configured on a virtual machine.

.. _alternate_guest_name:

alternateGuestName (str)
^^^^^^^^^^^^^^^^^^^^^^^^

    Used as display name for the operating system if guestId isotherorother-64. See :ref:`guest_full_name`.

annotation (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^

    Description for the virtual machine.

files (vim.vm.FileInfo)
^^^^^^^^^^^^^^^^^^^^^^^

    Information about the files associated with a virtual machine.
    This information does not include files for specific virtual disks or snapshots.

tools (vim.vm.ToolsConfigInfo, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Configuration of VMware Tools running in the guest operating system.

flags (vim.vm.FlagInfo)
^^^^^^^^^^^^^^^^^^^^^^^

    Additional flags for a virtual machine.

consolePreferences (vim.vm.ConsolePreferences, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Legacy console viewer preferences when doing power operations.

defaultPowerOps (vim.vm.DefaultPowerOpInfo)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Configuration of default power operations.

hardware (vim.vm.VirtualHardware)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Processor, memory, and virtual devices for a virtual machine.

cpuAllocation (vim.ResourceAllocationInfo, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Resource limits for CPU.

memoryAllocation (vim.ResourceAllocationInfo, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Resource limits for memory.

latencySensitivity (vim.LatencySensitivity, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The latency-sensitivity of the virtual machine.

memoryHotAddEnabled (bool, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Whether memory can be added while the virtual machine is running.

cpuHotAddEnabled (bool, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Whether virtual processors can be added while the virtual machine is running.

cpuHotRemoveEnabled (bool, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Whether virtual processors can be removed while the virtual machine is running.

hotPlugMemoryLimit (long, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The maximum amount of memory, in MB, than can be added to a running virtual machine.

hotPlugMemoryIncrementSize (long, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Memory, in MB that can be added to a running virtual machine.

cpuAffinity (vim.vm.AffinityInfo, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Affinity settings for CPU.

memoryAffinity (vim.vm.AffinityInfo, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Affinity settings for memory.

networkShaper (vim.vm.NetworkShaperInfo, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Resource limits for network.

extraConfig (vim.option.OptionValue, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Additional configuration information for the virtual machine.

cpuFeatureMask (vim.host.CpuIdInfo, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Specifies CPU feature compatibility masks that override the defaults from the ``GuestOsDescriptor`` of the virtual machine's guest OS.

datastoreUrl (vim.vm.ConfigInfo.DatastoreUrlPair, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Enumerates the set of datastores that the virtual machine is stored on, as well as the URL identification for each of these.

swapPlacement (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Virtual machine swapfile placement policy.

bootOptions (vim.vm.BootOptions, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Configuration options for the boot behavior of the virtual machine.

ftInfo (vim.vm.FaultToleranceConfigInfo, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Fault tolerance settings for the virtual machine.

vAppConfig (vim.vApp.VmConfigInfo, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    vApp meta-data for the virtual machine.

vAssertsEnabled (bool, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether user-configured virtual asserts will be triggered during virtual machine replay.

changeTrackingEnabled (bool, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether changed block tracking for the virtual machine's disks is active.

firmware (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^

    Information about firmware type for the virtual machine.

maxMksConnections (int, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates the maximum number of active remote display connections that the virtual machine will support.

guestAutoLockEnabled (bool, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether the guest operating system will logout any active sessions whenever there are no remote display connections open to the virtual machine.

managedBy (vim.ext.ManagedByInfo, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Specifies that the virtual machine is managed by a VC Extension.

.. _memory_reservation_locked_to_max:

memoryReservationLockedToMax (bool, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    If set true, memory resource reservation for the virtual machine will always be equal to the virtual machine's memory size; increases in memory size will be rejected when a corresponding reservation increase is not possible.

initialOverhead (vim.vm.ConfigInfo.OverheadInfo), optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Set of values to be used only to perform admission control when determining if a host has sufficient resources for the virtual machine to power on.

nestedHVEnabled (bool, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether the virtual machine is configured to use nested hardware-assisted virtualization.

vPMCEnabled (bool, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether the virtual machine have virtual CPU performance counters enabled.

scheduledHardwareUpgradeInfo (vim.vm.ScheduledHardwareUpgradeInfo, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Configuration of scheduled hardware upgrades and result from last attempt to run scheduled hardware upgrade.

vFlashCacheReservation (long, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Specifies the total vFlash resource reservation for the vFlash caches associated with the virtual machine's virtual disks, in bytes.

layout
------

Detailed information about the files that comprise the virtual machine.

configFile (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^

    A list of files that makes up the configuration of the virtual machine (excluding the .vmx file, since that file is represented in the FileInfo).
    These are relative paths from the configuration directory.
    A slash is always used as a separator.
    This list will typically include the NVRAM file, but could also include other meta-data files.

logFile (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^

    A list of files stored in the virtual machine's log directory.
    These are relative paths from the ``logDirectory``.
    A slash is always used as a separator.

disk (vim.vm.FileLayout.DiskLayout, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Files making up each virtual disk.

snapshot (vim.vm.FileLayout.SnapshotLayout, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Files of each snapshot.

swapFile (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^

    The swapfile specific to the virtual machine, if any. This is a complete datastore path, not a relative path.


layoutEx
--------

Detailed information about the files that comprise the virtual machine.

file (vim.vm.FileLayoutEx.FileInfo, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Information about all the files that constitute the virtual machine including configuration files, disks, swap file, suspend file, log files, core files, memory file and so on.

disk (vim.vm.FileLayoutEx.DiskLayout, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Layout of each virtual disk attached to the virtual machine.
    For a virtual machine with snaphots, this property gives only those disks that are attached to it at the current point of running.

snapshot (vim.vm.FileLayoutEx.SnapshotLayout, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Layout of each snapshot of the virtual machine.

timestamp (datetime)
^^^^^^^^^^^^^^^^^^^^

    Time when values in this structure were last updated.

storage (vim.vm.StorageInfo)
----------------------------

Storage space used by the virtual machine, split by datastore.

perDatastoreUsage (vim.vm.StorageInfo.UsageOnDatastore, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Storage space used by the virtual machine on all datastores that it is located on.
    Total storage space committed to the virtual machine across all datastores is simply an aggregate of the property ``committed``

timestamp (datetime)
^^^^^^^^^^^^^^^^^^^^

    Time when values in this structure were last updated.

environmentBrowser (vim.EnvironmentBrowser)
-------------------------------------------

The current virtual machine's environment browser object.
This contains information on all the configurations that can be used on the virtual machine.
This is identical to the environment browser on the ComputeResource to which the virtual machine belongs.

datastoreBrowser (vim.host.DatastoreBrowser)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    DatastoreBrowser to browse datastores that are available on this entity.

resourcePool (vim.ResourcePool)
-------------------------------

The current resource pool that specifies resource allocation for the virtual machine.
This property is set when a virtual machine is created or associated with a different resource pool.
Returns null if the virtual machine is a template or the session has no access to the resource pool.

summary (vim.ResourcePool.Summary)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Basic information about a resource pool.

runtime (vim.ResourcePool.RuntimeInfo)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Runtime information about a resource pool.

owner (vim.ComputeResource)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The ComputeResource to which this set of one or more nested resource pools belong.

resourcePool (vim.ResourcePool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The set of child resource pools.

vm (vim.VirtualMachine)
^^^^^^^^^^^^^^^^^^^^^^^

    The set of virtual machines associated with this resource pool.

config (vim.ResourceConfigSpec)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Configuration of this resource pool.

childConfiguration (vim.ResourceConfigSpec)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The resource configuration of all direct children (VirtualMachine and ResourcePool) of this resource group.

parentVApp (vim.ManagedEntity)
------------------------------

Reference to the parent vApp.

parent (vim.ManagedEntity)
^^^^^^^^^^^^^^^^^^^^^^^^^^

    Parent of this entity.
    This value is null for the root object and for (VirtualMachine) objects that are part of a (VirtualApp).

customValue (vim.CustomFieldsManager.Value)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Custom field values.

overallStatus (vim.ManagedEntity.Status)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    General health of this managed entity.

configStatus (vim.ManagedEntity.Status)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The configStatus indicates whether or not the system has detected a configuration issue involving this entity.
    For example, it might have detected a duplicate IP address or MAC address, or a host in a cluster might be out of ``compliance.property``.

configIssue (vim.event.Event)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Current configuration issues that have been detected for this entity.

effectiveRole (int)
^^^^^^^^^^^^^^^^^^^

    Access rights the current session has to this entity.

permission (vim.AuthorizationManager.Permission)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    List of permissions defined for this entity.

name (str)
^^^^^^^^^^

    Name of this entity, unique relative to its parent.
    Any / (slash), \ (backslash), character used in this name element will be escaped.
    Similarly, any % (percent) character used in this name element will be escaped, unless it is used to start an escape sequence.
    A slash is escaped as %2F or %2f. A backslash is escaped as %5C or %5c, and a percent is escaped as %25.

disabledMethod (str)
^^^^^^^^^^^^^^^^^^^^

    List of operations that are disabled, given the current runtime state of the entity.
    For example, a power-on operation always fails if a virtual machine is already powered on.

recentTask (vim.Task)
^^^^^^^^^^^^^^^^^^^^^

    The set of recent tasks operating on this managed entity.
    A task in this list could be in one of the four states: pending, running, success or error.

declaredAlarmState (vim.alarm.AlarmState)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    A set of alarm states for alarms that apply to this managed entity.

triggeredAlarmState (vim.alarm.AlarmState)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    A set of alarm states for alarms triggered by this entity or by its descendants.

alarmActionsEnabled (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^

    Whether alarm actions are enabled for this entity. True if enabled; false otherwise.

tag (vim.Tag)
^^^^^^^^^^^^^

    The set of tags associated with this managed entity. Experimental. Subject to change.

resourceConfig (vim.ResourceConfigSpec)
---------------------------------------

    The resource configuration for a virtual machine.

entity (vim.ManagedEntity, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Reference to the entity with this resource specification: either a VirtualMachine or a ResourcePool.

changeVersion (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The changeVersion is a unique identifier for a given version of the configuration. Each change to the configuration will update this value.
    This is typically implemented as an ever increasing count or a time-stamp.


lastModified (datetime, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Timestamp when the resources were last modified. This is ignored when the object is used to update a configuration.

cpuAllocation (vim.ResourceAllocationInfo)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Resource allocation for CPU.

memoryAllocation (vim.ResourceAllocationInfo)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Resource allocation for memory.

runtime (vim.vm.RuntimeInfo)
----------------------------

Execution state and history for the virtual machine.

device (vim.vm.DeviceRuntimeInfo, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Per-device runtime info. This array will be empty if the host software does not provide runtime info for any of the device types currently in use by the virtual machine.

host (vim.HostSystem, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The host that is responsible for running a virtual machine.
    This property is null if the virtual machine is not running and is not assigned to run on a particular host.

connectionState (vim.VirtualMachine.ConnectionState)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Indicates whether or not the virtual machine is available for management.

powerState (vim.VirtualMachine.PowerState)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The current power state of the virtual machine.

faultToleranceState (vim.VirtualMachine.FaultToleranceState)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The fault tolerance state of the virtual machine.

dasVmProtection (vim.vm.RuntimeInfo.DasProtectionState, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The vSphere HA protection state for a virtual machine.
    Property is unset if vSphere HA is not enabled.

toolsInstallerMounted (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Flag to indicate whether or not the VMware Tools installer is mounted as a CD-ROM.

suspendTime (datetime, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The timestamp when the virtual machine was most recently suspended.
    This property is updated every time the virtual machine is suspended.

bootTime (datetime, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The timestamp when the virtual machine was most recently powered on.
    This property is updated when the virtual machine is powered on from the poweredOff state, and is cleared when the virtual machine is powered off.
    This property is not updated when a virtual machine is resumed from a suspended state.

suspendInterval (long, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The total time the virtual machine has been suspended since it was initially powered on.
    This time excludes the current period, if the virtual machine is currently suspended.
    This property is updated when the virtual machine resumes, and is reset to zero when the virtual machine is powered off.

question (vim.vm.QuestionInfo, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The current question, if any, that is blocking the virtual machine's execution.

memoryOverhead (long, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The amount of memory resource (in bytes) that will be used by the virtual machine above its guest memory requirements.
    This value is set if and only if the virtual machine is registered on a host that supports memory resource allocation features.
    For powered off VMs, this is the minimum overhead required to power on the VM on the registered host.
    For powered on VMs, this is the current overhead reservation, a value which is almost always larger than the minimum overhead, and which grows with time.

maxCpuUsage (int, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Current upper-bound on CPU usage.
    The upper-bound is based on the host the virtual machine is current running on, as well as limits configured on the virtual machine itself or any parent resource pool.
    Valid while the virtual machine is running.

maxMemoryUsage (int, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Current upper-bound on memory usage.
    The upper-bound is based on memory configuration of the virtual machine, as well as limits configured on the virtual machine itself or any parent resource pool.
    Valid while the virtual machine is running.

numMksConnections (int)
^^^^^^^^^^^^^^^^^^^^^^^

    Number of active MKS connections to the virtual machine.

recordReplayState (vim.VirtualMachine.RecordReplayState)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Record / replay state of the virtual machine.

cleanPowerOff (bool, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    For a powered off virtual machine, indicates whether the virtual machine's last shutdown was an orderly power off or not.
    Unset if the virtual machine is running or suspended.

needSecondaryReason (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    If set, indicates the reason the virtual machine needs a secondary.

onlineStandby (bool)
^^^^^^^^^^^^^^^^^^^^

    This property indicates whether the guest has gone into one of the s1, s2 or s3 standby modes. False indicates the guest is awake.

minRequiredEVCModeKey (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    For a powered-on or suspended virtual machine in a cluster with Enhanced VMotion Compatibility (EVC) enabled, this identifies the least-featured EVC mode (among those for the appropriate CPU vendor) that could admit the virtual machine.
    This property will be unset if the virtual machine is powered off or is not in an EVC cluster.
    This property may be used as a general indicator of the CPU feature baseline currently in use by the virtual machine.
    However, the virtual machine may be suppressing some of the features present in the CPU feature baseline of the indicated mode, either explicitly (in the virtual machine's configured ``cpuFeatureMask``) or implicitly (in the default masks for the ``GuestOsDescriptor`` appropriate for the virtual machine's configured guest OS).

consolidationNeeded (bool)
^^^^^^^^^^^^^^^^^^^^^^^^^^

    Whether any disk of the virtual machine requires consolidation.
    This can happen for example when a snapshot is deleted but its associated disk is not committed back to the base disk.

offlineFeatureRequirement (vim.vm.FeatureRequirement, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    These requirements must have equivalent host capabilities ``featureCapability`` in order to power on.

featureRequirement (vim.vm.FeatureRequirement, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    These requirements must have equivalent host capabilities ``featureCapability`` in order to power on, resume, or migrate to the host.

featureMask (vim.host.FeatureMask, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    The masks applied to an individual virtual machine as a result of its configuration.

vFlashCacheAllocation (long, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Specifies the total allocated vFlash resource for the vFlash caches associated with VM's VMDKs when VM is powered on, in bytes.


guest (vim.vm.GuestInfo)
------------------------

Information about VMware Tools and about the virtual machine from the perspective of VMware Tools.
Information about the guest operating system is available in VirtualCenter.
Guest operating system information reflects the last known state of the virtual machine.
For powered on machines, this is current information.
For powered off machines, this is the last recorded state before the virtual machine was powered off.

toolsStatus (vim.vm.GuestInfo.ToolsStatus, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Current status of VMware Tools in the guest operating system, if known.

toolsVersionStatus (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Current version status of VMware Tools in the guest operating system, if known.

toolsVersionStatus2 (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Current version status of VMware Tools in the guest operating system, if known.

toolsRunningStatus (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Current running status of VMware Tools in the guest operating system, if known.

toolsVersion (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Current version of VMware Tools, if known.

guestId (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^

    Guest operating system identifier (short name), if known.

guestFamily (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Guest operating system family, if known.

guestFullName (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    See :ref:`guest_full_name`.

hostName (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^

    Hostname of the guest operating system, if known.

ipAddress (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^

    Primary IP address assigned to the guest operating system, if known.

net (vim.vm.GuestInfo.NicInfo, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Guest information about network adapters, if known.

ipStack (vim.vm.GuestInfo.StackInfo, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Guest information about IP networking stack, if known.

disk (vim.vm.GuestInfo.DiskInfo, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Guest information about disks.
    You can obtain Linux guest disk information for the following file system types only: Ext2, Ext3, Ext4, ReiserFS, ZFS, NTFS, VFAT, UFS, PCFS, HFS, and MS-DOS.

screen (vim.vm.GuestInfo.ScreenInfo, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Guest screen resolution info, if known.

guestState (str)
^^^^^^^^^^^^^^^^

    Operation mode of guest operating system.

appHeartbeatStatus (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Application heartbeat status.

appState (str, optional)
^^^^^^^^^^^^^^^^^^^^^^^^

    Application state.
    If vSphere HA is enabled and the vm is configured for Application Monitoring and this field's value is ``appStateNeedReset`` then HA will attempt immediately reset the virtual machine.
    There are some system conditions which may delay the immediate reset.
    The immediate reset will be performed as soon as allowed by vSphere HA and ESX.
    If during these conditions the value is changed to ``appStateOk`` the reset will be cancelled.

guestOperationsReady (bool, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Guest Operations availability. If true, the vitrual machine is ready to process guest operations.

interactiveGuestOperationsReady (bool, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Interactive Guest Operations availability. If true, the virtual machine is ready to process guest operations as the user interacting with the guest desktop.

generationInfo (vim.vm.GuestInfo.NamespaceGenerationInfo, privilege: VirtualMachine.Namespace.EventNotify, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    A list of namespaces and their corresponding generation numbers. Only namespaces with non-zero ``maxSizeEventsFromGuest`` are guaranteed to be present here.


summary (vim.vm.Summary)
------------------------

    Basic information about the virtual machine.

vm (vim.VirtualMachine, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Reference to the virtual machine managed object.

runtime (vim.vm.RuntimeInfo)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Runtime and state information of a running virtual machine.
    Most of this information is also available when a virtual machine is powered off.
    In that case, it contains information from the last run, if available.

guest (vim.vm.Summary.GuestSummary, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Guest operating system and VMware Tools information.

config (vim.vm.Summary.ConfigSummary)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Basic configuration information about the virtual machine.
    This information is not available when the virtual machine is unavailable, for instance, when it is being created or deleted.

storage (vim.vm.Summary.StorageSummary, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Storage information of the virtual machine.

quickStats (vim.vm.Summary.QuickStats)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    A set of statistics that are typically updated with near real-time regularity.

overallStatus (vim.ManagedEntity.Status)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Overall alarm status on this node.

customValue (vim.CustomFieldsManager.Value, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Custom field values.


datastore (vim.Datastore)
-------------------------

    A collection of references to the subset of datastore objects in the datacenter that is used by the virtual machine.

info (vim.Datastore.Info)
^^^^^^^^^^^^^^^^^^^^^^^^^

    Specific information about the datastore.

summary (vim.Datastore.Summary)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Global properties of the datastore.

host (vim.Datastore.HostMount)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Hosts attached to this datastore.

vm (vim.VirtualMachine)
^^^^^^^^^^^^^^^^^^^^^^^

    Virtual machines stored on this datastore.

browser (vim.host.DatastoreBrowser)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    DatastoreBrowser used to browse this datastore.

capability (vim.Datastore.Capability)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Capabilities of this datastore.

iormConfiguration (vim.StorageResourceManager.IORMConfigInfo)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Configuration of storage I/O resource management for the datastore.
    Currently VMware only support storage I/O resource management on VMFS volumes of a datastore.
    This configuration may not be available if the datastore is not accessible from any host, or if the datastore does not have VMFS volume.

network (vim.Network)
---------------------

    A collection of references to the subset of network objects in the datacenter that is used by the virtual machine.

name (str)
^^^^^^^^^^

    Name of this network.

summary (vim.Network.Summary)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Properties of a network.

host (vim.HostSystem)
^^^^^^^^^^^^^^^^^^^^^

    Hosts attached to this network.

vm (vim.VirtualMachine)
^^^^^^^^^^^^^^^^^^^^^^^

    Virtual machines using this network.


snapshot (vim.vm.SnapshotInfo)
-------------------------------

Current snapshot and tree.
The property is valid if snapshots have been created for the virtual machine.

currentSnapshot (vim.vm.Snapshot, optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Current snapshot of the virtual machineThis property is set by calling ``Snapshot.revert`` or ``VirtualMachine.createSnapshot``.
    This property will be empty when the working snapshot is at the root of the snapshot tree.

rootSnapshotList (vim.vm.SnapshotTree)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Data for the entire set of snapshots for one virtual machine.

rootSnapshot (vim.vm.Snapshot)
------------------------------

The roots of all snapshot trees for the virtual machine.

config (vim.vm.ConfigInfo)
^^^^^^^^^^^^^^^^^^^^^^^^^^

    Information about the configuration of the virtual machine when this snapshot was taken.
    The datastore paths for the virtual machine disks point to the head of the disk chain that represents the disk at this given snapshot.

childSnapshot (vim.vm.Snapshot)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    All snapshots for which this snapshot is the parent.

guestHeartbeatStatus (vim.ManagedEntity.Status)
-----------------------------------------------

    The guest heartbeat.

.. seealso::

    `pyVmomi <https://github.com/vmware/pyvmomi>`_
        The GitHub Page of pyVmomi
    `pyVmomi Issue Tracker <https://github.com/vmware/pyvmomi/issues>`_
        The issue tracker for the pyVmomi project
    rst/scenario_guides/guide_vmware.rst
        The GitHub Page of vSphere Automation SDK for Python
    `vSphere Automation SDK Issue Tracker <https://github.com/vmware/vsphere-automation-sdk-python/issues>`_
        The issue tracker for vSphere Automation SDK for Python
    :ref:`working_with_playbooks`
        An introduction to playbooks
    :ref:`playbooks_vault`
        Using Vault in playbooks
