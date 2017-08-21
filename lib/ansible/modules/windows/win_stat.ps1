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
$get_md5 = Get-AnsibleParam -obj $params -name "get_md5" -type "bool" -default $true
$get_checksum = Get-AnsibleParam -obj $params -name "get_checksum" -type "bool" -default $true
$checksum_algorithm = Get-AnsibleParam -obj $params -name "checksum_algorithm" -type "str" -default "sha1" -validateset "md5","sha1","sha256","sha384","sha512"

$result = @{
    changed = $false
    stat = @{
        exists = $false
    }
}

# Backward compatibility
if ($get_md5 -eq $true -and (Get-Member -inputobject $params -name "get_md5") ) {
    Add-DeprecationWarning $result "The parameter 'get_md5' is being replaced with 'checksum_algorithm: md5'"
}

If (Test-Path -Path $path)
{
    $result.stat.exists = $true

    # Initial values
    $result.stat.isdir = $false
    $result.stat.islnk = $false
    $result.stat.isreg = $false
    $result.stat.isshared = $false

    # Need to use -Force so it picks up hidden files
    $info = Get-Item -Force $path

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
                Fail-Json -obj $result -message "failed to get MD5 hash of file, set get_md5 to False to ignore this error: $($_.Exception.Message)"
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
