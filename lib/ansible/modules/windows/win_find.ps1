#!powershell

# Copyright: (c) 2016, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

$params = Parse-Args -arguments $args -supports_check_mode $true
$_remote_tmp = Get-AnsibleParam $params "_ansible_remote_tmp" -type "path" -default $env:TMP

$paths = Get-AnsibleParam -obj $params -name 'paths' -failifempty $true

$age = Get-AnsibleParam -obj $params -name 'age'
$age_stamp = Get-AnsibleParam -obj $params -name 'age_stamp' -default 'mtime' -ValidateSet 'mtime','ctime','atime'
$file_type = Get-AnsibleParam -obj $params -name 'file_type' -default 'file' -ValidateSet 'file','directory'
$follow = Get-AnsibleParam -obj $params -name 'follow' -type "bool" -default $false
$hidden = Get-AnsibleParam -obj $params -name 'hidden' -type "bool" -default $false
$patterns = Get-AnsibleParam -obj $params -name 'patterns' -aliases "regex","regexp"
$recurse = Get-AnsibleParam -obj $params -name 'recurse' -type "bool" -default $false
$size = Get-AnsibleParam -obj $params -name 'size'
$use_regex = Get-AnsibleParam -obj $params -name 'use_regex' -type "bool" -default $false
$get_checksum = Get-AnsibleParam -obj $params -name 'get_checksum' -type "bool" -default $true
$checksum_algorithm = Get-AnsibleParam -obj $params -name 'checksum_algorithm' -default 'sha1' -ValidateSet 'md5', 'sha1', 'sha256', 'sha384', 'sha512'

$result = @{
    files = @()
    examined = 0
    matched = 0
    changed = $false
}

# C# code to determine link target, copied from http://chrisbensen.blogspot.com.au/2010/06/getfinalpathnamebyhandle.html
$symlink_util = @"
using System;
using System.Text;
using Microsoft.Win32.SafeHandles;
using System.ComponentModel;
using System.Runtime.InteropServices;

namespace Ansible.Command {
    public class SymLinkHelper {
        private const int FILE_SHARE_WRITE = 2;
        private const int CREATION_DISPOSITION_OPEN_EXISTING = 3;
        private const int FILE_FLAG_BACKUP_SEMANTICS = 0x02000000;

        [DllImport("kernel32.dll", EntryPoint = "GetFinalPathNameByHandleW", CharSet = CharSet.Unicode, SetLastError = true)]
        public static extern int GetFinalPathNameByHandle(IntPtr handle, [In, Out] StringBuilder path, int bufLen, int flags);

        [DllImport("kernel32.dll", EntryPoint = "CreateFileW", CharSet = CharSet.Unicode, SetLastError = true)]
        public static extern SafeFileHandle CreateFile(string lpFileName, int dwDesiredAccess,
        int dwShareMode, IntPtr SecurityAttributes, int dwCreationDisposition, int dwFlagsAndAttributes, IntPtr hTemplateFile);

