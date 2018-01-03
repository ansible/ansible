# Copyright (c) 2017 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

# Replacement for the below classes that support paths that are greater than 260 chars
# See each URL for a list of method/properties that are supported
#     System.IO.File - https://msdn.microsoft.com/en-us/library/system.io.file(v=vs.110).aspx
#     System.IO.FileInfo - https://msdn.microsoft.com/en-us/library/system.io.fileinfo(v=vs.110).aspx
#     System.IO.Directory - https://msdn.microsoft.com/en-us/library/system.io.directory(v=vs.110).aspx
#     System.IO.DirectoryInfo - https://msdn.microsoft.com/en-us/library/system.io.directoryinfo(v=vs.110).aspx
#
# To use, make sure this function is called and then it can be used like
#     $dir = New-Object -TypeName Ansible.IO.DirectoryInfo -ArgumentList "\\?\C:\temp"
#     [Ansible.IO.Directory]::CreateDirectory("\\?\C:\temp")
# You can also use a normal path like "C:\temp" as you would normally with the System.IO.*
# classes but they are still subjectr to the restriction of 260 characters in the path
Function Load-FileUtilFunctions {
    $file_util = @"
using Microsoft.Win32.SafeHandles;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Text;

namespace Ansible.IO
{
    internal static class Win32Errors
    {

        public const UInt32 ERROR_SUCCESS = 0;
        public const UInt32 ERROR_FILE_NOT_FOUND = 2;
        public const UInt32 ERROR_PATH_NOT_FOUND = 3;
        public const UInt32 ERROR_NO_MORE_FILES = 18;
        public const UInt32 ERROR_FILE_EXISTS = 80;
        public const UInt32 ERROR_DIR_NOT_EMPTY = 145;
        public const UInt32 ERROR_ALREADY_EXISTS = 183;
    }

    internal class Win32Exception : System.ComponentModel.Win32Exception
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

    public class NativeHelpers
    {
        public enum GET_FILEEX_INFO_LEVELS
        {
            GetFileExInfoStandard,
            GetFileExMaxInfoLevel
        }

        public enum SE_OBJECT_TYPE
        {
            SE_UNKNOWN_OBJECT_TYPE = 0,
            SE_FILE_OBJECT,
            SE_SERVICE,
            SE_PRINTER,
            SE_REGISTRY_KEY,
            SE_LMSHARE,
            SE_KERNEL_OBJECT,
            SE_WINDOW_OBJECT,
            SE_DS_OBJECT,
            SE_DS_OBJECT_ALL,
            SE_PROVIDER_DEFINED_OBJECT,
            SE_WMIGUID_OBJECT,
            SE_REGISTRY_WOW64_32KEY
        }

        [Flags]
        public enum SECURITY_INFORMATION : uint
        {
            NONE = 0x00000000,
            OWNER_SECURITY_INFORMATION = 0x00000001,
            GROUP_SECURITY_INFORMATION = 0x00000002,
            DACL_SECURITY_INFORMATION = 0x00000004,
            SACL_SECURITY_INFORMATION = 0x00000008,
            UNPROTECTED_SACL_SECURITY_INFORMATION = 0x10000000,
            UNPROTECTED_DACL_SECURITY_INFORMATION = 0x20000000,
            PROTECTED_SACL_SECURITY_INFORMATION = 0x40000000,
            PROTECTED_DACL_SECURITY_INFORMATION = 0x80000000
        }

        [Flags]
        public enum FlagsAndAttributes : uint
        {
            NONE = 0x00000000,
            FILE_ATTRIBUTE_READONLY = 0x00000001,
            FILE_ATTRIBUTE_HIDDEN = 0x00000002,
            FILE_ATTRIBUTE_SYSTEM = 0x00000004,
            FILE_ATTRIBUTE_ARCHIVE = 0x00000020,
            FILE_ATTRIBUTE_NORMAL = 0x00000080,
            FILE_ATTRIBUTE_TEMPORARY = 0x00000100,
            FILE_ATTRIBUTE_OFFLINE = 0x00001000,
            FILE_ATTRIBUTE_ENCRYPTED = 0x00004000,
            FILE_FLAG_OPEN_NO_RECALL = 0x00100000,
            FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000,
            FILE_FLAG_SESSION_AWARE = 0x00800000,
            FILE_FLAG_BACKUP_SEMANTICS = 0x02000000,
            FILE_FLAG_DELETE_ON_CLOSE = 0x04000000,
            FILE_FLAG_SEQUENTIAL_SCAN = 0x08000000,
            FILE_FLAG_RANDOM_ACCESS = 0x10000000,
            FILE_FLAG_NO_BUFFERING = 0x20000000,
            FILE_FLAG_OVERLAPPED = 0x40000000,
            FILE_FLAG_WRITE_THROUGH = 0x80000000,
        }

        [Flags]
        public enum SECURITY_DESCRIPTOR_CONTROL : uint
        {
            SE_NONE = 0x0000,
            SE_OWNER_DEFAULTED = 0x0001,
            SE_GROUP_DEFAULTED = 0x0002,
            SE_DACL_PRESENT = 0x0004,
            SE_DACL_DEFAULTED = 0x0008,
            SE_SACL_DEFAULTED = 0x0008,
            SE_SACL_PRESENT = 0x0010,
            SE_DACL_AUTO_INHERIT_REQ = 0x0100,
            SE_SACL_AUTO_INHERIT_REQ = 0x0200,
            SE_DACL_AUTO_INHERITED = 0x0400,
            SE_SACL_AUTO_INHERITED = 0x0800,
            SE_DACL_PROTECTED = 0x1000,
            SE_SACL_PROTECTED = 0x2000,
            SE_RM_CONTROL_VALID = 0x4000,
            SE_SELF_RELATIVE = 0x8000,
        }

        [Flags]
        public enum MoveFlags : uint
        {
            MOVEFILE_NONE = 0x00,
            MOVEFILE_REPLACE_EXISTING = 0x01,
            MOVEFILE_COPY_ALLOWED = 0x02,
            MOVEFILE_DELAY_UNTIL_REBOOT = 0x04,
            MOVEFILE_WRITE_THROUGH = 0x08,
            MOVEFILE_CREATE_HARDLINK = 0x10,
            MOVEFILE_FAIL_IF_NOT_TRACKABLE = 0x20,
        }

        [Flags]
        public enum ReplaceFlags : uint
        {
            REPLACEFILE_WRITE_THROUGH = 0x00000001,
            REPLACEFILE_IGNORE_MERGE_ERRORS = 0x00000002,
            REAPLCEFILE_IGNORE_ACL_ERRORS = 0x00000004,
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct FILETIME
        {
            private UInt32 dwLowDateTime;
            private UInt32 dwHighDateTime;

            public static implicit operator long(FILETIME v) { return v.ToLong(); }
            public long ToLong() { return (long)this.dwHighDateTime << 32 | (long)this.dwLowDateTime; }
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct WIN32_FILE_ATTRIBUTE_DATA
        {
            public FileAttributes dwFileAttributes;
            public FILETIME ftCreationTime;
            public FILETIME ftLastAccessTime;
            public FILETIME ftLastWriteTime;
            public UInt32 nFileSizeHigh;
            public UInt32 nFileSizeLow;
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
        public struct WIN32_FIND_DATA
        {
            public FileAttributes dwFileAttributes;
            public FILETIME ftCreationTime;
            public FILETIME ftLastAccessTime;
            public FILETIME ftLastWriteTime;
            public UInt32 nFileSizeHigh;
            public UInt32 nFileSizeLow;
            public UInt32 dwReserved0;
            public UInt32 dwReserved1;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)] public string cFileName;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 14)] public string cAlternateFileName;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct LUID
        {
            public UInt32 LowPart;
            public UInt32 HighPart;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct TOKEN_PRIVILEGES
        {
            public UInt32 PrivilegeCount;
            public LUID Luid;
            public UInt32 Attributes;
        }

        [StructLayout(LayoutKind.Sequential)]
        public class SecurityAttributes : IDisposable
        {
            public UInt32 nLength = 0;
            public IntPtr lpSecurityDescriptor = IntPtr.Zero;
            public bool bInheritHandle = false;

            public SecurityAttributes(ObjectSecurity securityDescriptor)
            {
                if (securityDescriptor != null)
                {
                    byte[] secDesc = securityDescriptor.GetSecurityDescriptorBinaryForm();
                    nLength = (UInt32)secDesc.Length;
                    lpSecurityDescriptor = Marshal.AllocHGlobal(secDesc.Length);
                    Marshal.Copy(secDesc, 0, lpSecurityDescriptor, secDesc.Length);
                }
            }

            public void Dispose()
            {
                if (lpSecurityDescriptor != IntPtr.Zero)
                    Marshal.FreeHGlobal(lpSecurityDescriptor);
                GC.SuppressFinalize(this);
            }
            ~SecurityAttributes() { Dispose(); }
        }
    }

    internal class NativeMethods
    {
        [DllImport("advapi32.dll", SetLastError = true)]
        internal static extern bool AdjustTokenPrivileges(
            IntPtr TokenHandle,
            [MarshalAs(UnmanagedType.Bool)] bool DisableAllPrivileges,
            ref NativeHelpers.TOKEN_PRIVILEGES NewState,
            UInt32 BufferLength,
            IntPtr PreviousState,
            IntPtr ReturnLength);

        [DllImport("kernel32.dll")]
        internal static extern bool CloseHandle(
            IntPtr hObject);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool CopyFileW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpExistingFileName,
            [MarshalAs(UnmanagedType.LPWStr)] string lpNewFileName,
            [MarshalAs(UnmanagedType.Bool)] bool bFailIfExists);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool CreateDirectoryW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpPathName,
            NativeHelpers.SecurityAttributes lpSecurityAttributes);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern SafeFileHandle CreateFileW(
             [MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
             [MarshalAs(UnmanagedType.U4)] FileSystemRights dwDesiredAccess,
             [MarshalAs(UnmanagedType.U4)] FileShare dwShareMode,
             NativeHelpers.SecurityAttributes lpSecurityAttributes,
             [MarshalAs(UnmanagedType.U4)] FileMode dwCreationDisposition,
             NativeHelpers.FlagsAndAttributes dwFlagsAndAttributes,
             IntPtr hTemplateFile);

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool DecryptFileW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
            UInt32 dwReserved);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool DeleteFileW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpFileName);

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool EncryptFileW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpFileName);

        [DllImport("kernel32.dll", SetLastError = true)]
        internal static extern bool FindClose(
            IntPtr hFindFile);

        [DllImport("kernel32", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern IntPtr FindFirstFileW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
            out NativeHelpers.WIN32_FIND_DATA lpFindFileData);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool FindNextFileW(
            IntPtr hFindFile,
            out NativeHelpers.WIN32_FIND_DATA lpFindFIleData);

        [DllImport("kernel32.dll")]
        internal static extern IntPtr GetCurrentProcess();

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool GetFileAttributesExW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
            NativeHelpers.GET_FILEEX_INFO_LEVELS fInfoLevelId,
            out NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA lpFileInformation);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern UInt32 GetFullPathNameW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
            UInt32 nBufferLength,
            StringBuilder lpBuffer,
            out IntPtr lpFilePart);

        [DllImport("advapi32.dll", CharSet = CharSet.Unicode)]
        internal static extern UInt32 GetNamedSecurityInfoW(
            [MarshalAs(UnmanagedType.LPWStr)] string pObjectName,
            NativeHelpers.SE_OBJECT_TYPE ObjectType,
            NativeHelpers.SECURITY_INFORMATION SecurityInfo,
            out IntPtr ppsidOwner,
            out IntPtr ppsidGroup,
            out IntPtr ppDacl,
            out IntPtr ppSacl,
            out IntPtr ppSecurityDescriptor);

        [DllImport("advapi32.dll")]
        internal static extern UInt32 GetSecurityDescriptorLength(
            IntPtr pSecurityDescriptor);

        [DllImport("advapi32.dll", SetLastError = true)]
        internal static extern bool GetSecurityDescriptorControl(
            IntPtr pSecurityDescriptor,
            out NativeHelpers.SECURITY_DESCRIPTOR_CONTROL pControl,
            out UInt32 lpdwRevision);

        [DllImport("advapi32.dll", SetLastError = true)]
        internal static extern bool GetSecurityDescriptorDacl(
            IntPtr pSecurityDescriptor,
            [MarshalAs(UnmanagedType.Bool)] out bool lpbDaclPresent,
            out IntPtr pDacl,
            [MarshalAs(UnmanagedType.Bool)] out bool lpbDaclDefaulted);

        [DllImport("advapi32.dll", SetLastError = true)]
        internal static extern bool GetSecurityDescriptorGroup(
            IntPtr pSecurityDescriptor,
            out IntPtr pGroup,
            [MarshalAs(UnmanagedType.Bool)] out bool lpbGroupDefaulted);

        [DllImport("advapi32.dll", SetLastError = true)]
        internal static extern bool GetSecurityDescriptorOwner(
            IntPtr pSecurityDescriptor,
            out IntPtr pOwner,
            [MarshalAs(UnmanagedType.Bool)] out bool lpbOwnerDefaulted);

        [DllImport("advapi32.dll", SetLastError = true)]
        internal static extern bool GetSecurityDescriptorSacl(
            IntPtr pSecurityDescriptor,
            [MarshalAs(UnmanagedType.Bool)] out bool lpbSaclPresent,
            out IntPtr pSacl,
            [MarshalAs(UnmanagedType.Bool)] out bool lpbSaclDefaulted);

        [DllImport("kernel32.dll")]
        internal static extern IntPtr LocalFree(
            IntPtr hMem);

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool LookupPrivilegeValueW(
            string lpSystemName,
            string lpName,
            [MarshalAs(UnmanagedType.Struct)] out NativeHelpers.LUID lpLuid);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool MoveFileExW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpExistingFileName,
            [MarshalAs(UnmanagedType.LPWStr)] string lpNewFileName,
            NativeHelpers.MoveFlags dwFlags);

        [DllImport("advapi32.dll", SetLastError = true)]
        internal static extern bool OpenProcessToken(
            IntPtr ProcessHandle,
            UInt32 DesiredAccess,
            out IntPtr TokenHandle);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool ReplaceFileW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpReplacedFileName,
            [MarshalAs(UnmanagedType.LPWStr)] string lpReplacementFileName,
            [MarshalAs(UnmanagedType.LPWStr)] string lpBackupFileName,
            NativeHelpers.ReplaceFlags dwReplaceFlags,
            IntPtr lpExclude,
            IntPtr lpReserved);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool SetFileAttributesW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
            FileAttributes dwFileAttributes);

        [DllImport("kernel32.dll", SetLastError = true)]
        internal static extern bool SetFileTime(
            SafeFileHandle hFile,
            ref long lpCreationTime,
            ref long lpLastAccessTime,
            ref long lpLastWriteTime);

        [DllImport("advapi32.dll")]
        internal static extern UInt32 SetNamedSecurityInfoW(
            [MarshalAs(UnmanagedType.LPWStr)] string pObjectName,
            NativeHelpers.SE_OBJECT_TYPE objectType,
            NativeHelpers.SECURITY_INFORMATION securityInfo,
            IntPtr pSidOwner,
            IntPtr pSidGroup,
            IntPtr pDacl,
            IntPtr pSacl);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool RemoveDirectoryW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpPathName);
    }

    public static class Privileges
    {
        public static void EnablePrivilege(string privilege)
        {
            NativeHelpers.TOKEN_PRIVILEGES tkpPrivileges;
            IntPtr hToken;
            // Open Process Token with TOKEN_ADJUST_PRIVILEGES 0x20 and TOKEN_QUERY 0x8
            if (!NativeMethods.OpenProcessToken(NativeMethods.GetCurrentProcess(), 0x20 | 0x8, out hToken))
                throw new Win32Exception("OpenProcessToken() failed");

            try
            {
                NativeHelpers.LUID luid;
                if (!NativeMethods.LookupPrivilegeValueW(null, privilege, out luid))
                    throw new Win32Exception(String.Format("LookupPrivilegeValueW({0}) failed", privilege));

                tkpPrivileges.PrivilegeCount = 1;
                tkpPrivileges.Luid = luid;
                tkpPrivileges.Attributes = 0x00000002; // SE_PRIVILEGE_ENABLED

                if (!NativeMethods.AdjustTokenPrivileges(hToken, false, ref tkpPrivileges, 0, IntPtr.Zero, IntPtr.Zero))
                    throw new Win32Exception("AdjustTokenPrivileges() failed");
            }
            finally
            {
                NativeMethods.CloseHandle(hToken);
            }
        }
    }

    public abstract class FileSystemInfo : MarshalByRefObject
    {
        #region Fields
        internal bool IsInitialized = false;
        internal NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA Win32AttributeData;
        internal string OriginalPath;
        internal string FullPath;
        #endregion // Fields

        #region Properties
        public FileAttributes Attributes
        {
            get {
                RefreshIfNotInitialized();
                return Win32AttributeData.dwFileAttributes;
            }
            set
            {
                if (!NativeMethods.SetFileAttributesW(FullPath, value))
                    throw new Win32Exception(String.Format("SetFileAttributesW({0}) failed", FullPath));
            }
        }

        public DateTime CreationTime
        {
            get { return CreationTimeUtc.ToLocalTime(); }
            set { CreationTimeUtc = value.ToUniversalTime(); }
        }

        public DateTime CreationTimeUtc
        {
            get
            {
                RefreshIfNotInitialized();
                return DateTime.FromFileTimeUtc(Win32AttributeData.ftCreationTime);
            }
            set { SetFileTime(FullPath, value, null, null); }
        }

        public abstract bool Exists { get; }

        public string Extension
        {
            get { return System.IO.Path.GetExtension(FullPath); }
        }

        public string FullName
        {
            get { return FullPath; }
        }

        public DateTime LastAccessTime
        {
            get { return LastAccessTimeUtc.ToLocalTime(); }
            set { LastAccessTimeUtc = value.ToUniversalTime(); }
        }

        public DateTime LastAccessTimeUtc
        {
            get
            {
                RefreshIfNotInitialized();
                return DateTime.FromFileTimeUtc(Win32AttributeData.ftLastAccessTime);
            }
            set { SetFileTime(FullPath, null, value, null); }
        }

        public DateTime LastWriteTime
        {
            get { return LastWriteTimeUtc.ToLocalTime(); }
            set { LastWriteTimeUtc = value.ToUniversalTime(); }
        }

        public DateTime LastWriteTimeUtc
        {
            get
            {
                RefreshIfNotInitialized();
                return DateTime.FromFileTimeUtc(Win32AttributeData.ftLastWriteTime);
            }
            set { SetFileTime(FullPath, null, null, value); }
        }

        public abstract string Name { get; }
        #endregion // Properties

        #region Methods
        public abstract void Delete();

        protected void RefreshIfNotInitialized()
        {
            if (!IsInitialized)
                Refresh();
        }

        public void Refresh()
        {
            Win32AttributeData = GetFileAttributes(FullPath);
            IsInitialized = true;
        }

        internal void Initialize(string path, bool isDirectory)
        {
            OriginalPath = path;

            UInt32 bufferLength = 0;
            StringBuilder lpBuffer = new StringBuilder(0);
            IntPtr lpFilePart = IntPtr.Zero;
            UInt32 returnLength = NativeMethods.GetFullPathNameW(path, bufferLength, lpBuffer, out lpFilePart);
            if (returnLength == 0)
                throw new Win32Exception(String.Format("GetFullPathName({0}) failed when getting buffer size", path));

            lpBuffer.EnsureCapacity((int)returnLength);
            returnLength = NativeMethods.GetFullPathNameW(path, returnLength, lpBuffer, out lpFilePart);
            if (returnLength == 0)
                throw new Win32Exception(String.Format("GetFullPathName({0}, {1}) failed when getting full path", path, returnLength));
            FullPath = lpBuffer.ToString();
        }

        // Custom Methods
        public static void Copy(string source, string target, bool failIfExists)
        {
            if (!NativeMethods.CopyFileW(source, target, failIfExists))
                throw new Win32Exception(String.Format("CopyFileW failed to copy {0} to {1}", source, target));
        }

        public static T GetAcl<T>(string path, AccessControlSections includeSections) where T : ObjectSecurity, new()
        {
            NativeHelpers.SECURITY_INFORMATION secInfo = NativeHelpers.SECURITY_INFORMATION.NONE;
            if ((includeSections & AccessControlSections.Access) != 0)
                secInfo |= NativeHelpers.SECURITY_INFORMATION.DACL_SECURITY_INFORMATION;
            if ((includeSections & AccessControlSections.Audit) != 0)
            {
                secInfo |= NativeHelpers.SECURITY_INFORMATION.SACL_SECURITY_INFORMATION;
                Ansible.IO.Privileges.EnablePrivilege("SeSecurityPrivilege");
            }
            if ((includeSections & AccessControlSections.Group) != 0)
                secInfo |= NativeHelpers.SECURITY_INFORMATION.GROUP_SECURITY_INFORMATION;
            if ((includeSections & AccessControlSections.Owner) != 0)
                secInfo |= NativeHelpers.SECURITY_INFORMATION.OWNER_SECURITY_INFORMATION;

            IntPtr pSidOwner, pSidGroup, pDacl, pSacl, pSecurityDescriptor = IntPtr.Zero;
            UInt32 res = NativeMethods.GetNamedSecurityInfoW(path, NativeHelpers.SE_OBJECT_TYPE.SE_FILE_OBJECT, secInfo,
                out pSidOwner, out pSidGroup, out pDacl, out pSacl, out pSecurityDescriptor);
            if (res != Win32Errors.ERROR_SUCCESS)
                throw new Win32Exception((int)res, String.Format("GetNamedSecurityInfoW({0}) failed", path));

            var acl = new T();
            try
            {
                UInt32 length = NativeMethods.GetSecurityDescriptorLength(pSecurityDescriptor);
                byte[] securityDescriptor = new byte[length];
                Marshal.Copy(pSecurityDescriptor, securityDescriptor, 0, (int)length);
                acl.SetSecurityDescriptorBinaryForm(securityDescriptor);
            }
            finally
            {
                NativeMethods.LocalFree(pSecurityDescriptor);
            }

            return acl;
        }

        public static string GetDirectoryName(string path)
        {
            // return null if path is null or if the path denotes a root directory
            if (path == null)
                return null;

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

        public static string GetPathRoot(string path)
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

        public static NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA GetFileAttributes(string path)
        {
            NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA attrData = new NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA();
            if (!NativeMethods.GetFileAttributesExW(path, NativeHelpers.GET_FILEEX_INFO_LEVELS.GetFileExInfoStandard, out attrData))
            {
                int lastErr = Marshal.GetLastWin32Error();
                if ((uint)lastErr == Win32Errors.ERROR_FILE_NOT_FOUND || (uint)lastErr == Win32Errors.ERROR_PATH_NOT_FOUND)
                    attrData.dwFileAttributes = (FileAttributes)(-1);
                else
                    throw new Win32Exception(String.Format("GetFileAttributesExW({0}) failed", path));
            }
            return attrData;
        }

        public static void Move(string sourcePath, string targetPath)
        {
            NativeHelpers.MoveFlags moveFlags = NativeHelpers.MoveFlags.MOVEFILE_WRITE_THROUGH;
            if (!NativeMethods.MoveFileExW(sourcePath, targetPath, moveFlags))
                throw new Win32Exception(String.Format("MoveFileExW() failed to copy {0} to {1}", sourcePath, targetPath));
        }

        public static void SetAcl(string path, ObjectSecurity objectSecurity)
        {
            byte[] securityInfoBytes = objectSecurity.GetSecurityDescriptorBinaryForm();
            IntPtr securityInfo = Marshal.AllocHGlobal(securityInfoBytes.Length);
            Marshal.Copy(securityInfoBytes, 0, securityInfo, securityInfoBytes.Length);
            try
            {
                NativeHelpers.SECURITY_INFORMATION securityInformation = NativeHelpers.SECURITY_INFORMATION.NONE;

                NativeHelpers.SECURITY_DESCRIPTOR_CONTROL control;
                UInt32 lpdwRevision;
                if (!NativeMethods.GetSecurityDescriptorControl(securityInfo, out control, out lpdwRevision))
                    throw new Win32Exception("GetSecurityDescriptorControl() failed");

                IntPtr pDacl = IntPtr.Zero;
                bool daclPresent, daclDefaulted;
                if (!NativeMethods.GetSecurityDescriptorDacl(securityInfo, out daclPresent, out pDacl, out daclDefaulted))
                    throw new Win32Exception("GetSecurityDescriptorDacl() failed");
                if (daclPresent)
                {
                    securityInformation |= NativeHelpers.SECURITY_INFORMATION.DACL_SECURITY_INFORMATION;
                    securityInformation |= (control & NativeHelpers.SECURITY_DESCRIPTOR_CONTROL.SE_DACL_PROTECTED) != 0
                        ? NativeHelpers.SECURITY_INFORMATION.PROTECTED_DACL_SECURITY_INFORMATION
                        : NativeHelpers.SECURITY_INFORMATION.UNPROTECTED_DACL_SECURITY_INFORMATION;
                }

                IntPtr pGroup = IntPtr.Zero;
                bool groupDefaulted;
                if (!NativeMethods.GetSecurityDescriptorGroup(securityInfo, out pGroup, out groupDefaulted))
                    throw new Win32Exception("GetSecurityDescriptorGroup() failed");
                if (pGroup != IntPtr.Zero)
                    securityInformation |= NativeHelpers.SECURITY_INFORMATION.GROUP_SECURITY_INFORMATION;

                IntPtr pOwner = IntPtr.Zero;
                bool ownerDefaulted;
                if (!NativeMethods.GetSecurityDescriptorOwner(securityInfo, out pOwner, out ownerDefaulted))
                    throw new Win32Exception("GetSecurityDescriptorOwner() failed");
                if (pOwner != IntPtr.Zero)
                    securityInformation |= NativeHelpers.SECURITY_INFORMATION.OWNER_SECURITY_INFORMATION;

                IntPtr pSacl = IntPtr.Zero;
                bool saclPresent, saclDefaulted;
                if (!NativeMethods.GetSecurityDescriptorSacl(securityInfo, out saclPresent, out pSacl, out saclDefaulted))
                    throw new Win32Exception("GetSecurityDescriptorSacl() failed");
                if (saclPresent)
                {
                    securityInformation |= NativeHelpers.SECURITY_INFORMATION.SACL_SECURITY_INFORMATION;
                    securityInformation |= (control & NativeHelpers.SECURITY_DESCRIPTOR_CONTROL.SE_SACL_PROTECTED) != 0
                        ? NativeHelpers.SECURITY_INFORMATION.PROTECTED_SACL_SECURITY_INFORMATION
                        : NativeHelpers.SECURITY_INFORMATION.UNPROTECTED_SACL_SECURITY_INFORMATION;
                    Ansible.IO.Privileges.EnablePrivilege("SeSecurityPrivilege");
                }

                UInt32 res = NativeMethods.SetNamedSecurityInfoW(path, NativeHelpers.SE_OBJECT_TYPE.SE_FILE_OBJECT, securityInformation, pOwner, pGroup, pDacl, pSacl);
                if (res != Win32Errors.ERROR_SUCCESS)
                    throw new Win32Exception((int)res, String.Format("SetNamedSecurityInfoW({0}) failed", path));
            }
            finally
            {
                Marshal.FreeHGlobal(securityInfo);
            }
        }

        public static void SetFileTime(string path, DateTime? creationTime, DateTime? lastAccessTime, DateTime? lastWriteTime)
        {
            SafeFileHandle fileHandle = NativeMethods.CreateFileW(path, FileSystemRights.WriteAttributes, FileShare.Delete | FileShare.Write,
                null, FileMode.Open, NativeHelpers.FlagsAndAttributes.FILE_FLAG_BACKUP_SEMANTICS, IntPtr.Zero);
            if (fileHandle.IsInvalid)
                throw new Win32Exception(String.Format("CreateFileW({0}) failed", path));

            try
            {
                long creation = creationTime.HasValue ? creationTime.Value.ToFileTimeUtc() : (long)0;
                long access = lastAccessTime.HasValue ? lastAccessTime.Value.ToFileTimeUtc() : (long)0;
                long write = lastWriteTime.HasValue ? lastWriteTime.Value.ToFileTimeUtc() : (long)0;

                if (!NativeMethods.SetFileTime(fileHandle, ref creation, ref access, ref write))
                    throw new Win32Exception(String.Format("SetFileTime() for file {0} failed", path));
            }
            finally
            {
                fileHandle.Close();
            }
        }

        public override string ToString() { return OriginalPath; }
        #endregion // Methods
    }

    public static class File
    {
        private static Encoding DefaultEncoding = Encoding.UTF8;
        private static int DefaultBuffer = 4096;

        public static void AppendAllLines(string path, IEnumerable<string> contents) { AppendAllLines(path, contents, DefaultEncoding); }
        public static void AppendAllLines(string path, IEnumerable<string> contents, Encoding encoding)
        {
            using (StreamWriter writer = AppendText(path))
            {
                foreach (string content in contents)
                    writer.Write(content);
            }
        }
        public static void AppendAllText(string path, string contents) { AppendAllText(path, contents, DefaultEncoding); }
        public static void AppendAllText(string path, string contents, Encoding encoding)
        {
            using (StreamWriter writer = AppendText(path))
            {
                writer.Write(contents);
            }
        }
        public static StreamWriter AppendText(string path) { return AppendText(path, DefaultEncoding); }
        public static StreamWriter AppendText(string path, Encoding encoding)
        {
            FileStream fs = File.Open(path, FileMode.OpenOrCreate, FileAccess.Write);
            try
            {
                fs.Seek(0, SeekOrigin.End);
                return new StreamWriter(fs, encoding);
            }
            catch
            {
                fs.Close();
                throw;
            }
        }
        public static void Copy(string sourceFileName, string destFileName) { Copy(sourceFileName, destFileName, false); }
        public static void Copy(string sourceFileName, string destFileName, bool overwrite) { FileSystemInfo.Copy(sourceFileName, destFileName, !overwrite); }
        public static FileStream Create(string path) { return Open(path, FileMode.Create, FileAccess.ReadWrite); }
        public static FileStream Create(string path, int bufferSize) { return Open(path, FileMode.Create, FileAccess.ReadWrite, FileShare.None, bufferSize, FileOptions.None); }
        public static FileStream Create(string path, int bufferSize, FileOptions options) { return Open(path, FileMode.Create, FileAccess.ReadWrite, FileShare.None, bufferSize, options); }
        public static FileStream Create(string path, int bufferSize, FileOptions options, FileSecurity fileSecurity)
        {
            SafeFileHandle fileHandle = CreateFileHandle(path, FileMode.Create, FileAccess.ReadWrite, FileShare.None, options, fileSecurity);
            try
            {
                return new FileStream(fileHandle, FileAccess.ReadWrite, DefaultBuffer, options.HasFlag(FileOptions.Asynchronous));
            }
            catch
            {
                fileHandle.Dispose();
                throw;
            }
        }
        public static StreamWriter CreateText(string path) { return new StreamWriter(Open(path, FileMode.Create, FileAccess.ReadWrite)); }
        public static void Decrypt(string path)
        {
            if (!NativeMethods.DecryptFileW(path, 0))
                throw new Win32Exception(String.Format("DecryptFileW({0}) failed", path));
        }
        public static void Delete(string path)
        {
            if (!NativeMethods.DeleteFileW(path))
                throw new Win32Exception(String.Format("DeleteFileW({0}) failed", path));
        }
        public static void Encrypt(string path)
        {
            if (!NativeMethods.EncryptFileW(path))
                throw new Win32Exception(String.Format("EncryptFIleW({0}) failed", path));
        }
        public static bool Exists(string path) { return new FileInfo(path).Exists; }
        public static FileSecurity GetAccessControl(string path) { return GetAccessControl(path, AccessControlSections.Access | AccessControlSections.Group | AccessControlSections.Owner); }
        public static FileSecurity GetAccessControl(string path, AccessControlSections includeSections) { return FileSystemInfo.GetAcl<FileSecurity>(path, includeSections); }
        public static FileAttributes GetAttributes(string path) { return FileSystemInfo.GetFileAttributes(path).dwFileAttributes; }
        public static DateTime GetCreationTime(string path) { return new FileInfo(path).CreationTime; }
        public static DateTime GetCreationTimeUtc(string path) { return new FileInfo(path).CreationTimeUtc; }
        public static DateTime GetLastAccessTime(string path) { return new FileInfo(path).LastAccessTime; }
        public static DateTime GetLastAccessTimeUtc(string path) { return new FileInfo(path).LastAccessTimeUtc; }
        public static DateTime GetLastWriteTime(string path) { return new FileInfo(path).LastWriteTime; }
        public static DateTime GetLastWriteTimeUtc(string path) { return new FileInfo(path).LastWriteTimeUtc; }
        public static void Move(string sourceFileName, string destFileName) { FileSystemInfo.Move(sourceFileName, destFileName); }
        public static FileStream Open(string path, FileMode mode) { return Open(path, mode, mode == FileMode.Append ? FileAccess.Write : FileAccess.ReadWrite, FileShare.None); }
        public static FileStream Open(string path, FileMode mode, FileAccess access) { return Open(path, mode, access, FileShare.None); }
        public static FileStream Open(string path, FileMode mode, FileAccess access, FileShare share) { return Open(path, mode, access, share, DefaultBuffer, FileOptions.None); }
        public static FileStream Open(string path, FileMode mode, FileAccess access, FileShare share, int bufferSize, FileOptions options)
        {
            SafeFileHandle fileHandle = CreateFileHandle(path, mode, access, share, options, null);
            try
            {
                return new FileStream(fileHandle, access, bufferSize, options.HasFlag(FileOptions.Asynchronous));
            }
            catch
            {
                fileHandle.Dispose();
                throw;
            }
        }
        public static FileStream OpenRead(string path) { return Open(path, FileMode.Open, FileAccess.Read); }
        public static StreamReader OpenText(string path) { return OpenText(path, DefaultEncoding); }
        public static StreamReader OpenText(string path, Encoding encoding) { return new StreamReader(OpenRead(path), encoding); }
        public static FileStream OpenWrite(string path) { return Open(path, FileMode.OpenOrCreate, FileAccess.Write); }
        public static byte[] ReadAllBytes(string path)
        {
            byte[] buffer = null;
            using (FileStream fs = OpenRead(path))
            {
                buffer = new byte[fs.Length];
                fs.Read(buffer, 0, (int)fs.Length);
            }
            return buffer;
        }
        public static string[] ReadAllLines(string path) { return ReadLines(path, DefaultEncoding).ToArray(); }
        public static string[] ReadAllLines(string path, Encoding encoding) { return ReadLines(path, encoding).ToArray(); }
        public static string ReadAllText(string path) { return ReadAllText(path, DefaultEncoding); }
        public static string ReadAllText(string path, Encoding encoding)
        {
            using (StreamReader reader = OpenText(path, encoding)) {
                return reader.ReadToEnd();
            }
        }
        public static IEnumerable<string> ReadLines(string path) { return ReadLines(path, DefaultEncoding); }
        public static IEnumerable<string> ReadLines(string path, Encoding encoding)
        {
            using (StreamReader reader = OpenText(path, encoding))
            {
                string line = null;
                while ((line = reader.ReadLine()) != null)
                    yield return line;
            }
        }
        public static void Replace(string sourceFileName, string destinationFileName, string destinationBackupFileName) { Replace(sourceFileName, destinationFileName, destinationBackupFileName, false); }
        public static void Replace(string sourceFileName, string destinationFileName, string destinationBackupFileName, bool ignoreMetadataErrors)
        {
            NativeHelpers.ReplaceFlags replaceFlags = ignoreMetadataErrors ? NativeHelpers.ReplaceFlags.REPLACEFILE_IGNORE_MERGE_ERRORS | NativeHelpers.ReplaceFlags.REAPLCEFILE_IGNORE_ACL_ERRORS : 0;
            if (!NativeMethods.ReplaceFileW(destinationFileName, sourceFileName, destinationBackupFileName, replaceFlags, IntPtr.Zero, IntPtr.Zero))
                throw new Win32Exception(String.Format("ReplaceFileW() failed to replace file {0} with {1} with the backup path {2}", destinationFileName, sourceFileName, destinationBackupFileName));
        }
        public static void SetAccessControl(string path, FileSecurity fileSecurity) { FileSystemInfo.SetAcl(path, fileSecurity); }
        public static void SetAttributes(string path, FileAttributes fileAttributes) { new FileInfo(path).Attributes = fileAttributes; }
        public static void SetCreationTime(string path, DateTime creationTime) { SetCreationTimeUtc(path, creationTime.ToUniversalTime()); }
        public static void SetCreationTimeUtc(string path, DateTime creationTimeUtc) { FileSystemInfo.SetFileTime(path, creationTimeUtc, null, null); }
        public static void SetLastAccessTime(string path, DateTime lastAccessTime) { SetLastAccessTimeUtc(path, lastAccessTime.ToUniversalTime()); }
        public static void SetLastAccessTimeUtc(string path, DateTime lastAccessTimeUtc) { FileSystemInfo.SetFileTime(path, null, lastAccessTimeUtc, null); }
        public static void SetLastWriteTime(string path, DateTime lastWriteTime) { SetLastWriteTimeUtc(path, lastWriteTime.ToUniversalTime()); }
        public static void SetLastWriteTimeUtc(string path, DateTime lastWriteTimeUtc) { FileSystemInfo.SetFileTime(path, null, null, lastWriteTimeUtc); }
        public static void WriteAllBytes(string path, byte[] bytes)
        {
            using (FileStream fs = Open(path, FileMode.Create, FileAccess.ReadWrite, FileShare.None))
            {
                fs.Write(bytes, 0, bytes.Length);
            }
        }
        public static void WriteAllLines(string path, IEnumerable<string> contents) { WriteAllLines(path, contents, DefaultEncoding); }
        public static void WriteAllLines(string path, IEnumerable<string> contents, Encoding encoding)
        {
            using (StreamWriter writer = WriteText(path, encoding))
            {
                foreach (string line in contents)
                {
                    writer.WriteLine(line);
                }
            }
        }
        public static void WriteAllLines(string path, string[] contents) { WriteAllLines(path, contents, DefaultEncoding); }
        public static void WriteAllLines(string path, string[] contents, Encoding encoding)
        {
            using (StreamWriter writer = WriteText(path, encoding))
            {
                foreach (string line in contents)
                {
                    writer.WriteLine(line);
                }
            }
        }
        public static void WriteAllText(string path, string contents) { WriteAllText(path, contents, DefaultEncoding); }
        public static void WriteAllText(string path, string contents, Encoding encoding)
        {
            using (StreamWriter writer = WriteText(path, encoding))
            {
                writer.Write(contents);
            }
        }
        public static StreamWriter WriteText(string path) { return WriteText(path, DefaultEncoding); }
        public static StreamWriter WriteText(string path, Encoding encoding) { return new StreamWriter(Open(path, FileMode.Create, FileAccess.ReadWrite, FileShare.None), encoding); }

        private static SafeFileHandle CreateFileHandle(string path, FileMode mode, FileAccess access, FileShare share, FileOptions options, FileSecurity fileSecurity)
        {
            FileSystemRights accessRights;
            if (access == FileAccess.Read)
                accessRights = FileSystemRights.Read;
            else if (access == FileAccess.Write)
                accessRights = FileSystemRights.WriteData;
            else
                accessRights = FileSystemRights.ReadData | FileSystemRights.WriteData;
            NativeHelpers.FlagsAndAttributes attr = (NativeHelpers.FlagsAndAttributes)options;
            NativeHelpers.SecurityAttributes secAttr = new NativeHelpers.SecurityAttributes(fileSecurity);
            if (fileSecurity != null)
                accessRights |= (FileSystemRights)0x01000000;  // ACCESS_SYSTEM_SECURITY - Bit 24

            SafeFileHandle fileHandle = NativeMethods.CreateFileW(path, accessRights, share, secAttr, mode, attr, IntPtr.Zero);
            secAttr.Dispose();
            if (fileHandle.IsInvalid)
                throw new Win32Exception(String.Format("CreateFileW({0}) failed", path));
            return fileHandle;
        }
    }

    public sealed class FileInfo : FileSystemInfo
    {
        #region Constructor
        public FileInfo(string path)
        {
            Initialize(path, false);
        }
        #endregion // Constructor

        #region Properties
        public DirectoryInfo Directory { get { return new Ansible.IO.DirectoryInfo(GetDirectoryName(FullPath)); } }
        public string DirectoryName { get { return GetDirectoryName(FullPath); } }
        public override bool Exists
        {
            get
            {
                try
                {
                    RefreshIfNotInitialized();
                    FileAttributes attr = Win32AttributeData.dwFileAttributes;
                    return (!attr.Equals((FileAttributes)(-1)) && !attr.HasFlag(FileAttributes.Directory));
                }
                catch
                {
                    return false;
                }
            }

        }
        public bool IsReadOnly
        {
            get
            {
                RefreshIfNotInitialized();
                return (Attributes & FileAttributes.ReadOnly) != 0;
            }
            set
            {
                if (value)
                    Attributes |= FileAttributes.ReadOnly;
                else
                    Attributes &= ~FileAttributes.ReadOnly;
            }
        }
        public long Length
        {
            get
            {
                RefreshIfNotInitialized();
                FileAttributes attr = Win32AttributeData.dwFileAttributes;
                if (attr.Equals((FileAttributes)(-1)))
                    throw new IOException("Failed to initialize file data");
                if (attr.HasFlag(FileAttributes.Directory))
                    throw new FileNotFoundException("Cannot get Length for a directory");
                return (long)Win32AttributeData.nFileSizeHigh << 32 | (long)Win32AttributeData.nFileSizeLow;
            }
        }
        public override string Name { get { return System.IO.Path.GetFileName(FullPath); } }
        #endregion // Properties

        #region Methods
        public StreamWriter AppendText() { return File.AppendText(FullPath); }
        public FileInfo CopyTo(string destFileName) { return CopyTo(destFileName, false); }
        public FileInfo CopyTo(string destFileName, bool overwrite) {
            File.Copy(FullPath, destFileName, overwrite);
            return new FileInfo(destFileName);
        }
        public FileStream Create() { return File.Create(FullPath); }
        public StreamWriter CreateText() { return File.CreateText(FullPath); }
        public void Decrypt() { File.Decrypt(FullPath); }
        public override void Delete() { File.Delete(FullPath); }
        public void Encrypt() { File.Encrypt(FullPath); }
        public FileSecurity GetAccessControl() { return GetAccessControl(AccessControlSections.Access | AccessControlSections.Group | AccessControlSections.Owner); }
        public FileSecurity GetAccessControl(AccessControlSections includeSelections) { return GetAcl<FileSecurity>(FullPath, includeSelections); }
        public void MoveTo(string destFileName) { File.Move(FullPath, destFileName); }
        public FileStream Open(FileMode mode) { return Open(mode, FileAccess.Read, FileShare.None); }
        public FileStream Open(FileMode mode, FileAccess access) { return Open(mode, access, FileShare.None); }
        public FileStream Open(FileMode mode, FileAccess access, FileShare share) { return File.Open(FullPath, mode, access, share); }
        public FileStream OpenRead() { return File.OpenRead(FullPath); }
        public StreamReader OpenText() { return File.OpenText(FullPath); }
        public FileStream OpenWrite() { return File.OpenWrite(FullPath); }
        public FileInfo Replace(string destinationFileName, string destinationBackupFileName) { return Replace(destinationFileName, destinationBackupFileName, false); }
        public FileInfo Replace(string destinationFileName, string destinationBackupFileName, bool ignoreMetadataErrors)
        {
            File.Replace(FullPath, destinationFileName, destinationBackupFileName, ignoreMetadataErrors);
            return new FileInfo(destinationFileName);
        }
        public void SetAccessControl(FileSecurity fileSecurity) { SetAcl(FullPath, fileSecurity); }
        #endregion // Methods
    }

    public static class Directory
    {
        public static void Copy(string sourceDirPath, string destDirPath) { FileSystemInfo.Copy(sourceDirPath, destDirPath, true); }
        public static void Copy(string sourceDirPath, string destDirPath, bool overwrite) { FileSystemInfo.Copy(sourceDirPath, destDirPath, !overwrite); }
        public static DirectoryInfo CreateDirectory(string path) { return CreateDirectory(path, null); }
        public static DirectoryInfo CreateDirectory(string path, DirectorySecurity directorySecurity)
        {
            Stack<string> dirsToCreate = new Stack<string>();
            string directoryRoot = FileSystemInfo.GetPathRoot(path);
            string dir = path;
            while (directoryRoot != dir)
            {
                if (Exists(dir))
                    break;
                dirsToCreate.Push(dir);
                dir = FileSystemInfo.GetDirectoryName(dir);
            }

            NativeHelpers.SecurityAttributes secAttr = new NativeHelpers.SecurityAttributes(directorySecurity);
            while (dirsToCreate.Count > 0)
            {
                dir = dirsToCreate.Pop();
                if (!NativeMethods.CreateDirectoryW(dir, secAttr))
                {
                    int lastErr = Marshal.GetLastWin32Error();
                    if (lastErr != Win32Errors.ERROR_ALREADY_EXISTS)
                    {
                        secAttr.Dispose();
                        throw new Win32Exception(lastErr, String.Format("CreateDirectoryW({0}) failed", dir));
                    }
                }
            }
            secAttr.Dispose();

            return new DirectoryInfo(path);
        }
        public static void Delete(string path) { Delete(path, false); }
        public static void Delete(string path, bool recursive)
        {
            if (recursive)
            {
                foreach (string filePath in EnumerateFileSystemEntries(path))
                {
                    FileAttributes fileAttributes = File.GetAttributes(filePath);
                    if (fileAttributes.HasFlag(FileAttributes.Directory))
                        Delete(filePath, true);
                    else
                        File.Delete(filePath);
                }
            }

            if (!NativeMethods.RemoveDirectoryW(path))
            {
                int lastErr = Marshal.GetLastWin32Error();
                if (lastErr != Win32Errors.ERROR_PATH_NOT_FOUND && lastErr != Win32Errors.ERROR_FILE_NOT_FOUND)
                    throw new Win32Exception(lastErr, String.Format("RemoveDirectoryW({0}) failed", path));
            }
        }
        public static IEnumerable<string> EnumerateDirectories(string path) { return EnumerateDirectories(path, "*", SearchOption.TopDirectoryOnly); }
        public static IEnumerable<string> EnumerateDirectories(string path, string searchPattern) { return EnumerateDirectories(path, searchPattern, SearchOption.TopDirectoryOnly); }
        public static IEnumerable<string> EnumerateDirectories(string path, string searchPattern, SearchOption searchOption) { return EnumerateFolder<string>(path, searchPattern, searchOption, true, false); }
        public static IEnumerable<string> EnumerateFiles(string path) { return EnumerateFiles(path, "*", SearchOption.TopDirectoryOnly); }
        public static IEnumerable<string> EnumerateFiles(string path, string searchPattern) { return EnumerateFiles(path, searchPattern, SearchOption.TopDirectoryOnly); }
        public static IEnumerable<string> EnumerateFiles(string path, string searchPattern, SearchOption searchOption) { return EnumerateFolder<string>(path, searchPattern, searchOption, false, true); }
        public static IEnumerable<string> EnumerateFileSystemEntries(string path) { return EnumerateFileSystemEntries(path, "*", SearchOption.TopDirectoryOnly); }
        public static IEnumerable<string> EnumerateFileSystemEntries(string path, string searchPattern) { return EnumerateFileSystemEntries(path, searchPattern, SearchOption.TopDirectoryOnly); }
        public static IEnumerable<string> EnumerateFileSystemEntries(string path, string searchPattern, SearchOption searchOption) { return EnumerateFolder<string>(path, searchPattern, searchOption, true, true); }
        public static bool Exists(string path) { return new DirectoryInfo(path).Exists; }
        public static DirectorySecurity GetAccessControl(string path) { return GetAccessControl(path, AccessControlSections.Access | AccessControlSections.Group | AccessControlSections.Owner); }
        public static DirectorySecurity GetAccessControl(string path, AccessControlSections includeSelections) { return FileSystemInfo.GetAcl<DirectorySecurity>(path, includeSelections); }
        public static DateTime GetCreationTime(string path) { return new DirectoryInfo(path).CreationTime; }
        public static DateTime GetCreationTimeUtc(string path) { return new DirectoryInfo(path).CreationTimeUtc; }
        public static string[] GetDirectories(string path) { return EnumerateDirectories(path).ToArray(); }
        public static string[] GetDirectories(string path, string searchPattern) { return EnumerateDirectories(path, searchPattern).ToArray(); }
        public static string[] GetDirectories(string path, string searchPattern, SearchOption searchOption) { return EnumerateDirectories(path, searchPattern, searchOption).ToArray(); }
        public static string[] GetFiles(string path) { return EnumerateFiles(path).ToArray(); }
        public static string[] GetFiles(string path, string searchPattern) { return EnumerateFiles(path, searchPattern).ToArray(); }
        public static string[] GetFiles(string path, string searchPattern, SearchOption searchOption) { return EnumerateFiles(path, searchPattern, searchOption).ToArray(); }
        public static string[] GetFileSystemInfos(string path) { return EnumerateFileSystemEntries(path).ToArray(); }
        public static string[] GetFileSystemInfos(string path, string searchPattern) { return EnumerateFileSystemEntries(path, searchPattern).ToArray(); }
        public static string[] GetFileSystemInfos(string path, string searchPattern, SearchOption searchOption) { return EnumerateFileSystemEntries(path, searchPattern, searchOption).ToArray(); }
        public static DateTime GetLastAccessTime(string path) { return new DirectoryInfo(path).LastAccessTime; }
        public static DateTime GetLastAccessTimeUtc(string path) { return new DirectoryInfo(path).LastAccessTimeUtc; }
        public static DateTime GetLastWriteTime(string path) { return new DirectoryInfo(path).LastWriteTime; }
        public static DateTime GetLastWriteTimeUtc(string path) { return new DirectoryInfo(path).LastWriteTimeUtc; }
        public static DirectoryInfo GetParent(string path) { return new DirectoryInfo(path).Parent; }
        public static void Move(string sourceDirName, string destDirName) { FileSystemInfo.Move(sourceDirName, destDirName); }
        public static void SetAccessControl(string path, DirectorySecurity directorySecurity) { FileSystemInfo.SetAcl(path, directorySecurity); }
        public static void SetCreationTime(string path, DateTime creationTime) { SetCreationTimeUtc(path, creationTime.ToUniversalTime()); }
        public static void SetCreationTimeUtc(string path, DateTime creationTimeUtc) { FileSystemInfo.SetFileTime(path, creationTimeUtc, null, null); }
        public static void SetLastAccessTime(string path, DateTime lastAccessTime) { SetLastAccessTimeUtc(path, lastAccessTime.ToUniversalTime()); }
        public static void SetLastAccessTimeUtc(string path, DateTime lastAccessTimeUtc) { FileSystemInfo.SetFileTime(path, null, lastAccessTimeUtc, null); }
        public static void SetLastWriteTime(string path, DateTime lastWriteTime) { SetLastWriteTimeUtc(path, lastWriteTime.ToUniversalTime()); }
        public static void SetLastWriteTimeUtc(string path, DateTime lastWriteTimeUtc) { FileSystemInfo.SetFileTime(path, null, null, lastWriteTimeUtc); }

        internal static IEnumerable<T> EnumerateFolder<T>(string path, string searchPattern, SearchOption searchOption, bool returnFolders, bool returnFiles)
        {
            Queue<string> dirs = new Queue<string>();
            dirs.Enqueue(path);

            while (dirs.Count > 0)
            {
                string currentPath = dirs.Dequeue();
                string searchPath;
                if (currentPath.EndsWith("\\"))
                    searchPath = currentPath + searchPattern;
                else
                    searchPath = currentPath + "\\" + searchPattern;

                NativeHelpers.WIN32_FIND_DATA findData = new NativeHelpers.WIN32_FIND_DATA();
                IntPtr findHandle = NativeMethods.FindFirstFileW(searchPath, out findData);
                if (findHandle.ToInt64() == -1)
                    throw new Win32Exception(String.Format("FindFirstFileW({0}) failed", searchPath));

                do
                {
                    string fileName = findData.cFileName;
                    string filePath = System.IO.Path.Combine(currentPath, fileName);
                    FileAttributes attr = findData.dwFileAttributes;

                    if (attr.HasFlag(FileAttributes.Directory))
                    {
                        // Skip current directory and parent directory names
                        if (fileName == "." || fileName == "..")
                            continue;
                        else if (searchOption.HasFlag(SearchOption.AllDirectories))
                            dirs.Enqueue(filePath);

                        if (returnFolders)
                            if (typeof(T) == typeof(string))
                                yield return (T)(object)filePath;
                            else
                                yield return (T)(object)new DirectoryInfo(filePath);
                    }
                    else if (returnFiles)
                        if (typeof(T) == typeof(string))
                            yield return (T)(object)filePath;
                        else
                            yield return (T)(object)new FileInfo(filePath);
                } while (NativeMethods.FindNextFileW(findHandle, out findData));

                int lastErr = Marshal.GetLastWin32Error();
                NativeMethods.FindClose(findHandle);
                if (lastErr != Win32Errors.ERROR_NO_MORE_FILES)
                    throw new Win32Exception(lastErr, "FindNextFileW() failed");
            }
        }
    }

    public sealed class DirectoryInfo : FileSystemInfo
    {
        #region Constructor
        public DirectoryInfo(string path)
        {
            Initialize(path, true);
        }
        #endregion // Constructor

        #region Properties
        public override bool Exists
        {
            get
            {
                try
                {
                    RefreshIfNotInitialized();
                    FileAttributes attr = Win32AttributeData.dwFileAttributes;
                    return (!attr.Equals((FileAttributes)(-1)) && attr.HasFlag(FileAttributes.Directory));
                }
                catch
                {
                    return false;
                }
            }
        }
        public override string Name { get { return System.IO.Path.GetFileName(FullPath); } }
        public DirectoryInfo Parent { get { return new DirectoryInfo(GetDirectoryName(FullPath)); } }
        public DirectoryInfo Root { get { return new DirectoryInfo(GetPathRoot(FullPath)); } }
        #endregion // Properties

        #region Method
        public DirectoryInfo CopyTo(string destDirPath) { return CopyTo(destDirPath, false); }
        public DirectoryInfo CopyTo(string destDirPath, bool overwrite)
        {
            Directory.Copy(FullPath, destDirPath, overwrite);
            return new DirectoryInfo(destDirPath);
        }
        public void Create() { Directory.CreateDirectory(FullPath); }
        public void Create(DirectorySecurity directorySecurity) { Directory.CreateDirectory(FullPath, directorySecurity); }
        public DirectoryInfo CreateSubDirectory(string path) { return Directory.CreateDirectory(Path.Combine(FullName, path)); }
        public DirectoryInfo CreateSubDirectory(string path, DirectorySecurity directorySecurity) { return Directory.CreateDirectory(Path.Combine(FullName, path), directorySecurity); }
        public override void Delete() { Directory.Delete(FullPath); }
        public void Delete(bool recursive) { Directory.Delete(FullPath, recursive); }
        public IEnumerable<DirectoryInfo> EnumerateDirectories() { return EnumerateDirectories("*", SearchOption.TopDirectoryOnly); }
        public IEnumerable<DirectoryInfo> EnumerateDirectories(string searchPattern) { return EnumerateDirectories(searchPattern, SearchOption.TopDirectoryOnly); }
        public IEnumerable<DirectoryInfo> EnumerateDirectories(string searchPattern, SearchOption searchOption) { return Directory.EnumerateFolder<DirectoryInfo>(FullPath, searchPattern, searchOption, true, false); }
        public IEnumerable<FileInfo> EnumerateFiles() { return EnumerateFiles("*", SearchOption.TopDirectoryOnly); }
        public IEnumerable<FileInfo> EnumerateFiles(string searchPattern) { return EnumerateFiles(searchPattern, SearchOption.TopDirectoryOnly); }
        public IEnumerable<FileInfo> EnumerateFiles(string searchPattern, SearchOption searchOption) { return Directory.EnumerateFolder<FileInfo>(FullPath, searchPattern, searchOption, false, true); }
        public IEnumerable<FileSystemInfo> EnumerateFileSystemInfos() { return EnumerateFileSystemInfos("*", SearchOption.TopDirectoryOnly); }
        public IEnumerable<FileSystemInfo> EnumerateFileSystemInfos(string searchPattern) { return EnumerateFileSystemInfos(searchPattern, SearchOption.TopDirectoryOnly); }
        public IEnumerable<FileSystemInfo> EnumerateFileSystemInfos(string searchPattern, SearchOption searchOption) { return Directory.EnumerateFolder<FileSystemInfo>(FullPath, searchPattern, searchOption, true, true); }
        public DirectorySecurity GetAccessControl() { return Directory.GetAccessControl(FullPath); }
        public DirectorySecurity GetAccessControl(AccessControlSections includeSections) { return Directory.GetAccessControl(FullName, includeSections); }
        public DirectoryInfo[] GetDirectories() { return EnumerateDirectories().ToArray(); }
        public DirectoryInfo[] GetDirectories(string searchPattern) { return EnumerateDirectories(searchPattern).ToArray(); }
        public DirectoryInfo[] GetDirectories(string searchPattern, SearchOption searchOption) { return EnumerateDirectories(searchPattern, searchOption).ToArray(); }
        public FileInfo[] GetFiles() { return EnumerateFiles().ToArray(); }
        public FileInfo[] GetFiles(string searchPattern) { return EnumerateFiles(searchPattern).ToArray(); }
        public FileInfo[] GetFiles(string searchPattern, SearchOption searchOption) { return EnumerateFiles(searchPattern, searchOption).ToArray(); }
        public FileSystemInfo[] GetFileSystemInfos() { return EnumerateFileSystemInfos().ToArray(); }
        public FileSystemInfo[] GetFileSystemInfos(string searchPattern) { return EnumerateFileSystemInfos(searchPattern).ToArray(); }
        public FileSystemInfo[] GetFileSystemInfos(string searchPattern, SearchOption searchOption) { return EnumerateFileSystemInfos(searchPattern, searchOption).ToArray(); }
        public void MoveTo(string destDirName) { Directory.Move(FullPath, destDirName); }
        public void SetAccessControl(DirectorySecurity directorySecurity) { SetAcl(FullPath, directorySecurity); }
        #endregion // Methods
    }
}
"@
    Add-Type -TypeDefinition $file_util
}

