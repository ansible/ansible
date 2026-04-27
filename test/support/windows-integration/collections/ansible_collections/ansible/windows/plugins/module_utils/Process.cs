using Microsoft.Win32.SafeHandles;
using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;

//TypeAccelerator -Name Ansible.Windows.Process.ProcessInformation -TypeName ProcessInformation
//TypeAccelerator -Name Ansible.Windows.Process.ProcessUtil -TypeName ProcessUtil
//TypeAccelerator -Name Ansible.Windows.Process.Result -TypeName Result
//TypeAccelerator -Name Ansible.Windows.Process.SecurityAttributes -TypeName SecurityAttributes
//TypeAccelerator -Name Ansible.Windows.Process.StartupInfo -TypeName StartupInfo

namespace ansible_collections.ansible.windows.plugins.module_utils.Process
{
    internal class NativeHelpers
    {
        [StructLayout(LayoutKind.Sequential)]
        public struct JOBOBJECT_ASSOCIATE_COMPLETION_PORT
        {
            public IntPtr CompletionKey;
            public IntPtr CompletionPort;
        }

        [StructLayout(LayoutKind.Sequential)]
        public class SECURITY_ATTRIBUTES
        {
            public UInt32 nLength;
            public IntPtr lpSecurityDescriptor;
            public bool bInheritHandle = false;
            public SECURITY_ATTRIBUTES()
            {
                nLength = (UInt32)Marshal.SizeOf(this);
            }
        }

        [StructLayout(LayoutKind.Sequential)]
        public class STARTUPINFOW
        {
            public UInt32 cb;
            public IntPtr lpReserved;
            [MarshalAs(UnmanagedType.LPWStr)] public string lpDesktop;
            [MarshalAs(UnmanagedType.LPWStr)] public string lpTitle;
            public UInt32 dwX;
            public UInt32 dwY;
            public UInt32 dwXSize;
            public UInt32 dwYSize;
            public UInt32 dwXCountChars;
            public UInt32 dwYCountChars;
            public UInt32 dwFillAttribute;
            public StartupInfoFlags dwFlags;
            public UInt16 wShowWindow;
            public UInt16 cbReserved2;
            public IntPtr lpReserved2;
            public SafeHandle hStdInput = new SafeNativeHandle(IntPtr.Zero, false);
            public SafeHandle hStdOutput = new SafeNativeHandle(IntPtr.Zero, false);
            public SafeHandle hStdError = new SafeNativeHandle(IntPtr.Zero, false);

            public STARTUPINFOW()
            {
                cb = (UInt32)Marshal.SizeOf(this);
            }
        }

        [StructLayout(LayoutKind.Sequential)]
        public class STARTUPINFOEX
        {
            public STARTUPINFOW startupInfo;
            public SafeHandle lpAttributeList = new SafeNativeHandle(IntPtr.Zero, false);
            public STARTUPINFOEX()
            {
                startupInfo = new STARTUPINFOW();
                startupInfo.cb = (UInt32)Marshal.SizeOf(this);
            }
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct PROCESS_INFORMATION
        {
            public IntPtr hProcess;
            public IntPtr hThread;
            public int dwProcessId;
            public int dwThreadId;
        }


        [Flags]
        public enum DuplicateHandleOptions : uint
        {
            NONE = 0x0000000,
            DUPLICATE_CLOSE_SOURCE = 0x00000001,
            DUPLICATE_SAME_ACCESS = 0x00000002,
        }

        public enum JobObjectInformationClass : uint
        {
            JobObjectAssociateCompletionPortInformation = 7,
        }

        [Flags]
        public enum StartupInfoFlags : uint
        {
            STARTF_USESHOWWINDOW = 0x00000001,
            USESTDHANDLES = 0x00000100,
        }

        [Flags]
        public enum HandleFlags : uint
        {
            None = 0,
            INHERIT = 1
        }
    }

    internal class NativeMethods
    {
        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool AllocConsole();

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool AssignProcessToJobObject(
            SafeHandle hJob,
            IntPtr hProcess);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool CloseHandle(
            IntPtr hObject);

