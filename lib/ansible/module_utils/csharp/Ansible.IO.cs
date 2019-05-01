using Microsoft.Win32.SafeHandles;
using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.ConstrainedExecution;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Text;
using Ansible.Privilege;

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
        public enum GET_FILEEX_INFO_LEVELS
        {
            GetFileExInfoStandard,
            GetFileExMaxInfoLevel
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
        public enum ReplaceFlags : uint
        {
            REPLACEFILE_WRITE_THROUGH = 0x00000001,
            REPLACEFILE_IGNORE_MERGE_ERRORS = 0x00000002,
            REAPLCEFILE_IGNORE_ACL_ERRORS = 0x00000004,
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct FILETIME
        {
            internal UInt32 dwLowDateTime;
            internal UInt32 dwHighDateTime;

            public static implicit operator Int64(FILETIME v) { return ((Int64)v.dwHighDateTime << 32) + v.dwLowDateTime; }
            public static explicit operator DateTimeOffset(FILETIME v) { return DateTimeOffset.FromFileTime(v); }
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct WIN32_FILE_ATTRIBUTE_DATA
        {
            public Int32 dwFileAttributes;
            public FILETIME ftCreationTime;
            public FILETIME ftLastAccessTime;
            public FILETIME ftLastWriteTime;
            public UInt32 nFileSizeHigh;
            public UInt32 nFileSizeLow;
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
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
    }

    internal class NativeMethods
    {
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool CopyFileW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpExistingFileName,
            [MarshalAs(UnmanagedType.LPWStr)] string lpNewFileName,
            [MarshalAs(UnmanagedType.Bool)] bool bFailIfExists);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool CreateDirectoryW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpPathName,
            IntPtr lpSecurityAttributes);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern SafeFileHandle CreateFileW(
             [MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
             [MarshalAs(UnmanagedType.U4)] FileSystemRights dwDesiredAccess,
             [MarshalAs(UnmanagedType.U4)] FileShare dwShareMode,
             IntPtr lpSecurityAttributes,
             [MarshalAs(UnmanagedType.U4)] FileMode dwCreationDisposition,
             NativeHelpers.FlagsAndAttributes dwFlagsAndAttributes,
             IntPtr hTemplateFile);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool DeleteFileW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpFileName);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool FindClose(
            IntPtr hFindFile);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern SafeFindHandle FindFirstFileW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
            out NativeHelpers.WIN32_FIND_DATA lpFindFileData);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool FindNextFileW(
            SafeFindHandle hFindFile,
            out NativeHelpers.WIN32_FIND_DATA lpFindFileData);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool GetFileAttributesExW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
            NativeHelpers.GET_FILEEX_INFO_LEVELS fInfoLevelId,
            out NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA lpFileInformation);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern UInt32 GetFullPathNameW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
            UInt32 nBufferLength,
            StringBuilder lpBuffer,
            out IntPtr lpFilePart);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool MoveFileW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpExistingFileName,
            [MarshalAs(UnmanagedType.LPWStr)] string lpNewFileName);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool RemoveDirectoryW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpPathName);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool ReplaceFileW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpReplacedFileName,
            [MarshalAs(UnmanagedType.LPWStr)] string lpReplacementFileName,
            [MarshalAs(UnmanagedType.LPWStr)] string lpBackupFileName,
            NativeHelpers.ReplaceFlags dwReplaceFlags,
            IntPtr lpExclude,
            IntPtr lpReserved);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool SetFileAttributesW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
            FileAttributes dwFileAttributes);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool SetFileTime(
            SafeFileHandle hFile,
            ref Int64 lpCreationTime,
            ref Int64 lpLastAccessTime,
            ref Int64 lpLastWriteTime);
    }

    internal class SafeFindHandle : SafeHandleMinusOneIsInvalid
    {
        public SafeFindHandle() : base(true) { }
        public SafeFindHandle(IntPtr handle) : base(true) { this.handle = handle; }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.MayFail)]
        protected override bool ReleaseHandle()
        {
            return NativeMethods.FindClose(handle);
        }
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
                    string msg = new System.ComponentModel.Win32Exception(errorCode).Message;
                    return new IOException(
                        string.IsNullOrEmpty(path) ? msg : String.Format("{0}: '{1}'", msg, path), MakeHRFromErrorCode(errorCode));
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

    public class FileAttributeData
    {
        public FileAttributes FileAttributes;
        public DateTimeOffset CreationTime;
        public DateTimeOffset LastAccessTime;
        public DateTimeOffset LastWriteTime;
        public Int64 FileSize;
    }

    public static class FileSystem
    {
        /// <summary>
        /// Copies the whole directory to another directory. Links and their contents are copied as normal files to
        /// the dest path, broken links are copied as an empty dir or file.
        /// </summary>
        /// <param name="sourceFullPath">The path to the directory to copy.</param>
        /// <param name="destFullPath">The path to the directory to copy to.</param>
        /// <param name="recurse">Whether to copy the contents of the directory.</param>
        /// <param name="overwrite">Whether to overwrite any files in the dest path.</param>
        public static void CopyDirectory(string sourceFullPath, string destFullPath, bool recurse, bool overwrite)
        {
            // Validate the input parameters
            if (FileExists(sourceFullPath))
                throw new IOException(String.Format("The source path '{0}' is a file, not a directory.", sourceFullPath),
                    Win32Marshal.MakeHRFromErrorCode(Win32Errors.ERROR_ACCESS_DENIED));
            else if (FileExists(destFullPath))
                throw new IOException(String.Format("The target path '{0}' is a file, not a directory.", destFullPath),
                    Win32Marshal.MakeHRFromErrorCode(Win32Errors.ERROR_ACCESS_DENIED));
            else if (!DirectoryExists(sourceFullPath))
                throw Win32Marshal.GetExceptionForWin32Error(Win32Errors.ERROR_PATH_NOT_FOUND, sourceFullPath);
            if (!DirectoryExists(destFullPath))
                throw Win32Marshal.GetExceptionForWin32Error(Win32Errors.ERROR_PATH_NOT_FOUND, destFullPath);

            // Create the initial destination directory
            string destDirPath = Path.Combine(destFullPath, Path.GetFileName(sourceFullPath));
            if (!DirectoryExists(destDirPath))
                CreateDirectory(destDirPath);

            if (recurse)
            {
                foreach (Tuple<string, NativeHelpers.WIN32_FIND_DATA> find in EnumerateFolderInternal(sourceFullPath, "*",
                    SearchOption.TopDirectoryOnly, false))
                {
                    if (find.Item2.dwFileAttributes.HasFlag(FileAttributes.Directory))
                        CopyDirectory(find.Item1, destDirPath, true, overwrite);
                    else
                        CopyFile(find.Item1, Path.Combine(destDirPath, find.Item2.cFileName), overwrite);
                }
            }
        }

        /// <summary>
        /// Copies a file from the source to dest path.
        /// </summary>
        /// <param name="sourceFullPath">The source file to copy.</param>
        /// <param name="destFullPath">The destination path.</param>
        /// <param name="overwrite">Whether to overwrite the file at destFullPath if it already exists.</param>
        public static void CopyFile(string sourceFullPath, string destFullPath, bool overwrite)
        {
            CopyFileInternal(sourceFullPath, destFullPath, overwrite);
        }

        /// <summary>
        /// Creates a directory at the path specified. Will create parent directories if they do not already exist.
        /// </summary>
        /// <param name="fullPath">The path to create the directory at.</param>
        public static void CreateDirectory(string fullPath)
        {
            if (DirectoryExists(fullPath))
                return;

            Stack<string> dirsToCreate = new Stack<string>();
            string directoryRoot = Path.GetPathRoot(fullPath);
            string dir = fullPath;
            while (directoryRoot != dir)
            {
                if (DirectoryExists(dir))
                    break;
                dirsToCreate.Push(dir);
                dir = Path.GetDirectoryName(dir);
            }

            using (new PrivilegeEnabler(false, "SeRestorePrivilege", "SeTakeOwnershipPrivilege"))
            {
                while (dirsToCreate.Count > 0)
                {
                    dir = dirsToCreate.Pop();
                    if (!NativeMethods.CreateDirectoryW(dir, IntPtr.Zero))
                    {
                        int errorCode = Marshal.GetLastWin32Error();

                        // Do no fail if the error is ERROR_ALREADY_EXISTS and it is already a dir
                        if (!(errorCode == Win32Errors.ERROR_ALREADY_EXISTS && DirectoryExists(dir)))
                            throw Win32Marshal.GetExceptionForWin32Error(errorCode, dir);
                    }
                }
            }
        }

        /// <summary>
        /// Creates or opens a handle to the file specified. The way the system is opened is based on the mode set.
        /// </summary>
        /// <param name="path">The path to open the handle at.</param>
        /// <param name="mode">The System.IO.FileMode enum that specifies how the system should open a file.</param>
        /// <param name="access">The System.IO.FileAccess enum flags that specifies the access required.</param>
        /// <param name="share">The System.IO.FileShare enum flags that define the allowed access for newer handles on the same file.</param>
        /// <param name="options">The System.IO.FileOptions enum flags that specifies advanced options when opening a file.</param>
        /// <returns>SafeFileHandle of the file opened. Call .Dispose() to close the handle.</returns>
        public static SafeFileHandle CreateFile(string path, FileMode mode, FileAccess access, FileShare share, FileOptions options)
        {
            FileSystemRights accessRights;
            if (access == FileAccess.Read)
                accessRights = FileSystemRights.Read;
            else if (access == FileAccess.Write)
                accessRights = FileSystemRights.WriteData;
            else
                accessRights = FileSystemRights.ReadData | FileSystemRights.WriteData;

            NativeHelpers.FlagsAndAttributes attr = (NativeHelpers.FlagsAndAttributes)options;
            SafeFileHandle fileHandle = NativeMethods.CreateFileW(path, accessRights, share, IntPtr.Zero, mode, attr, IntPtr.Zero);
            if (fileHandle.IsInvalid)
                throw Win32Marshal.GetExceptionForLastWin32Error(path);
            return fileHandle;
        }

        /// <summary>
        /// Deletes the file at the path specified.
        /// </summary>
        /// <param name="fullPath">The file to delete.</param>
        public static void DeleteFile(string fullPath)
        {
            DeleteFileInternal(fullPath, retry: false);
        }

        /// <summary>
        /// Checks whether a directory already exists. 
        /// </summary>
        /// <param name="fullPath">The path to the directory to check.</param>
        /// <returns>System.Boolean that is true when a directory exists and false when it doesn't.</returns>
        public static bool DirectoryExists(string fullPath)
        {
            NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA data = new NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA();
            int lastError = FillAttributeInfo(fullPath, ref data, returnErrorOnNotFound: true);
            return (lastError == 0) && (data.dwFileAttributes != -1) && ((data.dwFileAttributes & (int)FileAttributes.Directory) != 0);
        }

        /// <summary>
        /// Enumerates the contents of the folder specified.
        /// </summary>
        /// <param name="path">The path to the directory to search in.</param>
        /// <param name="searchPattern">The search pattern, '?' is a wildcard for an individual char and '*' is a wildcard for multiple chars.</param>
        /// <param name="searchOption">The System.IO.SearchOption enum that states whether to search recursively or not.</param>
        /// <param name="returnFolders">Whether to return folders found in the search.</param>
        /// <param name="returnFiles">Whether to return files found in the search.</param>
        /// <returns>IEnumerable<string> of the path of each folder child item.</string></returns>
        public static IEnumerable<string> EnumerateFolder(string path, string searchPattern, SearchOption searchOption, bool returnFolders, bool returnFiles)
        {
            foreach (Tuple<string, NativeHelpers.WIN32_FIND_DATA> find in EnumerateFolderInternal(path, searchPattern, searchOption, false))
            {
                bool isDir = find.Item2.dwFileAttributes.HasFlag(FileAttributes.Directory);
                if (!returnFolders && isDir)
                    continue;
                else if (!returnFiles && !isDir)
                    continue;

                yield return find.Item1;
            }
        }

        /// <summary>
        /// Checks whether a file or directory already exists. 
        /// </summary>
        /// <param name="fullPath">The path to the file or directory to check.</param>
        /// <returns>System.Boolean that is true when a file or directory exists and false when it doesn't.</returns>
        public static bool Exists(string fullPath)
        {
            NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA data = new NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA();
            int errorCode = FillAttributeInfo(fullPath, ref data, returnErrorOnNotFound: true);
            return (errorCode == 0) && (data.dwFileAttributes != -1);
        }

        /// <summary>
        /// Checks whether a file already exists. 
        /// </summary>
        /// <param name="fullPath">The path to the file to check.</param>
        /// <returns>System.Boolean that is true when a file exists and false when it doesn't.</returns>
        public static bool FileExists(string fullPath)
        {
            NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA data = new NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA();
            int errorCode = FillAttributeInfo(fullPath, ref data, returnErrorOnNotFound: true);
            return (errorCode == 0) && (data.dwFileAttributes != -1) && ((data.dwFileAttributes & (int)FileAttributes.Directory) == 0);
        }

        /// <summary>
        /// Returns info on the file or directory specified.
        /// </summary>
        /// <param name="fullPath">The path to the file or directory to get the info on.</param>
        /// <returns>Ansible.IO.FileAttributeData that contains the attributes, size, and date stamps of the file or directory.</returns>
        public static FileAttributeData GetFileAttributeData(string fullPath)
        {
            NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA data = new NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA();
            FillAttributeInfo(fullPath, ref data, returnErrorOnNotFound: false);

            return new FileAttributeData()
            {
                FileAttributes = (FileAttributes)data.dwFileAttributes,
                CreationTime = (DateTimeOffset)data.ftCreationTime,
                LastAccessTime = (DateTimeOffset)data.ftLastAccessTime,
                LastWriteTime = (DateTimeOffset)data.ftLastWriteTime,
                FileSize = (Int64)((data.nFileSizeHigh) << 32 | data.nFileSizeLow & 0xFFFFFFFFL),
            };
        }

        /// <summary>
        /// Moves the file or directory to the path specified.
        /// </summary>
        /// <param name="sourceFullPath">The source path.</param>
        /// <param name="destFullPath">The destination path.</param>
        public static void MoveFile(string sourceFullPath, string destFullPath)
        {
            using (new PrivilegeEnabler(false, "SeBackupPrivilege", "SeRestorePrivilege", "SeTakeOwnershipPrivilege"))
            {
                if (!NativeMethods.MoveFileW(sourceFullPath, destFullPath))
                    RaiseExceptionForFileCopy(sourceFullPath, destFullPath);
            }
        }

        /// <summary>
        /// Removes the directory at the path specified.
        /// </summary>
        /// <param name="fullPath">The path to the directory to remove.</param>
        /// <param name="recursive">Set to true to delete a directory that is not empty.</param>
        public static void RemoveDirectory(string fullPath, bool recursive)
        {
            // Typically we only set this when actually doing the native call but this has a lot of recursive
            // functions that can rely on these privileges so we just set it at the parent level.
            using (new PrivilegeEnabler(false, "SeBackupPrivilege", "SeRestorePrivilege", "SeTakeOwnershipPrivilege"))
            {
                if (!recursive)
                {
                    RemoveDirectoryInternal(fullPath, topLevel: true);
                    return;
                }

                NativeHelpers.WIN32_FIND_DATA findData = new NativeHelpers.WIN32_FIND_DATA();
                GetFindData(fullPath, ref findData);
                if (IsNameSurrogateReparsePoint(findData))
                    // Don't recurse
                    RemoveDirectoryInternal(fullPath, topLevel: true);
                else
                    RemoveDirectoryRecursive(fullPath, ref findData, topLevel: true);
            }
        }

        /// <summary>
        /// Replaces and creates an optional backup of a file.
        /// </summary>
        /// <param name="sourceFullPath">The path to the file that will replace the file.</param>
        /// <param name="destFullPath">The path to the file that will be replaced.</param>
        /// <param name="destBackupFullPath">An optional path that will be a backup of destFullPath is set.</param>
        /// <param name="ignoreMetadataErrors">Whether to ignore metadata merging from source to dest on replacement.</param>
        public static void ReplaceFile(string sourceFullPath, string destFullPath, string destBackupFullPath, bool ignoreMetadataErrors)
        {
            // Make sure destBackupFullPath is null, PowerShell marshaling changes $null to "" which we don't want.
            destBackupFullPath = String.IsNullOrEmpty(destBackupFullPath) ? null : destBackupFullPath;
            NativeHelpers.ReplaceFlags flags = ignoreMetadataErrors ? NativeHelpers.ReplaceFlags.REPLACEFILE_IGNORE_MERGE_ERRORS : 0;

            using (new PrivilegeEnabler(false, "SeBackupPrivilege", "SeRestorePrivilege", "SeTakeOwnershipPrivilege"))
            {
                if (!NativeMethods.ReplaceFileW(destFullPath, sourceFullPath, destBackupFullPath, flags, IntPtr.Zero, IntPtr.Zero))
                    RaiseExceptionForFileCopy(sourceFullPath, destFullPath);
            }
        }

        /// <summary>
        /// Sets the attributes of the file or directory specified.
        /// </summary>
        /// <param name="fullPath">The path of the file or directory to set the attributes for.</param>
        /// <param name="attributes">The System.IO.FileAttributes to set, some attributes cannot be set this way.</param>
        public static void SetAttributes(string fullPath, FileAttributes attributes)
        {
            using (new PrivilegeEnabler(false, "SeRestorePrivilege"))
            {
                if (!NativeMethods.SetFileAttributesW(fullPath, attributes))
                {
                    int errorCode = Marshal.GetLastWin32Error();
                    if (errorCode == Win32Errors.ERROR_INVALID_PARAMETER)
                        throw new ArgumentException("Invalid File or Directory attributes value.", "attributes");
                    throw Win32Marshal.GetExceptionForWin32Error(errorCode, fullPath);
                }
            }
        }

        /// <summary>
        /// Sets the datestamps of the file or directory specified.
        /// </summary>
        /// <param name="fullPath">The path of the file or directory to set the datestamps for.</param>
        /// <param name="creationTime">The creation time of the file, set to null to not set/change.</param>
        /// <param name="lastAccessTime">The last access time of the file, set to null to not set/change.</param>
        /// <param name="lastWriteTime">The last write time of the file, set to null to not set/change.</param>
        public static void SetFileTime(string fullPath, DateTime? creationTime, DateTime? lastAccessTime, DateTime? lastWriteTime)
        {
            using (new PrivilegeEnabler(false, "SeRestorePrivilege"))
            using (SafeFileHandle handle = NativeMethods.CreateFileW(fullPath, FileSystemRights.WriteAttributes, FileShare.ReadWrite | FileShare.Delete,
                IntPtr.Zero, FileMode.Open, NativeHelpers.FlagsAndAttributes.FILE_FLAG_BACKUP_SEMANTICS, IntPtr.Zero))
            {
                if (handle.IsInvalid)
                    throw Win32Marshal.GetExceptionForLastWin32Error(fullPath);
                Int64 creation = creationTime.HasValue ? creationTime.Value.ToFileTimeUtc() : 0;
                Int64 access = lastAccessTime.HasValue ? lastAccessTime.Value.ToFileTimeUtc() : 0;
                Int64 write = lastWriteTime.HasValue ? lastWriteTime.Value.ToFileTimeUtc() : 0;

                if (!NativeMethods.SetFileTime(handle, ref creation, ref access, ref write))
                    throw Win32Marshal.GetExceptionForLastWin32Error(fullPath);
            }
        }

        private static void CopyFileInternal(string sourceFullPath, string destFullPath, bool overwrite, bool retry = false)
        {
            bool res = NativeMethods.CopyFileW(sourceFullPath, destFullPath, !overwrite);
            int errorCode = Marshal.GetLastWin32Error();

            if (!res)
            {
                if (FileExists(sourceFullPath) && FileExists(destFullPath) && errorCode == Win32Errors.ERROR_ACCESS_DENIED)
                {
                    RemoveReadOnlyAndHidden(destFullPath, errorCode, retry);
                    CopyFileInternal(sourceFullPath, destFullPath, overwrite, retry: true);
                }
                else if (FileExists(sourceFullPath) && errorCode == Win32Errors.ERROR_FILE_NOT_FOUND)
                {
                    // Source file is a broken file symlink, we just create an empty file as a placeholder.
                    FileMode createMode = overwrite ? FileMode.Create : FileMode.CreateNew;
                    SafeFileHandle handle = CreateFile(destFullPath, createMode, FileAccess.Write,
                        FileShare.None, FileOptions.None);
                    handle.Dispose();
                }
                else
                {
                    RaiseExceptionForFileCopy(sourceFullPath, destFullPath, errorCode: errorCode);
                }
            }
        }

        private static void DeleteFileInternal(string fullPath, bool retry = false)
        {
            bool res;
            int errorCode = 0;
            using (new PrivilegeEnabler(false, "SeRestorePrivilege", "SeTakeOwnershipPrivilege"))
            {
                res = NativeMethods.DeleteFileW(fullPath);
                errorCode = Marshal.GetLastWin32Error();
            }

            if (!res)
            {
                if (errorCode == Win32Errors.ERROR_ACCESS_DENIED)
                {
                    RemoveReadOnlyAndHidden(fullPath, errorCode, retry);
                    DeleteFileInternal(fullPath, retry: true);
                }
                else if (errorCode != Win32Errors.ERROR_FILE_NOT_FOUND)
                    throw Win32Marshal.GetExceptionForWin32Error(errorCode, fullPath);
            }
        }

        private static IEnumerable<Tuple<string, NativeHelpers.WIN32_FIND_DATA>> EnumerateFolderInternal(string path, string searchPattern,
            SearchOption searchOption, bool strict)
        {
            Queue<string> dirs = new Queue<string>();
            dirs.Enqueue(path);

            while (dirs.Count > 0)
            {
                string currentPath = dirs.Dequeue();

                // We need to manually get all directories if AllDirectories is specified. We can't rely on the
                // enumeration below as the searchPattern may not be '*'.
                if (searchOption == SearchOption.AllDirectories)
                {
                    foreach (var directory in EnumerateFolderInternal(currentPath, "*", SearchOption.TopDirectoryOnly, strict))
                    {
                        if (directory.Item2.dwFileAttributes.HasFlag(FileAttributes.Directory))
                            dirs.Enqueue(directory.Item1);
                    }
                }

                // Now search the directory based on the actual input search pattern.
                string searchPath = Path.Combine(currentPath, Path.TrimEndingDirectorySeparator(searchPattern));

                NativeHelpers.WIN32_FIND_DATA findData = new NativeHelpers.WIN32_FIND_DATA();
                using (new PrivilegeEnabler(false, "SeBackupPrivilege"))
                using (SafeFindHandle findHandle = NativeMethods.FindFirstFileW(searchPath, out findData))
                {
                    if (findHandle.IsInvalid)
                    {
                        if (strict)
                            throw Win32Marshal.GetExceptionForLastWin32Error(path);
                        else
                            continue;
                    }

                    do
                    {
                        string fileName = findData.cFileName;
                        string filePath = Path.Combine(currentPath, fileName);
                        FileAttributes attr = findData.dwFileAttributes;

                        if (attr.HasFlag(FileAttributes.Directory) && (fileName == "." || fileName == ".."))
                            continue;

                        yield return Tuple.Create<string, NativeHelpers.WIN32_FIND_DATA>(filePath, findData);
                    } while (NativeMethods.FindNextFileW(findHandle, out findData));

                    int lastErr = Marshal.GetLastWin32Error();
                    if (lastErr != Win32Errors.ERROR_NO_MORE_FILES)
                        throw Win32Marshal.GetExceptionForWin32Error(lastErr);
                }
            }
        }

        private static int FillAttributeInfo(string path, ref NativeHelpers.WIN32_FILE_ATTRIBUTE_DATA data, bool returnErrorOnNotFound)
        {
            // Remove any trailing separators
            path = Path.TrimEndingDirectorySeparator(path);
            int errorCode = Win32Errors.ERROR_SUCCESS;
            using (new PrivilegeEnabler(false, "SeBackupPrivilege"))
            {
                if (!NativeMethods.GetFileAttributesExW(path, NativeHelpers.GET_FILEEX_INFO_LEVELS.GetFileExInfoStandard, out data))
                {
                    errorCode = Marshal.GetLastWin32Error();
                    // special system files like pagefile.sys returns
                    // ERROR_SHARING_VIOLATION but FindFirstFileW works so we try
                    // that here
                    if (errorCode == Win32Errors.ERROR_SHARING_VIOLATION)
                    {
                        NativeHelpers.WIN32_FIND_DATA findData;
                        using (SafeFindHandle findHandle = NativeMethods.FindFirstFileW(path, out findData))
                        {
                            if (findHandle.IsInvalid)
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
                }
            }

            if (errorCode != Win32Errors.ERROR_SUCCESS && !returnErrorOnNotFound)
                throw Win32Marshal.GetExceptionForWin32Error(errorCode, path);

            return errorCode;
        }

        private static void GetFindData(string fullPath, ref NativeHelpers.WIN32_FIND_DATA findData)
        {
            using (new PrivilegeEnabler(false, "SeBackupPrivilege"))
            using (SafeFindHandle handle = NativeMethods.FindFirstFileW(fullPath, out findData))
            {
                if (handle.IsInvalid)
                {
                    int errorCode = Marshal.GetLastWin32Error();
                    // File not found doesn't make much sense coming from a directory delete.
                    if (errorCode == Win32Errors.ERROR_FILE_NOT_FOUND)
                        errorCode = Win32Errors.ERROR_PATH_NOT_FOUND;
                    throw Win32Marshal.GetExceptionForWin32Error(errorCode, fullPath);
                }
            }
        }

        private static bool IsNameSurrogateReparsePoint(NativeHelpers.WIN32_FIND_DATA data)
        {
            // Reparse points that are not name surrogates should be treated like any other directory
            return data.dwFileAttributes.HasFlag(FileAttributes.ReparsePoint) && (data.dwReserved0 & 0x20000000) != 0;
        }

        private static void RemoveDirectoryRecursive(string fullPath, ref NativeHelpers.WIN32_FIND_DATA findData, bool topLevel)
        {
            Exception exception = null;

            foreach (Tuple<string, NativeHelpers.WIN32_FIND_DATA> find in EnumerateFolderInternal(fullPath, "*", SearchOption.TopDirectoryOnly, true))
            {
                string filePath = find.Item1;
                findData = find.Item2;

                bool isDir = findData.dwFileAttributes.HasFlag(FileAttributes.Directory);
                if (isDir)
                {
                    try
                    {
                        if (IsNameSurrogateReparsePoint(findData))
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
                else
                    DeleteFile(filePath);
            }

            if (exception != null)
                throw exception;

            RemoveDirectoryInternal(fullPath, topLevel: topLevel, allowDirectoryNotEmpty: true);
        }

        private static void RaiseExceptionForFileCopy(string sourcePath, string destPath, int? errorCode = null)
        {
            // Copy and move operations have 2 paths where the problem could lie, we default to having the destPath
            // being the problematic one but still check for cases where sourcePath is a better file.
            int win32Error = errorCode == null ? Marshal.GetLastWin32Error() : (int)errorCode;

            string fileName = destPath;
            if (errorCode != Win32Errors.ERROR_FILE_EXISTS)
            {
                // For some error codes we don't know if the problem was source or dest, try reading source to
                // rule it out.
                using (SafeFileHandle handle = NativeMethods.CreateFileW(sourcePath, FileSystemRights.Read,
                    FileShare.Read, IntPtr.Zero, FileMode.Open, 0, IntPtr.Zero))
                {
                    if (handle.IsInvalid)
                        fileName = sourcePath;
                }

                // Special case when trying to copy/move a file to a dir
                if (errorCode == Win32Errors.ERROR_ACCESS_DENIED)
                {
                    string msg = null;
                    if (FileSystem.DirectoryExists(sourcePath))
                        msg = String.Format("The source file '{0}' is a directory, not a file.", sourcePath);
                    else if (FileSystem.DirectoryExists(destPath))
                        msg = String.Format("The target file '{0}' is a directory, not a file.", destPath);

                    if (msg != null)
                        throw new IOException(msg, Win32Marshal.MakeHRFromErrorCode(win32Error));
                }
            }

            throw Win32Marshal.GetExceptionForWin32Error(win32Error, fileName);
        }

        private static void RemoveDirectoryInternal(string fullPath, bool topLevel, bool allowDirectoryNotEmpty = false, bool retry = false)
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
                        RemoveReadOnlyAndHidden(fullPath, errorCode, retry);
                        RemoveDirectoryInternal(fullPath, topLevel, allowDirectoryNotEmpty, retry: true);
                        return;
                }
                throw Win32Marshal.GetExceptionForWin32Error(errorCode, fullPath);
            }
        }

        private static void RemoveReadOnlyAndHidden(string fullPath, int errorCode, bool retry)
        {
            // Delete operations can fail if ReadOnly is set as an attribute on the object. We try and this attribute
            // before trying the deletion again.
            try
            {
                FileAttributes existingAttributes = GetFileAttributeData(fullPath).FileAttributes;

                bool isUnset = (existingAttributes & FileAttributes.ReadOnly) == 0 &&
                    (existingAttributes & FileAttributes.Hidden) == 0;
                if (retry || isUnset)
                    // This is the 2nd call to the delete operation or ReadOnly/Hidden is not set,
                    // raise the original excep.
                    throw Win32Marshal.GetExceptionForWin32Error(errorCode, fullPath);

                SetAttributes(fullPath, existingAttributes & ~FileAttributes.ReadOnly & ~FileAttributes.Hidden);
            }
            catch (Exception)
            {
                // Failed to perform the prepartion task, just raise the original exception.
                throw Win32Marshal.GetExceptionForWin32Error(errorCode, fullPath);
            }
        }
    }

    /// <summary>
    /// Meant to be a very close copy of System.IO.Path but support paths exceeding MAX_PATH.
    /// </summary>
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
                throw Win32Marshal.GetExceptionForLastWin32Error(path);

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
}

