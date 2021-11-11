# Copyright (c) 2017 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

#Requires -Module Ansible.ModuleUtils.PrivilegeUtil

Function Load-LinkUtils {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute("PSUseSingularNouns", "", Justification = "Cannot change the name now")]
    param ()

    $link_util = @'
using Microsoft.Win32.SafeHandles;
using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;

namespace Ansible
{
    public enum LinkType
    {
        SymbolicLink,
        JunctionPoint,
        HardLink
    }

    public class LinkUtilWin32Exception : System.ComponentModel.Win32Exception
    {
        private string _msg;

        public LinkUtilWin32Exception(string message) : this(Marshal.GetLastWin32Error(), message) { }

        public LinkUtilWin32Exception(int errorCode, string message) : base(errorCode)
        {
            _msg = String.Format("{0} ({1}, Win32ErrorCode {2})", message, base.Message, errorCode);
        }

        public override string Message { get { return _msg; } }
        public static explicit operator LinkUtilWin32Exception(string message) { return new LinkUtilWin32Exception(message); }
    }

    public class LinkInfo
    {
        public LinkType Type { get; internal set; }
        public string PrintName { get; internal set; }
        public string SubstituteName { get; internal set; }
        public string AbsolutePath { get; internal set; }
        public string TargetPath { get; internal set; }
        public string[] HardTargets { get; internal set; }
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct REPARSE_DATA_BUFFER
    {
        public UInt32 ReparseTag;
        public UInt16 ReparseDataLength;
        public UInt16 Reserved;
        public UInt16 SubstituteNameOffset;
        public UInt16 SubstituteNameLength;
        public UInt16 PrintNameOffset;
        public UInt16 PrintNameLength;

        [MarshalAs(UnmanagedType.ByValArray, SizeConst = LinkUtil.MAXIMUM_REPARSE_DATA_BUFFER_SIZE)]
        public char[] PathBuffer;
    }

    public class LinkUtil
    {
        public const int MAXIMUM_REPARSE_DATA_BUFFER_SIZE = 1024 * 16;

        private const UInt32 FILE_FLAG_BACKUP_SEMANTICS = 0x02000000;
        private const UInt32 FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000;

        private const UInt32 FSCTL_GET_REPARSE_POINT = 0x000900A8;
        private const UInt32 FSCTL_SET_REPARSE_POINT = 0x000900A4;
        private const UInt32 FILE_DEVICE_FILE_SYSTEM = 0x00090000;

        private const UInt32 IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003;
        private const UInt32 IO_REPARSE_TAG_SYMLINK = 0xA000000C;

        private const UInt32 SYMLINK_FLAG_RELATIVE = 0x00000001;

        private const Int64 INVALID_HANDLE_VALUE = -1;

        private const UInt32 SIZE_OF_WCHAR = 2;

        private const UInt32 SYMBOLIC_LINK_FLAG_FILE = 0x00000000;
        private const UInt32 SYMBOLIC_LINK_FLAG_DIRECTORY = 0x00000001;

        [DllImport("kernel32.dll", CharSet = CharSet.Auto)]
        private static extern SafeFileHandle CreateFile(
            string lpFileName,
            [MarshalAs(UnmanagedType.U4)] FileAccess dwDesiredAccess,
            [MarshalAs(UnmanagedType.U4)] FileShare dwShareMode,
            IntPtr lpSecurityAttributes,
            [MarshalAs(UnmanagedType.U4)] FileMode dwCreationDisposition,
            UInt32 dwFlagsAndAttributes,
            IntPtr hTemplateFile);

        // Used by GetReparsePointInfo()
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        private static extern bool DeviceIoControl(
            SafeFileHandle hDevice,
            UInt32 dwIoControlCode,
            IntPtr lpInBuffer,
            UInt32 nInBufferSize,
            out REPARSE_DATA_BUFFER lpOutBuffer,
            UInt32 nOutBufferSize,
            out UInt32 lpBytesReturned,
            IntPtr lpOverlapped);

