# Copyright (c) 2017 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

#Requires -Module Ansible.ModuleUtils.PrivilegeUtil
#Requires -Module Ansible.ModuleUtils.FileUtil

$ansible_link_util_namespaces = @(
    "Microsoft.Win32.SafeHandles",
    "System",
    "System.Collections.Generic",
    "System.IO",
    "System.Runtime.InteropServices",
    "System.Text"
)

$ansible_link_util_code = @'
namespace Ansible.LinkUtil
{
    public enum LinkType
    {
        SymbolicLink,
        JunctionPoint,
        HardLink
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

        // If LinkType is HardLinnk, this is an array of paths that are linked together
        public string[] HardTargets { get; internal set; }
    }

    internal class NativeHelpers
    {
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        internal struct REPARSE_DATA_BUFFER
        {
            public UInt32 ReparseTag;
            public UInt16 ReparseDataLength;
            public UInt16 Reserved;
            public UInt16 SubstituteNameOffset;
            public UInt16 SubstituteNameLength;
            public UInt16 PrintNameOffset;
            public UInt16 PrintNameLength;

            [MarshalAs(UnmanagedType.ByValArray, SizeConst = Links.MAXIMUM_REPARSE_DATA_BUFFER_SIZE)]
            public byte[] PathBuffer;
        }
    }

    internal class NativeMethods
    {
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern SafeFileHandle CreateFileW(
            string lpFileName,
            [MarshalAs(UnmanagedType.U4)] FileAccess dwDesiredAccess,
            [MarshalAs(UnmanagedType.U4)] FileShare dwShareMode,
            IntPtr lpSecurityAttributes,
            [MarshalAs(UnmanagedType.U4)] FileMode dwCreationDisposition,
            UInt32 dwFlagsAndAttributes,
            IntPtr hTemplateFile);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool CreateHardLinkW(
            string lpFileName,
            string lpExistingFileName,
            IntPtr lpSecurityAttributes);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        [return: MarshalAs(UnmanagedType.I1)]
        internal static extern bool CreateSymbolicLinkW(
            string lpSymlinkFileName,
            string lpTargetFileName,
            UInt32 dwFlags);

        // Used by GetReparsePointInfo()
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool DeviceIoControl(
            SafeFileHandle hDevice,
            UInt32 dwIoControlCode,
            IntPtr lpInBuffer,
            UInt32 nInBufferSize,
            out NativeHelpers.REPARSE_DATA_BUFFER lpOutBuffer,
            UInt32 nOutBufferSize,
            out UInt32 lpBytesReturned,
            IntPtr lpOverlapped);

        // Used by CreateJunctionPoint()
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool DeviceIoControl(
            SafeFileHandle hDevice,
            UInt32 dwIoControlCode,
            ref NativeHelpers.REPARSE_DATA_BUFFER lpInBuffer,
            UInt32 nInBufferSize,
            IntPtr lpOutBuffer,
            UInt32 nOutBufferSize,
            out UInt32 lpBytesReturned,
            IntPtr lpOverlapped);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool GetVolumePathNameW(
            string lpszFileName,
            StringBuilder lpszVolumePathName,
            ref UInt32 cchBufferLength);

        [DllImport("kernel32.dll", SetLastError = true)]
        internal static extern bool FindClose(
            IntPtr hFindFile);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern IntPtr FindFirstFileNameW(
            string lpFileName,
            UInt32 dwFlags,
            ref UInt32 StringLength,
            StringBuilder LinkName);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool FindNextFileNameW(
            IntPtr hFindStream,
            ref UInt32 StringLength,
            StringBuilder LinkName);
    }

    public class Links
    {
        public const int MAXIMUM_REPARSE_DATA_BUFFER_SIZE = 16384 - 16;  // 16 KiB - 16 bytes for the REPARSE_DATA_BUFFER headers

        private const UInt32 FILE_FLAG_BACKUP_SEMANTICS = 0x02000000;
        private const UInt32 FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000;

        private const UInt32 FSCTL_GET_REPARSE_POINT = 0x000900A8;
        private const UInt32 FSCTL_SET_REPARSE_POINT = 0x000900A4;

        private const UInt32 IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003;
        private const UInt32 IO_REPARSE_TAG_SYMLINK = 0xA000000C;

        private const UInt32 SYMLINK_FLAG_RELATIVE = 0x00000001;

        private const Int64 INVALID_HANDLE_VALUE = -1;

