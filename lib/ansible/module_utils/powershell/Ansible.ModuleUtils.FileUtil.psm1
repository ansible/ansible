# Copyright (c) 2017 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

#Requires -Module Ansible.ModuleUtils.PrivilegeUtil

$ansible_file_util_namespaces = @(
    "Microsoft.Win32.SafeHandles",
    "System",
    "System.Collections.Generic",
    "System.ComponentModel",
    "System.IO",
    "System.Linq",
    "System.Runtime.InteropServices",
    "System.Security.AccessControl",
    "System.Text"
)

# Most of the C# code has been slightly modified from the .NET Framework repo
# https://github.com/dotnet/corefx but includes support for long file paths
# The original code is licensed to the .NET Foundation under the MIT license.
$ansible_file_util_code = @'
namespace Ansible.IO
{
    internal static class Win32Errors
    {
        public const Int32 ERROR_SUCCESS = 0x00000000;
        public const Int32 ERROR_FILE_NOT_FOUND = 0x00000002;
        public const Int32 ERROR_PATH_NOT_FOUND = 0x00000003;
        public const Int32 ERROR_ACCESS_DENIED = 0x00000005;
        public const Int32 ERROR_NO_MORE_FILES = 0x00000012;
        public const Int32 ERROR_NOT_READY = 0x00000015;
        public const Int32 ERROR_SHARING_VIOLATION = 0x00000020;
        public const Int32 ERROR_HANDLE_EOF = 0x00000026;
        public const Int32 ERROR_FILE_EXISTS = 0x00000050;
        public const Int32 ERROR_INVALID_PARAMETER = 0x00000057;
        public const Int32 ERROR_INVALID_NAME = 0x0000007B;
        public const Int32 ERROR_DIR_NOT_EMPTY = 0x00000091;
        public const Int32 ERROR_ALREADY_EXISTS = 0x000000B7;
        public const Int32 ERROR_FILENAME_EXCED_RANGE = 0x000000CE;
        public const Int32 ERROR_MORE_DATA = 0x000000EA;
        public const Int32 ERROR_OPERATION_ABORTED = 0x000003E3;
    }

    internal class NativeHelpers
    {
        internal enum GET_FILEEX_INFO_LEVELS
        {
            GetFileExInfoStandard,
            GetFileExMaxInfoLevel
        }

        internal enum SE_OBJECT_TYPE
        {
            SE_FILE_OBJECT = 1,
        }

        [Flags]
        internal enum FileSystemFlags : uint
        {
            CaseSensitiveSearch = 0x00000001,
            CasePreservedName = 0x00000002,
            UnicodeOnDisk = 0x00000004,
            PersistentAcls = 0x00000008,
            FileCompression = 0x00000010,
            VolumeQuotas = 0x00000020,
            SupportsSparseFiles = 0x00000040,
            SupportsReparsePoints = 0x00000080,
            VolumeIsCompressed = 0x00008000,
            SupportsObjectIds = 0x00010000,
            SupportsEncryption = 0x00020000,
            NamedStreams = 0x00040000,            
            ReadOnlyVolume = 0x00080000,
            SequentialWriteOnce = 0x00100000,
            SupportsTransactions = 0x00200000,
            SupportsHardLinks = 0x00400000,
            SupportsExtendedAttributes = 0x00800000,
            SupportsOpenByFileId = 0x01000000,
            SupportsUsnJournal = 0x02000000,
        }

        [Flags]
        internal enum FlagsAndAttributes : uint
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
        internal enum ReplaceFlags : uint
        {
            REPLACEFILE_WRITE_THROUGH = 0x00000001,
            REPLACEFILE_IGNORE_MERGE_ERRORS = 0x00000002,
            REAPLCEFILE_IGNORE_ACL_ERRORS = 0x00000004,
        }

        [Flags]
        internal enum SECURITY_DESCRIPTOR_CONTROL : uint
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
        internal enum SECURITY_INFORMATION : uint
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

        [StructLayout(LayoutKind.Sequential)]
        internal struct FILE_ALLOCATED_RANGE_BUFFER
        {
            internal Int64 FileOffset;
            internal Int64 Length;
        }

        [StructLayout(LayoutKind.Sequential)]
        internal struct FILE_ZERO_DATA_INFORMATION
        {
            internal Int64 FileOffset;
            internal Int64 BeyondFinalZero;
        }

        [StructLayout(LayoutKind.Sequential)]
        internal struct FILETIME
        {
            internal UInt32 dwLowDateTime;
            internal UInt32 dwHighDateTime;

            public static implicit operator long(FILETIME v) { return ((long)v.dwHighDateTime << 32) + v.dwLowDateTime; }
            public static explicit operator DateTime(FILETIME v) { return DateTime.FromFileTimeUtc(v); }
            public static explicit operator DateTimeOffset(FILETIME v) { return DateTimeOffset.FromFileTime(v); }
        }

        [StructLayout(LayoutKind.Sequential)]
        internal struct WIN32_FILE_ATTRIBUTE_DATA
        {
            public Int32 dwFileAttributes;
            public FILETIME ftCreationTime;
            public FILETIME ftLastAccessTime;
            public FILETIME ftLastWriteTime;
            public UInt32 nFileSizeHigh;
            public UInt32 nFileSizeLow;
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        internal struct WIN32_FIND_DATA
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

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        internal struct WIN32_FIND_STREAM_DATA
        {
            public Int64 StreamSize;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 296)] public string cStreamName;
        }

        [StructLayout(LayoutKind.Sequential)]
        internal class SecurityAttributes : IDisposable
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

    // This is also used in Ansible.ModuleUtils.LinkUtil.psm1
    internal class PrivilegeEnabler : IDisposable
    {
        private SafeWaitHandle process;
        private Dictionary<string, bool?> previousState;

        internal PrivilegeEnabler(string[] privileges)
        {
            if (privileges.Length > 0)
            {
                process = Ansible.PrivilegeUtil.Privileges.GetCurrentProcess();
                Dictionary<string, bool?> newState = new Dictionary<string, bool?>();
                for (int i = 0; i < privileges.Length; i++)
                    newState.Add(privileges[i], true);
                try
                {
                    previousState = Ansible.PrivilegeUtil.Privileges.SetTokenPrivileges(process, newState);
                }
                catch (Win32Exception e)
                {
                    string msg = String.Format("Failed to enable privilege(s) {0}: {1}", String.Join(", ", privileges), e.Message);
                    throw new Win32Exception(e.ErrorCode, msg);
                }
            }
        }

        public void Dispose()
        {
            // disables any privileges that were enabled by this class
            if (previousState != null)
                Ansible.PrivilegeUtil.Privileges.SetTokenPrivileges(process, previousState);
            GC.SuppressFinalize(this);
        }
        ~PrivilegeEnabler() { Dispose(); }
    }

    internal class NativeMethods
    {
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

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool DeviceIoControl(
            SafeFileHandle hDevice,
            UInt32 dwIoControlCode,
            IntPtr lpInBuffer,
            UInt32 nInBufferSize,
            IntPtr lpOutBuffer,
            UInt32 nOutBufferSize,
            out UInt32 lpBytesReturned,
            IntPtr lpOverlapped);

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool EncryptFileW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpFileName);