        public static string GetSymbolicLinkTarget(System.IO.DirectoryInfo symlink) {
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
$original_tmp = $env:TMP
$env:TMP = $_remote_tmp
Add-Type -TypeDefinition $symlink_util
$env:TMP = $original_tmp

Function Assert-Age($info) {
    $valid_match = $true

    if ($null -ne $age) {
        $seconds_per_unit = @{'s'=1; 'm'=60; 'h'=3600; 'd'=86400; 'w'=604800}
        $seconds_pattern = '^(-?\d+)(s|m|h|d|w)?$'
        $match = $age -match $seconds_pattern
        if ($match) {
            [int]$specified_seconds = $matches[1]
            if ($null -eq $matches[2]) {
                $chosen_unit = 's'
            } else {
                $chosen_unit = $matches[2]
            }

            $abs_seconds = $specified_seconds * ($seconds_per_unit.$chosen_unit)
            $epoch = New-Object -Type DateTime -ArgumentList 1970, 1, 1, 0, 0, 0, 0
            if ($age_stamp -eq 'mtime') {
                $age_comparison = $epoch.AddSeconds($info.lastwritetime)
            } elseif ($age_stamp -eq 'ctime') {
                $age_comparison = $epoch.AddSeconds($info.creationtime)
            } elseif ($age_stamp -eq 'atime') {
                $age_comparison = $epoch.AddSeconds($info.lastaccesstime)
            }

            if ($specified_seconds -ge 0) {
                $start_date = (Get-Date).AddSeconds($abs_seconds * -1)
                if ($age_comparison -gt $start_date) {
                    $valid_match = $false
                }
            } else {
                $start_date = (Get-Date).AddSeconds($abs_seconds)
                if ($age_comparison -lt $start_date) {
                    $valid_match = $false
                }
            }
        } else {
            throw "failed to process age for file $($info.FullName)"
        }
    }

    $valid_match
}

Function Assert-FileType($info) {
    $valid_match = $true

    if ($file_type -eq 'directory' -and $info.isdir -eq $false) {
        $valid_match = $false
    }
    if ($file_type -eq 'file' -and $info.isdir -eq $true) {
        $valid_match = $false
    }

    $valid_match
}

Function Assert-Hidden($info) {
    $valid_match = $true

    if ($hidden -eq $true -and $info.ishidden -eq $false) {
        $valid_match = $false
    }
    if ($hidden -eq $false -and $info.ishidden -eq $true) {
        $valid_match = $false
    }

    $valid_match
}

Function Assert-Pattern($info) {
    $valid_match = $false

    if ($null -ne $patterns) {
        foreach ($pattern in $patterns) {
            if ($use_regex -eq $true) {
                # Use -match for regex matching
                if ($info.filename -match $pattern) {
                    $valid_match = $true
                }
            } else {
                # Use -like for wildcard matching
                if ($info.filename -like $pattern) {
                    $valid_match = $true
                }
            }
        }
    } else {
        $valid_match = $true
    }

    $valid_match
}

Function Assert-Size($info) {
    $valid_match = $true

    if ($null -ne $size) {
        $bytes_per_unit = @{'b'=1; 'k'=1024; 'm'=1024*1024; 'g'=1024*1024*1024; 't'=1024*1024*1024*1024}
        $size_pattern = '^(-?\d+)(b|k|m|g|t)?$'
        $match = $size -match $size_pattern
        if ($match) {
            [int64]$specified_size = $matches[1]
            if ($null -eq $matches[2]) {
                $chosen_byte = 'b'
            } else {
                $chosen_byte = $matches[2]
            }

            $abs_size = $specified_size * ($bytes_per_unit.$chosen_byte)
            if ($specified_size -ge 0) {
                if ($info.size -lt $abs_size) {
                    $valid_match = $false
                }
            } else {
                if ($info.size -gt $abs_size * -1) {
                    $valid_match = $false
                }
            }
        } else {
            throw "failed to process size for file $($info.FullName)"
        }
    }

    $valid_match
}

Function Assert-FileStat($info) {
    $age_match = Assert-Age -info $info
    $file_type_match = Assert-FileType -info $info
    $hidden_match = Assert-Hidden -info $info
    $pattern_match = Assert-Pattern -info $info
    $size_match = Assert-Size -info $info

    if ($age_match -and $file_type_match -and $hidden_match -and $pattern_match -and $size_match) {
        $info
    } else {
        $false
    }
}

Function Get-FileStat($file) {
    $epoch = New-Object -Type DateTime -ArgumentList 1970, 1, 1, 0, 0, 0, 0
    $access_control = $file.GetAccessControl()
    $attributes = @()
    foreach ($attribute in ($file.Attributes -split ',')) {
        $attributes += $attribute.Trim()
    }

    $file_stat = @{
        isreadonly = $attributes -contains 'ReadOnly'
        ishidden = $attributes -contains 'Hidden'
        isarchive = $attributes -contains 'Archive'
        attributes = $file.Attributes.ToString()
        owner = $access_control.Owner
        lastwritetime = (New-TimeSpan -Start $epoch -End $file.LastWriteTime).TotalSeconds
        creationtime = (New-TimeSpan -Start $epoch -End $file.CreationTime).TotalSeconds
        lastaccesstime = (New-TimeSpan -Start $epoch -End $file.LastAccessTime).TotalSeconds
        path = $file.FullName
        filename = $file.Name
    }

    $islnk = $false
    $isdir = $false
    $isshared = $false

    if ($attributes -contains 'ReparsePoint') {
        # TODO: Find a way to differenciate between soft and junction links
        $islnk = $true
        $isdir = $true

        # Try and get the symlink source, can result in failure if link is broken
        try {
            $lnk_source = [Ansible.Command.SymLinkHelper]::GetSymbolicLinkTarget($file)
            $file_stat.lnk_source = $lnk_source
        } catch {}
    } elseif ($file.PSIsContainer) {
        $isdir = $true

        $share_info = Get-CIMInstance -Class Win32_Share -Filter "Path='$($file.Fullname -replace '\\', '\\')'"
        if ($null -ne $share_info) {
            $isshared = $true
            $file_stat.sharename = $share_info.Name
        }

        # only get the size of a directory if there are files (not directories) inside the folder
        # Get-ChildItem -LiteralPath does not work properly on older OS', use .NET instead
        $dir_files = @()
        try {
            $dir_files = $file.EnumerateFiles("*", [System.IO.SearchOption]::AllDirectories)
        } catch [System.IO.DirectoryNotFoundException] { # Broken ReparsePoint/Symlink, cannot enumerate
      	} catch [System.UnauthorizedAccessException] {}  # No ListDirectory permissions, Get-ChildItem ignored this
        $size = 0
        foreach ($dir_file in $dir_files) {
            $size += $dir_file.Length
        }
        $file_stat.size = $size
    } else {
        $file_stat.size = $file.length
        $file_stat.extension = $file.Extension

        if ($get_checksum) {
            try {
                $checksum = Get-FileChecksum -path $path -algorithm $checksum_algorithm
                $file_stat.checksum = $checksum
            } catch {
                throw "failed to get checksum for file $($file.FullName)"
            }
        }
    }

    $file_stat.islnk = $islnk
    $file_stat.isdir = $isdir
    $file_stat.isshared = $isshared

    Assert-FileStat -info $file_stat
}

Function Get-FilesInFolder($path) {
    $items = @()

    # Get-ChildItem -LiteralPath can bomb out on older OS', use .NET instead
    $dir = New-Object -TypeName System.IO.DirectoryInfo -ArgumentList $path
    $dir_files = @()
    try {
        $dir_files = $dir.EnumerateFileSystemInfos("*", [System.IO.SearchOption]::TopDirectoryOnly)
    } catch [System.IO.DirectoryNotFoundException] { # Broken ReparsePoint/Symlink, cannot enumerate
    } catch [System.UnauthorizedAccessException] {}  # No ListDirectory permissions, Get-ChildItem ignored this
    foreach ($item in $dir_files) {
        if ($item -is [System.IO.DirectoryInfo] -and $recurse) {
            if (($item.Attributes -like '*ReparsePoint*' -and $follow) -or ($item.Attributes -notlike '*ReparsePoint*')) {
                # File is a link and we want to follow a link OR file is not a link
                $items += $item.FullName
                $items += Get-FilesInFolder -path $item.FullName
            } else {
                # File is a link but we don't want to follow a link
                $items += $item.FullName
            }
        } else {
            $items += $item.FullName
        }
    }

    $items
}

$paths_to_check = @()
foreach ($path in $paths) {
    if (Test-Path -LiteralPath $path) {
        if ((Get-Item -LiteralPath $path -Force).PSIsContainer) {
            $paths_to_check += Get-FilesInFolder -path $path
        } else {
            Fail-Json $result "Argument path $path is a file not a directory"
        }
    } else {
        Fail-Json $result "Argument path $path does not exist cannot get information on"
    }
}
$paths_to_check = $paths_to_check | Select-Object -Unique | Sort-Object

foreach ($path in $paths_to_check) {
    try {
        $file = Get-Item -LiteralPath $path -Force
        $info = Get-FileStat -file $file
    } catch {
        Add-Warning -obj $result -message "win_find failed to check some files, these files were ignored and will not be part of the result output"
        break
    }

    $new_examined = $result.examined + 1
    $result.examined = $new_examined

    if ($info -ne $false) {
        $files = $result.Files
        $files += $info

        $new_matched = $result.matched + 1
        $result.matched = $new_matched
        $result.files = $files
    }
}

Exit-Json $result
