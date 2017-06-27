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

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -default $false

$force = Get-AnsibleParam -obj $params -name "force" -type "bool" -default $false
$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true -aliases "dest","name"
$src = Get-AnsibleParam -obj $params -name "src" -type "path"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -validateset "absent","directory","file","touch","link","hard","junction"

if ($state -eq $null) {
    # state wasn't supplied try and determine based on the path
    $basename = Split-Path -Path $path -Leaf
    if ($basename.length -gt 0) {
        $state = "file"
    } else {
        $state = "directory"
    }
}

$result = @{
    changed = $false
}

# Used to interact with Links and windows
# Powershell does have native link handling through New-Item but was
# only added with V5 and Server 2016/Windows 10 onwards
$symlink_util = @"
using Microsoft.Win32.SafeHandles;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;

namespace Ansible
{
    public class SymLink
    {
        /*
         * Parts of this code has been derived from various sources
         * 
         * Jeff Brown - Creating Junction Points https://www.codeproject.com/Articles/15633/Manipulating-NTFS-Junction-Points-in-NET
         * Dave Midgley - Reparse Points in Vista https://www.codeproject.com/kb/vista/reparsepointid.aspx
         * 
         * Thanks to the above for help with structuring the processes
         * that is required
         * 
         */

        // Types of Links
        private const string SYMBOLIC_LINK = "link";
        private const string HARD_LINK = "hard";
        private const string JUNCTION_POINT = "junction";
        private const string MOUNT_POINT = "mount_point";

        // Constants used when setting SeBackupPrivilege
        private const uint TOKEN_ADJUST_PRIVILEGES = 0x00000020;
        private const uint SE_PRIVILEGE_ENABLED = 0x00000002;
        private const string SE_BACKUP_NAME = "SeBackupPrivilege";

        // Reparse Tags https://msdn.microsoft.com/en-US/library/windows/desktop/aa365511(v=vs.85).aspx - Values derived from WinNT.h
        private const uint IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003;
        private const uint IO_REPARSE_TAG_SYMLINK = 0xA000000C;

        // Flag set when the Soft Link path is a relative path
        private const uint SYMLINK_FLAG_RELATIVE = 0x00000001;

        // CTL_CODE Values
        private const int FSCTL_GET_REPARSE_POINT = 0x000900A8;
        private const int FSCTL_SET_REPARSE_POINT = 0x000900A4;
        private const uint FILE_DEVICE_FILE_SYSTEM = 0x00090000;
        private const uint FILE_FLAG_BACKUP_SEMANTICS = 0x02000000;
        private const uint FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000;
        private const uint FILE_ATTRIBUTE_ARCHIVE = 0x20000000;

        // Used when getting the Reparse Data
        private const int MAXIMUM_REPARSE_DATA_BUFFER_SIZE = 1024 * 16;

        // Size of the REPARSE_DATA_BUFFER headers (ReparseTag (4) + ReparseDataLength (2) + Reserved (2))
        private const int REPARSE_DATA_BUFFER_HEADER_SIZE = 8;

        // This prefix indicates to NTFS that the path is to be treated as a non-interpreted
        // path in the virtual file system.
        // https://stackoverflow.com/questions/14329653/does-the-substitutename-string-in-the-pathbuffer-of-a-reparse-data-buffer-stru
        private const string REPARSE_POINT_PATH_PREFIX = @"\??\";

        // https://msdn.microsoft.com/en-us/library/gg269344(v=exchg.10).aspx WCHAR is a 16-bit Unicode char, i.e. size of 2 bytes
        private const uint SIZE_OF_WCHAR = 2;

        // dwFlags in CreateSymbolicLink
        private const uint SYMBOLIC_LINK_FLAG_FILE = 0x00000000;
        private const uint SYMBOLIC_LINK_FLAG_DIRECTORY = 0x00000001;

        private string[] targets;
        private string type;

