 # Copyright (c) 2017 Ansible Project
 # Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

 Function Load-LinkUtils() {
    Add-Type -TypeDefinition @'
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

    public enum GET_FILEEX_INFO_LEVELS
    {
        GetFileExInfoStandard,
        GetFileExMaxInfoLevel
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct WIN32_FILE_ATTRIBUTE_DATA
    {
        public FileAttributes dwFileAttributes;
        public System.Runtime.InteropServices.ComTypes.FILETIME ftCreationTime;
        public System.Runtime.InteropServices.ComTypes.FILETIME ftLastAccessTime;
        public System.Runtime.InteropServices.ComTypes.FILETIME ftLastWriteTime;
        public UInt32 nFileSizeHigh;
        public UInt32 nFileSizeLow;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
    public struct WIN32_FIND_DATA
    {
        public FileAttributes dwFileAttributes;
        public System.Runtime.InteropServices.ComTypes.FILETIME ftCreationTime;
        public System.Runtime.InteropServices.ComTypes.FILETIME ftLastAccessTime;
        public System.Runtime.InteropServices.ComTypes.FILETIME ftLastWriteTime;
        public UInt32 nFileSizeHigh;
        public UInt32 nFileSizeLow;
        public UInt32 dwReserved0;
        public UInt32 dwReserved1;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)] public string cFileName;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 14)] public string cAlternateFileName;
    }

    public class LinkUtil
    {
        public const int MAXIMUM_REPARSE_DATA_BUFFER_SIZE = 1024 * 16;

        private const int TOKEN_ADJUST_PRIVILEGES = 0x00000020;
        private const int TOKEN_QUERY = 0x00000008;
        private const int SE_PRIVILEGE_ENABLED = 0x00000002;

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

        [DllImport("kernel32.dll")]
        private static extern IntPtr GetCurrentProcess();

        [DllImport("kernel32.dll")]
        private static extern bool CloseHandle(
            IntPtr hObject);

        [DllImport("advapi32.dll")]
        private static extern bool OpenProcessToken(
            IntPtr ProcessHandle,
            UInt32 DesiredAccess,
            out IntPtr TokenHandle);

        [DllImport("advapi32.dll", CharSet = CharSet.Unicode)]
        private static extern bool LookupPrivilegeValue(
            string lpSystemName,
            string lpName,
            [MarshalAs(UnmanagedType.Struct)] out LUID lpLuid);

        [DllImport("advapi32.dll")]
        private static extern bool AdjustTokenPrivileges(
            IntPtr TokenHandle,
            [MarshalAs(UnmanagedType.Bool)] bool DisableAllPrivileges,
            ref TOKEN_PRIVILEGES NewState,
            UInt32 BufferLength,
            IntPtr PreviousState,
            IntPtr ReturnLength);

        [DllImport("kernel32.dll", CharSet = CharSet.Unicode)]
        private static extern SafeFileHandle CreateFileW(
            string lpFileName,
            [MarshalAs(UnmanagedType.U4)] FileAccess dwDesiredAccess,
            [MarshalAs(UnmanagedType.U4)] FileShare dwShareMode,
            IntPtr lpSecurityAttributes,
            [MarshalAs(UnmanagedType.U4)] FileMode dwCreationDisposition,
            UInt32 dwFlagsAndAttributes,
            IntPtr hTemplateFile);

        // Used by GetReparsePointInfo()
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
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
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        private static extern bool DeviceIoControl(
            SafeFileHandle hDevice,
            UInt32 dwIoControlCode,
            REPARSE_DATA_BUFFER lpInBuffer,
            UInt32 nInBufferSize,
            IntPtr lpOutBuffer,
            UInt32 nOutBufferSize,
            out UInt32 lpBytesReturned,
            IntPtr lpOverlapped);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        private static extern bool GetVolumePathNameW(
            string lpszFileName,
            StringBuilder lpszVolumePathName,
            ref UInt32 cchBufferLength);

        [DllImport("kernel32", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern IntPtr FindFirstFileW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
            out WIN32_FIND_DATA lpFindFileData);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        private static extern IntPtr FindFirstFileNameW(
            string lpFileName,
            UInt32 dwFlags,
            ref UInt32 StringLength,
            StringBuilder LinkName);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        private static extern bool FindNextFileNameW(
            IntPtr hFindStream,
            ref UInt32 StringLength,
            StringBuilder LinkName);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool FindClose(
            IntPtr hFindFile);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        private static extern bool RemoveDirectoryW(
            string lpPathName);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        private static extern bool DeleteFileW(
            string lpFileName);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        private static extern bool CreateSymbolicLinkW(
            string lpSymlinkFileName,
            string lpTargetFileName,
            UInt32 dwFlags);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        private static extern bool CreateHardLinkW(
            string lpFileName,
            string lpExistingFileName,
            IntPtr lpSecurityAttributes);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool CreateDirectoryW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpPathName,
            IntPtr lpSecurityAttributes);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool GetFileAttributesExW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
            GET_FILEEX_INFO_LEVELS fInfoLevelId,
            out WIN32_FILE_ATTRIBUTE_DATA lpFileInformation);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern UInt32 GetFullPathNameW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
            UInt32 nBufferLength,
            StringBuilder lpBuffer,
            out IntPtr lpFilePart);

        public static void EnablePrivilege(string privilege)
        {
            TOKEN_PRIVILEGES tkpPrivileges;

            IntPtr hToken;
            if (!OpenProcessToken(GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, out hToken))
                throw new LinkUtilWin32Exception("OpenProcessToken failed");

            try
            {
                LUID luid;
                if (!LookupPrivilegeValue(null, privilege, out luid))
                    throw new LinkUtilWin32Exception(String.Format("LookupPrivilegeValue({0}) failed", privilege));

                tkpPrivileges.PrivilegeCount = 1;
                tkpPrivileges.Luid = luid;
                tkpPrivileges.Attributes = SE_PRIVILEGE_ENABLED;

                if (!AdjustTokenPrivileges(hToken, false, ref tkpPrivileges, 0, IntPtr.Zero, IntPtr.Zero))
                    throw new LinkUtilWin32Exception(String.Format("AdjustTokenPrivileges({0}) failed", privilege));
            }
            finally
            {
                CloseHandle(hToken);
            }
        }

        public static LinkInfo GetLinkInfo(string linkPath)
        {
            FileAttributes attr = GetFileAttributes(linkPath);
            if (attr.HasFlag(FileAttributes.ReparsePoint))
                return GetReparsePointInfo(linkPath);

            if (!attr.HasFlag(FileAttributes.Directory))
                return GetHardLinkInfo(linkPath);

            return null;
        }

        public static void DeleteLink(string linkPath)
        {
            bool success;
            FileAttributes attr = GetFileAttributes(linkPath);
            if (attr.HasFlag(FileAttributes.Directory))
            {
                success = RemoveDirectoryW(linkPath);
            }
            else
            {
                success = DeleteFileW(linkPath);
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
                    FileAttributes attr = GetFileAttributes(linkTarget);
                    if (attr.HasFlag(FileAttributes.Directory))
                        linkFlags = SYMBOLIC_LINK_FLAG_DIRECTORY;
                    else
                        linkFlags = SYMBOLIC_LINK_FLAG_FILE;

                    if (!CreateSymbolicLinkW(linkPath, linkTarget, linkFlags))
                        throw new LinkUtilWin32Exception(String.Format("CreateSymbolicLinkW({0}, {1}, {2}) failed", linkPath, linkTarget, linkFlags));
                    break;
                case LinkType.JunctionPoint:
                    CreateJunctionPoint(linkPath, linkTarget);
                    break;
                case LinkType.HardLink:
                    if (!CreateHardLinkW(linkPath, linkTarget, IntPtr.Zero))
                        throw new LinkUtilWin32Exception(String.Format("CreateHardLinkW({0}, {1}) failed", linkPath, linkTarget));
                    break;
            }
        }

        private static LinkInfo GetHardLinkInfo(string linkPath)
        {
            UInt32 maxPath = 260;
            List<string> result = new List<string>();

            StringBuilder sb = new StringBuilder((int)maxPath);
            UInt32 stringLength = maxPath;
            if (!GetVolumePathNameW(linkPath, sb, ref stringLength))
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
            SafeFileHandle fileHandle = CreateFileW(
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

            string printName = new string(buffer.PathBuffer, (int)(buffer.PrintNameOffset / SIZE_OF_WCHAR) + pathOffset, (int)(buffer.PrintNameLength / SIZE_OF_WCHAR));
            string substituteName = new string(buffer.PathBuffer, (int)(buffer.SubstituteNameOffset / SIZE_OF_WCHAR) + pathOffset, (int)(buffer.SubstituteNameLength / SIZE_OF_WCHAR));

            // Remove the leading Windows object directory \?\ from the path if present
            string targetPath = substituteName;
            if (targetPath.StartsWith("\\??\\"))
                targetPath = targetPath.Substring(4, targetPath.Length - 4);

            string absolutePath = targetPath;
            if (isRelative)
                absolutePath = GetFullPath(Path.Combine(GetParentDirectoryPath(linkPath), targetPath));
            else
            {
                // Make sure the target and absolute path also has the max path override if the
                // link itself has it as well
                if (linkPath.StartsWith(@"\\?\") && !targetPath.StartsWith(@"\\?\"))
                    targetPath = @"\\?\" + targetPath;
                if (linkPath.StartsWith(@"\\?\") && !absolutePath.StartsWith(@"\\?\"))
                    absolutePath = @"\\?\" + absolutePath;
            }

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
            if (!CreateDirectoryW(linkPath, IntPtr.Zero))
                throw new LinkUtilWin32Exception(String.Format("Failed to create directory {0}", linkPath));
            SafeFileHandle fileHandle = CreateFileW(
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
                string substituteName;
                if (linkTarget.StartsWith(@"\\?\"))
                    substituteName = @"\??\" + GetFullPath(linkTarget).Substring(4);
                else
                    substituteName = @"\??\" + GetFullPath(linkTarget);
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

        public static FileAttributes GetFileAttributes(string path)
        {
            WIN32_FILE_ATTRIBUTE_DATA attrData = new WIN32_FILE_ATTRIBUTE_DATA();
            if (!GetFileAttributesExW(path, GET_FILEEX_INFO_LEVELS.GetFileExInfoStandard, out attrData))
            {
                int lastErr = Marshal.GetLastWin32Error();
                // 2 = ERROR_FILE_NOT_FOUND, 3 = ERROR_PATH_NOT_FOUND, 32 = ERROR_SHARING_VIOLATION
                if (lastErr == 2 || lastErr == 3)
                    attrData.dwFileAttributes = (FileAttributes)(-1);
                else if (lastErr == 32)
                {
                    // For files that have a system lock like C:\pagefile.sys, use the FindFirstFileW function
                    // and populate the file data based on the find data
                    WIN32_FIND_DATA findData;
                    IntPtr findHandle = FindFirstFileW(path, out findData);
                    if (findHandle.ToInt64() == -1)
                        throw new LinkUtilWin32Exception("Failed to get file attributes for file in use");
                    FindClose(findHandle);
                    attrData.dwFileAttributes = findData.dwFileAttributes;
                    attrData.ftCreationTime = findData.ftCreationTime;
                    attrData.ftLastAccessTime = findData.ftLastAccessTime;
                    attrData.ftLastWriteTime = findData.ftLastWriteTime;
                    attrData.nFileSizeHigh = findData.nFileSizeHigh;
                    attrData.nFileSizeLow = findData.nFileSizeLow;
                }
                else
                    throw new LinkUtilWin32Exception(lastErr, "GetFileAttributesExW() failed");
            }

            return attrData.dwFileAttributes;
        }

        private static string GetFullPath(string path)
        {
            UInt32 bufferLength = 0;
            StringBuilder lpBuffer = new StringBuilder(0);
            IntPtr lpFilePart = IntPtr.Zero;
            UInt32 returnLength = GetFullPathNameW(path, bufferLength, lpBuffer, out lpFilePart);
            if (returnLength == 0)
                throw new LinkUtilWin32Exception(String.Format("GetFullPathName({0}) failed when getting buffer size", path));

            lpBuffer.EnsureCapacity((int)returnLength);
            returnLength = GetFullPathNameW(path, returnLength, lpBuffer, out lpFilePart);
            if (returnLength == 0)
                throw new LinkUtilWin32Exception(String.Format("GetFullPathName({0}, {1}) failed when getting full path", path, returnLength));
            return lpBuffer.ToString();
        }

        private static string GetParentDirectoryPath(string path)
        {
            int rootLength = GetPathRoot(path).Length;
            if (path.Length <= rootLength)
                return null;

            // Get the length up to the last \ or /
            char dirSeparator = System.IO.Path.DirectorySeparatorChar;
            char altDirSeparator = System.IO.Path.AltDirectorySeparatorChar;
            int length = path.Length;
            while (length > rootLength && path[--length] != dirSeparator && path[length] != altDirSeparator) { }

            return path.Substring(0, length);
        }

        private static string GetPathRoot(string path)
        {
            // Strip the extended length path prefix if present
            string pathPrefix = "";
            if (path.StartsWith(@"\\?\"))
            {
                path = path.Substring(4);
                pathPrefix = @"\\?\";
            }
            else if (path.ToUpper().StartsWith(@"\\UNC\"))
            {
                path = @"\\" + path.Substring(6);
                pathPrefix = @"\\UNC\";
            }

            // Make sure we don't exceed 256 chars and get the root from there
            // the extra path info isn't needed 
            if (path.Length > 256)
                path = path.Substring(0, 256);
            string pathRoot = System.IO.Path.GetPathRoot(path);

            // Make sure the \\server is changed back to \\UNC\server
            if (pathPrefix == @"\\UNC\")
                return pathPrefix + pathRoot.Substring(2);
            else
                return pathPrefix + pathRoot;
        }
    }
}
'@

    [Ansible.LinkUtil]::EnablePrivilege("SeBackupPrivilege")
}

Function Get-Link($link_path) {
    $link_info = [Ansible.LinkUtil]::GetLinkInfo($link_path)
    return $link_info
}

Function Remove-Link($link_path) {
    [Ansible.LinkUtil]::DeleteLink($link_path)
}

Function New-Link($link_path, $link_target, $link_type) {
    $target_attr = [Ansible.LinkUtil]::GetFileAttributes($link_target)
    if ([Int32]$target_attr -eq -1) {
        throw "link_target '$link_target' does not exist, cannot create link"
    }
    
    switch($link_type) {
        "link" {
            $type = [Ansible.LinkType]::SymbolicLink
        }
        "junction" {
            if (-not $target_attr.HasFlag([System.IO.FileAttributes]::Directory)) {
                throw "cannot set the target for a junction point to a file"
            }
            $type = [Ansible.LinkType]::JunctionPoint
        }
        "hard" {
            if ($target_attr.HasFlag([System.IO.FileAttributes]::Directory)) {
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

