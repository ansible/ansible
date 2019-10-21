#!powershell

# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.AddType

# This is a very basic skeleton of a possible Windows module for managing RAS connections. It is mostly barebones
# to enable testing for win_inet_proxy but I've done a bit of extra work in the PInvoke space to possible expand
# sometime in the future.

$spec = @{
    options = @{
        device_type = @{
            type = "str"
            choices = @("atm", "framerelay", "generic", "rda", "isdn", "modem", "pad",
                "parallel", "pppoe", "vpn", "serial", "sonet", "sw56", "x25")
        }
        device_name = @{ type = "str" }
        framing_protocol = @{ type = "str"; choices = @("ppp", "ras", "slip") }
        name = @{ type = "str"; required = $true }
        options = @{ type = "list" }
        state = @{ type = "str"; choices = @("absent", "present"); default = "present" }
        type = @{ type = "str"; choices = @("broadband", "direct", "phone", "vpn")}
    }
    required_if = @(
        ,@("state", "present", @("type", "device_name", "device_type", "framing_protocol"))
    )
    supports_check_mode = $false
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$device_type = $module.Params.device_type
$device_name = $module.Params.device_name
$framing_protocol = $module.Params.framing_protocol
$name = $module.Params.name
$options = $module.Params.options
$state = $module.Params.state
$type = $module.Params.type

$module.Result.guid = [System.Guid]::Empty

$win_ras_invoke = @'
using System;
using System.Runtime.InteropServices;

namespace Ansible.WinPhonebookEntry
{
    public class NativeHelpers
    {
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public class RASENTRYW
        {
            public UInt32 dwSize;
            public RasEntryOptions dwfOptions;
            public UInt32 dwCountryId;
            public UInt32 dwCountryCode;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 11)] public string szAreaCode;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 129)] public string szLocalPhoneNumber;
            public UInt32 dwAlternateOffset;
            public RASIPADDR ipaddr;
            public RASIPADDR ipaddrDns;
            public RASIPADDR ipaddrDnsAlt;
            public RASIPADDR ipaddrWins;
            public RASIPADDR ipaddrWinsAlt;
            public UInt32 dwFrameSize;
            public RasNetProtocols dwfNetProtocols;
            public RasFramingProtocol dwFramingProtocol;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)] public string szScript;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)] public string szAutodialDll;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)] public string szAutodialFunc;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 17)] public string szDeviceType;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 129)] public string szDeviceName;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 33)] public string szX25PadType;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 201)] public string szX25Address;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 201)] public string szX25Facilities;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 201)] public string szX25UserData;
            public UInt32 dwChannels;
            public UInt32 dwReserved1;
            public UInt32 dwReserved2;
            public UInt32 dwSubEntries;
            public RasDialMode dwDialMode;
            public UInt32 dwDialExtraPercent;
            public UInt32 dwDialExtraSampleSeconds;
            public UInt32 dwHangUpExtraPercent;
            public UInt32 dwHangUpExtraSampleSeconds;
            public UInt32 dwIdleDisconnectSeconds;
            public RasEntryTypes dwType;
            public RasEntryEncryption dwEntryptionType;
            public UInt32 dwCustomAuthKey;
            public Guid guidId;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)] public string szCustomDialDll;
            public RasVpnStrategy dwVpnStrategy;
            public RasEntryOptions2 dwfOptions2;
            public UInt32 dwfOptions3;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 256)] public string szDnsSuffix;
            public UInt32 dwTcpWindowSize;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)] public string szPrerequisitePbk;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 257)] public string szPrerequisiteEntry;
            public UInt32 dwRedialCount;
            public UInt32 dwRedialPause;
            public RASIPV6ADDR ipv6addrDns;
            public RASIPV6ADDR ipv6addrDnsAlt;
            public UInt32 dwIPv4InterfaceMatrix;
            public UInt32 dwIPv6InterfaceMatrix;
            // Server 2008 R2 / Windows 7+
            // We cannot include these fields when running in Server 2008 as it will break the SizeOf calc of the struct