        [DllImport("shell32.dll", SetLastError = true)]
        public static extern SafeMemoryBuffer CommandLineToArgvW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpCmdLine,
            out int pNumArgs);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern SafeNativeHandle CreateIoCompletionPort(
            IntPtr FileHandle,
            IntPtr ExistingCompletionPort,
            UIntPtr CompletionKey,
            UInt32 NumberOfConcurrentThreads);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern SafeNativeHandle CreateJobObjectW(
            IntPtr lpJobAttributes,
            string lpName);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool CreatePipe(
            out SafeFileHandle hReadPipe,
            out SafeFileHandle hWritePipe,
            NativeHelpers.SECURITY_ATTRIBUTES lpPipeAttributes,
            UInt32 nSize);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool CreateProcessW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpApplicationName,
            StringBuilder lpCommandLine,
            SafeMemoryBuffer lpProcessAttributes,
            SafeMemoryBuffer lpThreadAttributes,
            bool bInheritHandles,
            ProcessCreationFlags dwCreationFlags,
            SafeMemoryBuffer lpEnvironment,
            [MarshalAs(UnmanagedType.LPWStr)] string lpCurrentDirectory,
            NativeHelpers.STARTUPINFOEX lpStartupInfo,
            out NativeHelpers.PROCESS_INFORMATION lpProcessInformation);

        [DllImport("kernel32.dll")]
        public static extern void DeleteProcThreadAttributeList(
            IntPtr lpAttributeList);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool DuplicateHandle(
            SafeHandle hSourceProcessHandle,
            SafeHandle hSourceHandle,
            SafeHandle hTargetProcessHandle,
            out IntPtr lpTargetHandle,
            UInt32 dwDesiredAccess,
            bool bInheritHandle,
            NativeHelpers.DuplicateHandleOptions dwOptions);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool FreeConsole();

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern IntPtr GetConsoleWindow();

        [DllImport("kernel32.dll")]
        public static extern IntPtr GetCurrentProcess();

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool GetExitCodeProcess(
            SafeHandle hProcess,
            out UInt32 lpExitCode);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool GetQueuedCompletionStatus(
            SafeHandle CompletionPort,
            out UInt32 lpNumberOfBytesTransferred,
            out UIntPtr lpCompletionKey,
            out IntPtr lpOverlapped,
            UInt32 dwMilliseconds);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool InitializeProcThreadAttributeList(
            IntPtr lpAttributeList,
            Int32 dwAttributeCount,
            UInt32 dwFlags,
            ref IntPtr lpSize);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern SafeNativeHandle OpenProcess(
            Int32 dwDesiredAccess,
            bool bInheritHandle,
            Int32 dwProcessId);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern UInt32 ResumeThread(
            SafeHandle hThread);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool SetConsoleCP(
            UInt32 wCodePageID);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool SetConsoleOutputCP(
            UInt32 wCodePageID);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool SetHandleInformation(
            SafeHandle hObject,
            NativeHelpers.HandleFlags dwMask,
            NativeHelpers.HandleFlags dwFlags);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool SetInformationJobObject(
            SafeHandle hJob,
            NativeHelpers.JobObjectInformationClass JobObjectInformationClass,
            IntPtr lpJobObjectInformation,
            Int32 cbJobObjectInformationLength);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool UpdateProcThreadAttribute(
            SafeHandle lpAttributeList,
            UInt32 dwFlags,
            UIntPtr Attribute,
            SafeHandle lpValue,
            UIntPtr cbSize,
            IntPtr lpPreviousValue,
            IntPtr lpReturnSize);

