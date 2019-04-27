#!powershell

# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{
    options = @{
        name = @{ type = "str" }
        remove_multiple = @{ type = "bool"; default = $false }
        state = @{ type = "str"; default = "present"; choices = @("absent", "present") }
        username = @{ type = "sid"; }
    }
    required_if = @(
        @("state", "present", @("username")),
        @("state", "absent", @("name", "username"), $true)
    )
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)
$module.Result.path = $null

$name = $module.Params.name
$remove_multiple = $module.Params.remove_multiple
$state = $module.Params.state
$username = $module.Params.username

Add-CSharpType -AnsibleModule $module -References @'
using System;
using System.Runtime.InteropServices;
using System.Text;

namespace Ansible.WinUserProfile
{
    public class NativeMethods
    {
        [DllImport("Userenv.dll", CharSet = CharSet.Unicode)]
        public static extern int CreateProfile(
            [MarshalAs(UnmanagedType.LPWStr)] string pszUserSid,
            [MarshalAs(UnmanagedType.LPWStr)] string pszUserName,
            [Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder pszProfilePath,
            UInt32 cchProfilePath);

        [DllImport("Userenv.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool DeleteProfileW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpSidString,
            IntPtr lpProfile,
            IntPtr lpComputerName);

        [DllImport("Userenv.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool GetProfilesDirectoryW(
            [Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder lpProfileDir,
            ref UInt32 lpcchSize);
    }
}
'@

Function Get-LastWin32ExceptionMessage {
    param([int]$ErrorCode)
    $exp = New-Object -TypeName System.ComponentModel.Win32Exception -ArgumentList $ErrorCode
    $exp_msg = "{0} (Win32 ErrorCode {1} - 0x{1:X8})" -f $exp.Message, $ErrorCode
    return $exp_msg
}

Function Get-ExpectedProfilePath {
    param([String]$BaseName)

    # Environment.GetFolderPath does not have an enumeration to get the base profile dir, use PInvoke instead
    # and combine with the base name to return back to the user - best efforts
    $profile_path_length = 0
    [Ansible.WinUserProfile.NativeMethods]::GetProfilesDirectoryW($null,
        [ref]$profile_path_length) > $null

    $raw_profile_path = New-Object -TypeName System.Text.StringBuilder -ArgumentList $profile_path_length
    $res = [Ansible.WinUserProfile.NativeMethods]::GetProfilesDirectoryW($raw_profile_path,
        [ref]$profile_path_length)

    if ($res -eq $false) {
        $msg = Get-LastWin32ExceptionMessage -Error ([System.Runtime.InteropServices.Marshal]::GetLastWin32Error())
        $module.FailJson("Failed to determine profile path with the base name '$BaseName': $msg")
    }
    $profile_path = Join-Path -Path $raw_profile_path.ToString() -ChildPath $BaseName

    return $profile_path
}

$profiles = Get-ChildItem -LiteralPath "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList"

if ($state -eq "absent") {
    if ($null -ne $username) {
        $user_profiles = $profiles | Where-Object { $_.PSChildName -eq $username.Value }
    } else {
        # If the username was not provided, or we are removing a profile for a deleted user, we need to try and find
        # the correct SID to delete. We just verify that the path matches based on the name passed in
        $expected_profile_path = Get-ExpectedProfilePath -BaseName $name

        $user_profiles = $profiles | Where-Object {
            $profile_path = (Get-ItemProperty -LiteralPath $_.PSPath -Name ProfileImagePath).ProfileImagePath
            $profile_path -eq $expected_profile_path
        }

        if ($user_profiles.Length -gt 1 -and -not $remove_multiple) {
            $module.FailJson("Found multiple profiles matching the path '$expected_profile_path', set 'remove_multiple=True' to remove all the profiles for this match")
        }
    }

    foreach ($user_profile in $user_profiles) {
        $profile_path = (Get-ItemProperty -LiteralPath $user_profile.PSPath -Name ProfileImagePath).ProfileImagePath
        if (-not $module.CheckMode) {
            $res = [Ansible.WinUserProfile.NativeMethods]::DeleteProfileW($user_profile.PSChildName, [IntPtr]::Zero,
                [IntPtr]::Zero)
            if ($res -eq $false) {
                $msg = Get-LastWin32ExceptionMessage -Error ([System.Runtime.InteropServices.Marshal]::GetLastWin32Error())
                $module.FailJson("Failed to delete the profile for $($user_profile.PSChildName): $msg")
            }
        }

        # While we may have multiple profiles when the name option was used, it will always be the same path due to
        # how we match name to a profile so setting it mutliple time sis fine
        $module.Result.path = $profile_path
        $module.Result.changed = $true
    }
} elseif ($state -eq "present") {
    # Now we know the SID, see if the profile already exists
    $user_profile = $profiles | Where-Object { $_.PSChildName -eq $username.Value }
    if ($null -eq $user_profile) {
        # In case a SID was set as the username we still need to make sure the SID is mapped to a valid local account
        try {
            $account_name = $username.Translate([System.Security.Principal.NTAccount])
        } catch [System.Security.Principal.IdentityNotMappedException] {
            $module.FailJson("Fail to map the account '$($username.Value)' to a valid user")
        }

        # If the basename was not provided, determine it from the actual username
        if ($null -eq $name) {
            $name = $account_name.Value.Split('\', 2)[-1]
        }

        if ($module.CheckMode) {
            $profile_path = Get-ExpectedProfilePath -BaseName $name
        } else {
            $raw_profile_path = New-Object -TypeName System.Text.StringBuilder -ArgumentList 260
            $res = [Ansible.WinUserProfile.NativeMethods]::CreateProfile($username.Value, $name, $raw_profile_path,
                $raw_profile_path.Capacity)

            if ($res -ne 0) {
                $exp = [System.Runtime.InteropServices.Marshal]::GetExceptionForHR($res)
                $module.FailJson("Failed to create profile for user '$username': $($exp.Message)")
            }
            $profile_path = $raw_profile_path.ToString()
        }

        $module.Result.changed = $true
        $module.Result.path = $profile_path
    } else {
        $module.Result.path = (Get-ItemProperty -LiteralPath $user_profile.PSPath -Name ProfileImagePath).ProfileImagePath
    }
}

$module.ExitJson()