        [DllImport("kernel32.dll", SetLastError = true)]
        internal static extern bool FindClose(
            IntPtr hFindFile);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern IntPtr FindFirstFileW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
            out NativeHelpers.WIN32_FIND_DATA lpFindFileData);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern IntPtr FindFirstStreamW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpFIleName,
            UInt32 InfoLevel,
            out NativeHelpers.WIN32_FIND_STREAM_DATA lpFindStreamData,
            UInt32 dwFlags);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool FindNextFileW(
            IntPtr hFindFile,
            out NativeHelpers.WIN32_FIND_DATA lpFindFileData);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool FindNextStreamW(
            IntPtr hFindStream,
            out NativeHelpers.WIN32_FIND_STREAM_DATA lpFindStreamData);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern UInt32 GetCompressedFileSizeW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
            out UInt32 lpFileSizeHigh);

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

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public extern static bool GetVolumeInformationByHandleW(
            SafeHandle hFile,
            StringBuilder lpVolumeNameBuffer,
            UInt32 nVolumeNameSize,
            out UInt32 lpVolumeSerialNumber,
            out UInt32 lpMaximumComponentLength,
            out NativeHelpers.FileSystemFlags lpFileSystemFlags,
            StringBuilder lpFileSystemNameBuffer,
            UInt32 nFileSystemNameSize);

        [DllImport("kernel32.dll")]
        internal static extern IntPtr LocalFree(
            IntPtr hMem);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        internal static extern bool MoveFileW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpExistingFileName,
            [MarshalAs(UnmanagedType.LPWStr)] string lpNewFileName);

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

    internal class VolumeInformation
    {
        internal string VolumeName;
        internal string SystemName;
        internal UInt32 SerialNumber;
        internal NativeHelpers.FileSystemFlags SystemFlags;
    }

    internal static class Win32Marshal
    {
        internal static Exception GetExceptionForLastWin32Error(string path = "") { return GetExceptionForWin32Error(Marshal.GetLastWin32Error(), path); }

        internal static Exception GetExceptionForWin32Error(int errorCode, string path = "")
        {
            switch (errorCode)
            {
                case Win32Errors.ERROR_FILE_NOT_FOUND:
                    return new FileNotFoundException(
                        string.IsNullOrEmpty(path) ? "Unable to find the specified file." : String.Format("Could not find file '{0}'", path), path);
                case Win32Errors.ERROR_PATH_NOT_FOUND:
                    return new DirectoryNotFoundException(
                        string.IsNullOrEmpty(path) ? "Could not find a part of the path." : String.Format("Could not find a part of the path '{0}'.", path));
                case Win32Errors.ERROR_ACCESS_DENIED:
                    return new UnauthorizedAccessException(
                        string.IsNullOrEmpty(path) ? "Access to the path is denied." : String.Format("Access to the path '{0}' is denied.", path));
                case Win32Errors.ERROR_ALREADY_EXISTS:
                    if (string.IsNullOrEmpty(path))
                        goto default;
                    return new IOException(
                        String.Format("Cannot create '{0}' because a file or directory with the same name already exists.", path), MakeHRFromErrorCode(errorCode));
                case Win32Errors.ERROR_SHARING_VIOLATION:
                    return new IOException(string.IsNullOrEmpty(path) ?
                        "The process cannot access the file because it is being used by another process." :
                        String.Format("The process cannot access the file '{0}' because it is being used by another process.", path),
                        MakeHRFromErrorCode(errorCode));
                case Win32Errors.ERROR_FILE_EXISTS:
                    if (string.IsNullOrEmpty(path))
                        goto default;
                    return new IOException(
                        String.Format("The file '{0}' already exists.", path), MakeHRFromErrorCode(errorCode));
                case Win32Errors.ERROR_OPERATION_ABORTED:
                    return new OperationCanceledException();
                case Win32Errors.ERROR_INVALID_NAME:
                    return new NotSupportedException("Illegal characters in path.");
                case Win32Errors.ERROR_INVALID_PARAMETER:
                default:
                    string msg = new Win32Exception(errorCode).Message;
                    return new IOException(
                        string.IsNullOrEmpty(path) ? msg : String.Format("{0} : '{1}'", msg, path), MakeHRFromErrorCode(errorCode));
            }
        }

        internal static int MakeHRFromErrorCode(int errorCode)
        {
            // Don't convert it if it is already an HRESULT
            if ((0xFFFF0000 & errorCode) != 0)
                return errorCode;
            return unchecked(((int)0x80070000) | errorCode);
        }
    }

    internal static partial class FileSystem
    {
        public static void CopyFile(string sourceFullPath, string destFullPath, bool overwrite)
        {
            if (!NativeMethods.CopyFileW(sourceFullPath, destFullPath, !overwrite))
            {
                int errorCode = Marshal.GetLastWin32Error();
                string fileName = destFullPath;
                if (errorCode != Win32Errors.ERROR_FILE_EXISTS)
                {
                    // For some error codes we don't know if the problem was
                    // source or dest, try reading source to rule it out
                    SafeFileHandle handle = NativeMethods.CreateFileW(sourceFullPath,
                        FileSystemRights.Read, FileShare.Read, null, FileMode.Open,
                        (NativeHelpers.FlagsAndAttributes)0, IntPtr.Zero);
                    if (handle.IsInvalid)
                        fileName = sourceFullPath;
                    else
                        handle.Dispose();

                    if (errorCode == Win32Errors.ERROR_ACCESS_DENIED)
                    {
                        if (DirectoryExists(destFullPath))
                            throw new IOException(String.Format("The target file '{0}' is a directory, not a file.", destFullPath, Win32Errors.ERROR_ACCESS_DENIED));
                    }

                }
                throw Win32Marshal.GetExceptionForWin32Error(errorCode, fileName);
            }
        }

        public static void ReplaceFile(string sourceFullPath, string destFullPath, string destBackupFullPath, bool ignoreMetadataErrors)
        {
            NativeHelpers.ReplaceFlags flags = ignoreMetadataErrors ? NativeHelpers.ReplaceFlags.REPLACEFILE_IGNORE_MERGE_ERRORS : 0;
            if (!NativeMethods.ReplaceFileW(destFullPath, sourceFullPath, destBackupFullPath, flags, IntPtr.Zero, IntPtr.Zero))
                throw Win32Marshal.GetExceptionForLastWin32Error();
        }

        public static void CreateDirectory(string fullPath, DirectorySecurity directorySecurity)
        {
            if (DirectoryExists(fullPath))
                return;

            Stack<string> dirsToCreate = new Stack<string>();
            string directoryRoot = Ansible.IO.Path.GetPathRoot(fullPath);
            string dir = fullPath;
            while (directoryRoot != dir)
            {
                if (DirectoryExists(dir))
                    break;
                dirsToCreate.Push(dir);
                dir = Ansible.IO.Path.GetDirectoryName(dir);
            }

            NativeHelpers.SecurityAttributes secAttr = new NativeHelpers.SecurityAttributes(directorySecurity);
            try
            {
                while (dirsToCreate.Count > 0)
                {
                    dir = dirsToCreate.Pop();
                    if (!NativeMethods.CreateDirectoryW(dir, secAttr))
                    {
                        int errorCode = Marshal.GetLastWin32Error();
                        if (errorCode != Win32Errors.ERROR_ALREADY_EXISTS)
                            throw Win32Marshal.GetExceptionForWin32Error(errorCode, dir);
                    }
                }
            }
            finally
            {
                secAttr.Dispose();
            }
        }

        public static void Decrypt(string fullPath)
        {
            VolumeInformation info;
            using (SafeHandle handle = OpenHandle(fullPath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete, FileOptions.None, null))
                info = GetVolumeInformation(handle);

            if (!info.SystemFlags.HasFlag(NativeHelpers.FileSystemFlags.SupportsEncryption))
                throw new NotSupportedException(String.Format("The volume '{0}' does not support encryption", info.VolumeName.ToString()));

            if (!NativeMethods.DecryptFileW(fullPath, 0))
                throw new Win32Exception(Marshal.GetLastWin32Error(), String.Format("DecryptFileW({0}) failed", fullPath));
        }

        public static void DeleteFile(string fullPath)
        {
            if (!NativeMethods.DeleteFileW(fullPath))
            {
                int errorCode = Marshal.GetLastWin32Error();
                if (errorCode != Win32Errors.ERROR_FILE_NOT_FOUND)
                    throw Win32Marshal.GetExceptionForWin32Error(errorCode, fullPath);
            }
        }

        public static bool DirectoryExists(string fullPath)
        {
            NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA data = new NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA();
            int lastError = FillAttributeInfo(fullPath, ref data, returnErrorOnNotFound: true);
            return (lastError == 0) && (data.dwFileAttributes != -1) && ((data.dwFileAttributes & (int)FileAttributes.Directory) != 0);
        }

        public static void Encrypt(string fullPath)
        {
            VolumeInformation info;
            using (SafeHandle handle = OpenHandle(fullPath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete, FileOptions.None, null))
                info = GetVolumeInformation(handle);

            if (!info.SystemFlags.HasFlag(NativeHelpers.FileSystemFlags.SupportsEncryption))
                throw new NotSupportedException(String.Format("The volume '{0}' does not support encryption", info.VolumeName.ToString()));

            if (!NativeMethods.EncryptFileW(fullPath))
                throw new Win32Exception(Marshal.GetLastWin32Error(), String.Format("EncryptFileW({0}) failed", fullPath));
        }

        internal static int FillAttributeInfo(string path, ref NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA data, bool returnErrorOnNotFound)
        {
            // Remove any trailing separators
            path = Ansible.IO.Path.TrimEndingDirectorySeparator(path);
            int errorCode = Win32Errors.ERROR_SUCCESS;
            if (!NativeMethods.GetFileAttributesExW(path, NativeHelpers.GET_FILEEX_INFO_LEVELS.GetFileExInfoStandard, out data))
            {
                errorCode = Marshal.GetLastWin32Error();
                // special system files like pagefile.sys returns
                // ERROR_SHARING_VIOLATION but FindFirstFileW works so we try
                // that here
                if (errorCode == Win32Errors.ERROR_SHARING_VIOLATION)
                {
                    NativeHelpers.WIN32_FIND_DATA findData;
                    IntPtr findHandle = NativeMethods.FindFirstFileW(path, out findData);
                    if (findHandle.ToInt64() == -1)
                        errorCode = Marshal.GetLastWin32Error();
                    else
                    {
                        errorCode = Win32Errors.ERROR_SUCCESS;
                        data.dwFileAttributes = (int)findData.dwFileAttributes;
                        data.ftCreationTime = findData.ftCreationTime;
                        data.ftLastAccessTime = findData.ftLastAccessTime;
                        data.ftLastWriteTime = findData.ftLastWriteTime;
                        data.nFileSizeHigh = findData.nFileSizeHigh;
                        data.nFileSizeLow = findData.nFileSizeLow;
                    }
                }
            }

            if (errorCode != Win32Errors.ERROR_SUCCESS && !returnErrorOnNotFound)
            {
                switch (errorCode)
                {
                    case Win32Errors.ERROR_FILE_NOT_FOUND:
                    case Win32Errors.ERROR_PATH_NOT_FOUND:
                    case Win32Errors.ERROR_NOT_READY:
                        // Return default value for backwards compatibility
                        data.dwFileAttributes = -1;
                        return Win32Errors.ERROR_SUCCESS;
                }
            }

            return errorCode;
        }

        public static bool FileExists(string fullPath)
        {
            NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA data = new NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA();
            int errorCode = FillAttributeInfo(fullPath, ref data, returnErrorOnNotFound: true);
            return (errorCode == 0) && (data.dwFileAttributes != -1) && ((data.dwFileAttributes & (int)FileAttributes.Directory) == 0);
        }

        public static FileAttributes GetAttributes(string fullPath) { return (FileAttributes)GetFileAttributeData(fullPath).dwFileAttributes; }

        public static DateTimeOffset GetCreationTime(string fullPath) { return (DateTimeOffset)GetFileAttributeData(fullPath).ftCreationTime; }

        private static NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA GetFileAttributeData(string path)
        {
            NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA data = new NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA();
            int errorCode = FillAttributeInfo(path, ref data, returnErrorOnNotFound: true);
            if (errorCode != Win32Errors.ERROR_SUCCESS)
                throw Win32Marshal.GetExceptionForWin32Error(errorCode, path);
            return data;
        }

        public static DateTimeOffset GetLastAccessTime(string fullPath) { return (DateTimeOffset)GetFileAttributeData(fullPath).ftLastAccessTime; }
        public static DateTimeOffset GetLastWriteTime(string fullPath) { return (DateTimeOffset)GetFileAttributeData(fullPath).ftLastAccessTime; }

        public static List<StreamInformation> GetStreamInfo(string fullPath)
        {
            VolumeInformation info;
            using (SafeHandle volumeHandle = OpenHandle(fullPath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete, FileOptions.None, null))
                info = GetVolumeInformation(volumeHandle);

            if (!info.SystemFlags.HasFlag(NativeHelpers.FileSystemFlags.NamedStreams))
                throw new NotSupportedException(String.Format("The volume '{0}' does not support named streams", info.VolumeName.ToString()));

            List<StreamInformation> streams = new List<StreamInformation>();
            NativeHelpers.WIN32_FIND_STREAM_DATA data = new NativeHelpers.WIN32_FIND_STREAM_DATA(); ;
            IntPtr handle = NativeMethods.FindFirstStreamW(fullPath, 0, out data, 0);
            if (handle.ToInt64() == -1)
                throw Win32Marshal.GetExceptionForLastWin32Error(fullPath);

            try
            {
                do
                {
                    string[] streamNameSplit = data.cStreamName.Split(':');
                    StreamInformation streamInfo = new StreamInformation()
                    {
                        Length = data.StreamSize,
                        StreamName = streamNameSplit[1],
                        StreamPath = fullPath + data.cStreamName,
                        StreamType = streamNameSplit[2],
                    };
                    streams.Add(streamInfo);
                } while (NativeMethods.FindNextStreamW(handle, out data));

                int errorCode = Marshal.GetLastWin32Error();
                if (errorCode != Win32Errors.ERROR_SUCCESS && errorCode != Win32Errors.ERROR_HANDLE_EOF)
                    throw Win32Marshal.GetExceptionForWin32Error(errorCode, fullPath);
            }
            finally
            {
                NativeMethods.FindClose(handle);
            }

            return streams;
        }

        public static VolumeInformation GetVolumeInformation(SafeHandle handle)
        {
            StringBuilder volumeName = new StringBuilder(261);  // MAX_PATH + 1
            StringBuilder systemName = new StringBuilder(261);
            UInt32 serialNumber;
            UInt32 componentLength;
            NativeHelpers.FileSystemFlags flagAttributes;
            if (!NativeMethods.GetVolumeInformationByHandleW(handle, volumeName, (UInt32)volumeName.Capacity, out serialNumber, out componentLength, out flagAttributes, systemName, (UInt32)systemName.Capacity))
                throw new Win32Exception(Marshal.GetLastWin32Error(), "Failed to get volume information");

            return new VolumeInformation()
            {
                SerialNumber = serialNumber,
                SystemName = systemName.ToString(),
                SystemFlags = flagAttributes,
                VolumeName = volumeName.ToString()
            };
        }

        public static void MoveDirectory(string sourceFullPath, string destFullPath)
        {
            if (!NativeMethods.MoveFileW(sourceFullPath, destFullPath))
            {
                int errorCode = Marshal.GetLastWin32Error();
                if (errorCode == Win32Errors.ERROR_FILE_NOT_FOUND)
                    throw Win32Marshal.GetExceptionForWin32Error(errorCode, sourceFullPath);
                // This check was originally put in for Win9x (unfortunately without special casing it to be for Win9x only). We can't change the NT codepath now for backcomp reasons.
                if (errorCode == Win32Errors.ERROR_ACCESS_DENIED)
                    throw new IOException(String.Format("Access to the path '{0}' is denied.", sourceFullPath), Win32Marshal.MakeHRFromErrorCode(errorCode));
                throw Win32Marshal.GetExceptionForWin32Error(errorCode);
            }
        }

        public static void MoveFile(string sourceFullPath, string destFullPath)
        {
            if (!NativeMethods.MoveFileW(sourceFullPath, destFullPath))
                throw Win32Marshal.GetExceptionForLastWin32Error();
        }

        internal static SafeFileHandle OpenHandle(string path, FileMode mode, FileAccess access, FileShare share, FileOptions options, FileSecurity fileSecurity)
        {
            FileSystemRights accessRights;
            if (access == FileAccess.Read)
                accessRights = FileSystemRights.Read;
            else if (access == FileAccess.Write)
                accessRights = FileSystemRights.WriteData;
            else
                accessRights = FileSystemRights.ReadData | FileSystemRights.WriteData;
            NativeHelpers.FlagsAndAttributes attr = (NativeHelpers.FlagsAndAttributes)options;

            List<string> privileges = new List<string>();
            if (fileSecurity != null)
            {
                byte[] securityInfoBytes = fileSecurity.GetSecurityDescriptorBinaryForm();
                IntPtr securityInfo = Marshal.AllocHGlobal(securityInfoBytes.Length);
                Marshal.Copy(securityInfoBytes, 0, securityInfo, securityInfoBytes.Length);
                try
                {
                    IntPtr pSacl = IntPtr.Zero;
                    bool saclPresent, saclDefaulted;
                    if (!NativeMethods.GetSecurityDescriptorSacl(securityInfo, out saclPresent, out pSacl, out saclDefaulted))
                        throw new Win32Exception(Marshal.GetLastWin32Error(), "GetSecurityDescriptorSacl() failed");

                    if (saclPresent)
                    {
                        accessRights |= (FileSystemRights)0x01000000;  // ACCESS_SYSTEM_SECURITY - Bit 24
                        privileges.Add("SeSecurityPrivilege");
                    }
                }
                finally
                {
                    Marshal.FreeHGlobal(securityInfo);
                }
            }

            NativeHelpers.SecurityAttributes secAttr = new NativeHelpers.SecurityAttributes(fileSecurity);
            SafeFileHandle fileHandle;
            using (new PrivilegeEnabler(privileges.ToArray()))
            {
                fileHandle = NativeMethods.CreateFileW(path, accessRights, share, secAttr, mode, attr, IntPtr.Zero);
                secAttr.Dispose();
                if (fileHandle.IsInvalid)
                    throw Win32Marshal.GetExceptionForLastWin32Error(path);
            }

            return fileHandle;
        }

        public static List<SparseAllocations> QuerySparseAllocatedRanges(string fullPath, Int64 offset, Int64 length)
        {
            List<SparseAllocations> ranges = new List<SparseAllocations>();
            using (SafeFileHandle handle = NativeMethods.CreateFileW(fullPath, FileSystemRights.Read, FileShare.None,
                null, FileMode.Open, NativeHelpers.FlagsAndAttributes.FILE_FLAG_BACKUP_SEMANTICS, IntPtr.Zero))
            {
                if (handle.IsInvalid)
                    throw Win32Marshal.GetExceptionForLastWin32Error(fullPath);

                Int64 rangeLength = length;
                int errorCode = Win32Errors.ERROR_MORE_DATA;
                while (errorCode == Win32Errors.ERROR_MORE_DATA)
                {
                    NativeHelpers.FILE_ALLOCATED_RANGE_BUFFER rangeBuffer = new NativeHelpers.FILE_ALLOCATED_RANGE_BUFFER()
                    {
                        FileOffset = offset,
                        Length = rangeLength
                    };
                    Int32 bufferSize = Marshal.SizeOf(typeof(NativeHelpers.FILE_ALLOCATED_RANGE_BUFFER));
                    IntPtr dataInfoPtr = Marshal.AllocHGlobal(bufferSize);

                    try
                    {
                        Marshal.StructureToPtr(rangeBuffer, dataInfoPtr, false);
                        IntPtr dataOutPtr = Marshal.AllocHGlobal(bufferSize);
                        try
                        {
                            UInt32 bytesReturned;
                            UInt32 FSCTL_QUERY_ALLOCATED_RANGES = 0x000940cf;
                            if (!NativeMethods.DeviceIoControl(handle, FSCTL_QUERY_ALLOCATED_RANGES, dataInfoPtr, (UInt32)bufferSize, dataOutPtr, (UInt32)bufferSize, out bytesReturned, IntPtr.Zero))
                                errorCode = Marshal.GetLastWin32Error();
                            else
                                errorCode = 0;

                            if (bytesReturned == 0)
                                continue;

                            NativeHelpers.FILE_ALLOCATED_RANGE_BUFFER outBuffer = (NativeHelpers.FILE_ALLOCATED_RANGE_BUFFER)Marshal.PtrToStructure(dataOutPtr, typeof(NativeHelpers.FILE_ALLOCATED_RANGE_BUFFER));
                            ranges.Add(new SparseAllocations()
                            {
                                FileOffset = outBuffer.FileOffset,
                                Length = outBuffer.Length,
                            });
                            offset = outBuffer.FileOffset + outBuffer.Length;
                            rangeLength = length - offset;
                        }
                        finally
                        {
                            Marshal.FreeHGlobal(dataOutPtr);
                        }
                    }
                    finally
                    {
                        Marshal.FreeHGlobal(dataInfoPtr);
                    }
                }

                if (errorCode != Win32Errors.ERROR_SUCCESS)
                    throw Win32Marshal.GetExceptionForWin32Error(errorCode, fullPath);
            }

            return ranges;
        }

        public static void RemoveDirectory(string fullPath, bool recursive)
        {
            if (!recursive)
            {
                RemoveDirectoryInternal(fullPath, topLevel: true);
                return;
            }

            NativeHelpers.WIN32_FIND_DATA findData = new NativeHelpers.WIN32_FIND_DATA();
            GetFindData(fullPath, ref findData);
            if (IsNameSurrogateReparsePoint(ref findData))
                // Don't recurse
                RemoveDirectoryInternal(fullPath, topLevel: true);
            else
                RemoveDirectoryRecursive(fullPath, ref findData, topLevel: true);
        }

        public static T GetAccessControl<T>(string fullpath, AccessControlSections includeSections) where T : ObjectSecurity, new()
        {
            NativeHelpers.SECURITY_INFORMATION secInfo = NativeHelpers.SECURITY_INFORMATION.NONE;
            List<string> privileges = new List<string>();
            if ((includeSections.HasFlag(AccessControlSections.Access)))
                secInfo |= NativeHelpers.SECURITY_INFORMATION.DACL_SECURITY_INFORMATION;
            if ((includeSections.HasFlag(AccessControlSections.Audit)))
            {
                secInfo |= NativeHelpers.SECURITY_INFORMATION.SACL_SECURITY_INFORMATION;
                privileges.Add("SeSecurityPrivilege");
            }
            if ((includeSections.HasFlag(AccessControlSections.Group)))
                secInfo |= NativeHelpers.SECURITY_INFORMATION.GROUP_SECURITY_INFORMATION;
            if ((includeSections.HasFlag(AccessControlSections.Owner)))
                secInfo |= NativeHelpers.SECURITY_INFORMATION.OWNER_SECURITY_INFORMATION;

            var acl = new T();
            using (new PrivilegeEnabler(privileges.ToArray()))
            {
                IntPtr pSidOwner, pSidGroup, pDacl, pSacl, pSecurityDescriptor = IntPtr.Zero;
                UInt32 res = NativeMethods.GetNamedSecurityInfoW(fullpath, NativeHelpers.SE_OBJECT_TYPE.SE_FILE_OBJECT, secInfo,
                    out pSidOwner, out pSidGroup, out pDacl, out pSacl, out pSecurityDescriptor);
                if (res != Win32Errors.ERROR_SUCCESS)
                    throw Win32Marshal.GetExceptionForWin32Error((int)res, fullpath);

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
            }

            return acl;
        }

        private static void GetFindData(string fullPath, ref NativeHelpers.WIN32_FIND_DATA findData)
        {
            IntPtr handle = NativeMethods.FindFirstFileW(fullPath, out findData);
            if (handle.ToInt64() == -1)
            {
                int errorCode = Marshal.GetLastWin32Error();
                // File not found doesn't make much sense coming from a directory delete.
                if (errorCode == Win32Errors.ERROR_FILE_NOT_FOUND)
                    errorCode = Win32Errors.ERROR_PATH_NOT_FOUND;
                throw Win32Marshal.GetExceptionForWin32Error(errorCode, fullPath);
            }
            NativeMethods.FindClose(handle);
        }

        private static bool IsNameSurrogateReparsePoint(ref NativeHelpers.WIN32_FIND_DATA data)
        {
            // Reparse points that are not name surrogates should be treated like any other directory
            return data.dwFileAttributes.HasFlag(FileAttributes.ReparsePoint) && (data.dwReserved0 & 0x20000000) != 0;
        }

        private static void RemoveDirectoryRecursive(string fullPath, ref NativeHelpers.WIN32_FIND_DATA findData, bool topLevel)
        {
            int errorCode;
            Exception exception = null;

            IntPtr handle = NativeMethods.FindFirstFileW(Ansible.IO.Path.Combine(fullPath, "*"), out findData);
            if (handle.ToInt64() == -1)
                throw Win32Marshal.GetExceptionForLastWin32Error(fullPath);

            try
            {
                do
                {
                    if ((findData.dwFileAttributes & FileAttributes.Directory) == 0)
                        DeleteFile(Ansible.IO.Path.Combine(fullPath, findData.cFileName));
                    else
                    {
                        string fileName = findData.cFileName;

                        // skip . and ..
                        if (fileName == "." || fileName == "..")
                            continue;

                        string filePath = Ansible.IO.Path.Combine(fullPath, fileName);
                        bool isNamedSurrogate = IsNameSurrogateReparsePoint(ref findData);
                        try
                        {
                            if (isNamedSurrogate == true)
                                RemoveDirectoryInternal(filePath, false, false);
                            else
                                RemoveDirectoryRecursive(filePath, ref findData, false);
                        }
                        catch (Exception e)
                        {
                            if (exception == null)
                                exception = e;
                        }
                    }
                } while (NativeMethods.FindNextFileW(handle, out findData));

                if (exception != null)
                    throw exception;

                errorCode = Marshal.GetLastWin32Error();
                if (errorCode != Win32Errors.ERROR_SUCCESS && errorCode != Win32Errors.ERROR_NO_MORE_FILES)
                    throw Win32Marshal.GetExceptionForWin32Error(errorCode, fullPath);
            }
            finally
            {
                NativeMethods.FindClose(handle);
            }
            RemoveDirectoryInternal(fullPath, topLevel: topLevel, allowDirectoryNotEmpty: true);
        }

        private static void RemoveDirectoryInternal(string fullPath, bool topLevel, bool allowDirectoryNotEmpty = false)
        {
            if (!NativeMethods.RemoveDirectoryW(fullPath))
            {
                int errorCode = Marshal.GetLastWin32Error();
                switch (errorCode)
                {
                    case Win32Errors.ERROR_FILE_NOT_FOUND:
                        errorCode = Win32Errors.ERROR_PATH_NOT_FOUND;
                        goto case Win32Errors.ERROR_PATH_NOT_FOUND;
                    case Win32Errors.ERROR_PATH_NOT_FOUND:
                        // we only throw for the top level directory not found, not for any contents.
                        if (!topLevel)
                            return;
                        break;
                    case Win32Errors.ERROR_DIR_NOT_EMPTY:
                        if (allowDirectoryNotEmpty)
                            return;
                        break;
                    case Win32Errors.ERROR_ACCESS_DENIED:
                        // This conversion was originally put in for Win9x. Keeping for compatibility.
                        throw new IOException(String.Format("Access to the path '{0}' is denied.", fullPath));
                }
                throw Win32Marshal.GetExceptionForWin32Error(errorCode, fullPath);
            }
        }

        public static void SetAccessControl(string fullPath, ObjectSecurity objectSecurity)
        {
            byte[] securityInfoBytes = objectSecurity.GetSecurityDescriptorBinaryForm();
            IntPtr securityInfo = Marshal.AllocHGlobal(securityInfoBytes.Length);
            try
            {
                Marshal.Copy(securityInfoBytes, 0, securityInfo, securityInfoBytes.Length);
                NativeHelpers.SECURITY_INFORMATION securityInformation = NativeHelpers.SECURITY_INFORMATION.NONE;
                List<string> privileges = new List<string>();

                NativeHelpers.SECURITY_DESCRIPTOR_CONTROL control;
                UInt32 lpdwRevision;
                if (!NativeMethods.GetSecurityDescriptorControl(securityInfo, out control, out lpdwRevision))
                    throw new Win32Exception(Marshal.GetLastWin32Error(), "GetSecurityDescriptorControl() failed");

                IntPtr pOwner = IntPtr.Zero;
                bool ownerDefaulted;
                if (!NativeMethods.GetSecurityDescriptorOwner(securityInfo, out pOwner, out ownerDefaulted))
                    throw new Win32Exception(Marshal.GetLastWin32Error(), "GetSecurityDescriptorOwner() failed");
                if (pOwner != IntPtr.Zero)
                {
                    securityInformation |= NativeHelpers.SECURITY_INFORMATION.OWNER_SECURITY_INFORMATION;
                    // Try and set some higher privileges, do not fail if this does not succeed as it may not be needed
                    SafeWaitHandle process = Ansible.PrivilegeUtil.Privileges.GetCurrentProcess();
                    Dictionary<string, Ansible.PrivilegeUtil.PrivilegeAttributes> currPrivileges = Ansible.PrivilegeUtil.Privileges.GetAllPrivilegeInfo(process);
                    if (currPrivileges.ContainsKey("SeTakeOwnershipPrivilege"))
                        privileges.Add("SeTakeOwnershipPrivilege");
                    if (currPrivileges.ContainsKey("SeRestorePrivilege"))
                        privileges.Add("SeRestorePrivilege");

                    // On Server 2008 (and R2), you need to set the owner before the DACL/SACL/Group
                    // in case we are taking ownership from another user so we do it first here
                    using (new PrivilegeEnabler(privileges.ToArray()))
                    {
                        UInt32 res = NativeMethods.SetNamedSecurityInfoW(fullPath, NativeHelpers.SE_OBJECT_TYPE.SE_FILE_OBJECT, securityInformation, pOwner, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero);
                        if (res != Win32Errors.ERROR_SUCCESS)
                            throw Win32Marshal.GetExceptionForWin32Error((int)res, fullPath);
                    }
                }

                bool setAgain = false;  // only set again if dacl/group/sacl is set
                IntPtr pDacl = IntPtr.Zero;
                bool daclPresent, daclDefaulted;
                if (!NativeMethods.GetSecurityDescriptorDacl(securityInfo, out daclPresent, out pDacl, out daclDefaulted))
                    throw new Win32Exception(Marshal.GetLastWin32Error(), "GetSecurityDescriptorDacl() failed");
                if (daclPresent)
                {
                    setAgain = true;
                    securityInformation |= NativeHelpers.SECURITY_INFORMATION.DACL_SECURITY_INFORMATION;
                    securityInformation |= (control & NativeHelpers.SECURITY_DESCRIPTOR_CONTROL.SE_DACL_PROTECTED) != 0
                        ? NativeHelpers.SECURITY_INFORMATION.PROTECTED_DACL_SECURITY_INFORMATION
                        : NativeHelpers.SECURITY_INFORMATION.UNPROTECTED_DACL_SECURITY_INFORMATION;
                }

                IntPtr pGroup = IntPtr.Zero;
                bool groupDefaulted;
                if (!NativeMethods.GetSecurityDescriptorGroup(securityInfo, out pGroup, out groupDefaulted))
                    throw new Win32Exception(Marshal.GetLastWin32Error(), "GetSecurityDescriptorGroup() failed");
                if (pGroup != IntPtr.Zero)
                {
                    setAgain = true;
                    securityInformation |= NativeHelpers.SECURITY_INFORMATION.GROUP_SECURITY_INFORMATION;
                }

                IntPtr pSacl = IntPtr.Zero;
                bool saclPresent, saclDefaulted;
                if (!NativeMethods.GetSecurityDescriptorSacl(securityInfo, out saclPresent, out pSacl, out saclDefaulted))
                    throw new Win32Exception(Marshal.GetLastWin32Error(), "GetSecurityDescriptorSacl() failed");
                if (saclPresent)
                {
                    setAgain = true;
                    securityInformation |= NativeHelpers.SECURITY_INFORMATION.SACL_SECURITY_INFORMATION;
                    securityInformation |= (control & NativeHelpers.SECURITY_DESCRIPTOR_CONTROL.SE_SACL_PROTECTED) != 0
                        ? NativeHelpers.SECURITY_INFORMATION.PROTECTED_SACL_SECURITY_INFORMATION
                        : NativeHelpers.SECURITY_INFORMATION.UNPROTECTED_SACL_SECURITY_INFORMATION;
                    privileges.Add("SeSecurityPrivilege");
                }

                if (setAgain)
                {
                    using (new PrivilegeEnabler(privileges.ToArray()))
                    {
                        UInt32 res = NativeMethods.SetNamedSecurityInfoW(fullPath, NativeHelpers.SE_OBJECT_TYPE.SE_FILE_OBJECT, securityInformation, pOwner, pGroup, pDacl, pSacl);
                        if (res != Win32Errors.ERROR_SUCCESS)
                            throw Win32Marshal.GetExceptionForWin32Error((int)res, fullPath);
                    }
                }
            }
            finally
            {
                Marshal.FreeHGlobal(securityInfo);
            }
        }

        public static void SetAttributes(string fullPath, FileAttributes attributes, FileAttributes existingAttributes)
        {
            if (attributes.HasFlag(FileAttributes.SparseFile) && !existingAttributes.HasFlag(FileAttributes.SparseFile))
                SetSparseFlag(fullPath, true);  // will overwrite the existing file so we call this first
            else if (!attributes.HasFlag(FileAttributes.SparseFile) && existingAttributes.HasFlag(FileAttributes.SparseFile))
                SetSparseFlag(fullPath, false);  // this could be dangerous if the file still has unfilled sparse regions

            if (!NativeMethods.SetFileAttributesW(fullPath, attributes))
            {
                int errorCode = Marshal.GetLastWin32Error();
                if (errorCode == Win32Errors.ERROR_INVALID_PARAMETER)
                    throw new ArgumentException("Invalid File or Directory attributes value.", "attributes");
                throw Win32Marshal.GetExceptionForWin32Error(errorCode, fullPath);
            }

            if (attributes.HasFlag(FileAttributes.Compressed) && !existingAttributes.HasFlag(FileAttributes.Compressed))
                SetCompression(fullPath, true);
            else if (!attributes.HasFlag(FileAttributes.Compressed) && existingAttributes.HasFlag(FileAttributes.Compressed))
                SetCompression(fullPath, false);

            if (attributes.HasFlag(FileAttributes.Encrypted) && !existingAttributes.HasFlag(FileAttributes.Encrypted))
                Encrypt(fullPath);
            else if (!attributes.HasFlag(FileAttributes.Encrypted) && existingAttributes.HasFlag(FileAttributes.Encrypted))
                Decrypt(fullPath);
        }

        public static void SetCompression(string fullPath, bool compress)
        {
            using (SafeFileHandle handle = NativeMethods.CreateFileW(fullPath, FileSystemRights.Read | FileSystemRights.Write, FileShare.None,
                null, FileMode.Open, NativeHelpers.FlagsAndAttributes.FILE_FLAG_BACKUP_SEMANTICS, IntPtr.Zero))
            {
                if (handle.IsInvalid)
                    throw Win32Marshal.GetExceptionForLastWin32Error(fullPath);

                VolumeInformation info = GetVolumeInformation(handle);
                if (!info.SystemFlags.HasFlag(NativeHelpers.FileSystemFlags.FileCompression))
                    throw new NotSupportedException(String.Format("The volume '{0}' does not support compression", info.VolumeName.ToString()));

                UInt16 compressionAlgo = (UInt16)(compress ? 1 : 0);
                IntPtr algoPointer = Marshal.AllocHGlobal(sizeof(UInt16));
                try
                {
                    Marshal.Copy(BitConverter.GetBytes(compressionAlgo), 0, algoPointer, sizeof(UInt16));
                    UInt32 bytesReturned = 0;
                    UInt32 FSCTL_SET_COMPRESSION = 0x0009C040;
                    if (!NativeMethods.DeviceIoControl(handle, FSCTL_SET_COMPRESSION, algoPointer, sizeof(UInt16), IntPtr.Zero, 0, out bytesReturned, IntPtr.Zero))
                        throw Win32Marshal.GetExceptionForLastWin32Error(fullPath);
                }
                finally
                {
                    Marshal.FreeHGlobal(algoPointer);
                }
            }
        }

        public static void SetFileTime(string fullPath, bool asDirectory, DateTime? creationTime, DateTime? lastAccessTime, DateTime? lastWriteTime)
        {
            using (SafeFileHandle handle = NativeMethods.CreateFileW(fullPath, FileSystemRights.WriteAttributes, FileShare.ReadWrite | FileShare.Delete,
                null, FileMode.Open, NativeHelpers.FlagsAndAttributes.FILE_FLAG_BACKUP_SEMANTICS, IntPtr.Zero))
            {
                if (handle.IsInvalid)
                    throw Win32Marshal.GetExceptionForLastWin32Error(fullPath);
                long creation = creationTime.HasValue ? creationTime.Value.ToFileTimeUtc() : 0;
                long access = lastAccessTime.HasValue ? lastAccessTime.Value.ToFileTimeUtc() : 0;
                long write = lastWriteTime.HasValue ? lastWriteTime.Value.ToFileTimeUtc() : 0;

                if (!NativeMethods.SetFileTime(handle, ref creation, ref access, ref write))
                    throw Win32Marshal.GetExceptionForLastWin32Error(fullPath);
            }
        }

        public static void SetSparseFlag(string fullPath, bool sparse)
        {
            using (SafeFileHandle handle = NativeMethods.CreateFileW(fullPath, FileSystemRights.Write, FileShare.None,
                null, FileMode.OpenOrCreate, NativeHelpers.FlagsAndAttributes.FILE_FLAG_BACKUP_SEMANTICS, IntPtr.Zero))
            {
                if (handle.IsInvalid)
                    throw Win32Marshal.GetExceptionForLastWin32Error(fullPath);

                VolumeInformation info = GetVolumeInformation(handle);
                if (!info.SystemFlags.HasFlag(NativeHelpers.FileSystemFlags.SupportsSparseFiles))
                    throw new NotSupportedException(String.Format("The volume '{0}' does not support sparse files", info.VolumeName.ToString()));

                byte[] setSparse = new byte[1];
                setSparse[0] = Convert.ToByte(sparse);
                IntPtr setSparsePtr = Marshal.AllocHGlobal(setSparse.Length);
                try
                {
                    Marshal.Copy(setSparse, 0, setSparsePtr, setSparse.Length);
                    UInt32 bytesReturned = 0;
                    UInt32 FSCTL_SET_SPARSE = 0x000900c4;
                    if (!NativeMethods.DeviceIoControl(handle, FSCTL_SET_SPARSE, setSparsePtr, (UInt32)setSparse.Length, IntPtr.Zero, 0, out bytesReturned, IntPtr.Zero))
                        throw Win32Marshal.GetExceptionForLastWin32Error(fullPath);
                }
                finally
                {
                    Marshal.FreeHGlobal(setSparsePtr);
                }
            }
        }

        public static void SetSparseZeroData(string fullPath, Int64 offset, Int64 length)
        {
            using (SafeFileHandle handle = NativeMethods.CreateFileW(fullPath, FileSystemRights.Write, FileShare.None,
                null, FileMode.Open, NativeHelpers.FlagsAndAttributes.FILE_FLAG_BACKUP_SEMANTICS, IntPtr.Zero))
            {
                if (handle.IsInvalid)
                    throw Win32Marshal.GetExceptionForLastWin32Error(fullPath);

                NativeHelpers.FILE_ZERO_DATA_INFORMATION dataInfo = new NativeHelpers.FILE_ZERO_DATA_INFORMATION()
                {
                    FileOffset = offset,
                    BeyondFinalZero = offset + length
                };
                Int32 bufferSize = Marshal.SizeOf(typeof(NativeHelpers.FILE_ZERO_DATA_INFORMATION));
                IntPtr dataInfoPtr = Marshal.AllocHGlobal(bufferSize);
                try
                {
                    Marshal.StructureToPtr(dataInfo, dataInfoPtr, false);
                    UInt32 bytesReturned = 0;
                    UInt32 FSCTL_SET_ZERO_DATA = 0x000980c8;
                    if (!NativeMethods.DeviceIoControl(handle, FSCTL_SET_ZERO_DATA, dataInfoPtr, (UInt32)bufferSize, IntPtr.Zero, 0, out bytesReturned, IntPtr.Zero))
                        throw Win32Marshal.GetExceptionForLastWin32Error(fullPath);
                }
                finally
                {
                    Marshal.FreeHGlobal(dataInfoPtr);
                }
            }
        }
    }

    public class SparseAllocations
    {
        public Int64 FileOffset;
        public Int64 Length;
    }

    public class StreamInformation
    {
        public Int64 Length;
        public string StreamName;
        public string StreamPath;
        public string StreamType;
    }

    public abstract class FileSystemInfo : MarshalByRefObject
    {
        // -1 is not initialized, else the res of getting the file attribute data
        private int _dataInitialized = -1;
        private NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA _data;
        private UInt32 _diskLengthLow;
        private UInt32 _diskLengthHigh;

        protected string FullPath;
        protected string OriginalPath;

        internal string _name;

        protected FileSystemInfo() { }

        public virtual string FullName
        {
            get { return FullPath; }
        }

        public string Extension
        {
            get { return Ansible.IO.Path.GetExtension(FullPath); }
        }

        public virtual string Name
        {
            get { return _name; }
        }

        public virtual bool Exists
        {
            get
            {
                if (_dataInitialized == -1)
                    Refresh();
                if (_dataInitialized != 0)
                    // Unable to init data but we don't throw an excp here
                    return false;
                return (_data.dwFileAttributes != -1) && ((this is Ansible.IO.DirectoryInfo) == ((_data.dwFileAttributes & (int)FileAttributes.Directory) == (int)FileAttributes.Directory));
            }
        }

        public abstract void Delete();

        public DateTime CreationTime
        {
            get { return CreationTimeUtc.ToLocalTime(); }
            set { CreationTimeUtc = value.ToUniversalTime(); }
        }

        public DateTime CreationTimeUtc
        {
            get
            {
                EnsureDataInitialized();
                return (DateTime)_data.ftCreationTime;
            }
            set
            {
                FileSystem.SetFileTime(FullPath, (this is Ansible.IO.DirectoryInfo), value, null, null);
                _dataInitialized = -1;
            }
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
                EnsureDataInitialized();
                return (DateTime)_data.ftLastAccessTime;
            }
            set
            {
                FileSystem.SetFileTime(FullPath, (this is Ansible.IO.DirectoryInfo), null, value, null);
                _dataInitialized = -1;
            }
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
                EnsureDataInitialized();
                return (DateTime)_data.ftLastWriteTime;
            }
            set
            {
                FileSystem.SetFileTime(FullPath, (this is Ansible.IO.DirectoryInfo), null, null, value);
                _dataInitialized = -1;
            }
        }

        internal long DiskLengthCore
        {
            get
            {
                EnsureDataInitialized();
                return ((long)_diskLengthHigh) << 32 | _diskLengthLow & 0xFFFFFFFFL;
            }
        }

        internal long LengthCore
        {
            get
            {
                EnsureDataInitialized();
                return ((long)_data.nFileSizeHigh) << 32 | _data.nFileSizeLow & 0xFFFFFFFFL;
            }
        }

        public override string ToString() { return OriginalPath ?? string.Empty; }
        internal void Invalidate() { _dataInitialized = -1; }

        public FileAttributes Attributes
        {
            get
            {
                EnsureDataInitialized();
                return (FileAttributes)_data.dwFileAttributes;
            }
            set
            {
                FileSystem.SetAttributes(FullPath, value, (FileAttributes)_data.dwFileAttributes);
                _dataInitialized = -1;
            }
        }

        private void EnsureDataInitialized()
        {
            if (_dataInitialized == -1)
            {
                _data = new NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA();
                _diskLengthLow = 0;
                _diskLengthHigh = 0;
                Refresh();
            }

            if (_dataInitialized != 0)  // Refresh was unable to init data
                throw Win32Marshal.GetExceptionForWin32Error(_dataInitialized, FullPath);
        }

        public void Compress() { FileSystem.SetCompression(FullPath, true); }
        public void Decompress() { FileSystem.SetCompression(FullPath, false); }
        public void Refresh()
        {
            _dataInitialized = FileSystem.FillAttributeInfo(FullPath, ref _data, returnErrorOnNotFound: false);
            _diskLengthHigh = 0xFFFFFFFF;
            _diskLengthLow = NativeMethods.GetCompressedFileSizeW(FullName, out _diskLengthHigh);
        }
    }

    public static class Directory
    {
        public static void Compress(string path) { FileSystem.SetCompression(Ansible.IO.Path.CheckAndGetFullPath(path), true); }
        public static void Copy(string sourceDirPath, string destDirPath) { Copy(sourceDirPath, destDirPath, false); }
        public static void Copy(string sourceDirPath, string destDirPath, bool overwrite) { FileSystem.CopyFile(sourceDirPath, destDirPath, !overwrite); }
        public static DirectoryInfo CreateDirectory(string path) { return CreateDirectory(path, null); }
        public static DirectoryInfo CreateDirectory(string path, DirectorySecurity directorySecurity)
        {
            string fullPath = Ansible.IO.Path.CheckAndGetFullPath(path);
            FileSystem.CreateDirectory(fullPath, directorySecurity);
            return new DirectoryInfo(path, fullPath, isNormalized: true);
        }
        public static void Decompress(string path) { FileSystem.SetCompression(Ansible.IO.Path.CheckAndGetFullPath(path), false); }
        public static void Delete(string path) { Delete(path, false); }
        public static void Delete(string path, bool recursive) { FileSystem.RemoveDirectory(Ansible.IO.Path.GetFullPath(path), recursive); }
        public static IEnumerable<string> EnumerateDirectories(string path) { return EnumerateDirectories(path, "*", SearchOption.TopDirectoryOnly); }
        public static IEnumerable<string> EnumerateDirectories(string path, string searchPattern) { return EnumerateDirectories(path, searchPattern, SearchOption.TopDirectoryOnly); }
        public static IEnumerable<string> EnumerateDirectories(string path, string searchPattern, SearchOption searchOption) { return InternalEnumerateFolder<string>(path, searchPattern, searchOption, true, false); }
        public static IEnumerable<string> EnumerateFiles(string path) { return EnumerateFiles(path, "*", SearchOption.TopDirectoryOnly); }
        public static IEnumerable<string> EnumerateFiles(string path, string searchPattern) { return EnumerateFiles(path, searchPattern, SearchOption.TopDirectoryOnly); }
        public static IEnumerable<string> EnumerateFiles(string path, string searchPattern, SearchOption searchOption) { return InternalEnumerateFolder<string>(path, searchPattern, searchOption, false, true); }
        public static IEnumerable<string> EnumerateFileSystemEntries(string path) { return EnumerateFileSystemEntries(path, "*", SearchOption.TopDirectoryOnly); }
        public static IEnumerable<string> EnumerateFileSystemEntries(string path, string searchPattern) { return EnumerateFileSystemEntries(path, searchPattern, SearchOption.TopDirectoryOnly); }
        public static IEnumerable<string> EnumerateFileSystemEntries(string path, string searchPattern, SearchOption searchOption) { return InternalEnumerateFolder<string>(path, searchPattern, searchOption, true, true); }
        public static bool Exists(string path) { return new DirectoryInfo(path).Exists; }
        public static DirectorySecurity GetAccessControl(string path) { return GetAccessControl(path, AccessControlSections.Access | AccessControlSections.Group | AccessControlSections.Owner); }
        public static DirectorySecurity GetAccessControl(string path, AccessControlSections includeSections) { return FileSystem.GetAccessControl<DirectorySecurity>(path, includeSections); }
        public static DateTime GetCreationTime(string path) { return File.GetCreationTime(path); }
        public static DateTime GetCreationTimeUtc(string path) { return File.GetCreationTimeUtc(path); }
        public static string[] GetDirectories(string path) { return EnumerateDirectories(path).ToArray(); }
        public static string[] GetDirectories(string path, string searchPattern) { return EnumerateDirectories(path, searchPattern).ToArray(); }
        public static string[] GetDirectories(string path, string searchPattern, SearchOption searchOption) { return EnumerateDirectories(path, searchPattern, searchOption).ToArray(); }
        public static string[] GetFiles(string path) { return EnumerateFiles(path).ToArray(); }
        public static string[] GetFiles(string path, string searchPattern) { return EnumerateFiles(path, searchPattern).ToArray(); }
        public static string[] GetFiles(string path, string searchPattern, SearchOption searchOption) { return EnumerateFiles(path, searchPattern, searchOption).ToArray(); }
        public static string[] GetFileSystemInfos(string path) { return EnumerateFileSystemEntries(path).ToArray(); }
        public static string[] GetFileSystemInfos(string path, string searchPattern) { return EnumerateFileSystemEntries(path, searchPattern).ToArray(); }
        public static string[] GetFileSystemInfos(string path, string searchPattern, SearchOption searchOption) { return EnumerateFileSystemEntries(path, searchPattern, searchOption).ToArray(); }
        public static DateTime GetLastAccessTime(string path) { return File.GetLastAccessTime(path); }
        public static DateTime GetLastAccessTimeUtc(string path) { return File.GetLastAccessTimeUtc(path); }
        public static DateTime GetLastWriteTime(string path) { return File.GetLastWriteTime(path); }
        public static DateTime GetLastWriteTimeUtc(string path) { return File.GetLastWriteTimeUtc(path); }
        public static DirectoryInfo GetParent(string path)
        {
            string fullPath = Ansible.IO.Path.CheckAndGetFullPath(path);
            string s = Ansible.IO.Path.GetDirectoryName(fullPath);
            if (s == null)
                return null;
            return new DirectoryInfo(s);
        }
        public static void Move(string sourceDirName, string destDirName)
        {
            string fullSource = Ansible.IO.Path.CheckAndGetFullPath(sourceDirName);
            string fullDest = Ansible.IO.Path.CheckAndGetFullPath(destDirName);

            if (fullSource == fullDest)
                throw new IOException("Source and destination path must be different.");

            if (Ansible.IO.Path.GetPathRoot(fullSource) != Ansible.IO.Path.GetPathRoot(fullDest))
                throw new IOException("Source and destination path must have identical roots. Move will not work across volumes.");

            if (!FileSystem.DirectoryExists(fullSource) && !FileSystem.FileExists(fullSource))
                throw new DirectoryNotFoundException(String.Format("Could not find a part of the path '{0}'.", fullSource));
            if (FileSystem.DirectoryExists(fullDest))
                throw new IOException(String.Format("Cannot create '{0}' because a file or directory with the same name already exists.", fullDest));
            FileSystem.MoveDirectory(fullSource, fullDest);
        }
        public static void SetAccessControl(string path, DirectorySecurity directorySecurity) { FileSystem.SetAccessControl(path, directorySecurity); }
        public static void SetCreationTime(string path, DateTime creationTime) { SetCreationTimeUtc(path, creationTime.ToUniversalTime()); }
        public static void SetCreationTimeUtc(string path, DateTime creationTimeUtc) { FileSystem.SetFileTime(Ansible.IO.Path.GetFullPath(path), true, creationTimeUtc, null, null); }
        public static void SetLastAccessTime(string path, DateTime lastAccessTime) { SetLastAccessTimeUtc(path, lastAccessTime.ToUniversalTime()); }
        public static void SetLastAccessTimeUtc(string path, DateTime lastAccessTimeUtc) { FileSystem.SetFileTime(Ansible.IO.Path.GetFullPath(path), true, null, lastAccessTimeUtc, null); }
        public static void SetLastWriteTime(string path, DateTime lastWriteTime) { SetLastWriteTimeUtc(path, lastWriteTime.ToUniversalTime()); }
        public static void SetLastWriteTimeUtc(string path, DateTime lastWriteTimeUtc) { FileSystem.SetFileTime(Ansible.IO.Path.GetFullPath(path), true, null, null, lastWriteTimeUtc); }

        internal static IEnumerable<T> InternalEnumerateFolder<T>(string path, string searchPattern, SearchOption searchOption, bool returnFolders, bool returnFiles)
        {
            Ansible.IO.File.GetAttributes(path);  // verifies the root path exists or throws exception if not
            Queue<string> dirs = new Queue<string>();
            dirs.Enqueue(path);

            while (dirs.Count > 0)
            {
                string currentPath = dirs.Dequeue();
                string searchPath = Ansible.IO.Path.Combine(currentPath, Ansible.IO.Path.TrimEndingDirectorySeparator(searchPattern));

                NativeHelpers.WIN32_FIND_DATA findData = new NativeHelpers.WIN32_FIND_DATA();
                IntPtr findHandle = NativeMethods.FindFirstFileW(searchPath, out findData);
                if (findHandle.ToInt64() == -1)
                    continue;  // failed to get find handle, just continue through the queue we have

                do
                {
                    string fileName = findData.cFileName;
                    string filePath = Ansible.IO.Path.Combine(currentPath, fileName);
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
                    throw Win32Marshal.GetExceptionForLastWin32Error();
            }
        }
    }

    public sealed class DirectoryInfo : FileSystemInfo
    {
        public DirectoryInfo(string path) { Init(originalPath: path, fullPath: Ansible.IO.Path.GetFullPath(path), isNormalized: true); }
        internal DirectoryInfo(string originalPath, string fullPath = null, string fileName = null, bool isNormalized = false) { Init(originalPath, fullPath, fileName, isNormalized); }

        private void Init(string originalPath, string fullPath = null, string fileName = null, bool isNormalized = false)
        {
            if (originalPath == null)
                throw new ArgumentNullException("path");
            OriginalPath = originalPath;

            fullPath = fullPath ?? originalPath;
            fullPath = isNormalized ? fullPath : Ansible.IO.Path.GetFullPath(fullPath);
            if (fileName == null && (Ansible.IO.Path.GetPathRoot(fullPath) != fullPath))
                _name = Ansible.IO.Path.GetFileName(Ansible.IO.Path.TrimEndingDirectorySeparator(fullPath));
            else if (fileName == null)
                _name = fullPath;
            else
                _name = fileName;
            FullPath = fullPath;
        }

        public DirectoryInfo Parent
        {
            get
            {
                string parentName = Ansible.IO.Path.GetDirectoryName(Ansible.IO.Path.TrimEndingDirectorySeparator(FullPath));
                return parentName != null
                    ? new DirectoryInfo(parentName, isNormalized: true)
                    : null;
            }
        }
        public DirectoryInfo Root
        {
            get
            {
                return new DirectoryInfo(Ansible.IO.Path.GetPathRoot(FullPath));
            }
        }

        public void Create() { Create(null); }
        public void Create(DirectorySecurity directorySecurity) { FileSystem.CreateDirectory(FullPath, directorySecurity); }
        public DirectoryInfo CreateSubdirectory(string path) { return CreateSubdirectory(path, null); }
        public DirectoryInfo CreateSubdirectory(string path, DirectorySecurity directorySecurity)
        {
            if (path == null)
                throw new ArgumentNullException("path");
            if (Ansible.IO.Path.IsEffectivelyEmpty(path))
                throw new ArgumentException("Path cannot be the empty string or all whitespace.", "path");
            if (Ansible.IO.Path.IsPathRooted(path))
                throw new ArgumentException("Second path fragment must not be a drive or UNC name.", "path");

            string newPath = Ansible.IO.Path.GetFullPath(Ansible.IO.Path.Combine(FullPath, path));
            DirectoryInfo subDir = new DirectoryInfo(newPath);
            subDir.Create(directorySecurity);
            return subDir;
        }
        public override void Delete() { Delete(false); }
        public void Delete(bool recursive) { FileSystem.RemoveDirectory(FullPath, recursive); }
        public IEnumerable<DirectoryInfo> EnumerateDirectories() { return EnumerateDirectories("*", SearchOption.TopDirectoryOnly); }
        public IEnumerable<DirectoryInfo> EnumerateDirectories(string searchPattern) { return EnumerateDirectories(searchPattern, SearchOption.TopDirectoryOnly); }
        public IEnumerable<DirectoryInfo> EnumerateDirectories(string searchPattern, SearchOption searchOption) { return Directory.InternalEnumerateFolder<DirectoryInfo>(FullPath, searchPattern, searchOption, true, false); }
        public IEnumerable<FileInfo> EnumerateFiles() { return EnumerateFiles("*", SearchOption.TopDirectoryOnly); }
        public IEnumerable<FileInfo> EnumerateFiles(string searchPattern) { return EnumerateFiles(searchPattern, SearchOption.TopDirectoryOnly); }
        public IEnumerable<FileInfo> EnumerateFiles(string searchPattern, SearchOption searchOption) { return Directory.InternalEnumerateFolder<FileInfo>(FullPath, searchPattern, searchOption, false, true); }
        public IEnumerable<FileSystemInfo> EnumerateFileSystemInfos() { return EnumerateFileSystemInfos("*", SearchOption.TopDirectoryOnly); }
        public IEnumerable<FileSystemInfo> EnumerateFileSystemInfos(string searchPattern) { return EnumerateFileSystemInfos(searchPattern, SearchOption.TopDirectoryOnly); }
        public IEnumerable<FileSystemInfo> EnumerateFileSystemInfos(string searchPattern, SearchOption searchOption) { return Directory.InternalEnumerateFolder<FileSystemInfo>(FullPath, searchPattern, searchOption, true, true); }
        public DirectorySecurity GetAccessControl() { return GetAccessControl(AccessControlSections.Access | AccessControlSections.Group | AccessControlSections.Owner); }
        public DirectorySecurity GetAccessControl(AccessControlSections includeSections) { return FileSystem.GetAccessControl<DirectorySecurity>(FullPath, includeSections); }
        public DirectoryInfo[] GetDirectories() { return EnumerateDirectories().ToArray(); }
        public DirectoryInfo[] GetDirectories(string searchPattern) { return EnumerateDirectories(searchPattern).ToArray(); }
        public DirectoryInfo[] GetDirectories(string searchPattern, SearchOption searchOption) { return EnumerateDirectories(searchPattern, searchOption).ToArray(); }
        public FileInfo[] GetFiles() { return EnumerateFiles().ToArray(); }
        public FileInfo[] GetFiles(string searchPattern) { return EnumerateFiles(searchPattern).ToArray(); }
        public FileInfo[] GetFiles(string searchPattern, SearchOption searchOption) { return EnumerateFiles(searchPattern, searchOption).ToArray(); }
        public FileSystemInfo[] GetFileSystemInfos() { return EnumerateFileSystemInfos().ToArray(); }
        public FileSystemInfo[] GetFileSystemInfos(string searchPattern) { return EnumerateFileSystemInfos(searchPattern).ToArray(); }
        public FileSystemInfo[] GetFileSystemInfos(string searchPattern, SearchOption searchOption) { return EnumerateFileSystemInfos(searchPattern, searchOption).ToArray(); }
        public void MoveTo(string destDirName)
        {
            if (destDirName == null)
                throw new ArgumentNullException("destDirName");
            if (destDirName.Length == 0)
                throw new ArgumentException("Empty file name is not legal.", "destDirName");

            string destination = Ansible.IO.Path.GetFullPath(destDirName);
            if (!Exists && !FileSystem.FileExists(FullPath))
                throw new DirectoryNotFoundException(String.Format("Could not find a part of the path '{0}'.", FullPath));
            if (FileSystem.DirectoryExists(destination))
                throw new IOException(String.Format("Cannot create '{0}' because a file or directory with the same name already exists.", destination));

            FileSystem.MoveDirectory(FullPath, destination);
            Init(destDirName, destination, _name, true);
            Invalidate();
        }
        public void SetAccessControl(DirectorySecurity directorySecurity) { FileSystem.SetAccessControl(FullPath, directorySecurity); }
    }

    public static class File
    {
        private static Encoding DefaultEncoding = new UTF8Encoding(false);
        private static int DefaultBuffer = 4096;

        public static void AppendAllLines(string path, IEnumerable<string> contents) { AppendAllLines(path, contents, DefaultEncoding); }
        public static void AppendAllLines(string path, IEnumerable<string> contents, Encoding encoding)
        {
            using (StreamWriter writer = AppendText(path, encoding))
            {
                foreach (string content in contents)
                    writer.Write(content);
            }
        }
        public static void AppendAllText(string path, string contents) { AppendAllText(path, contents, DefaultEncoding); }
        public static void AppendAllText(string path, string contents, Encoding encoding)
        {
            using (StreamWriter writer = AppendText(path, encoding))
                writer.Write(contents);
        }
        public static StreamWriter AppendText(string path) { return AppendText(path, DefaultEncoding); }
        public static StreamWriter AppendText(string path, Encoding encoding)
        {
            FileStream fs = Open(path, FileMode.OpenOrCreate, FileAccess.Write);
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
        public static void Compress(string path) { FileSystem.SetCompression(Ansible.IO.Path.CheckAndGetFullPath(path), true); }
        public static void Copy(string sourceFileName, string destFileName) { Copy(sourceFileName, destFileName, false); }
        public static void Copy(string sourceFileName, string destFileName, bool overwrite)
        {
            string fullSource = Ansible.IO.Path.CheckAndGetFullPath(sourceFileName);
            string fullDest = Ansible.IO.Path.CheckAndGetFullPath(destFileName);
            FileSystem.CopyFile(fullSource, fullDest, overwrite);
        }
        public static FileStream Create(string path) { return Open(path, FileMode.Create, FileAccess.ReadWrite); }
        public static FileStream Create(string path, int bufferSize) { return Open(path, FileMode.Create, FileAccess.ReadWrite, FileShare.None, bufferSize, FileOptions.None); }
        public static FileStream Create(string path, int bufferSize, FileOptions options) { return Open(path, FileMode.Create, FileAccess.ReadWrite, FileShare.None, bufferSize, options); }
        public static FileStream Create(string path, int bufferSize, FileOptions options, FileSecurity fileSecurity)
        {
            using (SafeFileHandle handle = FileSystem.OpenHandle(path, FileMode.Create, FileAccess.ReadWrite, FileShare.None, options, fileSecurity))
                return new FileStream(handle, FileAccess.ReadWrite, DefaultBuffer, options.HasFlag(FileOptions.Asynchronous));
        }
        public static StreamWriter CreateText(string path) { return new StreamWriter(Open(path, FileMode.Create, FileAccess.ReadWrite)); }
        public static void Decompress(string path) { FileSystem.SetCompression(Ansible.IO.Path.CheckAndGetFullPath(path), false); }
        public static void Decrypt(string path) { FileSystem.Decrypt(Ansible.IO.Path.CheckAndGetFullPath(path)); }
        public static void Delete(string path)
        {
            if (path == null)
                throw new ArgumentNullException("path");
            FileSystem.DeleteFile(Ansible.IO.Path.GetFullPath(path));
        }
        public static void Encrypt(string path) { FileSystem.Encrypt(Ansible.IO.Path.CheckAndGetFullPath(path)); }
        public static bool Exists(string path) { return new FileInfo(path).Exists; }
        public static FileSecurity GetAccessControl(string path) { return GetAccessControl(path, AccessControlSections.Access | AccessControlSections.Group | AccessControlSections.Owner); }
        public static FileSecurity GetAccessControl(string path, AccessControlSections includeSections) { return FileSystem.GetAccessControl<FileSecurity>(path, includeSections); }
        public static FileAttributes GetAttributes(string path) { return FileSystem.GetAttributes(Ansible.IO.Path.GetFullPath(path)); }
        public static DateTime GetCreationTime(string path) { return FileSystem.GetCreationTime(Ansible.IO.Path.GetFullPath(path)).LocalDateTime; }
        public static DateTime GetCreationTimeUtc(string path) { return FileSystem.GetCreationTime(Ansible.IO.Path.GetFullPath(path)).UtcDateTime; }
        public static DateTime GetLastAccessTime(string path) { return FileSystem.GetLastAccessTime(Ansible.IO.Path.GetFullPath(path)).LocalDateTime; }
        public static DateTime GetLastAccessTimeUtc(string path) { return FileSystem.GetLastAccessTime(Ansible.IO.Path.GetFullPath(path)).UtcDateTime; }
        public static DateTime GetLastWriteTime(string path) { return FileSystem.GetLastWriteTime(Ansible.IO.Path.GetFullPath(path)).LocalDateTime; }
        public static DateTime GetLastWriteTimeUtc(string path) { return FileSystem.GetLastWriteTime(Ansible.IO.Path.GetFullPath(path)).UtcDateTime; }
        public static List<StreamInformation> GetStreamInfo(string path) { return FileSystem.GetStreamInfo(Ansible.IO.Path.CheckAndGetFullPath(path)); }
        public static void Move(string sourceFileName, string destFileName)
        {
            string fullSourceFileName = Ansible.IO.Path.CheckAndGetFullPath(sourceFileName);
            string fullDestFileName = Ansible.IO.Path.CheckAndGetFullPath(destFileName);

            if (!FileSystem.FileExists(fullSourceFileName))
                throw new FileNotFoundException(String.Format("Could not find file '{0}'.", fullSourceFileName), fullSourceFileName);
            FileSystem.MoveFile(fullSourceFileName, fullDestFileName);
        }
        public static FileStream Open(string path, FileMode mode) { return Open(path, mode, mode == FileMode.Append ? FileAccess.Write : FileAccess.ReadWrite, FileShare.None); }
        public static FileStream Open(string path, FileMode mode, FileAccess access) { return Open(path, mode, access, FileShare.None); }
        public static FileStream Open(string path, FileMode mode, FileAccess access, FileShare share) { return Open(path, mode, access, share, DefaultBuffer, FileOptions.None); }
        public static FileStream Open(string path, FileMode mode, FileAccess access, FileShare share, int bufferSize, FileOptions options)
        {
            if (path == null)
                throw new ArgumentNullException("path");

            FileMode fileMode;
            if (mode == FileMode.Append)
                fileMode = FileMode.Open;
            else
                fileMode = mode;

            SafeFileHandle handle = FileSystem.OpenHandle(path, fileMode, access, share, options, null);
            FileStream fs = null;
            try
            {
                fs = new FileStream(handle, access, bufferSize, options.HasFlag(FileOptions.Asynchronous));
                if (mode == FileMode.Append)
                    fs.Seek(0, SeekOrigin.End);
                return fs;
            }
            catch
            {
                handle.Dispose();
                if (fs != null)
                    fs.Close();
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
            using (StreamReader reader = OpenText(path, encoding))
                return reader.ReadToEnd();
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
            string fullSource = Ansible.IO.Path.CheckAndGetFullPath(sourceFileName);
            string fullDest = Ansible.IO.Path.CheckAndGetFullPath(destinationFileName);
            FileSystem.ReplaceFile(fullSource, fullDest,
                destinationBackupFileName != null ? Ansible.IO.Path.GetFullPath(destinationBackupFileName) : null,
                ignoreMetadataErrors);
        }
        public static void SetAccessControl(string path, FileSecurity fileSecurity) { FileSystem.SetAccessControl(path, fileSecurity); }
        public static void SetAttributes(string path, FileAttributes fileAttributes)
        {
            string fullPath = Ansible.IO.Path.GetFullPath(path);
            FileAttributes existingAttributes = File.GetAttributes(fullPath);
            FileSystem.SetAttributes(fullPath, fileAttributes, existingAttributes);
        }
        public static void SetCreationTime(string path, DateTime creationTime) { SetCreationTimeUtc(path, creationTime.ToUniversalTime()); }
        public static void SetCreationTimeUtc(string path, DateTime creationTimeUtc) { FileSystem.SetFileTime(Ansible.IO.Path.GetFullPath(path), false, creationTimeUtc, null, null); }
        public static void SetLastAccessTime(string path, DateTime lastAccessTime) { SetLastAccessTimeUtc(path, lastAccessTime.ToUniversalTime()); }
        public static void SetLastAccessTimeUtc(string path, DateTime lastAccessTimeUtc) { FileSystem.SetFileTime(Ansible.IO.Path.GetFullPath(path), false, null, lastAccessTimeUtc, null); }
        public static void SetLastWriteTime(string path, DateTime lastWriteTime) { SetLastWriteTimeUtc(path, lastWriteTime.ToUniversalTime()); }
        public static void SetLastWriteTimeUtc(string path, DateTime lastWriteTimeUtc) { FileSystem.SetFileTime(Ansible.IO.Path.GetFullPath(path), false, null, null, lastWriteTimeUtc); }
        public static void WriteAllBytes(string path, byte[] bytes)
        {
            using (FileStream fs = Open(path, FileMode.Create, FileAccess.ReadWrite, FileShare.None))
                fs.Write(bytes, 0, bytes.Length);
        }
        public static void WriteAllLines(string path, IEnumerable<string> contents) { WriteAllLines(path, contents, DefaultEncoding); }
        public static void WriteAllLines(string path, IEnumerable<string> contents, Encoding encoding)
        {
            using (StreamWriter writer = WriteText(path, encoding))
                foreach (string line in contents)
                    writer.WriteLine(line);
        }
        public static void WriteAllLines(string path, string[] contents) { WriteAllLines(path, contents, DefaultEncoding); }
        public static void WriteAllLines(string path, string[] contents, Encoding encoding)
        {
            using (StreamWriter writer = WriteText(path, encoding))
                foreach (string line in contents)
                    writer.WriteLine(line);
        }
        public static void WriteAllText(string path, string contents) { WriteAllText(path, contents, DefaultEncoding); }
        public static void WriteAllText(string path, string contents, Encoding encoding)
        {
            using (StreamWriter writer = WriteText(path, encoding))
                writer.Write(contents);
        }
        public static StreamWriter WriteText(string path) { return WriteText(path, DefaultEncoding); }
        public static StreamWriter WriteText(string path, Encoding encoding) { return new StreamWriter(Open(path, FileMode.Create, FileAccess.ReadWrite, FileShare.None), encoding); }
    }

    public sealed class FileInfo : FileSystemInfo
    {
        private FileInfo() { }

        public FileInfo(string fileName) : this(fileName, isNormalized: false) { }

        internal FileInfo(string originalPath, string fullpath = null, string fileName = null, bool isNormalized = false)
        {
            if (originalPath == null)
                throw new ArgumentNullException("fileName");
            OriginalPath = originalPath;
            fullpath = fullpath ?? originalPath;
            FullPath = isNormalized ? fullpath ?? originalPath : Ansible.IO.Path.GetFullPath(fullpath);
            _name = fileName ?? Ansible.IO.Path.GetFileName(originalPath);
        }

        public DirectoryInfo Directory
        {
            get { return (DirectoryName == null) ? null : new DirectoryInfo(DirectoryName); }
        }
        public string DirectoryName
        {
            get { return Ansible.IO.Path.GetDirectoryName(FullPath); }
        }
        public bool IsReadOnly
        {
            get { return (Attributes.HasFlag(FileAttributes.ReadOnly)); }
            set
            {
                if (value)
                    Attributes |= FileAttributes.ReadOnly;
                else
                    Attributes &= ~FileAttributes.ReadOnly;
            }

        }
        public long DiskLength
        {
            get
            {
                if (Attributes.HasFlag(FileAttributes.Directory))
                    throw new FileNotFoundException(String.Format("Could not find file '{0}'.", FullPath), FullPath);
                return DiskLengthCore;
            }
        }
        public long Length
        {
            get
            {
                if (Attributes.HasFlag(FileAttributes.Directory))
                    throw new FileNotFoundException(String.Format("Could not find file '{0}'.", FullPath), FullPath);
                return LengthCore;
            }
        }

        public StreamWriter AppendText() { return File.AppendText(FullPath); }
        public FileInfo CopyTo(string destFileName) { return CopyTo(destFileName, false); }
        public FileInfo CopyTo(string destFileName, bool overwrite)
        {
            string destinationPath = Ansible.IO.Path.CheckAndGetFullPath(destFileName);
            FileSystem.CopyFile(FullPath, destinationPath, overwrite);
            return new FileInfo(destinationPath, isNormalized: true);
        }
        public FileStream Create() { return File.Create(FullPath); }
        public StreamWriter CreateText() { return File.CreateText(FullPath); }
        public void Decrypt() { FileSystem.Decrypt(FullPath); }
        public override void Delete() { File.Delete(FullPath); }
        public void Encrypt() { FileSystem.Encrypt(FullPath); }
        public FileSecurity GetAccessControl() { return GetAccessControl(AccessControlSections.Access | AccessControlSections.Group | AccessControlSections.Owner); }
        public FileSecurity GetAccessControl(AccessControlSections includeSelections) { return FileSystem.GetAccessControl<FileSecurity>(FullPath, includeSelections); }
        public List<StreamInformation> GetStreamInfo() { return FileSystem.GetStreamInfo(FullPath); }
        public void MoveTo(string destFileName)
        {
            string fullDestFileName = Ansible.IO.Path.CheckAndGetFullPath(destFileName);

            if (!Directory.Exists)
                throw new DirectoryNotFoundException(String.Format("Could not find a part of the path '{0}'.", FullName));
            if (!Exists)
                throw new FileNotFoundException(String.Format("Could not find file '{0}'.", FullName), FullName);
            FileSystem.MoveFile(FullName, fullDestFileName);

            FullPath = fullDestFileName;
            OriginalPath = destFileName;
            _name = Ansible.IO.Path.GetFileName(fullDestFileName);
            Invalidate();
        }
        public FileStream Open(FileMode mode) { return Open(mode, FileAccess.Read, FileShare.None); }
        public FileStream Open(FileMode mode, FileAccess access) { return Open(mode, access, FileShare.None); }
        public FileStream Open(FileMode mode, FileAccess access, FileShare share) { return File.Open(FullPath, mode, access, share); }
        public FileStream OpenRead() { return File.OpenRead(FullPath); }
        public StreamReader OpenText() { return File.OpenText(FullPath); }
        public FileStream OpenWrite() { return File.OpenWrite(FullPath); }
        public FileInfo Replace(string destinationFileName, string destinationBackupFileName) { return Replace(destinationFileName, destinationBackupFileName, false); }
        public FileInfo Replace(string destinationFileName, string destinationBackupFileName, bool ignoreMetadataErrors)
        {
            if (destinationFileName == null)
                throw new ArgumentNullException("destinationFileName");
            FileSystem.ReplaceFile(FullPath, Ansible.IO.Path.GetFullPath(destinationFileName),
                destinationBackupFileName != null ? Ansible.IO.Path.GetFullPath(destinationBackupFileName) : null,
                ignoreMetadataErrors);
            return new FileInfo(destinationFileName);
        }
        public void SetAccessControl(FileSecurity fileSecurity) { FileSystem.SetAccessControl(FullPath, fileSecurity); }
    }

    public static class Path
    {
        internal const char DirectorySeparatorChar = '\\';
        internal const char AltDirectorySeparatorChar = '/';

        public static string ChangeExtension(string path, string extension) { return System.IO.Path.ChangeExtension(path, extension); }
        public static string Combine(params string[] paths) { return System.IO.Path.Combine(paths); }
        public static string GetDirectoryName(string path)
        {
            if (path == null || IsEffectivelyEmpty(path))
                return null;

            int end = GetDirectoryNameOffset(path);
            return end >= 0 ? NormalizeDirectorySeparators(path.Substring(0, end)) : null;
        }
        public static string GetExtension(string path) { return System.IO.Path.GetExtension(path); }
        public static string GetFileName(string path) { return System.IO.Path.GetFileName(path); }
        public static string GetFileNameWithoutExtension(string path) { return System.IO.Path.GetFileNameWithoutExtension(path); }
        public static string GetFullPath(string path)
        {
            if (path == null)
                throw new ArgumentNullException("The path is not of a legal form.");
            else if (IsEffectivelyEmpty(path))
                throw new ArgumentException("The path is not of a legal form.");

            if (path.IndexOf('\0') != -1)
                throw new ArgumentException("The path is not of a legal form.", "path");

            // Actual .NET returns the path if \\?\ is used, this is different from the behaviour of GetFullPathNameW which resolves relative paths which we want
            UInt32 bufferLength = 0;
            StringBuilder lpBuffer = new StringBuilder();
            IntPtr lpFilePart = IntPtr.Zero;
            UInt32 returnLength = NativeMethods.GetFullPathNameW(path, bufferLength, lpBuffer, out lpFilePart);

            lpBuffer.EnsureCapacity((int)returnLength);
            returnLength = NativeMethods.GetFullPathNameW(path, returnLength, lpBuffer, out lpFilePart);
            if (returnLength == 0)
                throw new Win32Exception(Marshal.GetLastWin32Error(), String.Format("GetFullPathName({0}, {1}) failed when getting full path", path, returnLength));

            return lpBuffer.ToString();
        }
        public static char[] GetInvalidFileNameChars() { return System.IO.Path.GetInvalidFileNameChars(); }
        public static char[] GetInvalidPathChars() { return System.IO.Path.GetInvalidPathChars(); }
        public static string GetPathRoot(string path)
        {
            // Strip the extended length path prefix if present
            string pathPrefix = "";
            if (path.StartsWith(@"\\?\UNC\", true, System.Globalization.CultureInfo.InvariantCulture))
            {
                path = @"\\" + path.Substring(8);
                pathPrefix = @"\\?\UNC\";
            }
            else if (path.StartsWith(@"\\?\"))
            {
                path = path.Substring(4);
                pathPrefix = @"\\?\";
            }

            // Make sure we don't exceed 256 chars and get the root from there
            // the extra path info isn't needed 
            if (path.Length > 256)
                path = path.Substring(0, 256);
            string pathRoot = System.IO.Path.GetPathRoot(path);

            // Make sure the \\server is changed back to \\?\UNC\server
            if (pathPrefix == @"\\?\UNC\")
                return pathPrefix + pathRoot.Substring(2);
            else
                return pathPrefix + pathRoot;
        }
        public static string GetRandomFileName() { return System.IO.Path.GetRandomFileName(); }
        public static string GetTempFileName() { return System.IO.Path.GetTempFileName(); }
        public static string GetTempPath() { return System.IO.Path.GetTempPath(); }
        public static bool HasExtension(string path) { return System.IO.Path.HasExtension(path); }
        public static bool IsPathRooted(string path) { return System.IO.Path.IsPathRooted(path); }

        internal static string CheckAndGetFullPath(string path)
        {
            if (path == null)
                throw new ArgumentNullException("path");
            if (path.Length == 0)
                throw new ArgumentException("Path cannot be the empty string or all whitespace.", "path");
            return GetFullPath(path);
        }
        internal static int GetDirectoryNameOffset(string path)
        {
            int rootLength = GetPathRoot(path).Length;
            int end = path.Length;
            if (end <= rootLength)
                return -1;

            while (end > rootLength && !IsDirectorySeparator(path[--end])) ;

            // Trim off any remaining separators (to deal with C:\foo\\bar)
            while (end > rootLength && IsDirectorySeparator(path[end - 1]))
                end--;

            return end;
        }
        internal static bool IsDirectorySeparator(char c) { return c == DirectorySeparatorChar || c == AltDirectorySeparatorChar; }
        internal static bool IsEffectivelyEmpty(string path)
        {
            if (path.Length == 0)
                return true;

            foreach (char c in path)
                if (c != ' ')
                    return false;
            return true;
        }
        internal static string NormalizeDirectorySeparators(string path)
        {
            if (string.IsNullOrEmpty(path))
                return path;
            if (path.StartsWith(@"\\?\"))
                return path;

            char current;

            // Make a pass to see if we need to normalize so we can potentially skip allocating
            bool normalized = true;

            for (int i = 0; i < path.Length; i++)
            {
                current = path[i];
                if (IsDirectorySeparator(current)
                    && (current != DirectorySeparatorChar
                        // Check for sequential separators past the first position (we need to keep initial two for UNC/extended)
                        || (i > 0 && i + 1 < path.Length && IsDirectorySeparator(path[i + 1]))))
                {
                    normalized = false;
                    break;
                }
            }

            if (normalized)
                return path;

            StringBuilder builder = new StringBuilder(path.Length);
            int start = 0;
            if (IsDirectorySeparator(path[start]))
            {
                start++;
                builder.Append(DirectorySeparatorChar);
            }

            for (int i = start; i < path.Length; i++)
            {
                current = path[i];

                // If we have a separator
                if (IsDirectorySeparator(current))
                {
                    // If the next is a separator, skip adding this
                    if (i + 1 < path.Length && IsDirectorySeparator(path[i + 1]))
                        continue;

                    // Ensure it is the primary separator
                    current = DirectorySeparatorChar;
                }
                builder.Append(current);
            }
            return builder.ToString();
        }
        internal static string TrimEndingDirectorySeparator(string path)
        {
            return (path.Length > 0 && IsDirectorySeparator(path[path.Length - 1])) && !(GetPathRoot(path) == path)
                ? path.Substring(0, path.Length - 1)
                : path;
        }
    }

    public static class SparseFile
    {
        public static void AddSparseAttribute(string path) { FileSystem.SetSparseFlag(Ansible.IO.Path.CheckAndGetFullPath(path), true); }
        public static List<SparseAllocations> GetAllAllocations(string path)
        {
            Ansible.IO.FileInfo fileInfo = new Ansible.IO.FileInfo(path);
            return FileSystem.QuerySparseAllocatedRanges(fileInfo.FullName, 0, fileInfo.Length);
        }
        public static List<SparseAllocations> GetAllocations(string path, Int64 offset, Int64 length) { return FileSystem.QuerySparseAllocatedRanges(Ansible.IO.Path.CheckAndGetFullPath(path), offset, length); }
        public static long GetDiskSize(string path) { return new Ansible.IO.FileInfo(path).DiskLength; }
        public static long GetFileSize(string path) { return new Ansible.IO.FileInfo(path).Length; }

        public static bool IsSparseFile(string path) { return File.GetAttributes(Ansible.IO.Path.CheckAndGetFullPath(path)).HasFlag(FileAttributes.SparseFile); }
        public static void RemoveSparseAttribute(string path) { FileSystem.SetSparseFlag(Ansible.IO.Path.CheckAndGetFullPath(path), false); }
        public static void ZeroData(string path, Int64 offset, Int64 length) { FileSystem.SetSparseZeroData(Ansible.IO.Path.CheckAndGetFullPath(path), offset, length); }
    }
}
'@

Function Import-FileUtil {
    <#
    .SYNOPSIS
    Compiles the C# code that loads the Ansible.IO namespace. This namespace
    contains classes that replicate the main System.IO classes but adds the
    ability to use paths that exceed MAX_PATH. More specifically this loads
    the following classes

        Ansible.IO.Directory
        Ansible.IO.DirectoryInfo
        Ansible.IO.File
        Ansible.IO.FileInfo
        Ansible.IO.Path

    Also adds Ansible.IO.SparseFile that exposes methods that deal with sparse
    files.

    By default they won't automatically work with paths that exceed 260 chars
    but by prefixing an existing path with \\?\ it will work, e.g.

        'C:\temp' == '\\?\C:\temp'
        '\\server\share\path' == '\\?\UNC\server\share\path'

    This module util is reliant on Ansible.ModuleUtils.PrivilegeUtil. Do not
    call the Import-PrivilegeUtil function as this relies on that namespace
    not being used upon loading.
    #>

    # check if Ansible.IO is already loaded before trying again, this check is
    # required because it could already be loaded from calling Import-LinkUtil
    $namespace_loaded = [System.AppDomain]::CurrentDomain.GetAssemblies() | Where-Object { "Ansible.IO" -in $_.ExportedTypes.Namespace }
    if ($namespace_loaded) {
        return
    }

    # build the C# code to compile
    $namespaces = $ansible_privilege_util_namespaces + $ansible_file_util_namespaces | Select-Object -Unique
    $namespace_import = ($namespaces | ForEach-Object { "using $_;" }) -join "`r`n"
    $platform_util = "$namespace_import`r`n`r`n$ansible_privilege_util_code`r`n`r`n$ansible_file_util_code"

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
}

Function Test-AnsiblePath {
    <#
    .SYNOPSIS
    Due to an underlying issue in the .NET framework, the Test-Path cmdlet is
    unable to work with special locked files like C:\pagefile.sys and files
    exceeding MAX_PATH. This cmdlet is designed to work with these files.
    #>
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter()][ValidateSet("Any", "Container", "Leaf")][string]$PathType = "Any"
    )

    $ps_providers = (Get-PSDrive).Name | Where-Object { $_ -notmatch "^[A-Za-z]$" -and $Path.Startswith("$($_):", $true, [System.Globalization.CultureInfo]::InvariantCulture) }
    if ($null -ne $ps_providers) {
        # When testing a path like Cert:\LocalMachine\My, System.IO.File will
        # not work, we just revert back to using Test-Path for this
        return Test-Path -Path $Path -PathType $PathType
    }

    # Use the Ansible.IO.File functions to get the info on the file
    Import-FileUtil
    try {
        $file_attributes = [Ansible.IO.File]::GetAttributes($Path)
    } catch [System.IO.FileNotFoundException], [System.IO.DirectoryNotFoundException] {
        return $false
    } catch [System.NotSupportedException] {
        # potentially contains illegal characters, try with Test-Path as a fallback
        return Test-Path -Path $Path -PathType $PathType
    }
    # also throw IOException, and UnauthorizedAccessException but Test-Path does the same

    if ([Int32]$file_attributes -eq -1) {
        return $false
    } elseif ($PathType -eq "Any") {
        return $true
    } elseif ($PathType -eq "Container" -and $file_attributes.HasFlag([System.IO.FileAttributes]::Directory)) {
        return $true
    } elseif ($PathType -eq "Leaf" -and (-not $file_attributes.HasFlag([System.IO.FileAttributes]::Directory))) {
        return $true
    } else {
        return $false
    }
}

Function Get-AnsibleItem {
    <#
    .SYNOPSIS
    Due to an underlying issue in the .NET framework, the Get-Item cmdlet is
    unable to work with special locked files like C:\pagefile.sys. This cmdlet
    is designed to work with these files.
    #>
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory=$true)][string]$Path
    )
    Import-FileUtil

    # Replacement for Get-Item
    try {
        $file_attributes = [Ansible.IO.File]::GetAttributes($Path)
    } catch [System.IO.FileNotFoundException], [System.IO.DirectoryNotFoundException] {
        throw New-Object -TypeName System.Management.Automation.ItemNotFoundException -ArgumentList "Cannot find path '$Path' because it does not exist."
    }
    
    if ([Int32]$file_attributes -eq -1) {
        throw New-Object -TypeName System.Management.Automation.ItemNotFoundException -ArgumentList "Cannot find path '$Path' because it does not exist."
    } elseif ($file_attributes.HasFlag([System.IO.FileAttributes]::Directory)) {
        return New-Object -TypeName Ansible.IO.DirectoryInfo -ArgumentList $Path
    } else {
        return New-Object -TypeName Ansible.IO.FileInfo -ArgumentList $Path
    }
}

Function Get-AnsibleFileHash {
    <#
    .SYNOPSIS
    Get the hash of a file, also supports getting the hash of a file that
    exceeds MAX_PATH.
    #>#
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter()][string]$Algorithm = "sha1"
    )
    Import-FileUtil

    # Replacement for Get-FileHash
    $crypto_service_provider = "$($algorithm)CryptoServiceProvider"
    $sp = New-Object -TypeName System.Security.Cryptography.$crypto_service_provider
    $compute_method = $sp | Get-Member -Type Method | Where-Object { $_.Name -eq "ComputeHash" }
    if ($null -eq $compute_method) {
        throw New-Object -TypeName System.ArgumentException -ArgumentList "Unsupported hash algorithm supplied '$algorithm'"
    }

    $fs = [Ansible.IO.File]::Open($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::None)
    try {
        $hash = $sp.ComputeHash($fs)
        $hash_string = [System.BitConverter]::ToString($hash).Replace("-", "").ToLower()
    } finally {
        $fs.Close()
    }
    return $hash_string
}

Export-ModuleMember -Function Import-FileUtil, Test-AnsiblePath, Get-AnsibleItem, Get-AnsibleFileHash `
    -Variable ansible_file_util_namespaces, ansible_file_util_code
