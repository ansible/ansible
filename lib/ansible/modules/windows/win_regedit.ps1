#!powershell
# This file is part of Ansible

# (c) 2015, Adam Keech <akeech@chathamfinancial.com>, Josh Ludwig <jludwig@chathamfinancial.com>
# (c) 2017, Jordan Borean <jborean93@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false
$_remote_tmp = Get-AnsibleParam $params "_ansible_remote_tmp" -type "path" -default $env:TMP

$path = Get-AnsibleParam -obj $params -name "path" -type "str" -failifempty $true -aliases "key"
$name = Get-AnsibleParam -obj $params -name "name" -type "str" -aliases "entry","value"
$data = Get-AnsibleParam -obj $params -name "data"
$type = Get-AnsibleParam -obj $params -name "type" -type "str" -default "string" -validateset "none","binary","dword","expandstring","multistring","string","qword" -aliases "datatype"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent"
$delete_key = Get-AnsibleParam -obj $params -name "delete_key" -type "bool" -default $true
$hive = Get-AnsibleParam -obj $params -name "hive" -type "path"

$result = @{
    changed = $false
    data_changed = $false
    data_type_changed = $false
}

if ($diff_mode) {
    $result.diff = @{
        prepared = ""
    }
}

$registry_util = @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

namespace Ansible
{
    [StructLayout(LayoutKind.Sequential)]
    public struct LUID
    {
        public UInt32 LowPart;
        public Int32 HighPart;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct TOKEN_PRIVILEGES
    {
        public UInt32 PrivilegeCount;
        public LUID Luid;
        public UInt32 Attributes;
    }

    public enum HKEY : uint
    {
        LOCAL_MACHINE = 0x80000002,
        USERS = 0x80000003
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

    public class RegistryUtil
    {

        public const int TOKEN_ADJUST_PRIVILEGES = 0x00000020;
        public const int TOKEN_QUERY = 0x00000008;
        public const int SE_PRIVILEGE_ENABLED = 0x00000002;

        [DllImport("kernel32.dll", CharSet = CharSet.Auto)]
        private static extern IntPtr GetCurrentProcess();

        [DllImport("kernel32.dll", CharSet = CharSet.Auto)]
        private static extern bool CloseHandle(
            IntPtr hObject);

        [DllImport("advapi32.dll", CharSet = CharSet.Auto)]
        private static extern bool OpenProcessToken(
            IntPtr ProcessHandle,
            UInt32 DesiredAccess,
            out IntPtr TokenHandle);

        [DllImport("advapi32.dll", CharSet = CharSet.Auto)]
        private static extern bool LookupPrivilegeValue(
            string lpSystemName,
            string lpName,
            [MarshalAs(UnmanagedType.Struct)] out LUID lpLuid);

        [DllImport("advapi32.dll", CharSet = CharSet.Auto)]
        private static extern bool AdjustTokenPrivileges(
            IntPtr TokenHandle,
            [MarshalAs(UnmanagedType.Bool)] bool DisableAllPrivileges,
            ref TOKEN_PRIVILEGES NewState,
            UInt32 BufferLength,
            IntPtr PreviousState,
            IntPtr ReturnLength);

