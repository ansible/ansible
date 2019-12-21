#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.AddType

$module = [Ansible.Basic.AnsibleModule]::Create($args, @{})

Add-CSharpType -AnsibleModule $module -References @'
using Microsoft.Win32.SafeHandles;
using System;
using System.Runtime.ConstrainedExecution;
using System.Runtime.InteropServices;
using System.Text;

namespace Ansible.TestAutoLogonInfo
{
    internal class NativeHelpers
    {
        [StructLayout(LayoutKind.Sequential)]
        public class LSA_OBJECT_ATTRIBUTES
        {
            public UInt32 Length = 0;
            public IntPtr RootDirectory = IntPtr.Zero;
            public IntPtr ObjectName = IntPtr.Zero;
            public UInt32 Attributes = 0;
            public IntPtr SecurityDescriptor = IntPtr.Zero;
            public IntPtr SecurityQualityOfService = IntPtr.Zero;
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        internal struct LSA_UNICODE_STRING
        {
            public UInt16 Length;
            public UInt16 MaximumLength;
            public IntPtr Buffer;

            public static explicit operator string(LSA_UNICODE_STRING s)
            {
                byte[] strBytes = new byte[s.Length];
                Marshal.Copy(s.Buffer, strBytes, 0, s.Length);
                return Encoding.Unicode.GetString(strBytes);
            }

            public static SafeMemoryBuffer CreateSafeBuffer(string s)
            {
                if (s == null)
                    return new SafeMemoryBuffer(IntPtr.Zero);

                byte[] stringBytes = Encoding.Unicode.GetBytes(s);
                int structSize = Marshal.SizeOf(typeof(LSA_UNICODE_STRING));
                IntPtr buffer = Marshal.AllocHGlobal(structSize + stringBytes.Length);
                try
                {
                    LSA_UNICODE_STRING lsaString = new LSA_UNICODE_STRING()
                    {
                        Length = (UInt16)(stringBytes.Length),
                        MaximumLength = (UInt16)(stringBytes.Length),
                        Buffer = IntPtr.Add(buffer, structSize),
                    };
                    Marshal.StructureToPtr(lsaString, buffer, false);
                    Marshal.Copy(stringBytes, 0, lsaString.Buffer, stringBytes.Length);
                    return new SafeMemoryBuffer(buffer);
                }
                catch
                {
                    // Make sure we free the pointer before raising the exception.
                    Marshal.FreeHGlobal(buffer);
                    throw;
                }
            }
        }
    }

    internal class NativeMethods
    {
        [DllImport("Advapi32.dll")]
        public static extern UInt32 LsaClose(
            IntPtr ObjectHandle);

        [DllImport("Advapi32.dll")]
        public static extern UInt32 LsaFreeMemory(
            IntPtr Buffer);

        [DllImport("Advapi32.dll")]
        internal static extern Int32 LsaNtStatusToWinError(
            UInt32 Status);

        [DllImport("Advapi32.dll")]
        public static extern UInt32 LsaOpenPolicy(
            IntPtr SystemName,
            NativeHelpers.LSA_OBJECT_ATTRIBUTES ObjectAttributes,
            UInt32 AccessMask,
            out SafeLsaHandle PolicyHandle);

        [DllImport("Advapi32.dll")]
        public static extern UInt32 LsaRetrievePrivateData(
            SafeLsaHandle PolicyHandle,
            SafeMemoryBuffer KeyName,
            out SafeLsaMemory PrivateData);
    }

    internal class SafeLsaMemory : SafeBuffer
    {
        internal SafeLsaMemory() : base(true) { }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.MayFail)]

        protected override bool ReleaseHandle()
        {
            return NativeMethods.LsaFreeMemory(handle) == 0;
        }
    }

    internal class SafeMemoryBuffer : SafeBuffer
    {
        internal SafeMemoryBuffer() : base(true) { }

        internal SafeMemoryBuffer(IntPtr ptr) : base(true)
        {
            base.SetHandle(ptr);
        }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.MayFail)]

        protected override bool ReleaseHandle()
        {
            if (handle != IntPtr.Zero)
                Marshal.FreeHGlobal(handle);
            return true;
        }
    }

    public class SafeLsaHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        internal SafeLsaHandle() : base(true) { }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.MayFail)]

        protected override bool ReleaseHandle()
        {
            return NativeMethods.LsaClose(handle) == 0;
        }
    }

    public class Win32Exception : System.ComponentModel.Win32Exception
    {
        private string _exception_msg;
        public Win32Exception(string message) : this(Marshal.GetLastWin32Error(), message) { }
        public Win32Exception(int errorCode, string message) : base(errorCode)
        {
            _exception_msg = String.Format("{0} - {1} (Win32 Error Code {2}: 0x{3})", message, base.Message, errorCode, errorCode.ToString("X8"));
        }
        public override string Message { get { return _exception_msg; } }
        public static explicit operator Win32Exception(string message) { return new Win32Exception(message); }
    }

    public class LsaUtil
    {
        public static SafeLsaHandle OpenPolicy(UInt32 access)
        {
            NativeHelpers.LSA_OBJECT_ATTRIBUTES oa = new NativeHelpers.LSA_OBJECT_ATTRIBUTES();
            SafeLsaHandle lsaHandle;
            UInt32 res = NativeMethods.LsaOpenPolicy(IntPtr.Zero, oa, access, out lsaHandle);
            if (res != 0)
                throw new Win32Exception(NativeMethods.LsaNtStatusToWinError(res),
                    String.Format("LsaOpenPolicy({0}) failed", access.ToString()));
            return lsaHandle;
        }

        public static string RetrievePrivateData(SafeLsaHandle handle, string key)
        {
            using (SafeMemoryBuffer keyBuffer = NativeHelpers.LSA_UNICODE_STRING.CreateSafeBuffer(key))
            {
                SafeLsaMemory buffer;
                UInt32 res = NativeMethods.LsaRetrievePrivateData(handle, keyBuffer, out buffer);
                using (buffer)
                {
                    if (res != 0)
                    {
                        // If the data object was not found we return null to indicate it isn't set.
                        if (res == 0xC0000034)  // STATUS_OBJECT_NAME_NOT_FOUND
                            return null;

                        throw new Win32Exception(NativeMethods.LsaNtStatusToWinError(res),
                            String.Format("LsaRetrievePrivateData({0}) failed", key));
                    }

                    NativeHelpers.LSA_UNICODE_STRING lsaString = (NativeHelpers.LSA_UNICODE_STRING)
                        Marshal.PtrToStructure(buffer.DangerousGetHandle(),
                        typeof(NativeHelpers.LSA_UNICODE_STRING));
                    return (string)lsaString;
                }
            }
        }
    }
}
'@

$details = Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon'
$module.Result.AutoAdminLogon = $details.AutoAdminLogon
$module.Result.DefaultUserName = $details.DefaultUserName
$module.Result.DefaultDomainName = $details.DefaultDomainName
$module.Result.DefaultPassword = $details.DefaultPassword
$module.Result.AutoLogonCount = $details.AutoLogonCount

$handle = [Ansible.TestAutoLogonInfo.LsaUtil]::OpenPolicy(0x00000004)
try {
    $password = [Ansible.TestAutoLogonInfo.LsaUtil]::RetrievePrivateData($handle, 'DefaultPassword')
    $module.Result.LsaPassword = $password
} finally {
    $handle.Dispose()
}

$module.ExitJson()
