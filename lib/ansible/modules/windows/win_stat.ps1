#!powershell
# This file is part of Ansible

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.FileUtil

# C# code to determine link target, copied from http://chrisbensen.blogspot.com.au/2010/06/getfinalpathnamebyhandle.html
$symlink_util = @"
using System;
using System.Text;
using Microsoft.Win32.SafeHandles;
using System.ComponentModel;
using System.Runtime.InteropServices;

namespace Ansible.Command
{
    public class SymLinkHelper
    {
        private const int FILE_SHARE_WRITE = 2;
        private const int CREATION_DISPOSITION_OPEN_EXISTING = 3;
        private const int FILE_FLAG_BACKUP_SEMANTICS = 0x02000000;

        [DllImport("kernel32.dll", EntryPoint = "GetFinalPathNameByHandleW", CharSet = CharSet.Unicode, SetLastError = true)]
        public static extern int GetFinalPathNameByHandle(IntPtr handle, [In, Out] StringBuilder path, int bufLen, int flags);

        [DllImport("kernel32.dll", EntryPoint = "CreateFileW", CharSet = CharSet.Unicode, SetLastError = true)]
        public static extern SafeFileHandle CreateFile(string lpFileName, int dwDesiredAccess,
        int dwShareMode, IntPtr SecurityAttributes, int dwCreationDisposition, int dwFlagsAndAttributes, IntPtr hTemplateFile);

        public static string GetSymbolicLinkTarget(System.IO.DirectoryInfo symlink)
        {
            SafeFileHandle directoryHandle = CreateFile(symlink.FullName, 0, 2, System.IntPtr.Zero, CREATION_DISPOSITION_OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS, System.IntPtr.Zero);
            if(directoryHandle.IsInvalid)
                throw new Win32Exception(Marshal.GetLastWin32Error());

            StringBuilder path = new StringBuilder(512);
            int size = GetFinalPathNameByHandle(directoryHandle.DangerousGetHandle(), path, path.Capacity, 0);

            if (size<0)
                throw new Win32Exception(Marshal.GetLastWin32Error()); // The remarks section of GetFinalPathNameByHandle mentions the return being prefixed with "\\?\" // More information about "\\?\" here -> http://msdn.microsoft.com/en-us/library/aa365247(v=VS.85).aspx
            if (path[0] == '\\' && path[1] == '\\' && path[2] == '?' && path[3] == '\\')
                return path.ToString().Substring(4);
            else
                return path.ToString();
        }
    }
}
"@
Add-Type -TypeDefinition $symlink_util

function Date_To_Timestamp($start_date, $end_date)
{
    If($start_date -and $end_date)
    {
        return (New-TimeSpan -Start $start_date -End $end_date).TotalSeconds
    }
}

$params = Parse-Args $args -supports_check_mode $true

$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true -aliases "dest","name"
$get_md5 = Get-AnsibleParam -obj $params -name "get_md5" -type "bool" -default $false
$get_checksum = Get-AnsibleParam -obj $params -name "get_checksum" -type "bool" -default $true
$checksum_algorithm = Get-AnsibleParam -obj $params -name "checksum_algorithm" -type "str" -default "sha1" -validateset "md5","sha1","sha256","sha384","sha512"

$result = @{
    changed = $false
    stat = @{
        exists = $false
    }
}

# get_md5 will be an undocumented option in 2.9 to be removed at a later
# date if possible (3.0+)
if (Get-Member -inputobject $params -name "get_md5") {
    Add-DepreactionWarning -obj $result -message "get_md5 has been deprecated along with the md5 return value, use get_checksum=True and checksum_algorithm=md5 instead" -version 2.9
}

$info = Get-FileItem -path $path
If ($info -ne $null)
{
    $result.stat.exists = $true

    # Initial values
    $result.stat.isdir = $false
    $result.stat.islnk = $false
    $result.stat.isreg = $false
    $result.stat.isshared = $false

    $epoch_date = Get-Date -Date "01/01/1970"
    $result.stat.creationtime = (Date_To_Timestamp $epoch_date $info.CreationTime)
    $result.stat.lastaccesstime = (Date_To_Timestamp $epoch_date $info.LastAccessTime)
    $result.stat.lastwritetime = (Date_To_Timestamp $epoch_date $info.LastWriteTime)

    $result.stat.filename = $info.Name
    $result.stat.path = $info.FullName

    $attributes = @()
    foreach ($attribute in ($info.Attributes -split ',')) {
        $attributes += $attribute.Trim()
    }
    $result.stat.attributes = $info.Attributes.ToString()
    $result.stat.isarchive = $attributes -contains "Archive"
    $result.stat.ishidden = $attributes -contains "Hidden"
    $result.stat.isreadonly = $attributes -contains "ReadOnly"

    If ($info)
    {
        $accesscontrol = $info.GetAccessControl()
    }
    Else
    {
        $accesscontrol = $null
    }
    $result.stat.owner = $accesscontrol.Owner

    $iscontainer = $info.PSIsContainer
    If ($attributes -contains 'ReparsePoint')
    {
        # TODO: Find a way to differenciate between soft and junction links
        $result.stat.islnk = $true
        $result.stat.isdir = $true
        # Try and get the symlink source, can result in failure if link is broken
        try {
            $result.stat.lnk_source = [Ansible.Command.SymLinkHelper]::GetSymbolicLinkTarget($path)
        } catch {
            $result.stat.lnk_source = $null
        }
    }
    ElseIf ($iscontainer)
    {
        $result.stat.isdir = $true

        $share_info = Get-WmiObject -Class Win32_Share -Filter "Path='$($info.Fullname -replace '\\', '\\')'"
        If ($share_info -ne $null)
        {
            $result.stat.isshared = $true
            $result.stat.sharename = $share_info.Name
        }

        $dir_files_sum = Get-ChildItem $info.FullName -Recurse | Measure-Object -property length -sum
        If ($dir_files_sum -eq $null)
        {
            $result.stat.size = 0
        }
        Else{
            $result.stat.size = $dir_files_sum.Sum
        }
    }
    Else
    {
        $result.stat.extension = $info.Extension
        $result.stat.isreg = $true
        $result.stat.size = $info.Length

        If ($get_md5) {
            try {
                $result.stat.md5 = Get-FileChecksum -path $path -algorithm "md5"
            } catch {
                Fail-Json -obj $result -message "failed to get MD5 hash of file, remove get_md5 to ignore this error: $($_.Exception.Message)"
            }
        }

        If ($get_checksum) {
            try {
                $result.stat.checksum = Get-FileChecksum -path $path -algorithm $checksum_algorithm
            } catch {
                Fail-Json -obj $result -message "failed to get hash of file, set get_checksum to False to ignore this error: $($_.Exception.Message)"
            }
        }
    }
}

Exit-Json $result