        [DllImport("kernel32.dll")]
        public static extern UInt32 WaitForSingleObject(
            SafeHandle hHandle,
            UInt32 dwMilliseconds);
    }

    internal class SafeDuplicateHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        private readonly SafeHandle _process;
        private readonly bool _ownsHandle;

        public SafeDuplicateHandle(IntPtr handle, SafeHandle process) : this(handle, process, true) { }

        public SafeDuplicateHandle(IntPtr handle, SafeHandle process, bool ownsHandle) : base(true)
        {
            SetHandle(handle);
            _process = process;
            _ownsHandle = ownsHandle;
        }

        protected override bool ReleaseHandle()
        {
            if (_ownsHandle)
            {
                // Cannot pass this SafeHandle object to DuplicateHandle as it
                // will appeared as closed/invalid already. Use a temporary
                // SafeHandle that is set not to dispose itself.
                ProcessUtil.DuplicateHandle(
                    _process,
                    new SafeNativeHandle(handle, false),
                    null,
                    0,
                    false,
                    NativeHelpers.DuplicateHandleOptions.DUPLICATE_CLOSE_SOURCE,
                    false);
                _process.Dispose();
            }
            return true;
        }
    }

    internal class SafeMemoryBuffer : SafeHandleZeroOrMinusOneIsInvalid
    {
        public SafeMemoryBuffer() : base(true) { }
        public SafeMemoryBuffer(int cb) : base(true)
        {
            base.SetHandle(Marshal.AllocHGlobal(cb));
        }
        public SafeMemoryBuffer(IntPtr handle) : base(true)
        {
            base.SetHandle(handle);
        }

        protected override bool ReleaseHandle()
        {
            Marshal.FreeHGlobal(handle);
            return true;
        }
    }

    internal class SafeProcThreadAttribute : SafeHandleZeroOrMinusOneIsInvalid
    {
        internal List<SafeHandle> values = new List<SafeHandle>();

        public SafeProcThreadAttribute() : base(true) { }
        public SafeProcThreadAttribute(IntPtr preexistingHandle, bool ownsHandle) : base(ownsHandle)
        {
            SetHandle(preexistingHandle);
        }

        public void AddValue(SafeHandle value)
        {
            values.Add(value);
        }

        protected override bool ReleaseHandle()
        {
            foreach (SafeHandle val in values)
            {
                val.Dispose();
            }

            NativeMethods.DeleteProcThreadAttributeList(handle);
            Marshal.FreeHGlobal(handle);

            return true;
        }
    }

    [Flags]
    public enum ProcessCreationFlags : uint
    {
        None = 0x00000000,
        DebugProcess = 0x00000001,
        DebugOnlyThisProcess = 0x00000002,
        CreateSuspended = 0x00000004,
        DetachedProcess = 0x00000008,
        CreateNewConsole = 0x00000010,
        NormalPriorityClass = 0x00000020,
        IdlePriorityClass = 0x00000040,
        HighPriorityClass = 0x00000080,
        RealtimePriorityClass = 0x00000100,
        CreateNewProcessGroup = 0x00000200,
        CreateUnicodeEnvironment = 0x00000400,
        CreateSeparateWowVdm = 0x00000800,
        CreateSharedWowVdm = 0x00001000,
        CreateForceDos = 0x00002000,
        BelowNormalPriorityClass = 0x00004000,
        AboveNormalPriorityClass = 0x00008000,
        InheritParentAffinity = 0x00010000,
        InheritCallerPriority = 0x00020000,
        CreateProtectedProcess = 0x00040000,
        ExtendedStartupInfoPresent = 0x00080000,
        ProcessModeBackgroundBegin = 0x00100000,
        ProcessModeBackgroundEnd = 0x00200000,
        CreateSecureProcess = 0x00400000,
        CreateBreakawayFromJob = 0x01000000,
        CreatePreserveCodeAuthzLevel = 0x02000000,
        CreateDefaultErrorMode = 0x04000000,
        CreateNoWindow = 0x08000000,
        ProfileUser = 0x10000000,
        ProfileKernel = 0x20000000,
        ProfileServer = 0x40000000,
        CreateIgnoreSystemDefault = 0x80000000,
    }

    public class SafeNativeHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        public SafeNativeHandle() : base(true) { }
        public SafeNativeHandle(IntPtr handle) : this(handle, true) { }
        public SafeNativeHandle(IntPtr handle, bool ownsHandle) : base(ownsHandle) { this.handle = handle; }

        protected override bool ReleaseHandle()
        {
            return NativeMethods.CloseHandle(handle);
        }
    }

    public class Win32Exception : System.ComponentModel.Win32Exception
    {
        private string _msg;

        public Win32Exception(string message) : this(Marshal.GetLastWin32Error(), message) { }
        public Win32Exception(int errorCode, string message) : base(errorCode)
        {
            _msg = String.Format("{0} ({1}, Win32ErrorCode {2} - 0x{2:X8})", message, base.Message, errorCode);
        }

        public override string Message { get { return _msg; } }
        public static explicit operator Win32Exception(string message) { return new Win32Exception(message); }
    }

    public class Result
    {
        public string StandardOut { get; internal set; }
        public string StandardError { get; internal set; }
        public uint ExitCode { get; internal set; }
    }

    public class ProcessInformation : IDisposable
    {
        public SafeNativeHandle Process { get; internal set; }
        public SafeNativeHandle Thread { get; internal set; }
        public int ProcessId { get; internal set; }
        public int ThreadId { get; internal set; }

        public void Dispose()
        {
            if (Process != null)
                Process.Dispose();

            if (Thread != null)
                Thread.Dispose();

            GC.SuppressFinalize(this);
        }
        ~ProcessInformation() { Dispose(); }
    }

    public class SecurityAttributes
    {
        public bool InheritHandle { get; set; }
        // TODO: Support SecurityDescriptor at some point.
        // Should it use RawSecurityDescriptor or create a Process SD class that inherits NativeObjectSecurity?
    }

    public class StartupInfo
    {
        public string Desktop { get; set; }
        public string Title { get; set; }
        public ProcessWindowStyle? WindowStyle { get; set; }
        public SafeHandle StandardInput { get; set; }
        public SafeHandle StandardOutput { get; set; }
        public SafeHandle StandardError { get; set; }
        public int ParentProcess { get; set; }

        // TODO: Support PROC_THREAD_ATTRIBUTE_HANDLE_LIST
    }

    public class ProcessUtil
    {
        /// <summary>
        /// Parses a command line string into an argv array according to the Windows rules
        /// </summary>
        /// <param name="lpCommandLine">The command line to parse</param>
        /// <returns>An array of arguments interpreted by Windows</returns>
        public static string[] CommandLineToArgv(string lpCommandLine)
        {
            int numArgs;
            using (SafeMemoryBuffer buf = NativeMethods.CommandLineToArgvW(lpCommandLine, out numArgs))
            {
                if (buf.IsInvalid)
                    throw new Win32Exception("Error parsing command line");
                IntPtr[] strptrs = new IntPtr[numArgs];
                Marshal.Copy(buf.DangerousGetHandle(), strptrs, 0, numArgs);
                return strptrs.Select(s => Marshal.PtrToStringUni(s)).ToArray();
            }
        }

        /// <summary>
        /// Creates a process based on the CreateProcess API call and wait for it to complete.
        /// </summary>
        /// <param name="lpApplicationName">The name of the executable or batch file to execute</param>
        /// <param name="lpCommandLine">The command line to execute, typically this includes lpApplication as the first argument</param>
        /// <param name="lpCurrentDirectory">The full path to the current directory for the process, null will have the same cwd as the calling process</param>
        /// <param name="environment">A dictionary of key/value pairs to define the new process environment</param>
        /// <param name="stdin">A byte array to send over the stdin pipe</param>
        /// <param name="outputEncoding">The character encoding for decoding stdout/stderr output of the process.</param>
        /// <param name="waitChildren">Whether to wait for any children spawned by the process to finished (Server2012 +).</param>
        /// <returns>Result object that contains the command output and return code</returns>
        public static Result CreateProcess(string lpApplicationName, string lpCommandLine, string lpCurrentDirectory,
            IDictionary environment, byte[] stdin, string outputEncoding, bool waitChildren)
        {
            ProcessCreationFlags creationFlags = ProcessCreationFlags.CreateSuspended |
                ProcessCreationFlags.CreateUnicodeEnvironment;
            StartupInfo si = new StartupInfo();
            ProcessInformation pi = null;

            SafeFileHandle stdoutRead, stdoutWrite, stderrRead, stderrWrite, stdinRead, stdinWrite;
            CreateStdioPipes(si, out stdoutRead, out stdoutWrite, out stderrRead, out stderrWrite, out stdinRead,
                out stdinWrite);

            using (stdoutRead)
            using (stdoutWrite)
            using (stderrRead)
            using (stderrWrite)
            using (stdinRead)
            using (stdinWrite)
            {
                FileStream stdinStream = new FileStream(stdinWrite, FileAccess.Write);

                bool isConsole = false;
                if (NativeMethods.GetConsoleWindow() == IntPtr.Zero)
                {
                    isConsole = NativeMethods.AllocConsole();

                    // Set console input/output codepage to UTF-8
                    NativeMethods.SetConsoleCP(65001);
                    NativeMethods.SetConsoleOutputCP(65001);
                }

                try
                {
                    pi = NativeCreateProcess(lpApplicationName, lpCommandLine, null, null, true, creationFlags,
                        environment, lpCurrentDirectory, si);
                }
                finally
                {
                    if (isConsole)
                        NativeMethods.FreeConsole();
                }

                using (pi)
                {
                    return WaitProcess(stdoutRead, stdoutWrite, stderrRead, stderrWrite, stdinStream, stdin, pi,
                        outputEncoding, waitChildren);
                }
            }
        }

        /// <summary>
        /// Wrapper around the Win32 CreateProcess API for low level use. This just spawns the new process and does not
        /// wait until it is complete before returning.
        /// </summary>
        /// <param name="applicationName">The name of the executable or batch file to execute</param>
        /// <param name="commandLine">The command line to execute, typically this includes applicationName as the first argument</param>
        /// <param name="processAttributes">SecurityAttributes to assign to the new process, set to null to use the defaults</param>
        /// <param name="threadAttributes">SecurityAttributes to assign to the new thread, set to null to use the defaults</param>
        /// <param name="inheritHandles">Any inheritable handles in the calling process is inherited in the new process</param>
        /// <param name="creationFlags">Custom creation flags to use when creating the new process</param>
        /// <param name="environment">A dictionary of key/value pairs to define the new process environment</param>
        /// <param name="currentDirectory">The full path to the current directory for the process, null will have the same cwd as the calling process</param>
        /// <param name="startupInfo">Custom StartupInformation to use when creating the new process</param>
        /// <returns>ProcessInformation containing a handle to the process and main thread as well as the pid/tid.</returns>
        public static ProcessInformation NativeCreateProcess(string applicationName, string commandLine,
            SecurityAttributes processAttributes, SecurityAttributes threadAttributes, bool inheritHandles,
            ProcessCreationFlags creationFlags, IDictionary environment, string currentDirectory, StartupInfo startupInfo)
        {
            // We always have the extended version present.
            creationFlags |= ProcessCreationFlags.ExtendedStartupInfoPresent;

            // $null from PowerShell ends up as an empty string, we need to convert back as an empty string doesn't
            // make sense for these parameters
            if (String.IsNullOrWhiteSpace(applicationName))
                applicationName = null;

            if (String.IsNullOrWhiteSpace(currentDirectory))
                currentDirectory = null;

            NativeHelpers.STARTUPINFOEX si = new NativeHelpers.STARTUPINFOEX();
            if (!String.IsNullOrWhiteSpace(startupInfo.Desktop))
                si.startupInfo.lpDesktop = startupInfo.Desktop;

            if (!String.IsNullOrWhiteSpace(startupInfo.Title))
                si.startupInfo.lpTitle = startupInfo.Title;

            if (startupInfo.WindowStyle != null)
            {
                switch (startupInfo.WindowStyle)
                {
                    case ProcessWindowStyle.Normal:
                        si.startupInfo.wShowWindow = 1;  // SW_SHOWNORMAL
                        break;
                    case ProcessWindowStyle.Hidden:
                        si.startupInfo.wShowWindow = 0;  // SW_HIDE
                        break;
                    case ProcessWindowStyle.Minimized:
                        si.startupInfo.wShowWindow = 6;  // SW_MINIMIZE
                        break;
                    case ProcessWindowStyle.Maximized:
                        si.startupInfo.wShowWindow = 3;  // SW_MAXIMIZE
                        break;
                }
                si.startupInfo.dwFlags |= NativeHelpers.StartupInfoFlags.STARTF_USESHOWWINDOW;
            }

            si.lpAttributeList = CreateProcThreadAttributes(startupInfo);

            NativeHelpers.PROCESS_INFORMATION pi = new NativeHelpers.PROCESS_INFORMATION();
            using (SafeHandle stdinHandle = PrepareStdioHandle(startupInfo.StandardInput, startupInfo))
            using (SafeHandle stdoutHandle = PrepareStdioHandle(startupInfo.StandardOutput, startupInfo))
            using (SafeHandle stderrHandle = PrepareStdioHandle(startupInfo.StandardError, startupInfo))
            using (SafeMemoryBuffer lpProcessAttr = CreateSecurityAttributes(processAttributes))
            using (SafeMemoryBuffer lpThreadAttributes = CreateSecurityAttributes(threadAttributes))
            using (SafeMemoryBuffer lpEnvironment = CreateEnvironmentPointer(environment))
            {
                si.startupInfo.hStdInput = stdinHandle;
                si.startupInfo.hStdOutput = stdoutHandle;
                si.startupInfo.hStdError = stderrHandle;
                if (
                    si.startupInfo.hStdInput.DangerousGetHandle() != IntPtr.Zero ||
                    si.startupInfo.hStdOutput.DangerousGetHandle() != IntPtr.Zero ||
                    si.startupInfo.hStdError.DangerousGetHandle() != IntPtr.Zero
                )
                {
                    si.startupInfo.dwFlags |= NativeHelpers.StartupInfoFlags.USESTDHANDLES;
                }

                StringBuilder commandLineBuff = new StringBuilder(commandLine);
                if (!NativeMethods.CreateProcessW(applicationName, commandLineBuff, lpProcessAttr, lpThreadAttributes,
                    inheritHandles, creationFlags, lpEnvironment, currentDirectory, si, out pi))
                {
                    throw new Win32Exception("CreateProcessW() failed");
                }
            }

            return new ProcessInformation
            {
                Process = new SafeNativeHandle(pi.hProcess),
                Thread = new SafeNativeHandle(pi.hThread),
                ProcessId = pi.dwProcessId,
                ThreadId = pi.dwThreadId,
            };
        }

        /// <summary>
        /// Resume a suspended thread.
        /// </summary>
        /// <param name="thread">The thread handle to resume</param>
        public static void ResumeThread(SafeHandle thread)
        {
            if (NativeMethods.ResumeThread(thread) == 0xFFFFFFFF)
                throw new Win32Exception("ResumeThread() failed");
        }

        /// <summary>
        /// Gets the exit code for the specified process handle.
        /// </summary>
        /// <param name="processHandle">The process handle to get the exit code for.</param>
        /// <returns>The process exit code.</returns>
        public static UInt32 GetProcessExitCode(SafeHandle processHandle)
        {
            NativeMethods.WaitForSingleObject(processHandle, 0xFFFFFFFF);

            UInt32 exitCode;
            if (!NativeMethods.GetExitCodeProcess(processHandle, out exitCode))
                throw new Win32Exception("GetExitCodeProcess() failed");
            return exitCode;
        }

        internal static void CreateStdioPipes(StartupInfo si, out SafeFileHandle stdoutRead,
            out SafeFileHandle stdoutWrite, out SafeFileHandle stderrRead, out SafeFileHandle stderrWrite,
            out SafeFileHandle stdinRead, out SafeFileHandle stdinWrite)
        {
            NativeHelpers.SECURITY_ATTRIBUTES pipesec = new NativeHelpers.SECURITY_ATTRIBUTES();
            pipesec.bInheritHandle = true;

            if (!NativeMethods.CreatePipe(out stdoutRead, out stdoutWrite, pipesec, 0))
                throw new Win32Exception("STDOUT pipe setup failed");
            if (!NativeMethods.SetHandleInformation(stdoutRead, NativeHelpers.HandleFlags.INHERIT, 0))
                throw new Win32Exception("STDOUT pipe handle setup failed");

            if (!NativeMethods.CreatePipe(out stderrRead, out stderrWrite, pipesec, 0))
                throw new Win32Exception("STDERR pipe setup failed");
            if (!NativeMethods.SetHandleInformation(stderrRead, NativeHelpers.HandleFlags.INHERIT, 0))
                throw new Win32Exception("STDERR pipe handle setup failed");

            if (!NativeMethods.CreatePipe(out stdinRead, out stdinWrite, pipesec, 0))
                throw new Win32Exception("STDIN pipe setup failed");
            if (!NativeMethods.SetHandleInformation(stdinWrite, NativeHelpers.HandleFlags.INHERIT, 0))
                throw new Win32Exception("STDIN pipe handle setup failed");

            si.StandardOutput = stdoutWrite;
            si.StandardError = stderrWrite;
            si.StandardInput = stdinRead;
        }

        internal static SafeMemoryBuffer CreateEnvironmentPointer(IDictionary environment)
        {
            IntPtr lpEnvironment = IntPtr.Zero;
            if (environment != null && environment.Count > 0)
            {
                StringBuilder environmentString = new StringBuilder();
                foreach (DictionaryEntry kv in environment)
                    environmentString.AppendFormat("{0}={1}\0", kv.Key, kv.Value);
                environmentString.Append('\0');

                lpEnvironment = Marshal.StringToHGlobalUni(environmentString.ToString());
            }
            return new SafeMemoryBuffer(lpEnvironment);
        }

        internal static SafeMemoryBuffer CreateSecurityAttributes(SecurityAttributes attributes)
        {
            IntPtr lpAttributes = IntPtr.Zero;
            if (attributes != null)
            {
                NativeHelpers.SECURITY_ATTRIBUTES attr = new NativeHelpers.SECURITY_ATTRIBUTES()
                {
                    bInheritHandle = attributes.InheritHandle,
                };

                lpAttributes = Marshal.AllocHGlobal(Marshal.SizeOf(attr));
                Marshal.StructureToPtr(attr, lpAttributes, false);
            }

            return new SafeMemoryBuffer(lpAttributes);
        }

        internal static SafeDuplicateHandle DuplicateHandle(SafeHandle sourceProcess, SafeHandle sourceHandle,
            SafeHandle targetProcess, UInt32 access, bool inherit, NativeHelpers.DuplicateHandleOptions options,
            bool ownsHandle)
        {
            if (targetProcess == null)
            {
                targetProcess = new SafeNativeHandle(IntPtr.Zero, false);
                // If closing the duplicate then mark the returned handle so it doesn't try to close itself again.
                ownsHandle = (options & NativeHelpers.DuplicateHandleOptions.DUPLICATE_CLOSE_SOURCE) == 0;
            }

            IntPtr dup = IntPtr.Zero;
            if (!NativeMethods.DuplicateHandle(sourceProcess, sourceHandle, targetProcess, out dup, access,
                inherit, options))
            {
                throw new Win32Exception("DuplicateHandle() failed");
            }

            return new SafeDuplicateHandle(dup, targetProcess, ownsHandle);
        }

        internal static Result WaitProcess(SafeFileHandle stdoutRead, SafeFileHandle stdoutWrite, SafeFileHandle stderrRead,
            SafeFileHandle stderrWrite, FileStream stdinStream, byte[] stdin, ProcessInformation pi,
            string outputEncoding, bool waitChildren)
        {
            // Default to using UTF-8 as the output encoding, this should be a sane default for most scenarios.
            outputEncoding = String.IsNullOrEmpty(outputEncoding) ? "utf-8" : outputEncoding;
            Encoding encodingInstance = Encoding.GetEncoding(outputEncoding);

            // If we aren't waiting for child processes we don't care if the below fails
            // Logic to wait for children is from Raymond Chen
            // https://devblogs.microsoft.com/oldnewthing/20130405-00/?p=4743
            using (SafeHandle job = CreateJob(!waitChildren))
            using (SafeHandle ioPort = CreateCompletionPort(!waitChildren))
            {
                // Need to assign the completion port to the job and then assigned the new process to that job.
                if (waitChildren)
                {
                    NativeHelpers.JOBOBJECT_ASSOCIATE_COMPLETION_PORT compPort = new NativeHelpers.JOBOBJECT_ASSOCIATE_COMPLETION_PORT()
                    {
                        CompletionKey = job.DangerousGetHandle(),
                        CompletionPort = ioPort.DangerousGetHandle(),
                    };
                    int compPortSize = Marshal.SizeOf(compPort);

                    using (SafeMemoryBuffer compPortPtr = new SafeMemoryBuffer(compPortSize))
                    {
                        Marshal.StructureToPtr(compPort, compPortPtr.DangerousGetHandle(), false);

                        if (!NativeMethods.SetInformationJobObject(job,
                            NativeHelpers.JobObjectInformationClass.JobObjectAssociateCompletionPortInformation,
                            compPortPtr.DangerousGetHandle(), compPortSize))
                        {
                            throw new Win32Exception("Failed to set job completion port information");
                        }
                    }

                    // Server 2012/Win 8 introduced the ability to nest jobs. Older versions will fail with
                    // ERROR_ACCESS_DENIED but we can't do anything about that except not wait for children.
                    if (!NativeMethods.AssignProcessToJobObject(job, pi.Process.DangerousGetHandle()))
                        throw new Win32Exception("Failed to assign new process to completion watcher job");
                }

                // Start the process and get the output.
                ResumeThread(pi.Thread);

                FileStream stdoutFS = new FileStream(stdoutRead, FileAccess.Read, 4096);
                StreamReader stdout = new StreamReader(stdoutFS, encodingInstance, true, 4096);
                stdoutWrite.Close();

                FileStream stderrFS = new FileStream(stderrRead, FileAccess.Read, 4096);
                StreamReader stderr = new StreamReader(stderrFS, encodingInstance, true, 4096);
                stderrWrite.Close();

                if (stdin != null)
                    stdinStream.Write(stdin, 0, stdin.Length);
                stdinStream.Close();

                string stdoutStr, stderrStr = null;
                GetProcessOutput(stdout, stderr, out stdoutStr, out stderrStr);
                UInt32 rc = GetProcessExitCode(pi.Process);

                if (waitChildren)
                {
                    // If the caller wants to wait for all child processes to finish, we continue to poll the job
                    // until it receives JOB_OBJECT_MSG_ACTIVE_PROCESS_ZERO (4).
                    UInt32 completionCode = 0xFFFFFFFF;
                    UIntPtr completionKey;
                    IntPtr overlapped;

                    while (NativeMethods.GetQueuedCompletionStatus(ioPort, out completionCode,
                        out completionKey, out overlapped, 0xFFFFFFFF) && completionCode != 4) { }
                }

                return new Result
                {
                    StandardOut = stdoutStr,
                    StandardError = stderrStr,
                    ExitCode = rc
                };
            }
        }

        internal static void GetProcessOutput(StreamReader stdoutStream, StreamReader stderrStream, out string stdout, out string stderr)
        {
            var sowait = new EventWaitHandle(false, EventResetMode.ManualReset);
            var sewait = new EventWaitHandle(false, EventResetMode.ManualReset);
            string so = null, se = null;
            ThreadPool.QueueUserWorkItem((s) =>
            {
                so = stdoutStream.ReadToEnd();
                sowait.Set();
            });
            ThreadPool.QueueUserWorkItem((s) =>
            {
                se = stderrStream.ReadToEnd();
                sewait.Set();
            });
            foreach (var wh in new WaitHandle[] { sowait, sewait })
                wh.WaitOne();
            stdout = so;
            stderr = se;
        }

        private static SafeHandle CreateJob(bool ignoreErrors)
        {
            SafeNativeHandle job = NativeMethods.CreateJobObjectW(IntPtr.Zero, null);
            if (job.IsInvalid && !ignoreErrors)
                throw new Win32Exception("Failed to create job object");

            return job;
        }

        private static SafeHandle CreateCompletionPort(bool ignoreErrors)
        {
            SafeNativeHandle ioPort = NativeMethods.CreateIoCompletionPort((IntPtr)(-1), IntPtr.Zero,
                UIntPtr.Zero, 1);

            if (ioPort.IsInvalid && !ignoreErrors)
                throw new Win32Exception("Failed to create IoCompletionPort");

            return ioPort;
        }

        private static SafeHandle CreateProcThreadAttributes(StartupInfo startupInfo)
        {
            int count = 0;
            if (startupInfo.ParentProcess > 0)
            {
                count++;
            }

            if (count == 0)
            {
                return new SafeNativeHandle(IntPtr.Zero, false);
            }

            SafeProcThreadAttribute attr = InitializeProcThreadAttributeList(count);
            try
            {
                if (startupInfo.ParentProcess > 0)
                {
                    SafeNativeHandle parentProcess = OpenProcess(startupInfo.ParentProcess,
                        0x00000080,  // PROCESS_CREATE_PROCESS
                        false);
                    attr.AddValue(parentProcess);

                    SafeMemoryBuffer val = new SafeMemoryBuffer(IntPtr.Size);
                    attr.AddValue(val);

                    Marshal.WriteIntPtr(val.DangerousGetHandle(), parentProcess.DangerousGetHandle());
                    UpdateProcThreadAttribute(attr,
                        0x00020000,  // PROC_THREAD_ATTRIBUTE_PARENT_PROCESS
                        val,
                        IntPtr.Size);
                }
            }
            catch
            {
                attr.Dispose();
                throw;
            }

            return attr;
        }

        private static SafeProcThreadAttribute InitializeProcThreadAttributeList(int count)
        {
            IntPtr size = IntPtr.Zero;
            NativeMethods.InitializeProcThreadAttributeList(IntPtr.Zero, count, 0, ref size);

            IntPtr h = Marshal.AllocHGlobal((int)size);
            try
            {
                if (!NativeMethods.InitializeProcThreadAttributeList(h, count, 0, ref size))
                    throw new Win32Exception("Failed to create process thread attribute list");

                return new SafeProcThreadAttribute(h, true);
            }
            catch
            {
                Marshal.FreeHGlobal(h);
                throw;
            }
        }

        private static SafeNativeHandle OpenProcess(int processId, int access, bool inherit)
        {
            SafeNativeHandle proc = NativeMethods.OpenProcess(access, inherit, processId);
            if (proc.DangerousGetHandle() == IntPtr.Zero)
            {
                throw new Win32Exception(string.Format(
                    "OpenProcess(0x{0:X8}, {1}, {2}) failed",
                    access, inherit, processId));
            }

            return proc;
        }

        private static SafeHandle PrepareStdioHandle(SafeHandle handle, StartupInfo startupInfo)
        {
            if (handle == null || handle.DangerousGetHandle() == IntPtr.Zero)
                return new SafeNativeHandle(IntPtr.Zero, false);

            if (startupInfo.ParentProcess > 0)
            {
                // The handle needs to be duplicated into the target process so
                // it can be inherited.
                SafeNativeHandle currentProcess = new SafeNativeHandle(NativeMethods.GetCurrentProcess(), false);
                SafeNativeHandle targetProcess = OpenProcess(startupInfo.ParentProcess,
                        0x00000040,  // PROCESS_DUP_HANDLE
                        false);

                return DuplicateHandle(currentProcess, handle, targetProcess, 0, true,
                    NativeHelpers.DuplicateHandleOptions.DUPLICATE_SAME_ACCESS, true);
            }
            else
            {
                // Create a copy of the handle and ensure it won't be disposed.
                // The original owner is still in charge of it.
                return new SafeNativeHandle(handle.DangerousGetHandle(), false);
            }
        }

        private static void UpdateProcThreadAttribute(SafeProcThreadAttribute attributeList, int attr,
            SafeHandle value, int size)
        {
            if (!NativeMethods.UpdateProcThreadAttribute(attributeList, 0, (UIntPtr)attr, value, (UIntPtr)size,
                IntPtr.Zero, IntPtr.Zero))
            {
                throw new Win32Exception("UpdateProcThreadAttribute() failed");
            }

            attributeList.AddValue(value);
        }
    }
}
