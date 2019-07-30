#!powershell

# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.AddType

$spec = @{
    options = @{
        connection = @{ type = "str" }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$connection = $module.Params.connection

$win_inet_invoke = @'
using Microsoft.Win32.SafeHandles;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.ConstrainedExecution;
using System.Runtime.InteropServices;

namespace Ansible.WinINetProxyInfo
{
    internal class NativeHelpers
    {
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public class INTERNET_PER_CONN_OPTION_LISTW : IDisposable
        {
            public UInt32 dwSize;
            public IntPtr pszConnection;
            public UInt32 dwOptionCount;
            public UInt32 dwOptionError;
            public IntPtr pOptions;

            public INTERNET_PER_CONN_OPTION_LISTW()
            {
                dwSize = (UInt32)Marshal.SizeOf(this);
            }

            public void Dispose()
            {
                if (pszConnection != IntPtr.Zero)
                    Marshal.FreeHGlobal(pszConnection);
                if (pOptions != IntPtr.Zero)
                    Marshal.FreeHGlobal(pOptions);
                GC.SuppressFinalize(this);
            }
            ~INTERNET_PER_CONN_OPTION_LISTW() { this.Dispose(); }
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public class INTERNET_PER_CONN_OPTIONW : IDisposable
        {
            public INTERNET_PER_CONN_OPTION dwOption;
            public ValueUnion Value;

            [StructLayout(LayoutKind.Explicit)]
            public class ValueUnion
            {
                [FieldOffset(0)]
                public UInt32 dwValue;

                [FieldOffset(0)]
                public IntPtr pszValue;

                [FieldOffset(0)]
                public System.Runtime.InteropServices.ComTypes.FILETIME ftValue;
            }

            public void Dispose()
            {
                // We can't just check if Value.pszValue is not IntPtr.Zero as the union means it could be set even
                // when the value is a UInt32 or FILETIME. We check against a known string option type and only free
                // the value in those cases.
                List<INTERNET_PER_CONN_OPTION> stringOptions = new List<INTERNET_PER_CONN_OPTION>
                {
                    { INTERNET_PER_CONN_OPTION.INTERNET_PER_CONN_AUTOCONFIG_URL },
                    { INTERNET_PER_CONN_OPTION.INTERNET_PER_CONN_PROXY_BYPASS },
                    { INTERNET_PER_CONN_OPTION.INTERNET_PER_CONN_PROXY_SERVER }
                };
                if (Value != null && Value.pszValue != IntPtr.Zero && stringOptions.Contains(dwOption))
                    Marshal.FreeHGlobal(Value.pszValue);
                GC.SuppressFinalize(this);
            }
            ~INTERNET_PER_CONN_OPTIONW() { this.Dispose(); }
        }

        public enum INTERNET_OPTION : uint
        {
            INTERNET_OPTION_PER_CONNECTION_OPTION = 75,
        }

        public enum INTERNET_PER_CONN_OPTION : uint
        {
            INTERNET_PER_CONN_FLAGS = 1,
            INTERNET_PER_CONN_PROXY_SERVER = 2,
            INTERNET_PER_CONN_PROXY_BYPASS = 3,
            INTERNET_PER_CONN_AUTOCONFIG_URL = 4,
            INTERNET_PER_CONN_AUTODISCOVERY_FLAGS = 5,
            INTERNET_PER_CONN_FLAGS_UI = 10,  // IE8+ - Included with Windows 7 and Server 2008 R2
        }

        [Flags]
        public enum PER_CONN_FLAGS : uint
        {
            PROXY_TYPE_DIRECT = 0x00000001,
            PROXY_TYPE_PROXY = 0x00000002,
            PROXY_TYPE_AUTO_PROXY_URL = 0x00000004,
            PROXY_TYPE_AUTO_DETECT = 0x00000008,
        }
    }

    internal class NativeMethods
    {
        [DllImport("Wininet.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool InternetQueryOptionW(
            IntPtr hInternet,
            NativeHelpers.INTERNET_OPTION dwOption,
            SafeMemoryBuffer lpBuffer,
            ref UInt32 lpdwBufferLength);
    }

    internal class SafeMemoryBuffer : SafeHandleZeroOrMinusOneIsInvalid
    {
        public SafeMemoryBuffer() : base(true) { }
        public SafeMemoryBuffer(int cb) : base(true)
        {
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

    public class WinINetProxy
    {
        private string Connection;

        public string AutoConfigUrl;
        public bool AutoDetect;
        public string Proxy;
        public string ProxyBypass;

        public WinINetProxy(string connection)
        {
            Connection = connection;
            Refresh();
        }

        public void Refresh()
        {
            using (var connFlags = CreateConnOption(NativeHelpers.INTERNET_PER_CONN_OPTION.INTERNET_PER_CONN_FLAGS_UI))
            using (var autoConfigUrl = CreateConnOption(NativeHelpers.INTERNET_PER_CONN_OPTION.INTERNET_PER_CONN_AUTOCONFIG_URL))
            using (var server = CreateConnOption(NativeHelpers.INTERNET_PER_CONN_OPTION.INTERNET_PER_CONN_PROXY_SERVER))
            using (var bypass = CreateConnOption(NativeHelpers.INTERNET_PER_CONN_OPTION.INTERNET_PER_CONN_PROXY_BYPASS))
            {
                NativeHelpers.INTERNET_PER_CONN_OPTIONW[] options = new NativeHelpers.INTERNET_PER_CONN_OPTIONW[]
                {
                    connFlags, autoConfigUrl, server, bypass
                };

                try
                {
                    QueryOption(options, Connection);
                }
                catch (Win32Exception e)
                {
                    if (e.NativeErrorCode == 87) // ERROR_INVALID_PARAMETER
                    {
                        // INTERNET_PER_CONN_FLAGS_UI only works for IE8+, try the fallback in case we are still working
                        // with an ancient version.
                        connFlags.dwOption = NativeHelpers.INTERNET_PER_CONN_OPTION.INTERNET_PER_CONN_FLAGS;
                        QueryOption(options, Connection);
                    }
                    else
                        throw;
                }

                NativeHelpers.PER_CONN_FLAGS flags = (NativeHelpers.PER_CONN_FLAGS)connFlags.Value.dwValue;

                AutoConfigUrl = flags.HasFlag(NativeHelpers.PER_CONN_FLAGS.PROXY_TYPE_AUTO_PROXY_URL)
                    ? Marshal.PtrToStringUni(autoConfigUrl.Value.pszValue) : null;
                AutoDetect = flags.HasFlag(NativeHelpers.PER_CONN_FLAGS.PROXY_TYPE_AUTO_DETECT);
                if (flags.HasFlag(NativeHelpers.PER_CONN_FLAGS.PROXY_TYPE_PROXY))
                {
                    Proxy = Marshal.PtrToStringUni(server.Value.pszValue);
                    ProxyBypass = Marshal.PtrToStringUni(bypass.Value.pszValue);
                }
                else
                {
                    Proxy = null;
                    ProxyBypass = null;
                }
            }
        }

        internal static NativeHelpers.INTERNET_PER_CONN_OPTIONW CreateConnOption(NativeHelpers.INTERNET_PER_CONN_OPTION option)
        {
            return new NativeHelpers.INTERNET_PER_CONN_OPTIONW
            {
                dwOption = option,
                Value = new NativeHelpers.INTERNET_PER_CONN_OPTIONW.ValueUnion(),
            };
        }

        internal static void QueryOption(NativeHelpers.INTERNET_PER_CONN_OPTIONW[] options, string connection = null)
        {
            using (NativeHelpers.INTERNET_PER_CONN_OPTION_LISTW optionList = new NativeHelpers.INTERNET_PER_CONN_OPTION_LISTW())
            using (SafeMemoryBuffer optionListPtr = MarshalOptionList(optionList, options, connection))
            {
                UInt32 bufferSize = optionList.dwSize;
                if (!NativeMethods.InternetQueryOptionW(
                    IntPtr.Zero,
                    NativeHelpers.INTERNET_OPTION.INTERNET_OPTION_PER_CONNECTION_OPTION,
                    optionListPtr,
                    ref bufferSize))
                {
                    throw new Win32Exception();
                }

                for (int i = 0; i < options.Length; i++)
                {
                    IntPtr opt = IntPtr.Add(optionList.pOptions, i * Marshal.SizeOf(typeof(NativeHelpers.INTERNET_PER_CONN_OPTIONW)));
                    NativeHelpers.INTERNET_PER_CONN_OPTIONW option = (NativeHelpers.INTERNET_PER_CONN_OPTIONW)Marshal.PtrToStructure(opt,
                        typeof(NativeHelpers.INTERNET_PER_CONN_OPTIONW));
                    options[i].Value = option.Value;
                    option.Value = null;  // Stops the GC from freeing the same memory twice
                }
            }
        }

        internal static SafeMemoryBuffer MarshalOptionList(NativeHelpers.INTERNET_PER_CONN_OPTION_LISTW optionList,
            NativeHelpers.INTERNET_PER_CONN_OPTIONW[] options, string connection)
        {
            optionList.pszConnection = Marshal.StringToHGlobalUni(connection);
            optionList.dwOptionCount = (UInt32)options.Length;

            int optionSize = Marshal.SizeOf(typeof(NativeHelpers.INTERNET_PER_CONN_OPTIONW));
            optionList.pOptions = Marshal.AllocHGlobal(optionSize * options.Length);
            for (int i = 0; i < options.Length; i++)
            {
                IntPtr option = IntPtr.Add(optionList.pOptions, i * optionSize);
                Marshal.StructureToPtr(options[i], option, false);
            }

            SafeMemoryBuffer optionListPtr = new SafeMemoryBuffer((int)optionList.dwSize);
            Marshal.StructureToPtr(optionList, optionListPtr.DangerousGetHandle(), false);
            return optionListPtr;
        }
    }
}
'@
Add-CSharpType -References $win_inet_invoke -AnsibleModule $module

$proxy = New-Object -TypeName Ansible.WinINetProxyInfo.WinINetProxy -ArgumentList @(,$connection)
$module.Result.auto_config_url = $proxy.AutoConfigUrl
$module.Result.auto_detect = $proxy.AutoDetect
$module.Result.proxy = $proxy.Proxy
$module.Result.bypass = $proxy.ProxyBypass

$module.ExitJson()
