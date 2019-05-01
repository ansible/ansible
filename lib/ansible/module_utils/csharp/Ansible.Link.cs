using Microsoft.Win32.SafeHandles;
using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Text;
using Ansible.IO;
using Ansible.Privilege;

namespace Ansible.Link
{
    internal class NativeHelpers
    {
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
            public byte[] PathBuffer;
        }
    }

    internal class NativeMethods
    {
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool CreateHardLinkW(
            string lpFileName,
            string lpExistingFileName,
            IntPtr lpSecurityAttributes);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool CreateSymbolicLinkW(
            string lpSymlinkFileName,
            string lpTargetFileName,
            UInt32 dwFlags);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool DeviceIoControl(
            SafeFileHandle hDevice,
            UInt32 dwIoControlCode,
            Ansible.Privilege.SafeMemoryBuffer lpInBuffer,
            UInt32 nInBufferSize,
            Ansible.Privilege.SafeMemoryBuffer lpOutBuffer,
            UInt32 nOutBufferSize,
            out UInt32 lpBytesReturned,
            IntPtr lpOverlapped);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern SafeFindHandle FindFirstFileNameW(
            string lpFileName,
            UInt32 dwFlags,
            ref UInt32 StringLength,
            StringBuilder LinkName);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool FindNextFileNameW(
            SafeFindHandle hFindStream,
            ref UInt32 StringLength,
            StringBuilder LinkName);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool GetVolumePathNameW(
            string lpszFileName,
            StringBuilder lpszVolumePathName,
            ref UInt32 cchBufferLength);
    }

    public enum LinkType
    {
        SymbolicLink,
        JunctionPoint,
        HardLink
    }

    public class LinkInfo
    {
        public LinkType Type { get; internal set; }

        // Part of REPARSE_DATA_BUFFER, this is just a label of the target
        public string PrintName { get; internal set; }

        // Part of REPARSE_DATA_BUFFER, this is the actual target using the NT Kernel path (differs from the Win32 path)
        public string SubstituteName { get; internal set; }

        // Converts the SubstituteName value to the Win32 path, this is the absolute path
        public string AbsolutePath { get; internal set; }

        // Converts the SubstituteName value to the Win32 path, this is not resolved to the absolute path and can be related to the path of the link itself
        public string TargetPath { get; internal set; }

        // If LinkType is HardLink, this is an array of paths that are linked together
        public string[] HardTargets { get; internal set; }
    }

    public class LinkUtil
    {
        public const int MAXIMUM_REPARSE_DATA_BUFFER_SIZE = 16384 - 16;  // 16 KiB - 16 bytes for the REPARSE_DATA_BUFFER headers

        private const UInt32 FSCTL_GET_REPARSE_POINT = 0x000900A8;
        private const UInt32 FSCTL_SET_REPARSE_POINT = 0x000900A4;

        private const UInt32 IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003;
        private const UInt32 IO_REPARSE_TAG_SYMLINK = 0xA000000C;

        private const UInt32 SYMLINK_FLAG_RELATIVE = 0x00000001;

        private const UInt32 SYMBOLIC_LINK_FLAG_FILE = 0x00000000;
        private const UInt32 SYMBOLIC_LINK_FLAG_DIRECTORY = 0x00000001;
        private const UInt32 SYMBOLIC_LINK_FLAG_ALLOW_UNPRIVILEGED_CREATE = 0x00000002;


        /// <summary>
        /// Gets the link info for the path specified.
        /// </summary>
        /// <param name="linkPath">The path of the link to check.</param>
        /// <returns>Ansible.Link.LinkInfo if the file is a link, null if it is not.</returns>
        public static LinkInfo GetLinkInfo(string linkPath)
        {
            FileAttributeData attrData = FileSystem.GetFileAttributeData(linkPath);
            if (attrData.FileAttributes.HasFlag(FileAttributes.ReparsePoint))
                return GetReparsePointInfo(linkPath);

            if (!attrData.FileAttributes.HasFlag(FileAttributes.Directory))
                return GetHardLinkInfo(linkPath);

            return null;
        }

        /// <summary>
        /// Deletes the link at the path specified.
        /// </summary>
        /// <param name="linkPath">The path to the link to delete.</param>
        public static void DeleteLink(string linkPath)
        {
            FileAttributeData attrData = FileSystem.GetFileAttributeData(linkPath);
            if (attrData.FileAttributes.HasFlag(FileAttributes.Directory))
                FileSystem.RemoveDirectory(linkPath, false);
            else
                FileSystem.DeleteFile(linkPath);
        }

        /// <summary>
        /// Creates a link.
        /// </summary>
        /// <param name="linkPath">The path to create the link at.</param>
        /// <param name="linkTarget">The target of the link, must be absolute unless LinkType is SymbolicLink.</param>
        /// <param name="linkType">The Ansible.Link.LinkType that specifies the type of link to create.</param>
        public static void CreateLink(string linkPath, string linkTarget, LinkType linkType)
        {
            switch (linkType)
            {
                case LinkType.SymbolicLink:
                    CreateSymbolicLink(linkPath, linkTarget);
                    break;
                case LinkType.JunctionPoint:
                    CreateJunctionPoint(linkPath, linkTarget);
                    break;
                case LinkType.HardLink:
                    using (new PrivilegeEnabler(false, "SeRestorePrivilege", "SeTakeOwnershipPrivilege"))
                    {
                        if (!NativeMethods.CreateHardLinkW(linkPath, linkTarget, IntPtr.Zero))
                            RaiseCreateLinkException(linkPath, linkTarget);
                    }
                    break;
            }
        }

        private static LinkInfo GetHardLinkInfo(string linkPath)
        {
            // GetVolumePathNameW requires a buffer length to be set for the output path. To be safe we just get the
            // length of the full path as the root will always be less than this.
            StringBuilder volumePathName = new StringBuilder(Ansible.IO.Path.GetFullPath(linkPath).Length);
            UInt32 bufferLength = (UInt32)volumePathName.Capacity;
            if (!NativeMethods.GetVolumePathNameW(linkPath, volumePathName, ref bufferLength))
                throw Ansible.IO.Win32Marshal.GetExceptionForLastWin32Error(linkPath);
            string volume = volumePathName.ToString();

            UInt32 stringLength = 0;
            StringBuilder linkName = new StringBuilder();
            NativeMethods.FindFirstFileNameW(linkPath, 0, ref stringLength, linkName);
            linkName.EnsureCapacity((int)stringLength);

            // No use setting SeBackupPrivilege as FindFirstFileNameW does not open the file with the backup flag
            List<string> result = new List<string>();
            using (SafeFindHandle findHandle = NativeMethods.FindFirstFileNameW(linkPath, 0, ref stringLength, linkName))
            {
                int errorCode = Marshal.GetLastWin32Error();
                if (findHandle.IsInvalid)
                {
                    // ERROR_NOT_SUPPORTED - Cannot enumerate network paths, so just return null, otherwise throw exp
                    if (errorCode == 0x00000032 && linkPath.StartsWith(@"\\"))
                        return null;
                    else
                        throw Ansible.IO.Win32Marshal.GetExceptionForLastWin32Error(linkPath);
                }    

                while (true)
                {
                    string hardLinkPath = linkName.ToString();
                    hardLinkPath = hardLinkPath.StartsWith(@"\") ? hardLinkPath.Substring(1) : hardLinkPath;
                    result.Add(Ansible.IO.Path.Combine(volume, hardLinkPath));

                    // get the buffer size for the next file
                    linkName = new StringBuilder();
                    stringLength = 0;
                    NativeMethods.FindNextFileNameW(findHandle, ref stringLength, linkName);
                    linkName.Capacity = (int)stringLength;

                    if (!NativeMethods.FindNextFileNameW(findHandle, ref stringLength, linkName))
                    {
                        errorCode = Marshal.GetLastWin32Error();
                        if (errorCode == 38)  // ERROR_HANDLE_EOF
                            break;
                        throw Ansible.IO.Win32Marshal.GetExceptionForWin32Error(errorCode);
                    }
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
            Ansible.IO.NativeHelpers.FlagsAndAttributes flagsAndAttr =
                Ansible.IO.NativeHelpers.FlagsAndAttributes.FILE_FLAG_OPEN_REPARSE_POINT |
                Ansible.IO.NativeHelpers.FlagsAndAttributes.FILE_FLAG_BACKUP_SEMANTICS;

            using (SafeMemoryBuffer outBuffer = new Ansible.Privilege.SafeMemoryBuffer(MAXIMUM_REPARSE_DATA_BUFFER_SIZE))
            using (new PrivilegeEnabler(false, "SeBackupPrivilege"))
            using (SafeFileHandle handle = Ansible.IO.NativeMethods.CreateFileW(linkPath, FileSystemRights.Read,
                FileShare.None, IntPtr.Zero, FileMode.Open, flagsAndAttr, IntPtr.Zero))
            {
                if (handle.IsInvalid)
                    throw Ansible.IO.Win32Marshal.GetExceptionForLastWin32Error(linkPath);

                UInt32 bytesReturned;
                if (!NativeMethods.DeviceIoControl(handle, FSCTL_GET_REPARSE_POINT, new SafeMemoryBuffer(0), 0, outBuffer,
                    MAXIMUM_REPARSE_DATA_BUFFER_SIZE, out bytesReturned, IntPtr.Zero))
                {
                    throw Ansible.IO.Win32Marshal.GetExceptionForLastWin32Error(linkPath);
                }
                NativeHelpers.REPARSE_DATA_BUFFER buffer = (NativeHelpers.REPARSE_DATA_BUFFER)Marshal.PtrToStructure(outBuffer.DangerousGetHandle(),
                    typeof(NativeHelpers.REPARSE_DATA_BUFFER));

                bool isRelative = false;
                LinkType linkType;
                int offset = 0;
                if (buffer.ReparseTag == IO_REPARSE_TAG_SYMLINK)
                {
                    linkType = LinkType.SymbolicLink;
                    UInt32 bufferFlags = BitConverter.ToUInt32(buffer.PathBuffer, 0);
                    if (bufferFlags == SYMLINK_FLAG_RELATIVE)
                        isRelative = true;
                    offset = 4;
                }
                else if (buffer.ReparseTag == IO_REPARSE_TAG_MOUNT_POINT)
                    linkType = LinkType.JunctionPoint;
                else
                    throw new Exception(String.Format("Unsupported Reparse Tag: 0x{0}", buffer.ReparseTag.ToString("X8")));

                string printName = Encoding.Unicode.GetString(buffer.PathBuffer, buffer.PrintNameOffset + offset, buffer.PrintNameLength);
                string substituteName = Encoding.Unicode.GetString(buffer.PathBuffer, buffer.SubstituteNameOffset + offset, buffer.SubstituteNameLength);
                string targetPath = substituteName;
                string absolutePath;

                if (isRelative)
                    absolutePath = Ansible.IO.Path.GetFullPath(Ansible.IO.Path.Combine(Ansible.IO.Path.GetDirectoryName(linkPath), targetPath));
                else
                {
                    // Remove the NT object namespace \??\, \DosDevices\ and get a normal Win32 path
                    if (targetPath.StartsWith(@"\??\UNC") && (linkPath.StartsWith(@"\\?\") || printName.Length > 250))
                        targetPath = @"\\?\" + targetPath.Substring(4, targetPath.Length - 4);
                    else if (targetPath.StartsWith(@"\??\UNC"))
                        targetPath = @"\" + targetPath.Substring(7, targetPath.Length - 7);
                    else if (targetPath.StartsWith(@"\??\") && (linkPath.StartsWith(@"\\?\") || printName.Length > 250))
                        targetPath = @"\\?\" + targetPath.Substring(4, targetPath.Length - 4);
                    else if (targetPath.StartsWith(@"\??\"))
                        targetPath = targetPath.Substring(4, targetPath.Length - 4);
                    else if (targetPath.StartsWith(@"\DosDevices\") && (linkPath.StartsWith(@"\\?\") || printName.Length > 250))
                        targetPath = @"\\?\" + targetPath.Substring(12, targetPath.Length - 12);
                    else if (targetPath.StartsWith(@"\DosDevices\"))
                        targetPath = targetPath.Substring(12, targetPath.Length - 12);
                    absolutePath = targetPath;
                }

                return new LinkInfo
                {
                    Type = linkType,
                    PrintName = printName,  // raw PrintName from buffer
                    SubstituteName = substituteName,  // raw SubstituteName from buffer (contains NT obj namespace)
                    AbsolutePath = absolutePath,  // The absolute path of TargetPath
                    TargetPath = targetPath  // SubstituteName but without the obj namespace
                };
            }
        }

        private static void CreateSymbolicLink(string linkPath, string linkTarget)
        {
            string absoluteTarget = linkTarget;
            if (!Ansible.IO.Path.IsPathRooted(linkTarget))
            {
                string parentDir = Ansible.IO.Path.GetDirectoryName(linkPath);
                absoluteTarget = Ansible.IO.Path.GetFullPath(Ansible.IO.Path.Combine(parentDir, linkTarget));
            }

            UInt32 linkFlags = 0;
            try
            {
                FileAttributeData attrData = FileSystem.GetFileAttributeData(absoluteTarget);
                if (attrData.FileAttributes.HasFlag(FileAttributes.Directory))
                    linkFlags = SYMBOLIC_LINK_FLAG_DIRECTORY;
                else
                    linkFlags = SYMBOLIC_LINK_FLAG_FILE;
            }
            catch (Exception e)
            {
                if (e is FileNotFoundException || e is DirectoryNotFoundException)
                    // Cannot determine link type based on the target as it does not exist, use dir if no extension is present otherwise file
                    linkFlags = Ansible.IO.Path.GetExtension(absoluteTarget) == "" && Ansible.IO.Path.GetExtension(linkPath) == ""
                        ? SYMBOLIC_LINK_FLAG_DIRECTORY
                        : SYMBOLIC_LINK_FLAG_FILE;
            }

            // Try and run with the new flag that allows non elevated processes to create symlinks
            // will return ERROR_INVALID_PARAMETER if on an unsupported host
            // added in Windows 10 build 14972
            linkFlags |= SYMBOLIC_LINK_FLAG_ALLOW_UNPRIVILEGED_CREATE;

            using (new PrivilegeEnabler(false, "SeRestorePrivilege"))
            {
                if (!NativeMethods.CreateSymbolicLinkW(linkPath, linkTarget, linkFlags))
                {
                    int errorCode = Marshal.GetLastWin32Error();
                    if (errorCode == Ansible.IO.Win32Errors.ERROR_INVALID_PARAMETER)  // try again without flag
                        if (NativeMethods.CreateSymbolicLinkW(linkPath, linkTarget, linkFlags &= ~SYMBOLIC_LINK_FLAG_ALLOW_UNPRIVILEGED_CREATE))
                            errorCode = 0;
                        else
                            errorCode = Marshal.GetLastWin32Error();

                    if (errorCode != 0)
                        RaiseCreateLinkException(linkPath, linkTarget, errorCode: errorCode);
                }
            }
        }

        private static void CreateJunctionPoint(string linkPath, string linkTarget)
        {
            if (!Ansible.IO.Path.IsPathRooted(linkTarget))
                throw new ArgumentException(String.Format("Cannot create junction point because target '{0}' is not an absolute path.", linkTarget));
            else if (Ansible.IO.FileSystem.FileExists(linkTarget))
                throw new ArgumentException(String.Format("Cannot create junction point because target '{0}' is a file.", linkTarget));

            string substituteName;
            if (linkTarget.StartsWith(@"\\?\"))
                substituteName = @"\??\" + Ansible.IO.Path.GetFullPath(linkTarget).Substring(4);
            else
                substituteName = @"\??\" + Ansible.IO.Path.GetFullPath(linkTarget);
            string printName = linkTarget;

            UInt16 substituteNameLength = (UInt16)Encoding.Unicode.GetByteCount(substituteName);
            UInt16 printNameLength = (UInt16)Encoding.Unicode.GetByteCount(printName);
            byte[] pathBuffer = Encoding.Unicode.GetBytes(substituteName + "\0" + printName + "\0");

            NativeHelpers.REPARSE_DATA_BUFFER buffer = new NativeHelpers.REPARSE_DATA_BUFFER();
            buffer.ReparseTag = IO_REPARSE_TAG_MOUNT_POINT;
            buffer.SubstituteNameOffset = 0;
            buffer.SubstituteNameLength = substituteNameLength;
            buffer.PrintNameOffset = (UInt16)(substituteNameLength + sizeof(char));  // offset include the null unicode terminator
            buffer.PrintNameLength = printNameLength;
            buffer.PathBuffer = new byte[MAXIMUM_REPARSE_DATA_BUFFER_SIZE];
            Array.Copy(pathBuffer, buffer.PathBuffer, pathBuffer.Length);
            buffer.ReparseDataLength = (UInt16)(pathBuffer.Length + (4 * sizeof(UInt16)));  // sizeof fields past Reserved in REPARSE_DATA_BUFFER
            UInt32 reparseHeaderSize = sizeof(UInt32) + (2 * sizeof(UInt16));  // sizof ReparseTag + ReparseDataLength + Reserved

            // We need to create the link as a dir beforehand
            FileSystem.CreateDirectory(linkPath);

            Ansible.IO.NativeHelpers.FlagsAndAttributes flagsAndAttr =
                Ansible.IO.NativeHelpers.FlagsAndAttributes.FILE_FLAG_OPEN_REPARSE_POINT |
                Ansible.IO.NativeHelpers.FlagsAndAttributes.FILE_FLAG_BACKUP_SEMANTICS;

            // Open a handle to the new dir and write the reparse buffer data
            using (SafeMemoryBuffer inBuffer = new SafeMemoryBuffer(Marshal.SizeOf(typeof(NativeHelpers.REPARSE_DATA_BUFFER))))
            using (new PrivilegeEnabler(false, "SeRestorePrivilege"))
            using (SafeFileHandle handle = Ansible.IO.NativeMethods.CreateFileW(linkPath, FileSystemRights.Write,
                FileShare.Read | FileShare.Write | FileShare.None, IntPtr.Zero, FileMode.Open,
                flagsAndAttr, IntPtr.Zero))
            {
                if (handle.IsInvalid)
                    throw Ansible.IO.Win32Marshal.GetExceptionForLastWin32Error(linkPath);

                Marshal.StructureToPtr(buffer, inBuffer.DangerousGetHandle(), false);
                UInt32 bytesReturned;
                if (!NativeMethods.DeviceIoControl(handle, FSCTL_SET_REPARSE_POINT, inBuffer,
                    reparseHeaderSize + buffer.ReparseDataLength, new SafeMemoryBuffer(0), 0, out bytesReturned, IntPtr.Zero))
                {
                    throw Ansible.IO.Win32Marshal.GetExceptionForLastWin32Error(linkPath);
                }
            }
        }

        private static void RaiseCreateLinkException(string linkPath, string linkTarget, int? errorCode = null)
        {
            // Some smarter logic when it comes to raising exceptions and the paths they are about.
            if (errorCode == null)
                errorCode = Marshal.GetLastWin32Error();

            string fileName = linkPath;
            if (errorCode == Ansible.IO.Win32Errors.ERROR_FILE_NOT_FOUND || errorCode == Ansible.IO.Win32Errors.ERROR_PATH_NOT_FOUND)
            {
                if (!Ansible.IO.FileSystem.Exists(linkTarget))
                    fileName = linkTarget;
            }
            else if (errorCode == Ansible.IO.Win32Errors.ERROR_ACCESS_DENIED && Ansible.IO.FileSystem.DirectoryExists(linkTarget))
            {
                // Hard link with target pointing to a directory
                throw new IOException(String.Format("The target file '{0}' is a directory, not a file.", linkTarget),
                    Ansible.IO.Win32Marshal.MakeHRFromErrorCode((int)errorCode));
            }


            throw Ansible.IO.Win32Marshal.GetExceptionForWin32Error((int)errorCode, fileName);
        }
    }
}