        [DllImport("advapi32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        private static extern int RegLoadKey(
            HKEY hKey,
            string lpSubKey,
            string lpFile);

        [DllImport("advapi32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        private static extern int RegUnLoadKey(
            HKEY hKey,
            string lpSubKey);

        public static void EnablePrivileges()
        {
            List<String> privileges = new List<String>()
            {
                "SeRestorePrivilege",
                "SeBackupPrivilege"
            };
            foreach (string privilege in privileges)
            {
                IntPtr hToken;
                LUID luid;
                TOKEN_PRIVILEGES tkpPrivileges;

                if (!OpenProcessToken(GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, out hToken))
                    throw new Win32Exception("OpenProcessToken() failed");

                try
                {
                    if (!LookupPrivilegeValue(null, privilege, out luid))
                        throw new Win32Exception("LookupPrivilegeValue() failed");

                    tkpPrivileges.PrivilegeCount = 1;
                    tkpPrivileges.Luid = luid;
                    tkpPrivileges.Attributes = SE_PRIVILEGE_ENABLED;

                    if (!AdjustTokenPrivileges(hToken, false, ref tkpPrivileges, 0, IntPtr.Zero, IntPtr.Zero))
                        throw new Win32Exception(String.Format("AdjustTokenPrivileges() failed to adjust privilege {0}", privilege));
                }
                finally
                {
                    CloseHandle(hToken);
                }
            }
        }

        public static void LoadHive(string lpSubKey, string lpFile)
        {
            int ret;
            ret = RegLoadKey(HKEY.LOCAL_MACHINE, lpSubKey, lpFile);
            if (ret != 0)
                throw new Win32Exception(ret, String.Format("Failed to load registry hive at {0}", lpFile));
        }

        public static void UnloadHive(string lpSubKey)
        {
            GC.Collect();
            int ret;
            ret = RegUnLoadKey(HKEY.LOCAL_MACHINE, lpSubKey);
            if (ret != 0)
                throw new Win32Exception(ret, String.Format("Failed to unload registry hive at {0}", lpSubKey));
        }
    }
}
'@

# fire a warning if the property name isn't specified, the (Default) key ($null) can only be a string
if ($name -eq $null -and $type -ne "string") {
    Add-Warning -obj $result -message "the data type when name is not specified can only be 'string', the type has automatically been converted"
    $type = "string"
}

# Check that the registry path is in PSDrive format: HKCC, HKCR, HKCU, HKLM, HKU
if ($path -notmatch "^HK(CC|CR|CU|LM|U):\\") {
    Fail-Json $result "path: $path is not a valid powershell path, see module documentation for examples."
}

# Create the required PSDrives if missing
$registry_hive = Split-Path -Path $path -Qualifier
if ($registry_hive -eq "HKCR:" -and (-not (Test-Path HKCR:\))) {
    New-PSDrive -Name HKCR -PSProvider Registry -Root HKEY_CLASSES_ROOT
}
if ($registry_hive -eq "HKU:" -and (-not (Test-Path HKU:\))) {
    New-PSDrive -Name HKU -PSProvider Registry -Root HKEY_USERS
}
if ($registry_hive -eq "HKCC:" -and (-not (Test-Path HKCC:\))) {
    New-PSDrive -Name HKCC -PSProvider Registry -Root HKEY_CURRENT_CONFIG
}

# Simplified version of Convert-HexStringToByteArray from
# https://cyber-defense.sans.org/blog/2010/02/11/powershell-byte-array-hex-convert
# Expects a hex in the format you get when you run reg.exe export,
# and converts to a byte array so powershell can modify binary registry entries
# import format is like 'hex:be,ef,be,ef,be,ef,be,ef,be,ef'
Function Convert-RegExportHexStringToByteArray($string) {
    # Remove 'hex:' from the front of the string if present
    $string = $string.ToLower() -replace '^hex\:',''

    # Remove whitespace and any other non-hex crud.
    $string = $string -replace '[^a-f0-9\\,x\-\:]',''

    # Turn commas into colons
    $string = $string -replace ',',':'

    # Maybe there's nothing left over to convert...
    if ($string.Length -eq 0) {
        return ,@()
    }

    # Split string with or without colon delimiters.
    if ($string.Length -eq 1) {
        return ,@([System.Convert]::ToByte($string,16))
    } elseif (($string.Length % 2 -eq 0) -and ($string.IndexOf(":") -eq -1)) {
        return ,@($string -split '([a-f0-9]{2})' | foreach-object { if ($_) {[System.Convert]::ToByte($_,16)}})
    } elseif ($string.IndexOf(":") -ne -1) {
        return ,@($string -split ':+' | foreach-object {[System.Convert]::ToByte($_,16)})
    } else {
        return ,@()
    }
}

Function Test-RegistryProperty($path, $name) {
    # will validate if the registry key contains the property, returns true
    # if the property exists and false if the property does not
    try {
        $reg_key = Get-Item -Path $path
        $value = $reg_key.GetValue($name)
        # need to do it this way return ($value -eq $null) does not work
        if ($value -eq $null) {
            return $false
        } else {
            return $true
        }
    } catch [System.Management.Automation.ItemNotFoundException] {
        # key didn't exist so the property mustn't
        return $false
    } finally {
        if ($reg_key) {
            $reg_key.Close()
        }
    }
}

Function Compare-RegistryProperties($existing, $new) {
    $mismatch = $false
    if ($existing -is [Array]) {
        if ((Compare-Object -ReferenceObject $existing -DifferenceObject $new -SyncWindow 0).Length -ne 0) {
            $mismatch = $true
        }
    } else {
        if ($existing -cne $new) {
            $mismatch = $true
        }
    }

    return $mismatch
}

Function Get-DiffValueString($type, $value) {
    $enum = [Microsoft.Win32.RegistryValueKind]
    if ($type -in @($enum::Binary, $enum::None)) {
        $hex_values = @()
        foreach ($dec_value in $value) {
            $hex_values += "0x$("{0:x2}" -f $dec_value)"
        }
        $diff_value = "$($type):[$($hex_values -join ", ")]"
    } elseif ($type -eq $enum::DWord) {
        $diff_value = "$($type):0x$("{0:x8}" -f $value)"
    } elseif ($type -eq $enum::QWord) {
        $diff_value = "$($type):0x$("{0:x16}" -f $value)"
    } elseif ($type -eq $enum::MultiString) {
        $diff_value = "$($type):[$($value -join ", ")]"
    } else {
        $diff_value = "$($type):$value"
    }

    return $diff_value
}

# convert property names "" to $null as "" refers to (Default)
if ($name -eq "") {
    $name = $null
}

# convert the data to the required format
if ($type -in @("binary", "none")) {
    if ($data -eq $null) {
        $data = ""
    }

    # convert the data from string to byte array if in hex: format
    if ($data -is [String]) {
        $data = [byte[]](Convert-RegExportHexStringToByteArray -string $data)
    } elseif ($data -is [Int]) {
        if ($data -gt 255) {
            Fail-Json $result "cannot convert binary data '$data' to byte array, please specify this value as a yaml byte array or a comma separated hex value string"
        }
        $data = [byte[]]@([byte]$data)
    } elseif ($data -is [Array]) {
        $data = [byte[]]$data
    }
} elseif ($type -in @("dword", "qword")) {
    # dword's and dword's don't allow null values, set to 0
    if ($data -eq $null) {
        $data = 0
    }

    if ($data -is [String]) {
        # if the data is a string we need to convert it to an unsigned int64
        # it needs to be unsigned as Ansible passes in an unsigned value while
        # powershell uses a signed data type. The value will then be converted
        # below
        $data = [UInt64]$data
    }

    if ($type -eq "dword") {
        if ($data -gt [UInt32]::MaxValue) {
            Fail-Json $result "data cannot be larger than 0xffffffff when type is dword"
        } elseif ($data -gt [Int32]::MaxValue) {
            # when dealing with larger int32 (> 2147483647 or 0x7FFFFFFF) powershell
            # automatically converts it to a signed int64. We need to convert this to
            # signed int32 by parsing the hex string value.
            $data = "0x$("{0:x}" -f $data)"
        }
        $data = [Int32]$data
    } else {
        if ($data -gt [UInt64]::MaxValue) {
            Fail-Json $result "data cannot be larger than 0xffffffffffffffff when type is qword"
        } elseif ($data -gt [Int64]::MaxValue) {
            $data = "0x$("{0:x}" -f $data)"
        }
        $data = [Int64]$data
    }
} elseif ($type -in @("string", "expandstring")) {
    # a null string or expandstring must be empty quotes
    if ($data -eq $null) {
        $data = ""
    }
} elseif ($type -eq "multistring") {
    # convert the data for a multistring to a String[] array
    if ($data -eq $null) {
        $data = [String[]]@()
    } elseif ($data -isnot [Array]) {
        $new_data = New-Object -TypeName String[] -ArgumentList 1
        $new_data[0] = $data.ToString([CultureInfo]::InvariantCulture)
        $data = $new_data
    } else {
        $new_data = New-Object -TypeName String[] -ArgumentList $data.Count
        foreach ($entry in $data) {
            $new_data[$data.IndexOf($entry)] = $entry.ToString([CultureInfo]::InvariantCulture)
        }
        $data = $new_data
    }
}

# convert the type string to the .NET class
$type = [System.Enum]::Parse([Microsoft.Win32.RegistryValueKind], $type, $true)

if ($hive) {
    if (-not (Test-Path $hive)) {
        Fail-Json -obj $result -message "hive at path '$hive' is not valid or accessible, cannot load hive"
    }

    $original_tmp = $env:TMP
    $original_temp = $env:TEMP
    $env:TMP = $_remote_tmp
    $env:TEMP = $_remote_tmp
    Add-Type -TypeDefinition $registry_util
    $env:TMP = $original_tmp
    $env:TEMP = $original_temp
    try {
        [Ansible.RegistryUtil]::EnablePrivileges()
    } catch [System.ComponentModel.Win32Exception] {
        Fail-Json -obj $result -message "failed to enable SeRestorePrivilege and SeRestorePrivilege for the current process: $($_.Exception.Message)"
    }

    if (Test-Path -Path HKLM:\ANSIBLE) {
        Add-Warning -obj $result -message "hive already loaded at HKLM:\ANSIBLE, had to unload hive for win_regedit to continue"
        try {
            [Ansible.RegistryUtil]::UnloadHive("ANSIBLE")
        } catch [System.ComponentModel.Win32Exception] {
            Fail-Json -obj $result -message "failed to unload registry hive HKLM:\ANSIBLE from $($hive): $($_.Exception.Message)"
        }
    }

    try {
        [Ansible.RegistryUtil]::LoadHive("ANSIBLE", $hive)
    } catch [System.ComponentModel.Win32Exception] {
        Fail-Json -obj $result -message "failed to load registry hive from '$hive' to HKLM:\ANSIBLE: $($_.Exception.Message)"
    }
}

try {
    if ($state -eq "present") {
        if (-not (Test-Path -path $path)) {
            # the key doesn't exist, create it so the next steps work
            try {
                $new_key = New-Item -Path $path -Type directory -Force -WhatIf:$check_mode
            } catch {
                Fail-Json $result "failed to create registry key at $($path): $($_.Exception.Message)"
            } finally {
                if ($new_key) {
                    $new_key.Close()
                }
            }
            $result.changed = $true
    
            if ($diff_mode) {
                $result.diff.prepared += @"
+[$path]            
"@
            }
        }
    
        if (Test-RegistryProperty -path $path -name $name) {
            # property exists, need to compare the values and type
            $existing_key = Get-Item -Path $path
            $existing_type = $existing_key.GetValueKind($name)
            $existing_data = $existing_key.GetValue($name, $false, [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
            $existing_key.Close()
            $change_value = $false
            
            if ($type -ne $existing_type) {
                $change_value = $true
                $result.data_type_changed = $true
                $data_mismatch = Compare-RegistryProperties -existing $existing_data -new $data
                if ($data_mismatch) {
                    $result.data_changed = $true
                }
            } else {
                $data_mismatch = Compare-RegistryProperties -existing $existing_data -new $data
                if ($data_mismatch) {
                    $change_value = $true
                    $result.data_changed = $true
                }
            }
    
            if ($change_value) {
                if (-not $check_mode) {
                    $reg_key = Get-Item -Path $path
                    try {
                        $sub_key = $reg_key.OpenSubKey($null, [Microsoft.Win32.RegistryKeyPermissionCheck]::ReadWriteSubTree)
                        try {
                            $sub_key.SetValue($name, $data, $type)
                        } finally {
                            $sub_key.Close()
                        }
                    } catch {
                        Fail-Json $result "failed to change registry property '$name' at $($path): $($_.Exception.Message)"
                    } finally {
                        $reg_key.Close()
                    }
                }
                $result.changed = $true
    
                if ($diff_mode) {
                    if ($result.diff.prepared) {
                        $key_prefix = "+"
                    } else {
                        $key_prefix = ""
                    }
                    
                    $result.diff.prepared = @"
$key_prefix[$path]
-"$name" = "$(Get-DiffValueString -type $existing_type -value $existing_data)"
+"$name" = "$(Get-DiffValueString -type $type -value $data)"
"@
                }
            }
        } else {
            # property doesn't exist just create a new one
            if (-not $check_mode) {
                $reg_key = Get-Item -Path $path
                try {
                    $sub_key = $reg_key.OpenSubKey($null, [Microsoft.Win32.RegistryKeyPermissionCheck]::ReadWriteSubTree)
                    try {
                        $sub_key.SetValue($name, $data, $type)
                    } finally {
                        $sub_key.Close()
                    }
                } catch {
                    Fail-Json $result "failed to change registry property '$name' at $($path): $($_.Exception.Message)"
                } finally {
                    $reg_key.Close()
                }
            }
            $result.changed = $true
            if ($diff_mode) {
                if ($result.diff.prepared) {
                    $key_prefix = "+"
                } else {
                    $key_prefix = ""
                }
                
                $result.diff.prepared = @"
$key_prefix[$path]
+"$name" = "$(Get-DiffValueString -type $type -value $data)"
"@
            }
        }
    } else {
        if (Test-Path -path $path) {
            if ($delete_key -and $name -eq $null) {
                # the clear_key flag is set and name is null so delete the entire key
                try {
                    $null = Remove-Item -Path $path -Force -Recurse -WhatIf:$check_mode
                } catch {
                    Fail-Json $result "failed to delete registry key at $($path): $($_.Exception.Message)"
                }
                $result.changed = $true
    
                if ($diff_mode) {
                    $result.diff.prepared += @"
-[$path]
"@
                }
            } else {
                # the clear_key flag is set or name is not null, check whether we need to delete a property
                if (Test-RegistryProperty -path $path -name $name) {
                    $existing_key = Get-Item -Path $path
                    $existing_type = $existing_key.GetValueKind($name)
                    $existing_data = $existing_key.GetValue($name, $false, [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
                    $existing_key.Close()
    
                    # cannot use Remove-ItemProperty as it fails when deleting the (Default) key ($name = $null)
                    if (-not $check_mode) {
                        $reg_key = Get-Item -Path $path
                        try {
                            $sub_key = $reg_key.OpenSubKey($null, [Microsoft.Win32.RegistryKeyPermissionCheck]::ReadWriteSubTree)
                            try {
                                $sub_key.DeleteValue($name)
                            } finally {
                                $sub_key.Close()
                            }
                        } catch {
                            Fail-Json $result "failed to delete registry property '$name' at $($path): $($_.Exception.Message)"
                        } finally {
                            $reg_key.Close()
                        }
                    }
                    $result.changed = $true
    
                    if ($diff_mode) {
                        $result.diff.prepared += @"
[$path]
-"$name" = "$(Get-DiffValueString -type $existing_type -value $existing_data)"
"@
                    }
                }
            }
        }
    }
} finally {
    if ($hive) {
        [GC]::Collect()
        [GC]::WaitForPendingFinalizers()
        try {
            [Ansible.RegistryUtil]::UnloadHive("ANSIBLE")
        } catch [System.ComponentModel.Win32Exception] {
            Fail-Json -obj $result -message "failed to unload registry hive HKLM:\ANSIBLE from $($hive): $($_.Exception.Message)"
        }
    }
}

Exit-Json $result