#if !LONGHORN
            public RASIPV6ADDR ipv6addr;
            public UInt32 dwIPv6PrefixLength;
            public UInt32 dwNetworkOutageTime;
#endif

            public RASENTRYW()
            {
                this.dwSize = (UInt32)Marshal.SizeOf(this);
            }
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct RASIPADDR
        {
            public byte a;
            public byte b;
            public byte c;
            public byte d;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct RASIPV6ADDR
        {
            byte a;
            byte b;
            byte c;
            byte d;
            byte e;
            byte f;
            byte g;
            byte h;
            byte i;
            byte j;
            byte k;
            byte l;
            byte m;
            byte n;
            byte o;
            byte p;
        }

        public enum RasDialMode : uint
        {
            RASEDM_DialAll = 1,
            RASEDM_DialAsNeeded = 2,
        }

        public enum RasEntryEncryption : uint
        {
            ET_None = 0,
            ET_Require = 1,
            ET_RequireMax = 2,
            ET_Optional = 3
        }

        [Flags]
        public enum RasEntryOptions : uint
        {
            RASEO_UseCountryAndAreaCodes = 0x00000001,
            RASEO_SpecificIpAddr = 0x00000002,
            RASEO_SpecificNameServers = 0x00000004,
            RASEO_IpHeaderCompression = 0x00000008,
            RASEO_RemoteDefaultGateway = 0x00000010,
            RASEO_DisableLcpExtensions = 0x00000020,
            RASEO_TerminalBeforeDial = 0x00000040,
            RASEO_TerminalAfterDial = 0x00000080,
            RASEO_ModemLights = 0x00000100,
            RASEO_SwCompression = 0x00000200,
            RASEO_RequireEncrptedPw = 0x00000400,
            RASEO_RequireMsEncrptedPw = 0x00000800,
            RASEO_RequireDataEncrption = 0x00001000,
            RASEO_NetworkLogon = 0x00002000,
            RASEO_UseLogonCredentials = 0x00004000,
            RASEO_PromoteAlternates = 0x00008000,
            RASEO_SecureLocalFiles = 0x00010000,
            RASEO_RequireEAP = 0x00020000,
            RASEO_RequirePAP = 0x00040000,
            RASEO_RequireSPAP = 0x00080000,
            RASEO_Custom = 0x00100000,
            RASEO_PreviewPhoneNumber = 0x00200000,
            RASEO_SharedPhoneNumbers = 0x00800000,
            RASEO_PreviewUserPw = 0x01000000,
            RASEO_PreviewDomain = 0x02000000,
            RASEO_ShowDialingProgress = 0x04000000,
            RASEO_RequireCHAP = 0x08000000,
            RASEO_RequireMsCHAP = 0x10000000,
            RASEO_RequireMsCHAP2 = 0x20000000,
            RASEO_RequireW95MSCHAP = 0x40000000,
            RASEO_CustomScript = 0x80000000,
        }

        [Flags]
        public enum RasEntryOptions2 : uint
        {
            RASEO2_None = 0x00000000,
            RASEO2_SecureFileAndPrint = 0x00000001,
            RASEO2_SecureClientForMSNet = 0x00000002,
            RASEO2_DontNegotiateMultilink = 0x00000004,
            RASEO2_DontUseRasCredentials = 0x00000008,
            RASEO2_UsePreSharedKey = 0x00000010,
            RASEO2_Internet = 0x00000020,
            RASEO2_DisableNbtOverIP = 0x00000040,
            RASEO2_UseGlobalDeviceSettings = 0x00000080,
            RASEO2_ReconnectIfDropped = 0x00000100,
            RASEO2_SharePhoneNumbers = 0x00000200,
            RASEO2_SecureRoutingCompartment = 0x00000400,
            RASEO2_UseTypicalSettings = 0x00000800,
            RASEO2_IPv6SpecificNameServers = 0x00001000,
            RASEO2_IPv6RemoteDefaultGateway = 0x00002000,
            RASEO2_RegisterIpWithDNS = 0x00004000,
            RASEO2_UseDNSSuffixForRegistration = 0x00008000,
            RASEO2_IPv4ExplicitMetric = 0x00010000,
            RASEO2_IPv6ExplicitMetric = 0x00020000,
            RASEO2_DisableIKENameEkuCheck = 0x00040000,
            // Server 2008 R2 / Windows 7+
            RASEO2_DisableClassBasedStaticRoute = 0x00800000,
            RASEO2_SpecificIPv6Addr = 0x01000000,
            RASEO2_DisableMobility = 0x02000000,
            RASEO2_RequireMachineCertificates = 0x04000000,
            // Server 2012 / Windows 8+
            RASEO2_UsePreSharedKeyForIkev2Initiator = 0x00800000,
            RASEO2_UsePreSharedKeyForIkev2Responder = 0x01000000,
            RASEO2_CacheCredentials = 0x02000000,
            // Server 2012 R2 / Windows 8.1+
            RASEO2_AutoTriggerCapable = 0x04000000,
            RASEO2_IsThirdPartyProfile = 0x08000000,
            RASEO2_AuthTypeIsOtp = 0x10000000,
            // Server 2016 / Windows 10+
            RASEO2_IsAlwaysOn = 0x20000000,
            RASEO2_IsPrivateNetwork = 0x40000000,
        }

        public enum RasEntryTypes : uint
        {
            RASET_Phone = 1,
            RASET_Vpn = 2,
            RASET_Direct = 3,
            RASET_Internet = 4,
            RASET_Broadband = 5,
        }

        public enum RasFramingProtocol : uint
        {
            RASFP_Ppp = 0x00000001,
            RASFP_Slip = 0x00000002,
            RASFP_Ras = 0x00000004
        }

        [Flags]
        public enum RasNetProtocols : uint
        {
            RASNP_NetBEUI = 0x00000001,
            RASNP_Ipx = 0x00000002,
            RASNP_Ip = 0x00000004,
            RASNP_Ipv6 = 0x00000008
        }

        public enum RasVpnStrategy : uint
        {
            VS_Default = 0,
            VS_PptpOnly = 1,
            VS_PptpFirst = 2,
            VS_L2tpOnly = 3,
            VS_L2tpFirst = 4,
            VS_SstpOnly = 5,
            VS_SstpFirst = 6,
            VS_Ikev2Only = 7,
            VS_Ikev2First = 8,
            VS_GREOnly = 9,
            VS_PptpSstp = 12,
            VS_L2tpSstp = 13,
            VS_Ikev2Sstp = 14,
        }
    }

    internal class NativeMethods
    {
        [DllImport("Rasapi32.dll", CharSet = CharSet.Unicode)]
        public static extern UInt32 RasDeleteEntryW(
            string lpszPhonebook,
            string lpszEntry);

        [DllImport("Rasapi32.dll", CharSet = CharSet.Unicode)]
        public static extern UInt32 RasGetEntryPropertiesW(
            string lpszPhonebook,
            string lpszEntry,
            [In, Out] NativeHelpers.RASENTRYW lpRasEntry,
            ref UInt32 dwEntryInfoSize,
            IntPtr lpbDeviceInfo,
            ref UInt32 dwDeviceInfoSize);

        [DllImport("Rasapi32.dll", CharSet = CharSet.Unicode)]
        public static extern UInt32 RasSetEntryPropertiesW(
            string lpszPhonebook,
            string lpszEntry,
            NativeHelpers.RASENTRYW lpRasEntry,
            UInt32 dwEntryInfoSize,
            IntPtr lpbDeviceInfo,
            UInt32 dwDeviceInfoSize);

        [DllImport("Rasapi32.dll", CharSet = CharSet.Unicode)]
        public static extern UInt32 RasValidateEntryNameW(
            string lpszPhonebook,
            string lpszEntry);
    }

    public class Phonebook
    {
        public static void CreateEntry(string entry, NativeHelpers.RASENTRYW details)
        {
            UInt32 res = NativeMethods.RasSetEntryPropertiesW(null, entry, details,
                details.dwSize, IntPtr.Zero, 0);

            if (res != 0)
                throw new Exception(String.Format("RasSetEntryPropertiesW({0}) failed {1}", entry, res));
        }

        public static void DeleteEntry(string entry)
        {
            UInt32 res = NativeMethods.RasDeleteEntryW(null, entry);
            if (res != 0)
                throw new Exception(String.Format("RasDeleteEntryW({0}) failed {1}", entry, res));
        }

        public static NativeHelpers.RASENTRYW GetEntry(string entry)
        {
            NativeHelpers.RASENTRYW details = new NativeHelpers.RASENTRYW();
            UInt32 dwEntryInfoSize = details.dwSize;
            UInt32 dwDeviceInfoSize = 0;

            UInt32 res = NativeMethods.RasGetEntryPropertiesW(null, entry, details, ref dwEntryInfoSize,
                IntPtr.Zero, ref dwDeviceInfoSize);

            if (res != 0)
                throw new Exception(String.Format("RasGetEntryPropertiesW({0}) failed {1}", entry, res));

            return details;
        }

        public static bool IsValidEntry(string entry)
        {
            // 183 == ENTRY_ALREADY_EXISTS
            return NativeMethods.RasValidateEntryNameW(null, entry) == 183;
        }
    }
}
'@

