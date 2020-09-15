#!powershell

# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.AddType

$spec = @{
    options = @{
        auto_detect = @{ type = "bool"; default = $true }
        auto_config_url = @{ type = "str" }
        proxy = @{ type = "raw" }
        bypass = @{ type = "list" }
        connection = @{ type = "str" }
    }
    required_by = @{
        bypass = @("proxy")
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$auto_detect = $module.Params.auto_detect
$auto_config_url = $module.Params.auto_config_url
$proxy = $module.Params.proxy
$bypass = $module.Params.bypass
$connection = $module.Params.connection

# Parse the raw value, it should be a Dictionary or String
if ($proxy -is [System.Collections.IDictionary]) {
    $valid_keys = [System.Collections.Generic.List`1[String]]@("http", "https", "ftp", "socks")
    # Check to make sure we don't have any invalid keys in the dict
    $invalid_keys = [System.Collections.Generic.List`1[String]]@()
    foreach ($k in $proxy.Keys) {
        if ($k -notin $valid_keys) {
            $invalid_keys.Add($k)
        }
    }

    if ($invalid_keys.Count -gt 0) {
        $invalid_keys = $invalid_keys | Sort-Object  # So our test assertion doesn't fail due to random ordering
        $module.FailJson("Invalid keys found in proxy: $($invalid_keys -join ', '). Valid keys are $($valid_keys -join ', ').")
    }

    # Build the proxy string in the form 'protocol=host;', the order of valid_keys is also important
    $proxy_list = [System.Collections.Generic.List`1[String]]@()
    foreach ($k in $valid_keys) {
        if ($proxy.ContainsKey($k)) {
            $proxy_list.Add("$k=$($proxy.$k)")
        }
    }
    $proxy = $proxy_list -join ";"
} elseif ($null -ne $proxy) {
    $proxy = $proxy.ToString()
}

if ($bypass) {
    if ([System.String]::IsNullOrEmpty($proxy)) {
        $module.FailJson("missing parameter(s) required by ''bypass'': proxy")
    }
    $bypass = $bypass -join ';'
}

$win_inet_invoke = @'
using Microsoft.Win32.SafeHandles;
using System;
using System.Collections.Generic;
using System.Runtime.ConstrainedExecution;
using System.Runtime.InteropServices;

namespace Ansible.WinINetProxy
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
            INTERNET_OPTION_PROXY_SETTINGS_CHANGED = 95,
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

        [DllImport("Wininet.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool InternetSetOptionW(
            IntPtr hInternet,
            NativeHelpers.INTERNET_OPTION dwOption,
            SafeMemoryBuffer lpBuffer,
            UInt32 dwBufferLength);

        [DllImport("Rasapi32.dll", CharSet = CharSet.Unicode)]
        public static extern UInt32 RasValidateEntryNameW(
            string lpszPhonebook,
            string lpszEntry);
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

    public class Win32Exception : System.ComponentModel.Win32Exception
    {
        private string _msg;

        public Win32Exception(string message) : this(Marshal.GetLastWin32Error(), message) { }
        public Win32Exception(int errorCode, string message) : base(errorCode)
        {
            _msg = String.Format("{0} ({1}, Win32ErrorCode {2})", message, base.Message, errorCode);
        }

        public override string Message { get { return _msg; } }
        public static explicit operator Win32Exception(string message) { return new Win32Exception(message); }
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

        public static bool IsValidConnection(string name)
        {
            // RasValidateEntryName is used to verify is a name can be a valid phonebook entry. It returns 0 if no
            // entry exists and 183 if it already exists. We just need to check if it returns 183 to verify the
            // connection name.
            return NativeMethods.RasValidateEntryNameW(null, name) == 183;
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

        public void Set()
        {
            using (var connFlags = CreateConnOption(NativeHelpers.INTERNET_PER_CONN_OPTION.INTERNET_PER_CONN_FLAGS_UI))
            using (var autoConfigUrl = CreateConnOption(NativeHelpers.INTERNET_PER_CONN_OPTION.INTERNET_PER_CONN_AUTOCONFIG_URL))
            using (var server = CreateConnOption(NativeHelpers.INTERNET_PER_CONN_OPTION.INTERNET_PER_CONN_PROXY_SERVER))
            using (var bypass = CreateConnOption(NativeHelpers.INTERNET_PER_CONN_OPTION.INTERNET_PER_CONN_PROXY_BYPASS))
            {
                List<NativeHelpers.INTERNET_PER_CONN_OPTIONW> options = new List<NativeHelpers.INTERNET_PER_CONN_OPTIONW>();

                // PROXY_TYPE_DIRECT seems to always be set, need to verify
                NativeHelpers.PER_CONN_FLAGS flags = NativeHelpers.PER_CONN_FLAGS.PROXY_TYPE_DIRECT;
                if (AutoDetect)
                    flags |= NativeHelpers.PER_CONN_FLAGS.PROXY_TYPE_AUTO_DETECT;

                if (!String.IsNullOrEmpty(AutoConfigUrl))
                {
                    flags |= NativeHelpers.PER_CONN_FLAGS.PROXY_TYPE_AUTO_PROXY_URL;
                    autoConfigUrl.Value.pszValue = Marshal.StringToHGlobalUni(AutoConfigUrl);
                }
                options.Add(autoConfigUrl);

                if (!String.IsNullOrEmpty(Proxy))
                {
                    flags |= NativeHelpers.PER_CONN_FLAGS.PROXY_TYPE_PROXY;
                    server.Value.pszValue = Marshal.StringToHGlobalUni(Proxy);
                }
                options.Add(server);

                if (!String.IsNullOrEmpty(ProxyBypass))
                    bypass.Value.pszValue = Marshal.StringToHGlobalUni(ProxyBypass);
                options.Add(bypass);

                connFlags.Value.dwValue = (UInt32)flags;
                options.Add(connFlags);

                SetOption(options.ToArray(), Connection);

                // Tell IE that the proxy settings have been changed.
                if (!NativeMethods.InternetSetOptionW(
                    IntPtr.Zero,
                    NativeHelpers.INTERNET_OPTION.INTERNET_OPTION_PROXY_SETTINGS_CHANGED,
                    new SafeMemoryBuffer(IntPtr.Zero),
                    0))
                {
                    throw new Win32Exception("InternetSetOptionW(INTERNET_OPTION_PROXY_SETTINGS_CHANGED) failed");
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
                    throw new Win32Exception("InternetQueryOptionW(INTERNET_OPTION_PER_CONNECTION_OPTION) failed");
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

        internal static void SetOption(NativeHelpers.INTERNET_PER_CONN_OPTIONW[] options, string connection = null)
        {
            using (NativeHelpers.INTERNET_PER_CONN_OPTION_LISTW optionList = new NativeHelpers.INTERNET_PER_CONN_OPTION_LISTW())
            using (SafeMemoryBuffer optionListPtr = MarshalOptionList(optionList, options, connection))
            {
                if (!NativeMethods.InternetSetOptionW(
                    IntPtr.Zero,
                    NativeHelpers.INTERNET_OPTION.INTERNET_OPTION_PER_CONNECTION_OPTION,
                    optionListPtr,
                    optionList.dwSize))
                {
                    throw new Win32Exception("InternetSetOptionW(INTERNET_OPTION_PER_CONNECTION_OPTION) failed");
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

# We need to validate the connection because WinINet will just silently continue even if the connection does not
# already exist.
if ($null -ne $connection -and -not [Ansible.WinINetProxy.WinINetProxy]::IsValidConnection($connection)) {
    $module.FailJson("The connection '$connection' does not exist.")
}

$actual_proxy = New-Object -TypeName Ansible.WinINetProxy.WinINetProxy -ArgumentList @(,$connection)
$module.Diff.before = @{
    auto_config_url = $actual_proxy.AutoConfigUrl
    auto_detect = $actual_proxy.AutoDetect
    bypass = $actual_proxy.ProxyBypass
    server = $actual_proxy.Proxy
}

# Make sure an empty string is converted to $null for easier comparisons
if ([String]::IsNullOrEmpty($auto_config_url)) {
    $auto_config_url = $null
}
if ([String]::IsNullOrEmpty($proxy)) {
    $proxy = $null
}
if ([String]::IsNullOrEmpty($bypass)) {
    $bypass = $null
}

# Record the original values in case we need to revert on a failure
$previous_auto_config_url = $actual_proxy.AutoConfigUrl
$previous_auto_detect = $actual_proxy.AutoDetect
$previous_proxy = $actual_proxy.Proxy
$previous_bypass = $actual_proxy.ProxyBypass

$changed = $false
if ($auto_config_url -ne $previous_auto_config_url) {
    $actual_proxy.AutoConfigUrl = $auto_config_url
    $changed = $true
}

if ($auto_detect -ne $previous_auto_detect) {
    $actual_proxy.AutoDetect = $auto_detect
    $changed = $true
}

if ($proxy -ne $previous_proxy) {
    $actual_proxy.Proxy = $proxy
    $changed = $true
}

if ($bypass -ne $previous_bypass) {
    $actual_proxy.ProxyBypass = $bypass
    $changed = $true
}

if ($changed -and -not $module.CheckMode) {
    $actual_proxy.Set()

    # Validate that the change was made correctly and revert if it wasn't. THe Set() method won't fail on invalid
    # values so we need to check again to make sure all was good
    $actual_proxy.Refresh()
    if ($actual_proxy.AutoConfigUrl -ne $auto_config_url -or
        $actual_proxy.AutoDetect -ne $auto_detect -or
        $actual_proxy.Proxy -ne $proxy -or
        $actual_proxy.ProxyBypass -ne $bypass) {

        $actual_proxy.AutoConfigUrl = $previous_auto_config_url
        $actual_proxy.AutoDetect = $previous_auto_detect
        $actual_proxy.Proxy = $previous_proxy
        $actual_proxy.ProxyBypass = $previous_bypass
        $actual_proxy.Set()

        $module.FailJson("Unknown error when trying to set auto_config_url '$auto_config_url', proxy '$proxy', or bypass '$bypass'")
    }
}
$module.Result.changed = $changed

$module.Diff.after = @{
    auto_config_url = $auto_config_url
    auto_detect = $auto_detect
    bypass = $bypass
    proxy = $proxy
}

$module.ExitJson()
