#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.AddType

$spec = @{
    options = @{
        hardware_id = @{ type = "str" }
        name = @{ type = "str" }
        path = @{ type = "path" }
        state = @{ type = "str"; choices = @("absent", "present"); default = "present" }
    }
    required_if = @(
        @("state", "present", @("path", "hardware_id"), $true),
        @("state", "absent", @(,"name"))
    )
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$hardware_id = $module.Params.hardware_id
$name = $module.Params.name
$path = $module.Params.path
$state = $module.Params.state

$module.Result.reboot_required = $false

Add-CSharpType -References @'
using Microsoft.Win32.SafeHandles;
using System;
using System.ComponentModel;
using System.Runtime.ConstrainedExecution;
using System.Runtime.InteropServices;
using System.Text;

namespace Ansible.Device
{
    public class NativeHelpers
    {
        [StructLayout(LayoutKind.Sequential)]
        public class SP_DEVINFO_DATA
        {
            public UInt32 cbSize;
            public Guid ClassGuid;
            public UInt32 DevInst;
            public IntPtr Reserved;

            public SP_DEVINFO_DATA()
            {
                this.cbSize = (UInt32)Marshal.SizeOf(this);
                this.ClassGuid = Guid.Empty;
            }
        }

        [Flags]
        public enum DeviceInfoCreationFlags : uint
        {
            DICD_GENERATE_ID = 0x00000001,
            DICD_INHERIT_CLASSDRVS = 0x00000002,
        }

        public enum DeviceProperty : uint
        {
            SPDRP_DEVICEDESC = 0x0000000,
            SPDRP_HARDWAREID = 0x0000001,
            SPDRP_COMPATIBLEIDS = 0x0000002,
            SPDRP_UNUSED0 = 0x0000003,
            SPDRP_SERVICE = 0x0000004,
            SPDRP_UNUSED1 = 0x0000005,
            SPDRP_UNUSED2 = 0x0000006,
            SPDRP_CLASS = 0x0000007,  // Read only - tied to ClassGUID
            SPDRP_CLASSGUID = 0x0000008,
            SPDRP_DRIVER = 0x0000009,
            SPDRP_CONFIGFLAGS = 0x000000a,
            SPDRP_MFG = 0x000000b,
            SPDRP_FRIENDLYNAME = 0x000000c,
            SPDRP_LOCATION_INFORMATION = 0x000000d,
            SPDRP_PHYSICAL_DEVICE_OBJECT_NAME = 0x000000e,  // Read only
            SPDRP_CAPABILITIES = 0x000000f,  // Read only
            SPDRP_UI_NUMBER = 0x0000010,  // Read only
            SPDRP_UPPERFILTERS = 0x0000011,
            SPDRP_LOWERFILTERS = 0x0000012,
            SPDRP_BUSTYPEGUID = 0x0000013,  // Read only
            SPDRP_LEGACYBUSTYPE = 0x0000014,  // Read only
            SPDRP_BUSNUMBER = 0x0000015,  // Read only
            SPDRP_ENUMERATOR_NAME = 0x0000016,  // Read only
            SPDRP_SECURITY = 0x0000017,
            SPDRP_SECURITY_SDS = 0x0000018,
            SPDRP_DEVTYPE = 0x0000019,
            SPDRP_EXCLUSIVE = 0x000001a,
            SPDRP_CHARACTERISTICS = 0x000001b,
            SPDRP_ADDRESS = 0x000001c,  // Read only
            SPDRP_UI_NUMBER_DESC_FORMAT = 0x000001d,
            SPDRP_DEVICE_POWER_DATA = 0x000001e,  // Read only
            SPDRP_REMOVAL_POLICY = 0x000001f,  // Read only
            SPDRP_REMOVAL_POLICY_HW_DEFAULT = 0x0000020,  // Read only
            SPDRP_REMOVAL_POLICY_OVERRIDE = 0x0000021,
            SPDRP_INSTALL_STATE = 0x0000022,  // Read only
            SPDRP_LOCATION_PATHS = 0x0000023,  // Read only
            SPDRP_BASE_CONTAINERID = 0x0000024,  // Read only
        }

        // https://docs.microsoft.com/en-us/previous-versions/ff549793%28v%3dvs.85%29
        public enum DifCodes : uint
        {
            DIF_SELECTDIVE = 0x00000001,
            DIF_INSTALLDEVICE = 0x00000002,
            DIF_ASSIGNRESOURCES = 0x00000003,
            DIF_PROPERTIES = 0x00000004,
            DIF_REMOVE = 0x00000005,
            DIF_FIRSTTIMESETUP = 0x00000006,
            DIF_FOUNDDEVICE = 0x00000007,
            DIF_SELECTCLASSDRIVERS = 0x00000008,
            DIF_VALIDATECLASSDRIVERS = 0x00000009,
            DIF_INSTALLCLASSDRIVERS = 0x0000000a,
            DIF_CALCDISKSPACE = 0x0000000b,
            DIF_DESTROYPRIVATEDATA = 0x0000000c,
            DIF_VALIDATEDRIVER = 0x0000000d,
            DIF_DETECT = 0x0000000f,
            DIF_INSTALLWIZARD = 0x00000010,
            DIF_DESTROYWIZARDDATA = 0x00000011,
            DIF_PROPERTYCHANGE = 0x00000012,
            DIF_ENABLECLASS = 0x00000013,
            DIF_DETECTVERIFY = 0x00000014,
            DIF_INSTALLDEVICEFILES = 0x00000015,
            DIF_UNREMOVE = 0x00000016,
            DIF_SELECTBESTCOMPATDRV = 0x00000017,
            DIF_ALLOW_INSTALL = 0x00000018,
            DIF_REGISTERDEVICE = 0x00000019,
            DIF_NEWDEVICEWIZARD_PRESELECT = 0x0000001a,
            DIF_NEWDEVICEWIZARD_SELECT = 0x0000001b,
            DIF_NEWDEVICEWIZARD_PREANALYZE = 0x0000001c,
            DIF_NEWDEVICEWIZARD_POSTANALYZE = 0x0000001d,
            DIF_NEWDEVICEWIZARD_FINISHINSTALL = 0x0000001e,
            DIF_UNUSED1 = 0x0000001e,
            DIF_INSTALLINTERFACES = 0x00000020,
            DIF_DETECTCANCEL = 0x00000021,
            DIF_REGISTER_COINSTALLERS = 0x00000022,
            DIF_ADDPROPERTYPAGE_ADVANCED = 0x00000023,
            DIF_ADDPROPERTYPAGE_BASIC = 0x00000024,
            DIF_RESERVED1 = 0x00000025,
            DIF_TROUBLESHOOTER = 0x00000026,
            DIF_POWERMESSAGEWAKE = 0x00000027,
            DIF_ADDREMOTEPROPERTYPAGE_ADVANCED = 0x00000028,
            DIF_UPDATEDRIVER_UI = 0x00000029,
            DIF_FINISHINSTALL_ACTION = 0x0000002a,
        }

        [Flags]
        public enum GetClassFlags : uint
        {
            DIGCF_DEFAULT = 0x00000001,
            DIGCF_PRESENT = 0x00000002,
            DIGCF_ALLCLASSES = 0x00000004,
            DIGCF_PROFILE = 0x00000008,
            DIGCF_DEVICEINTERFACE = 0x00000010,
        }

        [Flags]
        public enum InstallFlags : uint
        {
            INSTALLFLAG_FORCE = 0x00000001,
            INSTALLFLAG_READONLY = 0x00000002,
            INSTALLFLAG_NONINTERACTIVE = 0x00000004,
            INSTALLFLAG_BITS = 0x00000007,
        }
    }

    public class NativeMethods
    {
        [DllImport("Setupapi.dll", SetLastError = true)]
        public static extern bool SetupDiCallClassInstaller(
            NativeHelpers.DifCodes InstallFunction,
            SafeDeviceInfoSet DeviceInfoSet,
            NativeHelpers.SP_DEVINFO_DATA DeviceInfoData);

        [DllImport("Setupapi.dll", SetLastError = true)]
        public static extern SafeDeviceInfoSet SetupDiCreateDeviceInfoList(
            Guid ClassGuid,
            IntPtr hwndParent);

        [DllImport("Setupapi.dll", SetLastError = true)]
        public static extern bool SetupDiCreateDeviceInfoW(
            SafeDeviceInfoSet DeviceInfoSet,
            [MarshalAs(UnmanagedType.LPWStr)] string DeviceName,
            Guid ClassGuid,
            [MarshalAs(UnmanagedType.LPWStr)] string DeviceDescription,
            IntPtr hwndParent,
            NativeHelpers.DeviceInfoCreationFlags CreationFlags,
            NativeHelpers.SP_DEVINFO_DATA DeviceInfoData);

        [DllImport("Setupapi.dll", SetLastError = true)]
        public static extern bool SetupDiDestroyDeviceInfoList(
            IntPtr DeviceInfoSet);

        [DllImport("Setupapi.dll", SetLastError = true)]
        public static extern bool SetupDiEnumDeviceInfo(
            SafeDeviceInfoSet DeviceInfoSet,
            UInt32 MemberIndex,
            NativeHelpers.SP_DEVINFO_DATA DeviceInfoData);

        [DllImport("Setupapi.dll", SetLastError = true)]
        public static extern SafeDeviceInfoSet SetupDiGetClassDevsW(
            Guid ClassGuid,
            [MarshalAs(UnmanagedType.LPWStr)] string Enumerator,
            IntPtr hwndParent,
            NativeHelpers.GetClassFlags Flags);

        [DllImport("Setupapi.dll", SetLastError = true)]
        public static extern bool SetupDiGetDeviceRegistryPropertyW(
            SafeDeviceInfoSet DeviceInfoSet,
            NativeHelpers.SP_DEVINFO_DATA DeviceInfoData,
            NativeHelpers.DeviceProperty Property,
            out UInt32 PropertyRegDataType,
            SafeMemoryBuffer PropertyBuffer,
            UInt32 PropertyBufferSize,
            ref UInt32 RequiredSize);

        [DllImport("Setupapi.dll", SetLastError = true)]
        public static extern bool SetupDiGetINFClassW(
            [MarshalAs(UnmanagedType.LPWStr)] string InfName,
            ref Guid ClassGuid,
            [MarshalAs(UnmanagedType.LPWStr)] StringBuilder ClassName,
            UInt32 ClassNameSize,
            ref UInt32 RequiredSize);

        [DllImport("Setupapi.dll", SetLastError = true)]
        public static extern bool SetupDiSetDeviceRegistryPropertyW(
            SafeDeviceInfoSet DeviceInfoSet,
            NativeHelpers.SP_DEVINFO_DATA DeviceInfoData,
            NativeHelpers.DeviceProperty Property,
            SafeMemoryBuffer PropertyBuffer,
            UInt32 PropertyBufferSize);

        [DllImport("Newdev.dll", SetLastError = true)]
        public static extern bool UpdateDriverForPlugAndPlayDevicesW(
            IntPtr hwndParent,
            [MarshalAs(UnmanagedType.LPWStr)] string HardwareId,
            [MarshalAs(UnmanagedType.LPWStr)] string FullInfPath,
            NativeHelpers.InstallFlags InstallFlags,
            ref bool bRebootRequired);
    }

    public class SafeDeviceInfoSet : SafeHandleZeroOrMinusOneIsInvalid
    {
        public SafeDeviceInfoSet() : base(true) { }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.MayFail)]
        protected override bool ReleaseHandle()
        {
            return NativeMethods.SetupDiDestroyDeviceInfoList(handle);
        }
    }

    public class SafeMemoryBuffer : SafeHandleZeroOrMinusOneIsInvalid
    {
        public int Length = 0;

        public SafeMemoryBuffer() : base(true) { }

        public SafeMemoryBuffer(int cb) : base(true)
        {
            Length = cb;
            base.SetHandle(Marshal.AllocHGlobal(cb));
        }

        public SafeMemoryBuffer(string sz) : base(true)
        {
            Length = sz.Length * sizeof(char);
            base.SetHandle(Marshal.StringToHGlobalUni(sz));
        }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.MayFail)]
        protected override bool ReleaseHandle()
        {
            Marshal.FreeHGlobal(handle);
            return true;
        }
    }

    public class DeviceUtil
    {
        public static string GetDeviceFriendlyName(SafeDeviceInfoSet devInfoSet, NativeHelpers.SP_DEVINFO_DATA devInfo)
        {
            string friendlyName = GetDeviceStringProp(devInfoSet, devInfo, NativeHelpers.DeviceProperty.SPDRP_FRIENDLYNAME);

            // Older Windows versions may not have a friendly name set. This seems to be the case when the device has
            // a unique description so we fallback to that value.
            if (null == friendlyName)
                friendlyName = GetDeviceStringProp(devInfoSet, devInfo, NativeHelpers.DeviceProperty.SPDRP_DEVICEDESC);

            return friendlyName;
        }

        public static void SetDeviceHardwareId(SafeDeviceInfoSet devInfoSet, NativeHelpers.SP_DEVINFO_DATA devInfo,
            string hardwareId)
        {
            SetDeviceStringProp(devInfoSet, devInfo, NativeHelpers.DeviceProperty.SPDRP_HARDWAREID, hardwareId);
        }

        private static string GetDeviceStringProp(SafeDeviceInfoSet devInfoSet, NativeHelpers.SP_DEVINFO_DATA devInfo,
            NativeHelpers.DeviceProperty property)
        {
            using (SafeMemoryBuffer memBuf = GetDeviceProperty(devInfoSet, devInfo, property))
            {
                if (memBuf.IsInvalid)  // Property does not exist so just return null.
                    return null;

                return Marshal.PtrToStringUni(memBuf.DangerousGetHandle());
            }
        }

        private static SafeMemoryBuffer GetDeviceProperty(SafeDeviceInfoSet devInfoSet,
            NativeHelpers.SP_DEVINFO_DATA devInfo, NativeHelpers.DeviceProperty property)
        {
            UInt32 requiredSize = 0;
            UInt32 regDataType = 0;
            if (!NativeMethods.SetupDiGetDeviceRegistryPropertyW(devInfoSet, devInfo, property,
                out regDataType, new SafeMemoryBuffer(0), 0, ref requiredSize))
            {
                int errCode = Marshal.GetLastWin32Error();
                if (errCode == 0x0000000D)  // ERROR_INVALID_DATA
                    return new SafeMemoryBuffer();  // The FRIENDLYNAME property does not exist
                else if (errCode != 0x0000007A)  // ERROR_INSUFFICIENT_BUFFER
                    throw new Win32Exception(errCode);
            }

            SafeMemoryBuffer memBuf = new SafeMemoryBuffer((int)requiredSize);
            if (!NativeMethods.SetupDiGetDeviceRegistryPropertyW(devInfoSet, devInfo, property,
                out regDataType, memBuf, requiredSize, ref requiredSize))
            {
                int errCode = Marshal.GetLastWin32Error();
                memBuf.Dispose();

                throw new Win32Exception(errCode);
            }

            return memBuf;
        }

        private static void SetDeviceStringProp(SafeDeviceInfoSet devInfoSet, NativeHelpers.SP_DEVINFO_DATA devInfo,
            NativeHelpers.DeviceProperty property, string value)
        {
            using (SafeMemoryBuffer buffer = new SafeMemoryBuffer(value))
                SetDeviceProperty(devInfoSet, devInfo, property, buffer);
        }

        private static void SetDeviceProperty(SafeDeviceInfoSet devInfoSet, NativeHelpers.SP_DEVINFO_DATA devInfo,
            NativeHelpers.DeviceProperty property, SafeMemoryBuffer buffer)
        {
            if (!NativeMethods.SetupDiSetDeviceRegistryPropertyW(devInfoSet, devInfo, property, buffer,
                (UInt32)buffer.Length))
            {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }
        }
    }
}
'@