$add_type_params = @{
    Reference = $win_ras_invoke
    AnsibleModule = $module
}
# We need to set a custom compile option when running on Server 2008 due to the change in the RASENTRYW structure
$os_version = [Version](Get-Item -LiteralPath $env:SystemRoot\System32\kernel32.dll).VersionInfo.ProductVersion
if ($os_version -lt [Version]"6.1") {
    $add_type_params.CompileSymbols = @("LONGHORN")
}
Add-CSharpType @add_type_params

$exists = [Ansible.WinPhonebookEntry.Phonebook]::IsValidEntry($name)
if ($exists) {
    $entry = [Ansible.WinPhonebookEntry.Phonebook]::GetEntry($name)
    $module.Result.guid = $entry.guidId
}

if ($state -eq "present") {
    # Convert the input values to enum values
    $expected_type = switch ($type) {
        "broadband" { [Ansible.WinPhonebookEntry.NativeHelpers+RasEntryTypes]::RASET_Broadband }
        "direct" { [Ansible.WinPhonebookEntry.NativeHelpers+RasEntryTypes]::RASET_Direct }
        "phone" { [Ansible.WinPhonebookEntry.NativeHelpers+RasEntryTypes]::RASET_Phone }
        "vpn" { [Ansible.WinPhonebookEntry.NativeHelpers+RasEntryTypes]::RASET_Vpn }
    }

    $expected_framing_protocol = switch ($framing_protocol) {
        "ppp" { [Ansible.WinPhonebookEntry.NativeHelpers+RasFramingProtocol]::RASFP_Ppp }
        "ras" { [Ansible.WinPhonebookEntry.NativeHelpers+RasFramingProtocol]::RASFP_Ras }
        "slip" { [Ansible.WinPhonebookEntry.NativeHelpers+RasFramingProtocol]::RASFP_Slip }
    }

    $expected_options1 = [System.Collections.Generic.List`1[String]]@()
    $expected_options2 = [System.Collections.Generic.List`1[String]]@()
    $invalid_options = [System.Collections.Generic.List`1[String]]@()
    foreach ($option in $options) {
        # See https://msdn.microsoft.com/en-us/25c46850-4fb7-47a9-9645-139f0e869559 for more info on the options
        # TODO: some of these options are set to indicate entries in RASENTRYW, we should automatically add them
        # based on the input values.
        switch ($option) {
            # dwfOptions
            "use_country_and_area_codes" { $expected_options1.Add("RASEO_UseCountryAndAreaCode") }
            "specific_ip_addr" { $expected_options1.Add("RASEO_SpecificIpAddr") }
            "specific_name_servers" { $expected_options1.Add("RASEO_SpecificNameServers") }
            "ip_header_compression" { $expected_options1.Add("RASEO_IpHeaderCompression") }
            "remote_default_gateway" { $expected_options1.Add("RASEO_RemoteDefaultGateway") }
            "disable_lcp_extensions" { $expected_options1.Add("RASEO_DisableLcpExtensions") }
            "terminal_before_dial" { $expected_options1.Add("RASEO_TerminalBeforeDial") }
            "terminal_after_dial" { $expected_options1.Add("RASEO_TerminalAfterDial") }
            "modem_lights" { $expected_options1.Add("RASEO_ModemLights") }
            "sw_compression" { $expected_options1.Add("RASEO_SwCompression") }
            "require_encrypted_password" { $expected_options1.Add("RASEO_RequireEncrptedPw") }
            "require_ms_encrypted_password" { $expected_options1.Add("RASEO_RequireMsEncrptedPw") }
            "require_data_encryption" { $expected_options1.Add("RASEO_RequireDataEncrption") }
            "network_logon" { $expected_options1.Add("RASEO_NetworkLogon") }
            "use_logon_credentials" { $expected_options1.Add("RASEO_UseLogonCredentials") }
            "promote_alternates" { $expected_options1.Add("RASEO_PromoteAlternates") }
            "secure_local_files" { $expected_options1.Add("RASEO_SecureLocalFiles") }
            "require_eap" { $expected_options1.Add("RASEO_RequireEAP") }
            "require_pap" { $expected_options1.Add("RASEO_RequirePAP") }
            "require_spap" { $expected_options1.Add("RASEO_RequireSPAP") }
            "custom" { $expected_options1.Add("RASEO_Custom") }
            "preview_phone_number" { $expected_options1.Add("RASEO_PreviewPhoneNumber") }
            "shared_phone_numbers" { $expected_options1.Add("RASEO_SharedPhoneNumbers") }
            "preview_user_password" { $expected_options1.Add("RASEO_PreviewUserPw") }
            "preview_domain" { $expected_options1.Add("RASEO_PreviewDomain") }
            "show_dialing_progress" { $expected_options1.Add("RASEO_ShowDialingProgress") }
            "require_chap" { $expected_options1.Add("RASEO_RequireCHAP") }
            "require_ms_chap" { $expected_options1.Add("RASEO_RequireMsCHAP") }
            "require_ms_chap2" { $expected_options1.Add("RASEO_RequireMsCHAP2") }
            "require_w95_ms_chap" { $expected_options1.Add("RASEO_RequireW95MSCHAP") }
            "custom_script" { $expected_options1.Add("RASEO_CustomScript") }
            # dwfOptions2
            "secure_file_and_print" { $expected_options2.Add("RASEO2_SecureFileAndPrint") }
            "secure_client_for_ms_net" { $expected_options2.Add("RASEO2_SecureClientForMSNet") }
            "dont_negotiate_multilink" { $expected_options2.Add("RASEO2_DontNegotiateMultilink") }
            "dont_use_ras_credential" { $expected_options2.Add("RASEO2_DontUseRasCredentials") }
            "use_pre_shared_key" { $expected_options2.Add("RASEO2_UsePreSharedKey") }
            "internet" { $expected_options2.Add("RASEO2_Internet") }
            "disable_nbt_over_ip" { $expected_options2.Add("RASEO2_DisableNbtOverIP") }
            "use_global_device_settings" { $expected_options2.Add("RASEO2_UseGlobalDeviceSettings") }
            "reconnect_if_dropped" { $expected_options2.Add("RASEO2_ReconnectIfDropped") }
            "share_phone_numbers" { $expected_options2.Add("RASEO2_SharePhoneNumbers") }
            "secure_routing_compartment" { $expected_options2.Add("RASEO2_SecureRoutingCompartment") }
            "use_typical_settings" { $expected_options2.Add("RASEO2_UseTypicalSettings") }
            "ipv6_specific_name_servers" { $expected_options2.Add("RASEO2_IPv6SpecificNameServers") }
            "ipv6_remote_default_gateway" { $expected_options2.Add("RASEO2_IPv6RemoteDefaultGateway") }
            "register_ip_with_dns" { $expected_options2.Add("RASEO2_RegisterIpWithDNS") }
            "use_dns_suffix_for_registration" { $expected_options2.Add("RASEO2_UseDNSSuffixForRegistration") }
            "ipv4_explicit_metric" { $expected_options2.Add("RASEO2_IPv4ExplicitMetric") }
            "ipv6_explicit_metric" { $expected_options2.Add("RASEO2_IPv6ExplicitMetric") }
            "disable_ike_name_eku_check" { $expected_options2.Add("RASEO2_DisableIKENameEkuCheck") }
            # TODO: Version check for the below, OS Version >= 6.1
            "disable_class_based_static_route" { $expected_options2.Add("RASEO2_DisableClassBasedStaticRoute") }
            "specific_ipv6_addr" { $expected_options2.Add("RASEO2_SpecificIPv6Addr") }
            "disable_mobility" { $expected_options2.Add("RASEO2_DisableMobility") }
            "require_machine_certificates" { $expected_options2.Add("RASEO2_RequireMachineCertificates") }
            # TODO: Version check for the below, OS Version >= 6.2
            "use_pre_shared_key_for_ikev2_initiator" { $expected_options2.Add("RASEO2_UsePreSharedKeyForIkev2Initiator") }
            "use_pre_shared_key_for_ikev2_responder" { $expected_options2.Add("RASEO2_UsePreSharedKeyForIkev2Responder") }
            "cache_credentials" { $expected_options2.Add("RASEO2_CacheCredentials") }
            # TODO: Version check for the below, OS Version >= 6.3
            "auto_trigger_capable" { $expected_options2.Add("RASEO2_AutoTriggerCapable") }
            "is_third_party_profile" { $expected_options2.Add("RASEO2_IsThirdPartyProfile") }
            "auth_type_is_otp" { $expected_options2.Add("RASEO2_AuthTypeIsOtp") }
            # TODO: Version check for the below, OS Version >= 10.0
            "is_always_on" { $expected_options2.Add("RASEO2_IsAlwaysOn") }
            "is_private_network" { $expected_options2.Add("RASEO2_IsPrivateNetwork") }
            default { $invalid_options.Add($option) }
        }
    }
    if ($invalid_options.Count -gt 0) {
        $module.FailJson("Encountered invalid options: $($invalid_options -join ", ")")
    }
    $expected_options1 = [Ansible.WinPhonebookEntry.NativeHelpers+RasEntryOptions]($expected_options1 -join ", ")
    $expected_options2 = [Ansible.WinPhonebookEntry.NativeHelpers+RasEntryOptions2]($expected_options2 -join ", ")

    $property_map = @{
        szDeviceName = $device_name
        szDeviceType = $device_type
        dwFramingProtocol = $expected_framing_protocol
        dwfOptions = $expected_options1
        dwfOptions2 = $expected_options2
        dwType = $expected_type
    }

    if (-not $exists) {
        $entry = New-Object -TypeName Ansible.WinPhonebookEntry.NativeHelpers+RASENTRYW
        foreach ($kvp in $property_map.GetEnumerator()) {
            $entry."$($kvp.Key)" = $kvp.Value
        }

        [Ansible.WinPhonebookEntry.Phonebook]::CreateEntry($name, $entry)
        $module.Result.changed = $true

        # Once created we then get the entry object again to retrieve the unique GUID ID to return
        $entry = [Ansible.WinPhonebookEntry.Phonebook]::GetEntry($name)
        $module.Result.guid = $entry.guidId
    } else {
        $entry = [Ansible.WinPhonebookEntry.Phonebook]::GetEntry($name)
        $changed = $false
        foreach ($kvp in $property_map.GetEnumerator()) {
            $key = $kvp.Key
            $actual_value = $entry.$key
            if ($actual_value -ne $kvp.Value) {
                $entry.$key = $kvp.Value
                $changed = $true
            }
        }

        if ($changed) {
            [Ansible.WinPhonebookEntry.Phonebook]::CreateEntry($name, $entry)
            $module.Result.changed = $true
        }
    }
} else {
    if ($exists) {
        [Ansible.WinPhonebookEntry.Phonebook]::DeleteEntry($name)
        $module.Result.changed = $true
    }
}

$module.ExitJson()
