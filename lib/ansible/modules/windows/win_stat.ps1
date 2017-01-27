#!powershell
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# WANT_JSON
# POWERSHELL_COMMON

$params = Parse-Args -arguments $args -supports_check_mode $true;

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
        Write-Output (New-TimeSpan -Start $start_date -End $end_date).TotalSeconds
    }
}

function Get-Hash($path, $algorithm) {
    # Using PowerShell V4 and above we can use some powershell cmdlets instead of .net
    If ($PSVersionTable.PSVersion.Major -ge 4)
    {
        $hash = (Get-FileHash $path -Algorithm $algorithm).Hash
    }
    Else
    {
        $net_algorithm = [Security.Cryptography.HashAlgorithm]::Create($algorithm)
        $raw_hash = [System.BitConverter]::ToString($net_algorithm.ComputeHash([System.IO.File]::ReadAllBytes($path)))
        $hash = $raw_hash -replace '-'
    }

    $hash.ToLower()
}

$path = Get-AnsibleParam -obj $params -name 'path' -failifempty $true;
$get_md5 = Get-AnsibleParam -obj $params -name 'get_md5' -failifempty $false -default $true | ConvertTo-Bool;
$get_checksum = Get-AnsibleParam -obj $params -name 'get_checksum' -failifempty $false -default $true | ConvertTo-Bool;
$checksum_algorithm = Get-AnsibleParam -obj $params -name 'checksum_algorithm' -failifempty $false -default 'sha1' -ValidateSet 'sha1','sha256','sha384','sha512'

$result = New-Object psobject @{
    stat = New-Object psobject
    changed = $false
};

If (Test-Path $path)
{
    Set-Attr $result.stat "exists" $TRUE;

    # Need to use -Force so it picks up hidden files
    $info = Get-Item -Force $path;
    $iscontainer = $info.PSIsContainer;
    $filename = $info.Name;
    $filepath = $info.FullName;
    $attributes = @()
    foreach ($attribute in ($info.Attributes -split ',')) {
        $attributes += $attribute.Trim();
    }
    $attributes_string = $info.Attributes.ToString();
    $isreadonly = $attributes -contains 'ReadOnly';
    $ishidden = $attributes -contains 'Hidden';
    $isarchive = $attributes -contains 'Archive';

    If ($info)
    {
        $accesscontrol = $info.GetAccessControl();
    }
    Else
    {
        $accesscontrol = $null;
    }
    $owner = $accessControl.Owner;
    $creationtime = $info.CreationTime;
    $lastaccesstime = $info.LastAccessTime;
    $lastwritetime = $info.LastAccessTime;

    $epoch_date = Get-Date -Date "01/01/1970"
    $islink = $false
    $isdir = $false
    $isshared = $false

    If ($attributes -contains 'ReparsePoint')
    {
        # TODO: Find a way to differenciate between soft and junction links
        $islink = $true
        $isdir = $true
        # Try and get the symlink source, can result in failure if link is broken
        try {
            $lnk_source = [Ansible.Command.SymLinkHelper]::GetSymbolicLinkTarget($path)
            Set-Attr $result.stat "lnk_source" $lnk_source
        } catch {}
    } 
    ElseIf ($iscontainer)
    {
        $isdir = $true

        $share_info = Get-WmiObject -Class Win32_Share -Filter "Path='$($info.Fullname -replace '\\', '\\')'";
        If ($share_info -ne $null) 
        {
            $isshared = $true
            Set-Attr $result.stat "sharename" $share_info.Name;
        }

        $dir_files_sum = Get-ChildItem $info.FullName -Recurse | Measure-Object -property length -sum;
        If ($dir_files_sum -eq $null)
        {
            Set-Attr $result.stat "size" 0;
        }
        Else{
            Set-Attr $result.stat "size" $dir_files_sum.Sum;
        }
    }
    Else
    {
        Set-Attr $result.stat "size" $info.Length;
        Set-Attr $result.stat "extension" $info.extension;

        If ($get_md5) {
            $md5 = Get-Hash -path $path -algorithm 'md5'
            Set-Attr $result.stat "md5" $md5
        }

        If ($get_checksum) {
            $checksum = Get-Hash -path $path -algorithm $checksum_algorithm
            Set-Attr $result.stat "checksum" $checksum
        }
    }

    Set-Attr $result.stat "islink" $islink;
    Set-Attr $result.stat "isdir" $isdir;
    Set-Attr $result.stat "isshared" $isshared;
    Set-Attr $result.stat "isreadonly" $isreadonly;
    Set-Attr $result.stat "ishidden" $ishidden;
    Set-Attr $result.stat "isarchive" $isarchive;
    Set-Attr $result.stat "filename" $filename;
    Set-Attr $result.stat "path" $filepath;
    Set-Attr $result.stat "attributes" $attributes_string;
    Set-Attr $result.stat "owner" $owner;
    Set-Attr $result.stat "creationtime" (Date_To_Timestamp $epoch_date $creationtime);
    Set-Attr $result.stat "lastaccesstime" (Date_To_Timestamp $epoch_date $lastaccesstime);
    Set-Attr $result.stat "lastwritetime" (Date_To_Timestamp $epoch_date $lastwritetime);
}
Else
{
    Set-Attr $result.stat "exists" $FALSE;
}

Exit-Json $result;
