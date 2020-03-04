using Microsoft.Win32.SafeHandles;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.ConstrainedExecution;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;
using Ansible.Privilege;

namespace Ansible.Service
{
    internal class NativeHelpers
    {
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public struct ENUM_SERVICE_STATUSW
        {
            public string lpServiceName;
            public string lpDisplayName;
            public SERVICE_STATUS ServiceStatus;
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public struct QUERY_SERVICE_CONFIGW
        {
            public ServiceType dwServiceType;
            public ServiceStartType dwStartType;
            public ErrorControl dwErrorControl;
            [MarshalAs(UnmanagedType.LPWStr)] public string lpBinaryPathName;
            [MarshalAs(UnmanagedType.LPWStr)] public string lpLoadOrderGroup;
            public Int32 dwTagId;
            public IntPtr lpDependencies;  // Can't rely on marshaling as dependencies are delimited by \0.
            [MarshalAs(UnmanagedType.LPWStr)] public string lpServiceStartName;
            [MarshalAs(UnmanagedType.LPWStr)] public string lpDisplayName;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct SC_ACTION
        {
            public FailureAction Type;
            public UInt32 Delay;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct SERVICE_DELAYED_AUTO_START_INFO
        {
            public bool fDelayedAutostart;
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public struct SERVICE_DESCRIPTIONW
        {
            [MarshalAs(UnmanagedType.LPWStr)] public string lpDescription;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct SERVICE_FAILURE_ACTIONS_FLAG
        {
            public bool fFailureActionsOnNonCrashFailures;
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public struct SERVICE_FAILURE_ACTIONSW
        {
            public UInt32 dwResetPeriod;
            [MarshalAs(UnmanagedType.LPWStr)] public string lpRebootMsg;
            [MarshalAs(UnmanagedType.LPWStr)] public string lpCommand;
            public UInt32 cActions;
            public IntPtr lpsaActions;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct SERVICE_LAUNCH_PROTECTED_INFO
        {
            public LaunchProtection dwLaunchProtected;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct SERVICE_PREFERRED_NODE_INFO
        {
            public UInt16 usPreferredNode;
            public bool fDelete;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct SERVICE_PRESHUTDOWN_INFO
        {
            public UInt32 dwPreshutdownTimeout;
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public struct SERVICE_REQUIRED_PRIVILEGES_INFOW
        {
            // Can't rely on marshaling as privileges are delimited by \0.
            public IntPtr pmszRequiredPrivileges;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct SERVICE_SID_INFO
        {
            public ServiceSidInfo dwServiceSidType;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct SERVICE_STATUS
        {
            public ServiceType dwServiceType;
            public ServiceStatus dwCurrentState;
            public ControlsAccepted dwControlsAccepted;
            public UInt32 dwWin32ExitCode;
            public UInt32 dwServiceSpecificExitCode;
            public UInt32 dwCheckPoint;
            public UInt32 dwWaitHint;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct SERVICE_STATUS_PROCESS
        {
            public ServiceType dwServiceType;
            public ServiceStatus dwCurrentState;
            public ControlsAccepted dwControlsAccepted;
            public UInt32 dwWin32ExitCode;
            public UInt32 dwServiceSpecificExitCode;
            public UInt32 dwCheckPoint;
            public UInt32 dwWaitHint;
            public UInt32 dwProcessId;
            public ServiceFlags dwServiceFlags;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct SERVICE_TRIGGER
        {
            public TriggerType dwTriggerType;
            public TriggerAction dwAction;
            public IntPtr pTriggerSubtype;
            public UInt32 cDataItems;
            public IntPtr pDataItems;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct SERVICE_TRIGGER_SPECIFIC_DATA_ITEM
        {
            public TriggerDataType dwDataType;
            public UInt32 cbData;
            public IntPtr pData;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct SERVICE_TRIGGER_INFO
        {
            public UInt32 cTriggers;
            public IntPtr pTriggers;
            public IntPtr pReserved;
        }

        public enum ConfigInfoLevel : uint
        {
            SERVICE_CONFIG_DESCRIPTION = 0x00000001,
            SERVICE_CONFIG_FAILURE_ACTIONS = 0x00000002,
            SERVICE_CONFIG_DELAYED_AUTO_START_INFO = 0x00000003,
            SERVICE_CONFIG_FAILURE_ACTIONS_FLAG = 0x00000004,
            SERVICE_CONFIG_SERVICE_SID_INFO = 0x00000005,
            SERVICE_CONFIG_REQUIRED_PRIVILEGES_INFO = 0x00000006,
            SERVICE_CONFIG_PRESHUTDOWN_INFO = 0x00000007,
            SERVICE_CONFIG_TRIGGER_INFO = 0x00000008,
            SERVICE_CONFIG_PREFERRED_NODE = 0x00000009,
            SERVICE_CONFIG_LAUNCH_PROTECTED = 0x0000000c,
        }
    }

    internal class NativeMethods
    {
        [DllImport("Advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        public static extern bool ChangeServiceConfigW(
            SafeHandle hService,
            ServiceType dwServiceType,
            ServiceStartType dwStartType,
            ErrorControl dwErrorControl,
            string lpBinaryPathName,
            string lpLoadOrderGroup,
            IntPtr lpdwTagId,
            string lpDependencies,
            string lpServiceStartName,
            string lpPassword,
            string lpDisplayName);

        [DllImport("Advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        public static extern bool ChangeServiceConfig2W(
            SafeHandle hService,
            NativeHelpers.ConfigInfoLevel dwInfoLevel,
            IntPtr lpInfo);

        [DllImport("Advapi32.dll", SetLastError = true)]
        public static extern bool CloseServiceHandle(
            IntPtr hSCObject);

        [DllImport("Advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        public static extern SafeServiceHandle CreateServiceW(
            SafeHandle hSCManager,
            string lpServiceName,
            string lpDisplayName,
            ServiceRights dwDesiredAccess,
            ServiceType dwServiceType,
            ServiceStartType dwStartType,
            ErrorControl dwErrorControl,
            string lpBinaryPathName,
            string lpLoadOrderGroup,
            IntPtr lpdwTagId,
            string lpDependencies,
            string lpServiceStartName,
            string lpPassword);

        [DllImport("Advapi32.dll", SetLastError = true)]
        public static extern bool DeleteService(
            SafeHandle hService);

        [DllImport("Advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        public static extern bool EnumDependentServicesW(
            SafeHandle hService,
            UInt32 dwServiceState,
            SafeMemoryBuffer lpServices,
            UInt32 cbBufSize,
            out UInt32 pcbBytesNeeded,
            out UInt32 lpServicesReturned);

        [DllImport("Advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        public static extern SafeServiceHandle OpenSCManagerW(
            string lpMachineName,
            string lpDatabaseNmae,
            SCMRights dwDesiredAccess);

        [DllImport("Advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        public static extern SafeServiceHandle OpenServiceW(
            SafeHandle hSCManager,
            string lpServiceName,
            ServiceRights dwDesiredAccess);

        [DllImport("Advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        public static extern bool QueryServiceConfigW(
            SafeHandle hService,
            IntPtr lpServiceConfig,
            UInt32 cbBufSize,
            out UInt32 pcbBytesNeeded);

        [DllImport("Advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        public static extern bool QueryServiceConfig2W(
            SafeHandle hservice,
            NativeHelpers.ConfigInfoLevel dwInfoLevel,
            IntPtr lpBuffer,
            UInt32 cbBufSize,
            out UInt32 pcbBytesNeeded);

        [DllImport("Advapi32.dll", SetLastError = true)]
        public static extern bool QueryServiceStatusEx(
            SafeHandle hService,
            UInt32 InfoLevel,
            IntPtr lpBuffer,
            UInt32 cbBufSize,
            out UInt32 pcbBytesNeeded);
    }

    internal class SafeMemoryBuffer : SafeHandleZeroOrMinusOneIsInvalid
    {
        public UInt32 BufferLength { get; internal set; }

        public SafeMemoryBuffer() : base(true) { }
        public SafeMemoryBuffer(int cb) : base(true)
        {
            BufferLength = (UInt32)cb;
            base.SetHandle(Marshal.AllocHGlobal(cb));
        }
        public SafeMemoryBuffer(IntPtr handle) : base(true)
        {
            base.SetHandle(handle);
        }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.MayFail)]
        protected override bool ReleaseHandle()
        {
            Marshal.FreeHGlobal(handle);
            return true;
        }
    }

    internal class SafeServiceHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        public SafeServiceHandle() : base(true) { }
        public SafeServiceHandle(IntPtr handle) : base(true) { this.handle = handle; }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.MayFail)]
        protected override bool ReleaseHandle()
        {
            return NativeMethods.CloseServiceHandle(handle);
        }
    }

    [Flags]
    public enum ControlsAccepted : uint
    {
        None = 0x00000000,
        Stop = 0x00000001,
        PauseContinue = 0x00000002,
        Shutdown = 0x00000004,
        ParamChange = 0x00000008,
        NetbindChange = 0x00000010,
        HardwareProfileChange = 0x00000020,
        PowerEvent = 0x00000040,
        SessionChange = 0x00000080,
        PreShutdown = 0x00000100,
    }

    public enum ErrorControl : uint
    {
        Ignore = 0x00000000,
        Normal = 0x00000001,
        Severe = 0x00000002,
        Critical = 0x00000003,
    }

    public enum FailureAction : uint
    {
        None = 0x00000000,
        Restart = 0x00000001,
        Reboot = 0x00000002,
        RunCommand = 0x00000003,
    }

    public enum LaunchProtection : uint
    {
        None = 0,
        Windows = 1,
        WindowsLight = 2,
        AntimalwareLight = 3,
    }

    [Flags]
    public enum SCMRights : uint
    {
        Connect = 0x00000001,
        CreateService = 0x00000002,
        EnumerateService = 0x00000004,
        Lock = 0x00000008,
        QueryLockStatus = 0x00000010,
        ModifyBootConfig = 0x00000020,
        AllAccess = 0x000F003F,
    }

    [Flags]
    public enum ServiceFlags : uint
    {
        None = 0x0000000,
        RunsInSystemProcess = 0x00000001,
    }

    [Flags]
    public enum ServiceRights : uint
    {
        QueryConfig = 0x00000001,
        ChangeConfig = 0x00000002,
        QueryStatus = 0x00000004,
        EnumerateDependents = 0x00000008,
        Start = 0x00000010,
        Stop = 0x00000020,
        PauseContinue = 0x00000040,
        Interrogate = 0x00000080,
        UserDefinedControl = 0x00000100,
        Delete = 0x00010000,
        ReadControl = 0x00020000,
        WriteDac = 0x00040000,
        WriteOwner = 0x00080000,
        AllAccess = 0x000F01FF,
        AccessSystemSecurity = 0x01000000,
    }

    public enum ServiceStartType : uint
    {
        BootStart = 0x00000000,
        SystemStart = 0x00000001,
        AutoStart = 0x00000002,
        DemandStart = 0x00000003,
        Disabled = 0x00000004,

        // Not part of ChangeServiceConfig enumeration but built by the Srvice class for the StartType property.
        AutoStartDelayed = 0x1000000
    }

    [Flags]
    public enum ServiceType : uint
    {
        KernelDriver = 0x00000001,
        FileSystemDriver = 0x00000002,
        Adapter = 0x00000004,
        RecognizerDriver = 0x00000008,
        Driver = KernelDriver | FileSystemDriver | RecognizerDriver,
        Win32OwnProcess = 0x00000010,
        Win32ShareProcess = 0x00000020,
        Win32 = Win32OwnProcess | Win32ShareProcess,
        UserProcess = 0x00000040,
        UserOwnprocess = Win32OwnProcess | UserProcess,
        UserShareProcess = Win32ShareProcess | UserProcess,
        UserServiceInstance = 0x00000080,
        InteractiveProcess = 0x00000100,
        PkgService = 0x00000200,
    }

    public enum ServiceSidInfo : uint
    {
        None,
        Unrestricted,
        Restricted = 3,
    }

    public enum ServiceStatus : uint
    {
        Stopped = 0x00000001,
        StartPending = 0x00000002,
        StopPending = 0x00000003,
        Running = 0x00000004,
        ContinuePending = 0x00000005,
        PausePending = 0x00000006,
        Paused = 0x00000007,
    }

    public enum TriggerAction : uint
    {
        ServiceStart = 0x00000001,
        ServiceStop = 0x000000002,
    }

    public enum TriggerDataType : uint
    {
        Binary = 00000001,
        String = 0x00000002,
        Level = 0x00000003,
        KeywordAny = 0x00000004,
        KeywordAll = 0x00000005,
    }

    public enum TriggerType : uint
    {
        DeviceInterfaceArrival = 0x00000001,
        IpAddressAvailability = 0x00000002,
        DomainJoin = 0x00000003,
        FirewallPortEvent = 0x00000004,
        GroupPolicy = 0x00000005,
        NetworkEndpoint = 0x00000006,
        Custom = 0x00000014,
    }

    public class ServiceManagerException : System.ComponentModel.Win32Exception
    {
        private string _msg;

        public ServiceManagerException(string message) : this(Marshal.GetLastWin32Error(), message) { }
        public ServiceManagerException(int errorCode, string message) : base(errorCode)
        {
            _msg = String.Format("{0} ({1}, Win32ErrorCode {2} - 0x{2:X8})", message, base.Message, errorCode);
        }

        public override string Message { get { return _msg; } }
        public static explicit operator ServiceManagerException(string message)
        {
            return new ServiceManagerException(message);
        }
    }

    public class Action
    {
        public FailureAction Type;
        public UInt32 Delay;
    }

    public class FailureActions
    {
        public UInt32? ResetPeriod = null;  // Get is always populated, can be null on set to preserve existing.
        public string RebootMsg = null;
        public string Command = null;
        public List<Action> Actions = null;

        public FailureActions() { }

        internal FailureActions(NativeHelpers.SERVICE_FAILURE_ACTIONSW actions)
        {
            ResetPeriod = actions.dwResetPeriod;
            RebootMsg = actions.lpRebootMsg;
            Command = actions.lpCommand;
            Actions = new List<Action>();

            int actionLength = Marshal.SizeOf(typeof(NativeHelpers.SC_ACTION));
            for (int i = 0; i < actions.cActions; i++)
            {
                IntPtr actionPtr = IntPtr.Add(actions.lpsaActions, i * actionLength);

                NativeHelpers.SC_ACTION rawAction = (NativeHelpers.SC_ACTION)Marshal.PtrToStructure(
                    actionPtr, typeof(NativeHelpers.SC_ACTION));

                Actions.Add(new Action()
                {
                    Type = rawAction.Type,
                    Delay = rawAction.Delay,
                });
            }
        }
    }

    public class TriggerItem
    {
        public TriggerDataType Type;
        public object Data;  // Can be string, List<string>, byte, byte[], or Int64 depending on Type.

        public TriggerItem() { }

        internal TriggerItem(NativeHelpers.SERVICE_TRIGGER_SPECIFIC_DATA_ITEM dataItem)
        {
            Type = dataItem.dwDataType;

            byte[] itemBytes = new byte[dataItem.cbData];
            Marshal.Copy(dataItem.pData, itemBytes, 0, itemBytes.Length);

            switch (dataItem.dwDataType)
            {
                case TriggerDataType.String:
                    string value = Encoding.Unicode.GetString(itemBytes, 0, itemBytes.Length);

                    if (value.EndsWith("\0\0"))
                    {
                        // Multistring with a delimiter of \0 and terminated with \0\0.
                        Data = new List<string>(value.Split(new char[1] { '\0' }, StringSplitOptions.RemoveEmptyEntries));
                    }
                    else
                        // Just a single string with null character at the end, strip it off.
                        Data = value.Substring(0, value.Length - 1);
                    break;
                case TriggerDataType.Level:
                    Data = itemBytes[0];
                    break;
                case TriggerDataType.KeywordAll:
                case TriggerDataType.KeywordAny:
                    Data = BitConverter.ToUInt64(itemBytes, 0);
                    break;
                default:
                    Data = itemBytes;
                    break;
            }
        }
    }

    public class Trigger
    {
        // https://docs.microsoft.com/en-us/windows/win32/api/winsvc/ns-winsvc-service_trigger
        public const string NAMED_PIPE_EVENT_GUID = "1f81d131-3fac-4537-9e0c-7e7b0c2f4b55";
        public const string RPC_INTERFACE_EVENT_GUID = "bc90d167-9470-4139-a9ba-be0bbbf5b74d";
        public const string DOMAIN_JOIN_GUID = "1ce20aba-9851-4421-9430-1ddeb766e809";
        public const string DOMAIN_LEAVE_GUID = "ddaf516e-58c2-4866-9574-c3b615d42ea1";
        public const string FIREWALL_PORT_OPEN_GUID = "b7569e07-8421-4ee0-ad10-86915afdad09";
        public const string FIREWALL_PORT_CLOSE_GUID = "a144ed38-8e12-4de4-9d96-e64740b1a524";
        public const string MACHINE_POLICY_PRESENT_GUID = "659fcae6-5bdb-4da9-b1ff-ca2a178d46e0";
        public const string NETWORK_MANAGER_FIRST_IP_ADDRESS_ARRIVAL_GUID = "4f27f2de-14e2-430b-a549-7cd48cbc8245";
        public const string NETWORK_MANAGER_LAST_IP_ADDRESS_REMOVAL_GUID = "cc4ba62a-162e-4648-847a-b6bdf993e335";
        public const string USER_POLICY_PRESENT_GUID = "54fb46c8-f089-464c-b1fd-59d1b62c3b50";

        public TriggerType Type;
        public TriggerAction Action;
        public Guid SubType;
        public List<TriggerItem> DataItems = new List<TriggerItem>();

        public Trigger() { }

        internal Trigger(NativeHelpers.SERVICE_TRIGGER trigger)
        {
            Type = trigger.dwTriggerType;
            Action = trigger.dwAction;
            SubType = (Guid)Marshal.PtrToStructure(trigger.pTriggerSubtype, typeof(Guid));

            int dataItemLength = Marshal.SizeOf(typeof(NativeHelpers.SERVICE_TRIGGER_SPECIFIC_DATA_ITEM));
            for (int i = 0; i < trigger.cDataItems; i++)
            {
                IntPtr dataPtr = IntPtr.Add(trigger.pDataItems, i * dataItemLength);

                var dataItem = (NativeHelpers.SERVICE_TRIGGER_SPECIFIC_DATA_ITEM)Marshal.PtrToStructure(
                    dataPtr, typeof(NativeHelpers.SERVICE_TRIGGER_SPECIFIC_DATA_ITEM));

                DataItems.Add(new TriggerItem(dataItem));
            }
        }
    }

    public class Service : IDisposable
    {
        private const UInt32 SERVICE_NO_CHANGE = 0xFFFFFFFF;

        private SafeServiceHandle _scmHandle;
        private SafeServiceHandle _serviceHandle;
        private SafeMemoryBuffer _rawServiceConfig;
        private NativeHelpers.SERVICE_STATUS_PROCESS _statusProcess;

        private NativeHelpers.QUERY_SERVICE_CONFIGW _ServiceConfig
        {
            get
            {
                return (NativeHelpers.QUERY_SERVICE_CONFIGW)Marshal.PtrToStructure(
                    _rawServiceConfig.DangerousGetHandle(), typeof(NativeHelpers.QUERY_SERVICE_CONFIGW));
            }
        }

        // ServiceConfig
        public string ServiceName { get; private set; }

        public ServiceType ServiceType
        {
            get { return _ServiceConfig.dwServiceType; }
            set { ChangeServiceConfig(serviceType: value); }
        }

        public ServiceStartType StartType
        {
            get
            {
                ServiceStartType startType = _ServiceConfig.dwStartType;
                if (startType == ServiceStartType.AutoStart)
                {
                    var value = QueryServiceConfig2<NativeHelpers.SERVICE_DELAYED_AUTO_START_INFO>(
                        NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_DELAYED_AUTO_START_INFO);

                    if (value.fDelayedAutostart)
                        startType = ServiceStartType.AutoStartDelayed;
                }

                return startType;
            }
            set
            {
                ServiceStartType newStartType = value;
                bool delayedStart = false;
                if (value == ServiceStartType.AutoStartDelayed)
                {
                    newStartType = ServiceStartType.AutoStart;
                    delayedStart = true;
                }

                ChangeServiceConfig(startType: newStartType);

                var info = new NativeHelpers.SERVICE_DELAYED_AUTO_START_INFO()
                {
                    fDelayedAutostart = delayedStart,
                };
                ChangeServiceConfig2(NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_DELAYED_AUTO_START_INFO, info);
            }
        }

        public ErrorControl ErrorControl
        {
            get { return _ServiceConfig.dwErrorControl; }
            set { ChangeServiceConfig(errorControl: value); }
        }

        public string Path
        {
            get { return _ServiceConfig.lpBinaryPathName; }
            set { ChangeServiceConfig(binaryPath: value); }
        }

        public string LoadOrderGroup
        {
            get { return _ServiceConfig.lpLoadOrderGroup; }
            set { ChangeServiceConfig(loadOrderGroup: value); }
        }

        public List<string> DependentOn
        {
            get
            {
                StringBuilder deps = new StringBuilder();
                IntPtr depPtr = _ServiceConfig.lpDependencies;

                bool wasNull = false;
                while (true)
                {
                    // Get the current char at the pointer and add it to the StringBuilder.
                    byte[] charBytes = new byte[sizeof(char)];
                    Marshal.Copy(depPtr, charBytes, 0, charBytes.Length);
                    depPtr = IntPtr.Add(depPtr, charBytes.Length);
                    char currentChar = BitConverter.ToChar(charBytes, 0);
                    deps.Append(currentChar);

                    // If the previous and current char is \0 exit the loop.
                    if (currentChar == '\0' && wasNull)
                        break;
                    wasNull = currentChar == '\0';
                }

                return new List<string>(deps.ToString().Split(new char[1] { '\0' },
                    StringSplitOptions.RemoveEmptyEntries));
            }
            set { ChangeServiceConfig(dependencies: value); }
        }

        public IdentityReference Account
        {
            get
            {
                if (_ServiceConfig.lpServiceStartName == null)
                    // User services don't have the start name specified and will be null.
                    return null;
                else if (_ServiceConfig.lpServiceStartName == "LocalSystem")
                    // Special string used for the SYSTEM account, this is the same even for different localisations.
                    return (NTAccount)new SecurityIdentifier("S-1-5-18").Translate(typeof(NTAccount));
                else
                    return new NTAccount(_ServiceConfig.lpServiceStartName);
            }
            set
            {
                string startName = null;
                string pass = null;

                if (value != null)
                {
                    // Create a SID and convert back from a SID to get the Netlogon form regardless of the input
                    // specified.
                    SecurityIdentifier accountSid = (SecurityIdentifier)value.Translate(typeof(SecurityIdentifier));
                    NTAccount accountName = (NTAccount)accountSid.Translate(typeof(NTAccount));
                    string[] accountSplit = accountName.Value.Split(new char[1] { '\\' }, 2);

                    // SYSTEM, Local Service, Network Service
                    List<string> serviceAccounts = new List<string> { "S-1-5-18", "S-1-5-19", "S-1-5-20" };

                    // Well known service accounts and MSAs should have no password set. Explicitly blank out the
                    // existing password to ensure older passwords are no longer stored by Windows.
                    if (serviceAccounts.Contains(accountSid.Value) || accountSplit[1].EndsWith("$"))
                        pass = "";

                    // The SYSTEM account uses this special string to specify that account otherwise use the original
                    // NTAccount value in case it is in a custom format (not Netlogon) for a reason.
                    if (accountSid.Value == serviceAccounts[0])
                        startName = "LocalSystem";
                    else
                        startName = value.Translate(typeof(NTAccount)).Value;
                }

                ChangeServiceConfig(startName: startName, password: pass);
            }
        }

        public string Password { set { ChangeServiceConfig(password: value); } }

        public string DisplayName
        {
            get { return _ServiceConfig.lpDisplayName; }
            set { ChangeServiceConfig(displayName: value); }
        }

        // ServiceConfig2

        public string Description
        {
            get
            {
                var value = QueryServiceConfig2<NativeHelpers.SERVICE_DESCRIPTIONW>(
                    NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_DESCRIPTION);

                return value.lpDescription;
            }
            set
            {
                var info = new NativeHelpers.SERVICE_DESCRIPTIONW()
                {
                    lpDescription = value,
                };
                ChangeServiceConfig2(NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_DESCRIPTION, info);
            }
        }

        public FailureActions FailureActions
        {
            get
            {
                using (SafeMemoryBuffer b = QueryServiceConfig2(
                    NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_FAILURE_ACTIONS))
                {
                    NativeHelpers.SERVICE_FAILURE_ACTIONSW value = (NativeHelpers.SERVICE_FAILURE_ACTIONSW)
                        Marshal.PtrToStructure(b.DangerousGetHandle(), typeof(NativeHelpers.SERVICE_FAILURE_ACTIONSW));

                    return new FailureActions(value);
                }
            }
            set
            {
                // dwResetPeriod and lpsaActions must be set together, we need to read the existing config if someone
                // wants to update 1 or the other but both aren't explicitly defined.
                UInt32? resetPeriod = value.ResetPeriod;
                List<Action> actions = value.Actions;
                if ((resetPeriod != null && actions == null) || (resetPeriod == null && actions != null))
                {
                    FailureActions existingValue = this.FailureActions;

                    if (resetPeriod != null && existingValue.Actions.Count == 0)
                        throw new ArgumentException(
                            "Cannot set FailureAction ResetPeriod without explicit Actions and no existing Actions");
                    else if (resetPeriod == null)
                        resetPeriod = (UInt32)existingValue.ResetPeriod;

                    if (actions == null)
                        actions = existingValue.Actions;
                }

                var info = new NativeHelpers.SERVICE_FAILURE_ACTIONSW()
                {
                    dwResetPeriod = resetPeriod == null ? 0 : (UInt32)resetPeriod,
                    lpRebootMsg = value.RebootMsg,
                    lpCommand = value.Command,
                    cActions = actions == null ? 0 : (UInt32)actions.Count,
                    lpsaActions = IntPtr.Zero,
                };

                // null means to keep the existing actions whereas an empty list deletes the actions.
                if (actions == null)
                {
                    ChangeServiceConfig2(NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_FAILURE_ACTIONS, info);
                    return;
                }

                int actionLength = Marshal.SizeOf(typeof(NativeHelpers.SC_ACTION));
                using (SafeMemoryBuffer buffer = new SafeMemoryBuffer(actionLength * actions.Count))
                {
                    info.lpsaActions = buffer.DangerousGetHandle();
                    HashSet<string> privileges = new HashSet<string>();

                    for (int i = 0; i < actions.Count; i++)
                    {
                        IntPtr actionPtr = IntPtr.Add(info.lpsaActions, i * actionLength);
                        NativeHelpers.SC_ACTION action = new NativeHelpers.SC_ACTION()
                        {
                            Delay = actions[i].Delay,
                            Type = actions[i].Type,
                        };
                        Marshal.StructureToPtr(action, actionPtr, false);

                        // Need to make sure the SeShutdownPrivilege is enabled when adding a reboot failure action.
                        if (action.Type == FailureAction.Reboot)
                            privileges.Add("SeShutdownPrivilege");
                    }

                    using (new PrivilegeEnabler(true, privileges.ToList().ToArray()))
                        ChangeServiceConfig2(NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_FAILURE_ACTIONS, info);
                }
            }
        }

        public bool FailureActionsOnNonCrashFailures
        {
            get
            {
                var value = QueryServiceConfig2<NativeHelpers.SERVICE_FAILURE_ACTIONS_FLAG>(
                    NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_FAILURE_ACTIONS_FLAG);

                return value.fFailureActionsOnNonCrashFailures;
            }
            set
            {
                var info = new NativeHelpers.SERVICE_FAILURE_ACTIONS_FLAG()
                {
                    fFailureActionsOnNonCrashFailures = value,
                };
                ChangeServiceConfig2(NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_FAILURE_ACTIONS_FLAG, info);
            }
        }

        public ServiceSidInfo ServiceSidInfo
        {
            get
            {
                var value = QueryServiceConfig2<NativeHelpers.SERVICE_SID_INFO>(
                    NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_SERVICE_SID_INFO);

                return value.dwServiceSidType;
            }
            set
            {
                var info = new NativeHelpers.SERVICE_SID_INFO()
                {
                    dwServiceSidType = value,
                };
                ChangeServiceConfig2(NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_SERVICE_SID_INFO, info);
            }
        }

        public List<string> RequiredPrivileges
        {
            get
            {
                using (SafeMemoryBuffer buffer = QueryServiceConfig2(
                    NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_REQUIRED_PRIVILEGES_INFO))
                {
                    var value = (NativeHelpers.SERVICE_REQUIRED_PRIVILEGES_INFOW)Marshal.PtrToStructure(
                            buffer.DangerousGetHandle(), typeof(NativeHelpers.SERVICE_REQUIRED_PRIVILEGES_INFOW));

                    int structLength = Marshal.SizeOf(value);
                    int stringLength = ((int)buffer.BufferLength - structLength) / sizeof(char);

                    if (stringLength > 0)
                    {
                        string privilegesString = Marshal.PtrToStringUni(value.pmszRequiredPrivileges, stringLength);
                        return new List<string>(privilegesString.Split(new char[1] { '\0' },
                            StringSplitOptions.RemoveEmptyEntries));
                    }
                    else
                        return new List<string>();
                }
            }
            set
            {
                string privilegeString = String.Join("\0", value ?? new List<string>()) + "\0\0";

                using (SafeMemoryBuffer buffer = new SafeMemoryBuffer(Marshal.StringToHGlobalUni(privilegeString)))
                {
                    var info = new NativeHelpers.SERVICE_REQUIRED_PRIVILEGES_INFOW()
                    {
                        pmszRequiredPrivileges = buffer.DangerousGetHandle(),
                    };
                    ChangeServiceConfig2(NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_REQUIRED_PRIVILEGES_INFO, info);
                }
            }
        }

        public UInt32 PreShutdownTimeout
        {
            get
            {
                var value = QueryServiceConfig2<NativeHelpers.SERVICE_PRESHUTDOWN_INFO>(
                    NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_PRESHUTDOWN_INFO);

                return value.dwPreshutdownTimeout;
            }
            set
            {
                var info = new NativeHelpers.SERVICE_PRESHUTDOWN_INFO()
                {
                    dwPreshutdownTimeout = value,
                };
                ChangeServiceConfig2(NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_PRESHUTDOWN_INFO, info);
            }
        }

        public List<Trigger> Triggers
        {
            get
            {
                List<Trigger> triggers = new List<Trigger>();

                using (SafeMemoryBuffer b = QueryServiceConfig2(
                    NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_TRIGGER_INFO))
                {
                    var value = (NativeHelpers.SERVICE_TRIGGER_INFO)Marshal.PtrToStructure(
                        b.DangerousGetHandle(), typeof(NativeHelpers.SERVICE_TRIGGER_INFO));

                    int triggerLength = Marshal.SizeOf(typeof(NativeHelpers.SERVICE_TRIGGER));
                    for (int i = 0; i < value.cTriggers; i++)
                    {
                        IntPtr triggerPtr = IntPtr.Add(value.pTriggers, i * triggerLength);
                        var trigger = (NativeHelpers.SERVICE_TRIGGER)Marshal.PtrToStructure(triggerPtr,
                            typeof(NativeHelpers.SERVICE_TRIGGER));

                        triggers.Add(new Trigger(trigger));
                    }
                }

                return triggers;
            }
            set
            {
                var info = new NativeHelpers.SERVICE_TRIGGER_INFO()
                {
                    cTriggers = value == null ? 0 : (UInt32)value.Count,
                    pTriggers = IntPtr.Zero,
                    pReserved = IntPtr.Zero,
                };

                if (info.cTriggers == 0)
                {
                    try
                    {
                        ChangeServiceConfig2(NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_TRIGGER_INFO, info);
                    }
                    catch (ServiceManagerException e)
                    {
                        // Can fail with ERROR_INVALID_PARAMETER if no triggers were already set on the service, just
                        // continue as the service is what we want it to be.
                        if (e.NativeErrorCode != 87)
                            throw;
                    }
                    return;
                }

                // Due to the dynamic nature of the trigger structure(s) we need to manually calculate the size of the
                // data items on each trigger if present. This also serializes the raw data items to bytes here.
                int structDataLength = 0;
                int dataLength = 0;
                Queue<byte[]> dataItems = new Queue<byte[]>();
                foreach (Trigger trigger in value)
                {
                    if (trigger.DataItems == null || trigger.DataItems.Count == 0)
                        continue;

                    foreach (TriggerItem dataItem in trigger.DataItems)
                    {
                        structDataLength += Marshal.SizeOf(typeof(NativeHelpers.SERVICE_TRIGGER_SPECIFIC_DATA_ITEM));

                        byte[] dataItemBytes;
                        Type dataItemType = dataItem.Data.GetType();
                        if (dataItemType == typeof(byte))
                            dataItemBytes = new byte[1] { (byte)dataItem.Data };
                        else if (dataItemType == typeof(byte[]))
                            dataItemBytes = (byte[])dataItem.Data;
                        else if (dataItemType == typeof(UInt64))
                            dataItemBytes = BitConverter.GetBytes((UInt64)dataItem.Data);
                        else if (dataItemType == typeof(string))
                            dataItemBytes = Encoding.Unicode.GetBytes((string)dataItem.Data + "\0");
                        else if (dataItemType == typeof(List<string>))
                            dataItemBytes = Encoding.Unicode.GetBytes(
                                String.Join("\0", (List<string>)dataItem.Data) + "\0");
                        else
                            throw new ArgumentException(String.Format("Trigger data type '{0}' not a value type",
                                dataItemType.Name));

                        dataLength += dataItemBytes.Length;
                        dataItems.Enqueue(dataItemBytes);
                    }
                }

                using (SafeMemoryBuffer triggerBuffer = new SafeMemoryBuffer(
                    value.Count * Marshal.SizeOf(typeof(NativeHelpers.SERVICE_TRIGGER))))
                using (SafeMemoryBuffer triggerGuidBuffer = new SafeMemoryBuffer(
                    value.Count * Marshal.SizeOf(typeof(Guid))))
                using (SafeMemoryBuffer dataItemBuffer = new SafeMemoryBuffer(structDataLength))
                using (SafeMemoryBuffer dataBuffer = new SafeMemoryBuffer(dataLength))
                {
                    info.pTriggers = triggerBuffer.DangerousGetHandle();

                    IntPtr triggerPtr = triggerBuffer.DangerousGetHandle();
                    IntPtr guidPtr = triggerGuidBuffer.DangerousGetHandle();
                    IntPtr dataItemPtr = dataItemBuffer.DangerousGetHandle();
                    IntPtr dataPtr = dataBuffer.DangerousGetHandle();

                    foreach (Trigger trigger in value)
                    {
                        int dataCount = trigger.DataItems == null ? 0 : trigger.DataItems.Count;
                        var rawTrigger = new NativeHelpers.SERVICE_TRIGGER()
                        {
                            dwTriggerType = trigger.Type,
                            dwAction = trigger.Action,
                            pTriggerSubtype = guidPtr,
                            cDataItems = (UInt32)dataCount,
                            pDataItems = dataCount == 0 ? IntPtr.Zero : dataItemPtr,
                        };
                        guidPtr = StructureToPtr(trigger.SubType, guidPtr);

                        for (int i = 0; i < rawTrigger.cDataItems; i++)
                        {
                            byte[] dataItemBytes = dataItems.Dequeue();
                            var rawTriggerData = new NativeHelpers.SERVICE_TRIGGER_SPECIFIC_DATA_ITEM()
                            {
                                dwDataType = trigger.DataItems[i].Type,
                                cbData = (UInt32)dataItemBytes.Length,
                                pData = dataPtr,
                            };
                            Marshal.Copy(dataItemBytes, 0, dataPtr, dataItemBytes.Length);
                            dataPtr = IntPtr.Add(dataPtr, dataItemBytes.Length);

                            dataItemPtr = StructureToPtr(rawTriggerData, dataItemPtr);
                        }

                        triggerPtr = StructureToPtr(rawTrigger, triggerPtr);
                    }

                    ChangeServiceConfig2(NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_TRIGGER_INFO, info);
                }
            }
        }

        public UInt16? PreferredNode
        {
            get
            {
                try
                {
                    var value = QueryServiceConfig2<NativeHelpers.SERVICE_PREFERRED_NODE_INFO>(
                        NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_PREFERRED_NODE);

                    return value.usPreferredNode;
                }
                catch (ServiceManagerException e)
                {
                    // If host has no NUMA support this will fail with ERROR_INVALID_PARAMETER
                    if (e.NativeErrorCode == 0x00000057)  // ERROR_INVALID_PARAMETER
                        return null;

                    throw;
                }
            }
            set
            {
                var info = new NativeHelpers.SERVICE_PREFERRED_NODE_INFO();
                if (value == null)
                    info.fDelete = true;
                else
                    info.usPreferredNode = (UInt16)value;
                ChangeServiceConfig2(NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_PREFERRED_NODE, info);
            }
        }

        public LaunchProtection LaunchProtection
        {
            get
            {
                var value = QueryServiceConfig2<NativeHelpers.SERVICE_LAUNCH_PROTECTED_INFO>(
                    NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_LAUNCH_PROTECTED);

                return value.dwLaunchProtected;
            }
            set
            {
                var info = new NativeHelpers.SERVICE_LAUNCH_PROTECTED_INFO()
                {
                    dwLaunchProtected = value,
                };
                ChangeServiceConfig2(NativeHelpers.ConfigInfoLevel.SERVICE_CONFIG_LAUNCH_PROTECTED, info);
            }
        }

        // ServiceStatus
        public ServiceStatus State { get { return _statusProcess.dwCurrentState; } }

        public ControlsAccepted ControlsAccepted { get { return _statusProcess.dwControlsAccepted; } }

        public UInt32 Win32ExitCode { get { return _statusProcess.dwWin32ExitCode; } }

        public UInt32 ServiceExitCode { get { return _statusProcess.dwServiceSpecificExitCode; } }

        public UInt32 Checkpoint { get { return _statusProcess.dwCheckPoint; } }

        public UInt32 WaitHint { get { return _statusProcess.dwWaitHint; } }

        public UInt32 ProcessId { get { return _statusProcess.dwProcessId; } }

        public ServiceFlags ServiceFlags { get { return _statusProcess.dwServiceFlags; } }

        public Service(string name) : this(name, ServiceRights.AllAccess) { }

        public Service(string name, ServiceRights access) : this(name, access, SCMRights.Connect) { }

        public Service(string name, ServiceRights access, SCMRights scmAccess)
        {
            ServiceName = name;
            _scmHandle = OpenSCManager(scmAccess);
            _serviceHandle = NativeMethods.OpenServiceW(_scmHandle, name, access);
            if (_serviceHandle.IsInvalid)
                throw new ServiceManagerException(String.Format("Failed to open service '{0}'", name));

            Refresh();
        }

        private Service(SafeServiceHandle scmHandle, SafeServiceHandle serviceHandle, string name)
        {
            ServiceName = name;
            _scmHandle = scmHandle;
            _serviceHandle = serviceHandle;

            Refresh();
        }

        // EnumDependentServices
        public List<string> DependedBy
        {
            get
            {
                UInt32 bytesNeeded = 0;
                UInt32 numServices = 0;
                NativeMethods.EnumDependentServicesW(_serviceHandle, 3, new SafeMemoryBuffer(IntPtr.Zero), 0,
                    out bytesNeeded, out numServices);

                using (SafeMemoryBuffer buffer = new SafeMemoryBuffer((int)bytesNeeded))
                {
                    if (!NativeMethods.EnumDependentServicesW(_serviceHandle, 3, buffer, bytesNeeded, out bytesNeeded,
                        out numServices))
                    {
                        throw new ServiceManagerException("Failed to enumerated dependent services");
                    }

                    List<string> dependents = new List<string>();
                    Type enumType = typeof(NativeHelpers.ENUM_SERVICE_STATUSW);
                    for (int i = 0; i < numServices; i++)
                    {
                        var service = (NativeHelpers.ENUM_SERVICE_STATUSW)Marshal.PtrToStructure(
                            IntPtr.Add(buffer.DangerousGetHandle(), i * Marshal.SizeOf(enumType)), enumType);

                        dependents.Add(service.lpServiceName);
                    }

                    return dependents;
                }
            }
        }

        public static Service Create(string name, string binaryPath, string displayName = null,
            ServiceType serviceType = ServiceType.Win32OwnProcess,
            ServiceStartType startType = ServiceStartType.DemandStart, ErrorControl errorControl = ErrorControl.Normal,
            string loadOrderGroup = null, List<string> dependencies = null, string startName = null,
            string password = null)
        {
            SafeServiceHandle scmHandle = OpenSCManager(SCMRights.CreateService | SCMRights.Connect);

            if (displayName == null)
                displayName = name;

            string depString = null;
            if (dependencies != null && dependencies.Count > 0)
                depString = String.Join("\0", dependencies) + "\0\0";

            SafeServiceHandle serviceHandle = NativeMethods.CreateServiceW(scmHandle, name, displayName,
                ServiceRights.AllAccess, serviceType, startType, errorControl, binaryPath,
                loadOrderGroup, IntPtr.Zero, depString, startName, password);

            if (serviceHandle.IsInvalid)
                throw new ServiceManagerException(String.Format("Failed to create new service '{0}'", name));

            return new Service(scmHandle, serviceHandle, name);
        }

        public void Delete()
        {
            if (!NativeMethods.DeleteService(_serviceHandle))
                throw new ServiceManagerException("Failed to delete service");
            Dispose();
        }

        public void Dispose()
        {
            if (_serviceHandle != null)
                _serviceHandle.Dispose();

            if (_scmHandle != null)
                _scmHandle.Dispose();
            GC.SuppressFinalize(this);
        }

        public void Refresh()
        {
            UInt32 bytesNeeded;
            NativeMethods.QueryServiceConfigW(_serviceHandle, IntPtr.Zero, 0, out bytesNeeded);

            _rawServiceConfig = new SafeMemoryBuffer((int)bytesNeeded);
            if (!NativeMethods.QueryServiceConfigW(_serviceHandle, _rawServiceConfig.DangerousGetHandle(), bytesNeeded,
                out bytesNeeded))
            {
                throw new ServiceManagerException("Failed to query service config");
            }

            NativeMethods.QueryServiceStatusEx(_serviceHandle, 0, IntPtr.Zero, 0, out bytesNeeded);
            using (SafeMemoryBuffer buffer = new SafeMemoryBuffer((int)bytesNeeded))
            {
                if (!NativeMethods.QueryServiceStatusEx(_serviceHandle, 0, buffer.DangerousGetHandle(), bytesNeeded,
                    out bytesNeeded))
                {
                    throw new ServiceManagerException("Failed to query service status");
                }

                _statusProcess = (NativeHelpers.SERVICE_STATUS_PROCESS)Marshal.PtrToStructure(
                    buffer.DangerousGetHandle(), typeof(NativeHelpers.SERVICE_STATUS_PROCESS));
            }
        }

        private void ChangeServiceConfig(ServiceType serviceType = (ServiceType)SERVICE_NO_CHANGE,
            ServiceStartType startType = (ServiceStartType)SERVICE_NO_CHANGE,
            ErrorControl errorControl = (ErrorControl)SERVICE_NO_CHANGE, string binaryPath = null,
            string loadOrderGroup = null, List<string> dependencies = null, string startName = null,
            string password = null, string displayName = null)
        {
            string depString = null;
            if (dependencies != null && dependencies.Count > 0)
                depString = String.Join("\0", dependencies) + "\0\0";

            if (!NativeMethods.ChangeServiceConfigW(_serviceHandle, serviceType, startType, errorControl, binaryPath,
                loadOrderGroup, IntPtr.Zero, depString, startName, password, displayName))
            {
                throw new ServiceManagerException("Failed to change service config");
            }

            Refresh();
        }

        private void ChangeServiceConfig2(NativeHelpers.ConfigInfoLevel infoLevel, object info)
        {
            using (SafeMemoryBuffer buffer = new SafeMemoryBuffer(Marshal.SizeOf(info)))
            {
                Marshal.StructureToPtr(info, buffer.DangerousGetHandle(), false);

                if (!NativeMethods.ChangeServiceConfig2W(_serviceHandle, infoLevel, buffer.DangerousGetHandle()))
                    throw new ServiceManagerException("Failed to change service config");
            }
        }

        private static SafeServiceHandle OpenSCManager(SCMRights desiredAccess)
        {
            SafeServiceHandle handle = NativeMethods.OpenSCManagerW(null, null, desiredAccess);
            if (handle.IsInvalid)
                throw new ServiceManagerException("Failed to open SCManager");

            return handle;
        }

        private T QueryServiceConfig2<T>(NativeHelpers.ConfigInfoLevel infoLevel)
        {
            using (SafeMemoryBuffer buffer = QueryServiceConfig2(infoLevel))
                return (T)Marshal.PtrToStructure(buffer.DangerousGetHandle(), typeof(T));
        }

        private SafeMemoryBuffer QueryServiceConfig2(NativeHelpers.ConfigInfoLevel infoLevel)
        {
            UInt32 bytesNeeded = 0;
            NativeMethods.QueryServiceConfig2W(_serviceHandle, infoLevel, IntPtr.Zero, 0, out bytesNeeded);

            SafeMemoryBuffer buffer = new SafeMemoryBuffer((int)bytesNeeded);
            if (!NativeMethods.QueryServiceConfig2W(_serviceHandle, infoLevel, buffer.DangerousGetHandle(), bytesNeeded,
                out bytesNeeded))
            {
                throw new ServiceManagerException(String.Format("QueryServiceConfig2W({0}) failed",
                    infoLevel.ToString()));
            }

            return buffer;
        }

        private static IntPtr StructureToPtr(object structure, IntPtr ptr)
        {
            Marshal.StructureToPtr(structure, ptr, false);
            return IntPtr.Add(ptr, Marshal.SizeOf(structure));
        }

        ~Service() { Dispose(); }
    }
}