        private const UInt32 SYMBOLIC_LINK_FLAG_FILE = 0x00000000;
        private const UInt32 SYMBOLIC_LINK_FLAG_DIRECTORY = 0x00000001;
        private const UInt32 SYMBOLIC_LINK_FLAG_ALLOW_UNPRIVILEGED_CREATE = 0x00000002;

        public static LinkInfo GetLinkInfo(string linkPath)
        {
            FileAttributes attr = Ansible.IO.File.GetAttributes(linkPath);
            if (attr.HasFlag(FileAttributes.ReparsePoint))
                return GetReparsePointInfo(linkPath);

            if (!attr.HasFlag(FileAttributes.Directory))
                return GetHardLinkInfo(linkPath);

            return null;
        }

        public static void DeleteLink(string linkPath)
        {
            FileAttributes attr = Ansible.IO.File.GetAttributes(linkPath);
            if (attr.HasFlag(FileAttributes.Directory))
            {
                Ansible.IO.Directory.Delete(linkPath);
            }
            else
            {
                Ansible.IO.File.Delete(linkPath);
            }
        }

        public static void CreateLink(string linkPath, String linkTarget, LinkType linkType)
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
                    if (!NativeMethods.CreateHardLinkW(linkPath, linkTarget, IntPtr.Zero))
                        throw new Win32Exception(String.Format("CreateHardLinkW({0}, {1}) failed", linkPath, linkTarget));
                    break;
            }
        }

        private static LinkInfo GetHardLinkInfo(string linkPath)
        {
            // GetVolumePathNameW indicates to get the max buffer size by getting the size of
            // GetFullPathName which Ansible.IO.Path.GetFullPath() does
            string fullPath = Ansible.IO.Path.GetFullPath(linkPath);
            StringBuilder volumePathName = new StringBuilder(fullPath.Length);
            UInt32 bufferLength = (UInt32)fullPath.Length;
            if (!NativeMethods.GetVolumePathNameW(linkPath, volumePathName, ref bufferLength))
                throw new Win32Exception(String.Format("GetVolumePathNameW({0}) failed", linkPath));
            string volume = volumePathName.ToString();

            UInt32 stringLength = 0;
            StringBuilder linkName = new StringBuilder();
            NativeMethods.FindFirstFileNameW(linkPath, 0, ref stringLength, linkName);
            linkName.EnsureCapacity((int)stringLength);

            List<string> result = new List<string>();
            IntPtr findHandle = NativeMethods.FindFirstFileNameW(linkPath, 0, ref stringLength, linkName);
            if (findHandle.ToInt64() == INVALID_HANDLE_VALUE)
                throw new Win32Exception(String.Format("FindFirstFileNameW({0} failed", linkPath));

            try
            {
                while (true)
                {
                    string hardLinkPath = linkName.ToString();
                    hardLinkPath = hardLinkPath.StartsWith(@"\") ? hardLinkPath.Substring(1, hardLinkPath.Length - 1) : hardLinkPath;
                    result.Add(Ansible.IO.Path.Combine(volume, hardLinkPath));

                    // get the buffer size for the next file
                    linkName = new StringBuilder();
                    stringLength = 0;
                    NativeMethods.FindNextFileNameW(findHandle, ref stringLength, linkName);
                    linkName.Capacity = (int)stringLength;

                    if (!NativeMethods.FindNextFileNameW(findHandle, ref stringLength, linkName))
                    {
                        int errorCode = Marshal.GetLastWin32Error();
                        if (errorCode == 38)  // ERROR_HANDLE_EOF
                            break;
                        throw new Win32Exception(errorCode, "FindNextFIleNameW() failed");
                    }
                }
            }
            finally
            {
                NativeMethods.FindClose(findHandle);
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
            // enable the SeBackupPrivilege if possible so that CreateFileW can get a read handle
            // even if it does not have Read rights
            List<string> privileges = new List<string>();
            SafeWaitHandle process = Ansible.PrivilegeUtil.Privileges.GetCurrentProcess();
            if (Ansible.PrivilegeUtil.Privileges.GetAllPrivilegeInfo(process).ContainsKey("SeBackupPrivilege"))
                privileges.Add("SeBackupPrivilege");

            NativeHelpers.REPARSE_DATA_BUFFER buffer = new NativeHelpers.REPARSE_DATA_BUFFER();
            using (new Ansible.IO.PrivilegeEnabler(privileges.ToArray()))
            {
                using (SafeFileHandle handle = NativeMethods.CreateFileW(
                    linkPath, FileAccess.Read, FileShare.None, IntPtr.Zero, FileMode.Open,
                    FILE_FLAG_OPEN_REPARSE_POINT | FILE_FLAG_BACKUP_SEMANTICS, IntPtr.Zero))
                {
                    if (handle.IsInvalid)
                        throw new Win32Exception(String.Format("CreateFile({0}) failed", linkPath));

                    UInt32 bytesReturned;
                    if (!NativeMethods.DeviceIoControl(handle, FSCTL_GET_REPARSE_POINT, IntPtr.Zero, 0, out buffer,
                        MAXIMUM_REPARSE_DATA_BUFFER_SIZE, out bytesReturned, IntPtr.Zero))
                        throw new Win32Exception(String.Format("DeviceIoControl() failed for file at {0}", linkPath));
                }
            }

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
                SubstituteName = substituteName,  // raw SubstitueName from buffer (contains NT obj namespace)
                AbsolutePath = absolutePath,  // The absolute path of TargetPath
                TargetPath = targetPath  // SubstituteName but without the obj namespace
            };
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
                FileAttributes attr = Ansible.IO.File.GetAttributes(absoluteTarget);
                if (attr.HasFlag(FileAttributes.Directory))
                    linkFlags = SYMBOLIC_LINK_FLAG_DIRECTORY;
                else
                    linkFlags = SYMBOLIC_LINK_FLAG_FILE;
            }
            catch (Exception e)
            {
                if (e is FileNotFoundException || e is DirectoryNotFoundException)
                    // Cannot determine link type based on the target as it does not exist, use dir if no extension is present otherwise file
                    linkFlags = Ansible.IO.Path.GetExtension(absoluteTarget) == "" ? SYMBOLIC_LINK_FLAG_DIRECTORY : SYMBOLIC_LINK_FLAG_FILE;
            }

            // Try and run with the new flag that allows non elevated processes to create symlinks
            // will return ERROR_INVALID_PARAMETER if on an unsupported host
            // added in Windows 10 build 14972
            linkFlags |= SYMBOLIC_LINK_FLAG_ALLOW_UNPRIVILEGED_CREATE;

            if (!NativeMethods.CreateSymbolicLinkW(linkPath, linkTarget, linkFlags))
            {
                int errorCode = Marshal.GetLastWin32Error();
                if (errorCode == 0x00000057)  // ERROR_INVALID_PARAMETER - try again without flag
                    if (!NativeMethods.CreateSymbolicLinkW(linkPath, linkTarget, linkFlags &= ~SYMBOLIC_LINK_FLAG_ALLOW_UNPRIVILEGED_CREATE))
                        errorCode = Marshal.GetLastWin32Error();
                    else
                        errorCode = 0;

                if (errorCode != 0)
                    throw new Win32Exception(String.Format("CreateSymbolicLinkW({0}, {1}, {2}) failed", linkPath, linkTarget, linkFlags));
            }
        }

        private static void CreateJunctionPoint(string linkPath, string linkTarget)
        {
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
            Ansible.IO.Directory.CreateDirectory(linkPath);

            // Open a handle to the new dir and write the reparse buffer data
            using (SafeFileHandle handle = NativeMethods.CreateFileW(linkPath, FileAccess.Write,
                FileShare.Read | FileShare.Write | FileShare.None, IntPtr.Zero, FileMode.Open,
                FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT, IntPtr.Zero))
            {
                if (handle.IsInvalid)
                    throw new Win32Exception(String.Format("CreateFile({0}) failed", linkPath));

                UInt32 bytesReturned;
                if (!NativeMethods.DeviceIoControl(handle, FSCTL_SET_REPARSE_POINT, ref buffer,
                    reparseHeaderSize + buffer.ReparseDataLength, IntPtr.Zero, 0, out bytesReturned, IntPtr.Zero))
                    throw new Win32Exception(String.Format("DeviceIoControl() failed to create junction point at {0} to {1}", linkPath, linkTarget));
            }
        }
    }
}
'@