        // Used by CreateJunctionPoint()
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        private static extern bool DeviceIoControl(
            SafeFileHandle hDevice,
            UInt32 dwIoControlCode,
            REPARSE_DATA_BUFFER lpInBuffer,
            UInt32 nInBufferSize,
            IntPtr lpOutBuffer,
            UInt32 nOutBufferSize,
            out UInt32 lpBytesReturned,
            IntPtr lpOverlapped);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        private static extern bool GetVolumePathName(
            string lpszFileName,
            StringBuilder lpszVolumePathName,
            ref UInt32 cchBufferLength);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        private static extern IntPtr FindFirstFileNameW(
            string lpFileName,
            UInt32 dwFlags,
            ref UInt32 StringLength,
            StringBuilder LinkName);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        private static extern bool FindNextFileNameW(
            IntPtr hFindStream,
            ref UInt32 StringLength,
            StringBuilder LinkName);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool FindClose(
            IntPtr hFindFile);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        private static extern bool RemoveDirectory(
            string lpPathName);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        private static extern bool DeleteFile(
            string lpFileName);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        private static extern bool CreateSymbolicLink(
            string lpSymlinkFileName,
            string lpTargetFileName,
            UInt32 dwFlags);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        private static extern bool CreateHardLink(
            string lpFileName,
            string lpExistingFileName,
            IntPtr lpSecurityAttributes);

        public static LinkInfo GetLinkInfo(string linkPath)
        {
            FileAttributes attr = File.GetAttributes(linkPath);
            if (attr.HasFlag(FileAttributes.ReparsePoint))
                return GetReparsePointInfo(linkPath);

            if (!attr.HasFlag(FileAttributes.Directory))
                return GetHardLinkInfo(linkPath);

            return null;
        }

        public static void DeleteLink(string linkPath)
        {
            bool success;
            FileAttributes attr = File.GetAttributes(linkPath);
            if (attr.HasFlag(FileAttributes.Directory))
            {
                success = RemoveDirectory(linkPath);
            }
            else
            {
                success = DeleteFile(linkPath);
            }

            if (!success)
                throw new LinkUtilWin32Exception(String.Format("Failed to delete link at {0}", linkPath));
        }

        public static void CreateLink(string linkPath, String linkTarget, LinkType linkType)
        {
            switch (linkType)
            {
                case LinkType.SymbolicLink:
                    UInt32 linkFlags;
                    FileAttributes attr = File.GetAttributes(linkTarget);
                    if (attr.HasFlag(FileAttributes.Directory))
                        linkFlags = SYMBOLIC_LINK_FLAG_DIRECTORY;
                    else
                        linkFlags = SYMBOLIC_LINK_FLAG_FILE;

                    if (!CreateSymbolicLink(linkPath, linkTarget, linkFlags))
                        throw new LinkUtilWin32Exception(String.Format("CreateSymbolicLink({0}, {1}, {2}) failed", linkPath, linkTarget, linkFlags));
                    break;
                case LinkType.JunctionPoint:
                    CreateJunctionPoint(linkPath, linkTarget);
                    break;
                case LinkType.HardLink:
                    if (!CreateHardLink(linkPath, linkTarget, IntPtr.Zero))
                        throw new LinkUtilWin32Exception(String.Format("CreateHardLink({0}, {1}) failed", linkPath, linkTarget));
                    break;
            }
        }

        private static LinkInfo GetHardLinkInfo(string linkPath)
        {
            UInt32 maxPath = 260;
            List<string> result = new List<string>();

            StringBuilder sb = new StringBuilder((int)maxPath);
            UInt32 stringLength = maxPath;
            if (!GetVolumePathName(linkPath, sb, ref stringLength))
                throw new LinkUtilWin32Exception("GetVolumePathName() failed");
            string volume = sb.ToString();

            stringLength = maxPath;
            IntPtr findHandle = FindFirstFileNameW(linkPath, 0, ref stringLength, sb);
            if (findHandle.ToInt64() != INVALID_HANDLE_VALUE)
            {
                try
                {
                    do
                    {
                        string hardLinkPath = sb.ToString();
                        if (hardLinkPath.StartsWith("\\"))
                            hardLinkPath = hardLinkPath.Substring(1, hardLinkPath.Length - 1);

                        result.Add(Path.Combine(volume, hardLinkPath));
                        stringLength = maxPath;

                    } while (FindNextFileNameW(findHandle, ref stringLength, sb));
                }
                finally
                {
                    FindClose(findHandle);
                }
            }

            if (result.Count > 1)
                return new LinkInfo
                {
                    Type = LinkType.HardLink,
                    HardTargets = result.ToArray()
                };

            return null;
        }