Function Get-Win32ErrorMessage {
    Param ([System.Int32]$ErrorCode)

    $exp = New-Object -TypeName System.ComponentModel.Win32Exception -ArgumentList $ErrorCode
    return ("{0} (Win32 ErrorCode {1} - 0x{1:X8}" -f $exp.Message, $ErrorCode)
}

# Determine if the device is already installed
$dev_info_set = [Ansible.Device.NativeMethods]::SetupDiGetClassDevsW(
    [Guid]::Empty,
    [NullString]::Value,
    [System.IntPtr]::Zero,
    [Ansible.Device.NativeHelpers+GetClassFlags]::DIGCF_ALLCLASSES
); $err = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()

try {
    if ($dev_info_set.IsInvalid) {
        $msg = Get-Win32ErrorMessage -ErrorCode $err
        $module.FailJson("Failed to get device information set for installed devices: $msg")
    }

    $dev_info = $null
    if ($null -ne $name) {
        # Loop through the set of all devices and compare the name
        $idx = 0
        while ($true) {
            $dev_info = New-Object -TypeName Ansible.Device.NativeHelpers+SP_DEVINFO_DATA
            $res = [Ansible.Device.NativeMethods]::SetupDiEnumDeviceInfo(
                $dev_info_set,
                $idx,
                $dev_info
            ); $err = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()

            if (-not $res) {
                $dev_info = $null
                if ($err -eq 0x00000103) {  # ERROR_NO_MORE_ITEMS
                    break
                }

                $msg = Get-Win32ErrorMessage -ErrorCode $err
                $module.FailJson("Failed to enumerate device information set at index $($idx): $msg")
            }

            $device_name = [Ansible.Device.DeviceUtil]::GetDeviceFriendlyName($dev_info_set, $dev_info)
            if ($device_name -eq $name) {
                break
            }

            $dev_info = $null
            $idx++
        }
    }

    if ($state -eq "absent" -and $null -ne $dev_info) {
        if (-not $module.CheckMode) {
            $res = [Ansible.Device.NativeMethods]::SetupDiCallClassInstaller(
                [Ansible.Device.NativeHelpers+DifCodes]::DIF_REMOVE,
                $dev_info_set,
                $dev_info
            ); $err = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()

            if (-not $res) {
                $msg = Get-Win32ErrorMessage -ErrorCode $err
                $module.FailJson("Failed to remove device $($name): $msg")
            }
        }

        $module.Result.changed = $true
    } elseif ($state -eq "present" -and $null -eq $dev_info) {
        # Populate the class guid and display name if the path to an inf file was set.
        $class_id = [Guid]::Empty
        $class_name = $null
        if ($path) {
            if (-not (Test-Path -LiteralPath $path)) {
                $module.FailJson("Could not find the inf file specified at '$path'")
            }

            $class_name_sb = New-Object -TypeName System.Text.StringBuilder -ArgumentList 32  # MAX_CLASS_NAME_LEN
            $required_size = 0
            $res = [Ansible.Device.NativeMethods]::SetupDiGetINFClassW(
                $path,
                [ref]$class_id,
                $class_name_sb,
                $class_name_sb.Capacity,
                [ref]$required_size
            ); $err = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()

            if (-not $res) {
                $msg = Get-Win32ErrorMessage -ErrorCode $err
                $module.FailJson("Failed to parse driver inf at '$path': $msg")
            }

            $class_name = $class_name_sb.ToString()
        }

        # When creating a new device we want to start with a blank device information set.
        $dev_info_set.Dispose()

        $dev_info_set = [Ansible.Device.NativeMethods]::SetupDiCreateDeviceInfoList(
            $class_id,
            [System.IntPtr]::Zero
        ); $err = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()

        if ($dev_info_set.IsInvalid) {
            $msg = Get-Win32ErrorMessage -ErrorCode $err
            $module.FailJson("Failed to create device info set for the class $($class_id): $msg")
        }

        # Create the new device element and add it to the device info set
        $dev_info = New-Object -TypeName Ansible.Device.NativeHelpers+SP_DEVINFO_DATA
        $res = [Ansible.Device.NativeMethods]::SetupDiCreateDeviceInfoW(
            $dev_info_set,
            $class_name,
            $class_id,
            $null,
            [System.IntPtr]::Zero,
            [Ansible.Device.NativeHelpers+DeviceInfoCreationFlags]::DICD_GENERATE_ID,
            $dev_info
        ); $err = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()

        if (-not $res) {
            $msg = Get-Win32ErrorMessage -ErrorCode $err
            $module.FailJson("Failed to create new device element for class $($class_name): $msg")
        }

        # Set the hardware id of the new device so we can load the proper driver.
        [Ansible.Device.DeviceUtil]::SetDeviceHardwareId($dev_info_set, $dev_info, $hardware_id)

        if (-not $module.CheckMode) {
            # Install the device
            $res = [Ansible.Device.NativeMethods]::SetupDiCallClassInstaller(
                [Ansible.Device.NativeHelpers+DifCodes]::DIF_REGISTERDEVICE,
                $dev_info_set,
                $dev_info
            ); $err = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()

            if (-not $res) {
                $msg = Get-Win32ErrorMessage -ErrorCode $err
                $module.FailJson("Failed to register new device for class $($class_name): $msg")
            }

            # Load the drivers for the new device
            $reboot_required = $false
            $res = [Ansible.Device.NativeMethods]::UpdateDriverForPlugAndPlayDevicesW(
                [System.IntPtr]::Zero,
                $hardware_id,
                $path,
                [Ansible.Device.NativeHelpers+InstallFlags]'INSTALLFLAG_FORCE, INSTALLFLAG_NONINTERACTIVE',
                [ref]$reboot_required
            ); $err = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()

            if (-not $res) {
                # On a failure make sure we cleanup the "installed" device
                [Ansible.Device.NativeMethods]::SetupDiCallClassInstaller(
                    [Ansible.Device.NativeHelpers+DifCodes]::DIF_REMOVE,
                    $dev_info_set,
                    $dev_info
                ) > $null

                $msg = Get-Win32ErrorMessage -ErrorCode $err
                $module.FailJson("Failed to update device driver: $msg")
            }

            $module.Result.reboot_required = $reboot_required

            # Now get the name of the newly created device which we return back to Ansible.
            $name = [Ansible.Device.DeviceUtil]::GetDeviceFriendlyName($dev_info_set, $dev_info)
        } else {
            # Generate random name for check mode output
            $name = "Check mode generated device for $($class_name)"
        }
        $module.Result.changed = $true
    }
} finally {
    $dev_info_set.Dispose()
}

$module.Result.name = $name

$module.ExitJson()

