#!powershell

# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.AddType

$spec = @{
    options = @{
        bypass = @{ type = "list" }
        proxy = @{ type = "raw" }
        source = @{ type = "str"; choices = @("ie") }
    }
    mutually_exclusive = @(
        @("proxy", "source"),
        @("bypass", "source")
    )
    required_by = @{
        bypass = @("proxy")
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$proxy = $module.Params.proxy
$bypass = $module.Params.bypass
$source = $module.Params.source

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

$win_http_invoke = @'
using System;
using System.Runtime.InteropServices;

namespace Ansible.WinHttpProxy
{
    internal class NativeHelpers
    {
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public class WINHTTP_CURRENT_USER_IE_PROXY_CONFIG : IDisposable
        {
            public bool fAutoDetect;
            public IntPtr lpszAutoConfigUrl;
            public IntPtr lpszProxy;
            public IntPtr lpszProxyBypass;

            public void Dispose()
            {
                if (lpszAutoConfigUrl != IntPtr.Zero)
                    Marshal.FreeHGlobal(lpszAutoConfigUrl);
                if (lpszProxy != IntPtr.Zero)
                    Marshal.FreeHGlobal(lpszProxy);
                if (lpszProxyBypass != IntPtr.Zero)
                    Marshal.FreeHGlobal(lpszProxyBypass);
                GC.SuppressFinalize(this);
            }
            ~WINHTTP_CURRENT_USER_IE_PROXY_CONFIG() { this.Dispose(); }
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public class WINHTTP_PROXY_INFO : IDisposable
        {
            public UInt32 dwAccessType;
            public IntPtr lpszProxy;
            public IntPtr lpszProxyBypass;

            public void Dispose()
            {
                if (lpszProxy != IntPtr.Zero)
                    Marshal.FreeHGlobal(lpszProxy);
                if (lpszProxyBypass != IntPtr.Zero)
                    Marshal.FreeHGlobal(lpszProxyBypass);
                GC.SuppressFinalize(this);
            }
            ~WINHTTP_PROXY_INFO() { this.Dispose(); }
        }
    }

    internal class NativeMethods
    {
        [DllImport("Winhttp.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool WinHttpGetDefaultProxyConfiguration(
            [Out] NativeHelpers.WINHTTP_PROXY_INFO pProxyInfo);

        [DllImport("Winhttp.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool WinHttpGetIEProxyConfigForCurrentUser(
            [Out] NativeHelpers.WINHTTP_CURRENT_USER_IE_PROXY_CONFIG pProxyConfig);

        [DllImport("Winhttp.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool WinHttpSetDefaultProxyConfiguration(
            NativeHelpers.WINHTTP_PROXY_INFO pProxyInfo);
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
        public bool AutoDetect;
        public string AutoConfigUrl;
        public string Proxy;
        public string ProxyBypass;
    }

    public class WinHttpProxy
    {
        public string Proxy;
        public string ProxyBypass;

        public WinHttpProxy()
        {
            Refresh();
        }

        public void Set()
        {
            using (NativeHelpers.WINHTTP_PROXY_INFO proxyInfo = new NativeHelpers.WINHTTP_PROXY_INFO())
            {
                if (String.IsNullOrEmpty(Proxy))
                    proxyInfo.dwAccessType = 1; // WINHTTP_ACCESS_TYPE_NO_PROXY
                else
                {
                    proxyInfo.dwAccessType = 3; // WINHTTP_ACCESS_TYPE_NAMED_PROXY
                    proxyInfo.lpszProxy = Marshal.StringToHGlobalUni(Proxy);

                    if (!String.IsNullOrEmpty(ProxyBypass))
                        proxyInfo.lpszProxyBypass = Marshal.StringToHGlobalUni(ProxyBypass);
                }

                if (!NativeMethods.WinHttpSetDefaultProxyConfiguration(proxyInfo))
                    throw new Win32Exception("WinHttpSetDefaultProxyConfiguration() failed");
            }
        }

        public void Refresh()
        {
            using (NativeHelpers.WINHTTP_PROXY_INFO proxyInfo = new NativeHelpers.WINHTTP_PROXY_INFO())
            {
                if (!NativeMethods.WinHttpGetDefaultProxyConfiguration(proxyInfo))
                    throw new Win32Exception("WinHttpGetDefaultProxyConfiguration() failed");

                Proxy = Marshal.PtrToStringUni(proxyInfo.lpszProxy);
                ProxyBypass = Marshal.PtrToStringUni(proxyInfo.lpszProxyBypass);
            }
        }

        public static WinINetProxy GetIEProxyConfig()
        {
            using (NativeHelpers.WINHTTP_CURRENT_USER_IE_PROXY_CONFIG ieProxy = new NativeHelpers.WINHTTP_CURRENT_USER_IE_PROXY_CONFIG())
            {
                if (!NativeMethods.WinHttpGetIEProxyConfigForCurrentUser(ieProxy))
                    throw new Win32Exception("WinHttpGetIEProxyConfigForCurrentUser() failed");

                return new WinINetProxy
                {
                    AutoDetect = ieProxy.fAutoDetect,
                    AutoConfigUrl = Marshal.PtrToStringUni(ieProxy.lpszAutoConfigUrl),
                    Proxy = Marshal.PtrToStringUni(ieProxy.lpszProxy),
                    ProxyBypass = Marshal.PtrToStringUni(ieProxy.lpszProxyBypass),
                };
            }
        }
    }
}
'@
Add-CSharpType -References $win_http_invoke -AnsibleModule $module

$actual_proxy = New-Object -TypeName Ansible.WinHttpProxy.WinHttpProxy

$module.Diff.before = @{
    proxy = $actual_proxy.Proxy
    bypass = $actual_proxy.ProxyBypass
}

if ($source -eq "ie") {
    # If source=ie we need to get the server and bypass values from the IE configuration
    $ie_proxy = [Ansible.WinHttpProxy.WinHttpProxy]::GetIEProxyConfig()
    $proxy = $ie_proxy.Proxy
    $bypass = $ie_proxy.ProxyBypass
}

$previous_proxy = $actual_proxy.Proxy
$previous_bypass = $actual_proxy.ProxyBypass

# Make sure an empty string is converted to $null for easier comparisons
if ([String]::IsNullOrEmpty($proxy)) {
    $proxy = $null
}
if ([String]::IsNullOrEmpty($bypass)) {
    $bypass = $null
}

if ($previous_proxy -ne $proxy -or $previous_bypass -ne $bypass) {
    $actual_proxy.Proxy = $proxy
    $actual_proxy.ProxyBypass = $bypass

    if (-not $module.CheckMode) {
        $actual_proxy.Set()

        # Validate that the change was made correctly and revert if it wasn't. The Set() method won't fail on invalid
        # values so we need to check again to make sure all was good.
        $actual_proxy.Refresh()
        if ($actual_proxy.Proxy -ne $proxy -or $actual_proxy.ProxyBypass -ne $bypass) {
            $actual_proxy.Proxy = $previous_proxy
            $actual_proxy.ProxyBypass = $previous_bypass
            $actual_proxy.Set()

            $module.FailJson("Unknown error when trying to set proxy '$proxy' or bypass '$bypass'")
        }
    }

    $module.Result.changed = $true
}

$module.Diff.after = @{
    proxy = $proxy
    bypass = $bypass
}

$module.ExitJson()