        private static LinkInfo GetReparsePointInfo(string linkPath)
        {
            SafeFileHandle fileHandle = CreateFile(
                linkPath,
                FileAccess.Read,
                FileShare.None,
                IntPtr.Zero,
                FileMode.Open,
                FILE_FLAG_OPEN_REPARSE_POINT | FILE_FLAG_BACKUP_SEMANTICS,
                IntPtr.Zero);

            if (fileHandle.IsInvalid)
                throw new LinkUtilWin32Exception(String.Format("CreateFile({0}) failed", linkPath));

            REPARSE_DATA_BUFFER buffer = new REPARSE_DATA_BUFFER();
            UInt32 bytesReturned;
            try
            {
                if (!DeviceIoControl(
                    fileHandle,
                    FSCTL_GET_REPARSE_POINT,
                    IntPtr.Zero,
                    0,
                    out buffer,
                    MAXIMUM_REPARSE_DATA_BUFFER_SIZE,
                    out bytesReturned,
                    IntPtr.Zero))
                    throw new LinkUtilWin32Exception(String.Format("DeviceIoControl() failed for file at {0}", linkPath));
            }
            finally
            {
                fileHandle.Dispose();
            }

            bool isRelative = false;
            int pathOffset = 0;
            LinkType linkType;
            if (buffer.ReparseTag == IO_REPARSE_TAG_SYMLINK)
            {
                UInt32 bufferFlags = Convert.ToUInt32(buffer.PathBuffer[0]) + Convert.ToUInt32(buffer.PathBuffer[1]);
                if (bufferFlags == SYMLINK_FLAG_RELATIVE)
                    isRelative = true;
                pathOffset = 2;
                linkType = LinkType.SymbolicLink;
            }
            else if (buffer.ReparseTag == IO_REPARSE_TAG_MOUNT_POINT)
            {
                linkType = LinkType.JunctionPoint;
            }
            else
            {
                string errorMessage = String.Format("Invalid Reparse Tag: {0}", buffer.ReparseTag.ToString());
                throw new Exception(errorMessage);
            }

            string printName = new string(buffer.PathBuffer,
                (int)(buffer.PrintNameOffset / SIZE_OF_WCHAR) + pathOffset,
                (int)(buffer.PrintNameLength / SIZE_OF_WCHAR));
            string substituteName = new string(buffer.PathBuffer,
                (int)(buffer.SubstituteNameOffset / SIZE_OF_WCHAR) + pathOffset,
                (int)(buffer.SubstituteNameLength / SIZE_OF_WCHAR));

            // TODO: should we check for \?\UNC\server for convert it to the NT style \\server path
            // Remove the leading Windows object directory \?\ from the path if present
            string targetPath = substituteName;
            if (targetPath.StartsWith("\\??\\"))
                targetPath = targetPath.Substring(4, targetPath.Length - 4);

            string absolutePath = targetPath;
            if (isRelative)
                absolutePath = Path.GetFullPath(Path.Combine(new FileInfo(linkPath).Directory.FullName, targetPath));

            return new LinkInfo
            {
                Type = linkType,
                PrintName = printName,
                SubstituteName = substituteName,
                AbsolutePath = absolutePath,
                TargetPath = targetPath
            };
        }