<#
Test-Path/Get-Item cannot find/return info on files that are locked like
C:\pagefile.sys. These 2 functions are designed to work with these files and
provide similar functionality with the normal cmdlets with as minimal overhead
as possible. They work by using Get-ChildItem with a filter and return the
result from that.
#>

Function Test-AnsiblePath {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory=$true)][string]$Path
    )
    # Replacement for Test-Path
    try {
        $file_attributes = [System.IO.File]::GetAttributes($Path)
    } catch [System.IO.FileNotFoundException] {
        return $false
    }

    if ([Int32]$file_attributes -eq -1) {
        return $false
    } else {
        return $true
    }
}

Function Get-AnsibleItem {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory=$true)][string]$Path
    )
    # Replacement for Get-Item
    $file_attributes = [System.IO.File]::GetAttributes($Path)
    if ([Int32]$file_attributes -eq -1) {
        throw New-Object -TypeName System.Management.Automation.ItemNotFoundException -ArgumentList "Cannot find path '$Path' because it does not exist."
    } elseif ($file_attributes.HasFlag([System.IO.FileAttributes]::Directory)) {
        return New-Object -TypeName System.IO.DirectoryInfo -ArgumentList $Path
    } else {
        return New-Object -TypeName System.IO.FileInfo -ArgumentList $Path
    }
}

Export-ModuleMember -Function Test-FilePath, Get-FileItem, Load-FileUtilFunctions