Function Load-LinkUtils {
    <#
    .SYNOPSIS
    This is deprecated as Load is not a proper ps nouns and the verb should not
    be a plural. We will try and add a deprecation warning and call the proper
    cmdlet.
    #>
    if ((Get-Command -Name Add-DeprecationWarning -ErrorAction SilentlyContinue) -and (Get-Variable -Name result -ErrorAction SilentlyContinue)) {
        Add-DeprecationWarning -obj $result -message "Load-LinkUtils is deprecated in favour of Import-LinkUtil, this cmdlet will be removed in a future version" -version 2.11
    }
    Import-LinkUtil
}

Function Import-LinkUtil {
    <#
    .SYNOPSIS
    Compiles the C# code that can be used to manage links on Windows platforms.
    Once this function is called, the following cmdlets can be called

        Get-Link
        Remove-Link
        New-Link

    This module util is reliant on Ansible.ModuleUtils.PrivilegeUtil and
    Ansible.ModuleUtils.FileUtil. During the import it calls Import-FileUtil
    so a manual call to that is not necessary.
    #>
    # build the C# code to compile
    $namespaces = $ansible_privilege_util_namespaces + $ansible_file_util_namespaces + $ansible_link_util_namespaces | Select-Object -Unique
    $namespace_import = ($namespaces | ForEach-Object { "using $_;" }) -join "`r`n"

    $link_util = $ansible_link_util_code.Split([String[]]@("`r`n", "`r", "`n"), [System.StringSplitOptions]::None)
    $link_util_code = "$($link_util[0])`r`n`r`n$($link_util[1])`r`n`r`n$ansible_privilege_util_code`r`n`r`n$ansible_file_util_code`r`n`r`n$($link_util[2..$link_util.Length] -join "`r`n")"

    $platform_util = "$namespace_import`r`n`r`n$link_util_code"

    # FUTURE: find a better way to get the _ansible_remote_tmp variable
    $original_tmp = $env:TMP

    $remote_tmp = $original_tmp
    $module_params = Get-Variable -Name complex_args -ErrorAction SilentlyContinue
    if ($module_params) {
        if ($module_params.Value.ContainsKey("_ansible_remote_tmp") ) {
            $remote_tmp = $module_params.Value["_ansible_remote_tmp"]
            $remote_tmp = [System.Environment]::ExpandEnvironmentVariables($remote_tmp)
        }
    }

    $env:TMP = $remote_tmp
    Add-Type -TypeDefinition $platform_util
    $env:TMP = $original_tmp

    # cmdlets below call the Ansible.ModuleUtils.FileUtil namespace directly
    # so we also load that here
    Import-FileUtil
}