        private static void CreateJunctionPoint(string linkPath, string linkTarget)
        {
            // We need to create the link as a dir beforehand
            Directory.CreateDirectory(linkPath);
            SafeFileHandle fileHandle = CreateFile(
                linkPath,
                FileAccess.Write,
                FileShare.Read | FileShare.Write | FileShare.None,
                IntPtr.Zero,
                FileMode.Open,
                FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT,
                IntPtr.Zero);

            if (fileHandle.IsInvalid)
                throw new LinkUtilWin32Exception(String.Format("CreateFile({0}) failed", linkPath));

            try
            {
                string substituteName = "\\??\\" + Path.GetFullPath(linkTarget);
                string printName = linkTarget;

                REPARSE_DATA_BUFFER buffer = new REPARSE_DATA_BUFFER();
                buffer.SubstituteNameOffset = 0;
                buffer.SubstituteNameLength = (UInt16)(substituteName.Length * SIZE_OF_WCHAR);
                buffer.PrintNameOffset = (UInt16)(buffer.SubstituteNameLength + 2);
                buffer.PrintNameLength = (UInt16)(printName.Length * SIZE_OF_WCHAR);

                buffer.ReparseTag = IO_REPARSE_TAG_MOUNT_POINT;
                buffer.ReparseDataLength = (UInt16)(buffer.SubstituteNameLength + buffer.PrintNameLength + 12);
                buffer.PathBuffer = new char[MAXIMUM_REPARSE_DATA_BUFFER_SIZE];

                byte[] unicodeBytes = Encoding.Unicode.GetBytes(substituteName + "\0" + printName);
                char[] pathBuffer = Encoding.Unicode.GetChars(unicodeBytes);
                Array.Copy(pathBuffer, buffer.PathBuffer, pathBuffer.Length);

                UInt32 bytesReturned;
                if (!DeviceIoControl(
                    fileHandle,
                    FSCTL_SET_REPARSE_POINT,
                    buffer,
                    (UInt32)(buffer.ReparseDataLength + 8),
                    IntPtr.Zero, 0,
                    out bytesReturned,
                    IntPtr.Zero))
                    throw new LinkUtilWin32Exception(String.Format("DeviceIoControl() failed to create junction point at {0} to {1}", linkPath, linkTarget));
            }
            finally
            {
                fileHandle.Dispose();
            }
        }
    }
}
'@

    # FUTURE: find a better way to get the _ansible_remote_tmp variable
    $original_tmp = $env:TMP
    $original_lib = $env:LIB

    $remote_tmp = $original_tmp
    $module_params = Get-Variable -Name complex_args -ErrorAction SilentlyContinue
    if ($module_params) {
        if ($module_params.Value.ContainsKey("_ansible_remote_tmp") ) {
            $remote_tmp = $module_params.Value["_ansible_remote_tmp"]
            $remote_tmp = [System.Environment]::ExpandEnvironmentVariables($remote_tmp)
        }
    }

    $env:TMP = $remote_tmp
    $env:LIB = $null
    Add-Type -TypeDefinition $link_util
    $env:TMP = $original_tmp
    $env:LIB = $original_lib

    # enable the SeBackupPrivilege if it is disabled
    $state = Get-AnsiblePrivilege -Name SeBackupPrivilege
    if ($state -eq $false) {
        Set-AnsiblePrivilege -Name SeBackupPrivilege -Value $true
    }
}

Function Get-Link($link_path) {
    $link_info = [Ansible.LinkUtil]::GetLinkInfo($link_path)
    return $link_info
}

Function Remove-Link($link_path) {
    [Ansible.LinkUtil]::DeleteLink($link_path)
}

Function New-Link($link_path, $link_target, $link_type) {
    if (-not (Test-Path -LiteralPath $link_target)) {
        throw "link_target '$link_target' does not exist, cannot create link"
    }

    switch ($link_type) {
        "link" {
            $type = [Ansible.LinkType]::SymbolicLink
        }
        "junction" {
            if (Test-Path -LiteralPath $link_target -PathType Leaf) {
                throw "cannot set the target for a junction point to a file"
            }
            $type = [Ansible.LinkType]::JunctionPoint
        }
        "hard" {
            if (Test-Path -LiteralPath $link_target -PathType Container) {
                throw "cannot set the target for a hard link to a directory"
            }
            $type = [Ansible.LinkType]::HardLink
        }
        default { throw "invalid link_type option $($link_type): expecting link, junction, hard" }
    }
    [Ansible.LinkUtil]::CreateLink($link_path, $link_target, $type)
}

# this line must stay at the bottom to ensure all defined module parts are exported
Export-ModuleMember -Alias * -Function * -Cmdlet *