        // https://msdn.microsoft.com/en-us/library/windows/desktop/aa379630(v=vs.85).aspx
        private struct TOKEN_PRIVILEGES
        {
            public UInt32 PrivilegeCount;
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 1)]
            public LUID_AND_ATTRIBUTES[] Privileges;
        }

        // https://msdn.microsoft.com/en-us/library/windows/desktop/aa379263(v=vs.85).aspx
        [StructLayout(LayoutKind.Sequential)]
        private struct LUID_AND_ATTRIBUTES
        {
            public LUID Luid;
            public UInt32 Attributes;
        }

        // https://msdn.microsoft.com/en-us/library/windows/desktop/aa379261(v=vs.85).aspx
        [StructLayout(LayoutKind.Sequential)]
        private struct LUID
        {
            public UInt32 LowPart;
            public Int32 HighPart;
        }

        // https://msdn.microsoft.com/en-us/library/ff552012.aspx
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        private struct REPARSE_DATA_BUFFER
        {
            public uint ReparseTag;
            public short ReparseDataLength;
            public short Reserved;
            public short SubstituteNameOffset;
            public short SubstituteNameLength;
            public short PrintNameOffset;
            public short PrintNameLength;
            //public uint Flags; Don't set this as a Juntion/Mount Point don't return a value for this and breaks the PathBuffer
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = MAXIMUM_REPARSE_DATA_BUFFER_SIZE)]
            public char[] PathBuffer;
        }

        // https://msdn.microsoft.com/en-us/library/windows/desktop/aa363788(v=vs.85).aspx
        [StructLayout(LayoutKind.Sequential)]
        private struct BY_HANDLE_FILE_INFORMATION
        {
            public uint FileAttributes;
            public System.Runtime.InteropServices.ComTypes.FILETIME CreationTime;
            public System.Runtime.InteropServices.ComTypes.FILETIME LastAccessTime;
            public System.Runtime.InteropServices.ComTypes.FILETIME LastWriteTime;
            public uint VolumeSerialNumber;
            public uint FileSizeHigh;
            public uint FileSizeLow;
            public uint NumberOfLinks;
            public uint FileIndexHigh;
            public uint FileIndexLow;
        }

        // https://msdn.microsoft.com/en-us/library/windows/desktop/aa379295(v=vs.85).aspx
        [DllImport("advapi32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        static extern bool OpenProcessToken(
            IntPtr ProcessHandle,
            UInt32 DesiredAccess,
            out IntPtr TokenHandle);

        // https://msdn.microsoft.com/en-us/library/windows/desktop/aa379180(v=vs.85).aspx
        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        [return: MarshalAs(UnmanagedType.Bool)]
        static extern bool LookupPrivilegeValue(
            string lpSystemName,
            string lpName,
            out LUID lpLuid);

        // https://msdn.microsoft.com/en-us/library/windows/desktop/aa375202(v=vs.85).aspx
        [DllImport("advapi32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        static extern bool AdjustTokenPrivileges(
            IntPtr TokenHandle,
            [MarshalAs(UnmanagedType.Bool)]bool DisableAllPrivileges,
            ref TOKEN_PRIVILEGES NewState,
            Int32 BufferLength,
            IntPtr PreviousState,
            IntPtr ReturnLength);

        // https://msdn.microsoft.com/en-us/library/windows/desktop/ms724211(v=vs.85).aspx
        [DllImport("kernel32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        static extern bool CloseHandle(IntPtr hObject);

        // https://msdn.microsoft.com/en-us/library/windows/desktop/aa363216(v=vs.85).aspx
        [DllImport("kernel32.dll", ExactSpelling = true, SetLastError = true, CharSet = CharSet.Auto)]
        [return: MarshalAs(UnmanagedType.Bool)]
        static extern bool DeviceIoControl(
            SafeFileHandle hDevice,
            uint dwIoControlCode,
            IntPtr lpInBuffer,
            uint nInBufferSize,
            out REPARSE_DATA_BUFFER lpOutBuffer,
            uint nOutBufferSize,
            out uint lpBytesReturned,
            IntPtr lpOverlapped);

        // https://msdn.microsoft.com/en-us/library/windows/desktop/aa363858(v=vs.85).aspx
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        static extern SafeFileHandle CreateFile(
            string lpFileName,
            [MarshalAs(UnmanagedType.U4)] FileAccess dwDesiredAccess,
            [MarshalAs(UnmanagedType.U4)] FileShare dwShareMode,
            IntPtr lpSecurityAttributes,
            [MarshalAs(UnmanagedType.U4)] FileMode dwCreationDisposition,
            uint dwFlagsAndAttributes,
            IntPtr hTemplateFile);

        // https://msdn.microsoft.com/en-us/library/windows/desktop/aa363866(v=vs.85).aspx
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        static extern bool CreateSymbolicLink(
            string lpSymlinkFileName,
            string lpTargetFileName,
            uint dwFlags);

        // https://msdn.microsoft.com/en-us/library/windows/desktop/aa363860(v=vs.85).aspx
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        static extern bool CreateHardLink(
            string lpFileName,
            string lpExistingFileName,
            IntPtr lpSecurityAttributes);

        // https://msdn.microsoft.com/en-us/library/windows/desktop/aa364952(v=vs.85).aspx
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool GetFileInformationByHandle(
            SafeFileHandle hFile,
            out BY_HANDLE_FILE_INFORMATION lpFileInformation);

        // https://msdn.microsoft.com/en-us/library/windows/desktop/aa364421(v=vs.85).aspx
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        static extern IntPtr FindFirstFileNameW(
            string lpFileName,
            uint dwFlags,
            ref uint stringLength,
            StringBuilder linkName);

        // https://msdn.microsoft.com/en-us/library/windows/desktop/aa364429(v=vs.85).aspx
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        static extern bool FindNextFileNameW(
            IntPtr hFindStream,
            ref uint stringLength,
            StringBuilder linkName);

        // https://msdn.microsoft.com/en-us/library/windows/desktop/aa364413(v=vs.85).aspx
        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool FindClose(IntPtr hFindFile);

        // https://msdn.microsoft.com/en-us/library/windows/desktop/aa364996(v=vs.85).aspx
        [DllImport("kernel32.dll")]
        static extern bool GetVolumePathName(
            string lpszFileName,
            [Out] StringBuilder lpszVolumePathName,
            uint cchBufferLength);

        // https://msdn.microsoft.com/en-us/library/windows/desktop/hh707081(v=vs.85).aspx
        [DllImport("shlwapi.dll", CharSet = CharSet.Auto)]
        static extern bool PathAppend(
            [In, Out] StringBuilder pszPath,
            string pszMore);

        // https://msdn.microsoft.com/en-us/library/windows/desktop/aa365488(v=vs.85).aspx
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        public static extern bool RemoveDirectory(string lpPathName);

        // https://msdn.microsoft.com/en-us/library/windows/desktop/aa363915(v=vs.85).aspx
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        public static extern bool DeleteFile(string lpFileName);

        public SymLink(string path)
        {
            FileAttributes attr = File.GetAttributes(path);
            if (attr.HasFlag(FileAttributes.ReparsePoint))
            {
                // We are dealing with a Symbolic Link, Junction Point or Mount Point
                SetReparsePointInfo(path);
            }
            else
            {
                if (attr.HasFlag(FileAttributes.Directory))
                {
                    // It is a Directory but not a link
                    targets = new string[0];
                    type = "";
                }
                else
                {
                    // File is potentially a Hard Link, check and set info
                    SetHardLinkInfo(path);
                }
            }
        }

        public string[] Targets
        {
            get
            {
                return targets;
            }
        }

        public string Type
        {
            get
            {
                return type;
            }
        }

        // Will add the SeBackupPrivilege Token to the current Process (only call once)
        public static void EnableSeBackupPrivilege()
        {
            IntPtr token;
            TOKEN_PRIVILEGES tokenPrivileges = new TOKEN_PRIVILEGES();
            tokenPrivileges.Privileges = new LUID_AND_ATTRIBUTES[1];
            if (!OpenProcessToken(Process.GetCurrentProcess().Handle, TOKEN_ADJUST_PRIVILEGES, out token))
                throw new Win32Exception(Marshal.GetLastWin32Error());

            if (!LookupPrivilegeValue(null, SE_BACKUP_NAME, out tokenPrivileges.Privileges[0].Luid))
                throw new Win32Exception(Marshal.GetLastWin32Error());

            tokenPrivileges.PrivilegeCount = 1;
            tokenPrivileges.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED;
            if (!AdjustTokenPrivileges(token, false, ref tokenPrivileges, Marshal.SizeOf(tokenPrivileges), IntPtr.Zero, IntPtr.Zero))
                throw new Exception(String.Format("Failed to get token {0} for current process: {1}", SE_BACKUP_NAME, new Win32Exception(Marshal.GetLastWin32Error()).Message));

            CloseHandle(token);
        }

        // Will delete a symbolic link or junction point even when the target is missing
        public static void DeleteSymLink(string path)
        {
            bool success;
            FileAttributes attr = File.GetAttributes(path);
            if (attr.HasFlag(FileAttributes.Directory))
            {
                success = RemoveDirectory(path);
            }
            else
            {
                success = DeleteFile(path);
            }
            if (!success)
                throw new Exception(String.Format("Error deleting symlink: {0}", new Win32Exception(Marshal.GetLastWin32Error()).Message));
        }

        public static void CreateLink(string linkPath, String target, String type)
        {
            switch (type)
            {
                case SYMBOLIC_LINK:
                    CreateLinkSymbolic(linkPath, target);
                    break;
                case JUNCTION_POINT:
                    CreateJunctionPoint(linkPath, target);
                    break;
                case HARD_LINK:
                    CreateLinkHard(linkPath, target);
                    break;
                default:
                    throw new Exception(String.Format("Unknown Link option {0}", type));
            }
        }

        private static void CreateLinkSymbolic(string linkPath, String target)
        {
            uint linkFlags;
            FileAttributes attr = File.GetAttributes(target);
            if (attr.HasFlag(FileAttributes.Directory))
            {
                linkFlags = SYMBOLIC_LINK_FLAG_DIRECTORY;
            }
            else
            {
                linkFlags = SYMBOLIC_LINK_FLAG_FILE;
            }

            if (!CreateSymbolicLink(linkPath, target, linkFlags))
                throw new Exception(String.Format("Failed to create Symbolic Link {0} to Target {1}: {2}", linkPath, target, new Win32Exception(Marshal.GetLastWin32Error()).Message));
        }

        private static void CreateLinkHard(string linkPath, String target)
        {
            if (!CreateHardLink(linkPath, target, IntPtr.Zero))
                throw new Exception(String.Format("Failed to create Hard Link {0} to Target {1}: {2}", linkPath, target, new Win32Exception(Marshal.GetLastWin32Error()).Message));
        }

        private static void CreateJunctionPoint(string linkPath, string target)
        {
            Directory.CreateDirectory(linkPath);
            SafeFileHandle handle = CreateFile(linkPath, FileAccess.Write, FileShare.Read | FileShare.Write | FileShare.None, IntPtr.Zero, FileMode.Open, FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT, IntPtr.Zero);
            if (handle.IsInvalid)
                throw new Exception(String.Format("Unable to open Reparse Point at {0}: {1}", linkPath, new Win32Exception(Marshal.GetLastWin32Error()).Message));


            string substituteName = REPARSE_POINT_PATH_PREFIX + Path.GetFullPath(target);
            string printName = target;

            short substituteNameOffset = 0;
            short substituteNameLength = (short)(substituteName.Length * SIZE_OF_WCHAR);

            short printNameOffset = (short)(substituteNameLength + 2);
            short printNameLength = (short)(printName.Length * SIZE_OF_WCHAR);

            short reparseDataLength = (short)(substituteNameLength + printNameLength + 12);

            byte[] unicodeBytes = Encoding.Unicode.GetBytes(substituteName + "\0" + printName);
            char[] pathBuffer = Encoding.Unicode.GetChars(unicodeBytes);

            REPARSE_DATA_BUFFER reparseDataBuffer = new REPARSE_DATA_BUFFER();
            reparseDataBuffer.ReparseTag = IO_REPARSE_TAG_MOUNT_POINT;
            reparseDataBuffer.ReparseDataLength = reparseDataLength;
            reparseDataBuffer.SubstituteNameOffset = substituteNameOffset;
            reparseDataBuffer.SubstituteNameLength = substituteNameLength;
            reparseDataBuffer.PrintNameOffset = printNameOffset;
            reparseDataBuffer.PrintNameLength = printNameLength;
            reparseDataBuffer.PathBuffer = new char[MAXIMUM_REPARSE_DATA_BUFFER_SIZE];

            Array.Copy(pathBuffer, reparseDataBuffer.PathBuffer, pathBuffer.Length);
            int inBufferSize = Marshal.SizeOf(reparseDataBuffer);
            IntPtr inBuffer = Marshal.AllocHGlobal(inBufferSize);

            try
            {
                Marshal.StructureToPtr(reparseDataBuffer, inBuffer, false);
                uint bytesReturned;
                uint bufferSize = (uint)(reparseDataBuffer.ReparseDataLength + REPARSE_DATA_BUFFER_HEADER_SIZE);
                REPARSE_DATA_BUFFER outBuffer = new REPARSE_DATA_BUFFER();
                bool success = DeviceIoControl(handle, FSCTL_SET_REPARSE_POINT, inBuffer, bufferSize, out outBuffer, 0, out bytesReturned, IntPtr.Zero);
                if (!success)
                    throw new Exception(String.Format("Failed to create Juntion Link {0} to Target {1}: {2}", linkPath, target, new Win32Exception(Marshal.GetLastWin32Error()).Message));
            }
            finally
            {
                Marshal.FreeHGlobal(inBuffer);
            }
            handle.Dispose();
        }

        private void SetHardLinkInfo(string path)
        {
            string[] links = GetHardLinks(path);
            if (links.Length > 1)
            {
                type = HARD_LINK;
                targets = links;
            }
            else
            {
                type = "";
                targets = new string[0];
            }
        }

        // Get's a list of Hard Links for a file
        private static string[] GetHardLinks(string path)
        {
            List<string> result = new List<string>();
            uint stringLength = 256;
            StringBuilder sb = new StringBuilder((int)stringLength);
            GetVolumePathName(path, sb, stringLength);
            string volume = sb.ToString();
            sb.Length = 0;
            stringLength = 256;
            IntPtr findHandle = FindFirstFileNameW(path, 0, ref stringLength, sb);
            if (findHandle.ToInt64() != -1)
            {
                do
                {
                    StringBuilder pathSb = new StringBuilder(volume, (int)stringLength);
                    PathAppend(pathSb, sb.ToString());
                    result.Add(pathSb.ToString());
                    sb.Length = 0;
                    stringLength = 256;
                } while (FindNextFileNameW(findHandle, ref stringLength, sb));
                FindClose(findHandle);
                return result.ToArray();
            }
            else
            {
                return new string[0];
            }
        }

        private void SetReparsePointInfo(string path)
        {
            SafeFileHandle handle = CreateFile(path, FileAccess.Read, FileShare.None, IntPtr.Zero, FileMode.Open, FILE_FLAG_OPEN_REPARSE_POINT | FILE_FLAG_BACKUP_SEMANTICS, IntPtr.Zero);
            if (handle.IsInvalid)
                throw new Exception(String.Format("Unable to open Reparse Point at {0}: {1}", path, new Win32Exception(Marshal.GetLastWin32Error()).Message));

            REPARSE_DATA_BUFFER buffer = GetReparseData(handle);
            handle.Dispose();

            uint tag = buffer.ReparseTag;
            if (buffer.ReparseTag == IO_REPARSE_TAG_SYMLINK)
            {
                // Because we don't include the Flags in the REPARSE_DATA_BUFFER, we need to manually offset the PathBuffer value by 2
                string printName = new string(buffer.PathBuffer, (int)(buffer.PrintNameOffset / SIZE_OF_WCHAR) + 2, (int)(buffer.PrintNameLength / SIZE_OF_WCHAR));
                string substituteName = new string(buffer.PathBuffer, (int)(buffer.SubstituteNameOffset / SIZE_OF_WCHAR) + 2, (int)(buffer.SubstituteNameLength / SIZE_OF_WCHAR));
                int flags = Convert.ToInt32(buffer.PathBuffer[0]) + Convert.ToInt32(buffer.PathBuffer[1]);
                string linkPath;
                if (flags == SYMLINK_FLAG_RELATIVE)
                {
                    linkPath = Path.Combine(new FileInfo(path).Directory.FullName, printName);
                }
                else
                {
                    linkPath = printName;

                }
                targets = new string[1];
                if (linkPath.EndsWith("\\"))
                {
                    targets[0] = linkPath.Substring(0, linkPath.Length - 1);
                }
                else
                {
                    targets[0] = linkPath;
                }

                type = SYMBOLIC_LINK;
            }
            else if (buffer.ReparseTag == IO_REPARSE_TAG_MOUNT_POINT)
            {
                string printName = new string(buffer.PathBuffer, (int)(buffer.PrintNameOffset / SIZE_OF_WCHAR), (int)(buffer.PrintNameLength / SIZE_OF_WCHAR));
                string substituteName = new string(buffer.PathBuffer, (int)(buffer.SubstituteNameOffset / SIZE_OF_WCHAR), (int)(buffer.SubstituteNameLength / SIZE_OF_WCHAR));
                targets = new string[1];
                if (printName.EndsWith("\\"))
                {
                    targets[0] = printName.Substring(0, printName.Length - 1);
                }
                else
                {
                    targets[0] = printName;
                }
                if (substituteName.StartsWith("\\??\\Volume"))
                {
                    type = MOUNT_POINT;
                }
                else
                {
                    type = JUNCTION_POINT;
                }
            }
            else
            {
                string errorMessage = String.Format("Invalid Reparse Tag: {0}, expecting IO_REPARSE_TAG_SYMLINK {1} or IO_REPARSE_TAG_MOUNT_POINT {2}",
                                        buffer.ReparseTag.ToString(),
                                        IO_REPARSE_TAG_SYMLINK.ToString(),
                                        IO_REPARSE_TAG_MOUNT_POINT.ToString());
                throw new Exception(errorMessage);
            }
        }

        private REPARSE_DATA_BUFFER GetReparseData(SafeFileHandle fileHandle)
        {
            REPARSE_DATA_BUFFER buffer = new REPARSE_DATA_BUFFER();
            uint controlCode = FILE_DEVICE_FILE_SYSTEM | FSCTL_GET_REPARSE_POINT;
            uint bytesReturned;
            if (!DeviceIoControl(fileHandle, controlCode, IntPtr.Zero, 0, out buffer, MAXIMUM_REPARSE_DATA_BUFFER_SIZE, out bytesReturned, IntPtr.Zero))
                throw new Exception(String.Format("Failed to get Reparse Point Data Buffer: {0}", new Win32Exception(Marshal.GetLastWin32Error()).Message));

            return buffer;
        }
    }
}
"@
Add-Type -TypeDefinition $symlink_util
$symlink_helper = [Ansible.SymLink]
$symlink_helper::EnableSeBackupPrivilege()

# Used to delete directories and files with logic on handling symbolic links
function Remove-File($file) {
    try {
        if ($file.Attributes.HasFlag([System.IO.FileAttributes]::ReparsePoint)) {
            # Bug with powershell, if you try and delete a symbolic link that is pointing
            # to an invalid path it will fail, using Win32 API to do this instead
            if (-Not $check_mode) {
                $symlink_helper::DeleteSymLink($file.FullName)
            }
        } elseif ($file.PSIsContainer) {
            Remove-Directory -directory $file -WhatIf:$check_mode
        } else {
            Remove-Item -Path $file.FullName -Force:$true -Recurse:$true -Confirm:$false -WhatIf:$check_mode
        }
        $result.changed = $true
    } catch [Exception] {
        Fail-Json $result "Failed to delete $($file.FullName): $($_.Exception.Message)"
    }
}

function Remove-Directory($directory) {
    foreach ($file in Get-ChildItem $directory.FullName) {
        Remove-File -file $file
    }
    Remove-Item -Path $directory.FullName -Force:$true -Recurse:$true -Confirm:$false -WhatIf:$check_mode
}

function New-Link($link_path, $target, $type) {
    if (Test-Path -Path $target) {
        if ($type -eq "junction" -and (-not (Get-Item -Path $target).PSIsContainer)) {
            Fail-Json $result "Cannot create junction point $($path): junction point target $src is not a directory"
        } elseif ($type -eq "hard" -and (Get-Item -Path $target).PSIsContainer) {
            Fail-Json $result "Cannot create hard link $($path): hard link target $src is not a file"
        }
    } else {
        Fail-Json $result "Cannot create $type at $($link_path): $type target $target does not exist"
    }

    try {
        if (Test-Path -Path $link_path) {
            $link_details = New-Object -TypeName Ansible.Symlink -ArgumentList $link_path
            if ($link_details.Type -eq $type) {
                $current_targets = $link_details.Targets
                if ($current_targets -notcontains $target) {
                    Remove-File -file (Get-Item -Path $link_path)
                    if (-not $check_mode) {
                        $symlink_helper::CreateLink($link_path, $target, $type)
                    }
                    $result.changed = $true
                }
            } else {
                if ($force) {
                    Remove-File -File (Get-Item -Path $link_path)
                    if (-not $check_mode) {
                        $symlink_helper::CreateLink($link_path, $target, $type)
                    }
                    $result.changed = $true
                } else {
                    Fail-Json $result "Cannot create $type at $($link_path): $link_path already exists and is not a $type. Use force: True to override this"
                }
            }
        } else {
            $parent_path = Split-Path -Path $link_path -Parent
            if (-not (Test-Path -Path $parent_path)) {
                New-Item -Path $parent_path -ItemType Directory -WhatIf:$check_mode | Out-Null
                $result.changed = $true
            }
            if (-not $check_mode) {
                $symlink_helper::CreateLink($link_path, $target, $type)
            }
            $result.changed = $true
        }
    } catch {
        Fail-Json $result "Failed to create $type at $($link_path): $($_.Exception.Message)"
    }
}

# Link checks are complex, moving it out of the main code for easier readibility
if ($state -in @("link","junction","hard")) {
    if ($src -eq $null) {
        Fail-Json $result "Cannot create $state when src isn't specified"
    }
    New-Link -link_path $path -target $src -type $state
} else {
    if (Test-Path -Path $path) {
        $file_info = Get-Item -Path $path
        if ($state -eq "absent") {
            Remove-File -File $file_info
        } elseif ($state -eq "directory" -and -not $file_info.PSIsContainer) {
            Fail-Json $result "path $path is not a directory"
        } elseif ($state -eq "file" -and $file_info.PSIsContainer) {
            Fail-Json $result "path $path is not a file"
        } elseif ($state -eq "touch") {
            try {
                if (-not $check_mode) {
                    $file_info.LastWriteTime = Get-Date
                }
                $result.changed = $true
            } catch {
                Fail-Json $result "Failed to touch existing file $($file_info.FullName): $($_.Exception.Message)"
            }
        }
    } else {
        if ($state -eq "directory") {
            try {
                New-Item -Path $path -ItemType Directory -WhatIf:$check_mode | Out-Null
                $result.changed = $true
            } catch {
                Fail-Json $result "Failed to create directory $($path): $($_.Exception.Message)"
            }
        } elseif ($state -eq "file") {
            Fail-Json $result "path $path will not be created"
        } elseif ($state -eq "touch") {
            try {
                Write-Output $null | Out-File -FilePath $path -Encoding ASCII -WhatIf:$check_mode
                $result.changed = $true
            } catch {
                Fail-Json $result "Failed to touch new file $($file_info.FullName): $($_.Exception.Message)"
            }
        }
    }
}

Exit-Json $result