Function Get-Link($link_path) {
    <#
    .SYNOPSIS
    Returns a Ansible.LinkUtil.LinkInfo object that contains information
    about the file/dir specified by $link_path. This contains info such as
    the target of the link.
    #>
    $link_info = [Ansible.LinkUtil.Links]::GetLinkInfo($link_path)
    return $link_info
}

Function Remove-Link($link_path) {
    <#
    .SYNOPSIS
    Removes the file/dir specified by $link_path. This works with broken links
    unlike Remote-Item.
    #>
    [Ansible.LinkUtil.Links]::DeleteLink($link_path)
}

Function New-Link($link_path, $link_target, $link_type) {   
    <#
    .SYNOPSIS
    Creates a symbolic link, junction point, or hard link at the path specified
    by $link_path. The valid types at 'link', 'junction', or 'hard'.
    #>
    switch($link_type) {
        "link" {
            $type = [Ansible.LinkUtil.LinkType]::SymbolicLink
        }
        "junction" {
            if ([Ansible.IO.File]::Exists($link_target)) {
                throw "cannot set the target for a junction point to a file"
            }
            $type = [Ansible.LinkUtil.LinkType]::JunctionPoint
        }
        "hard" {
            if ([Ansible.IO.Directory]::Exists($link_target)) {
                throw "cannot set the target for a hard link to a directory"
            } elseif (-not ([Ansible.IO.File]::Exists($link_target))) {
                throw "link_target '$link_target' does not exist, cannot create hard link"
            }
            $type = [Ansible.LinkUtil.LinkType]::HardLink
        }
        default { throw "invalid link_type option $($link_type): expecting link, junction, hard" }
    }
    [Ansible.LinkUtil.Links]::CreateLink($link_path, $link_target, $type)
}

# this line must stay at the bottom to ensure all defined module parts are exported
Export-ModuleMember -Function Import-LinkUtil, Load-LinkUtils, Get-Link, Remove-Link, New-Link `
    -Variable ansible_link_util_code, ansible_link_util_namespaces
