using Microsoft.Win32.SafeHandles;
using System;
using System.Collections;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;

namespace Ansible.Process
{
    internal class NativeHelpers
    {
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
        public class STARTUPINFO
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
            public SafeFileHandle hStdInput;
            public SafeFileHandle hStdOutput;
            public SafeFileHandle hStdError;
            public STARTUPINFO()
            {
                cb = (UInt32)Marshal.SizeOf(this);
            }
        }

        [StructLayout(LayoutKind.Sequential)]
        public class STARTUPINFOEX
        {
            public STARTUPINFO startupInfo;
            public IntPtr lpAttributeList;
            public STARTUPINFOEX()
            {
                startupInfo = new STARTUPINFO();
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
        public enum ProcessCreationFlags : uint
        {
            CREATE_NEW_CONSOLE = 0x00000010,
            CREATE_UNICODE_ENVIRONMENT = 0x00000400,
            EXTENDED_STARTUPINFO_PRESENT = 0x00080000
        }

        [Flags]
        public enum StartupInfoFlags : uint
        {
            USESTDHANDLES = 0x00000100
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

        [DllImport("shell32.dll", SetLastError = true)]
        public static extern SafeMemoryBuffer CommandLineToArgvW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpCmdLine,
            out int pNumArgs);

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
            IntPtr lpProcessAttributes,
            IntPtr lpThreadAttributes,
            bool bInheritHandles,
            NativeHelpers.ProcessCreationFlags dwCreationFlags,
            SafeMemoryBuffer lpEnvironment,
            [MarshalAs(UnmanagedType.LPWStr)] string lpCurrentDirectory,
            NativeHelpers.STARTUPINFOEX lpStartupInfo,
            out NativeHelpers.PROCESS_INFORMATION lpProcessInformation);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool FreeConsole();

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern IntPtr GetConsoleWindow();

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool GetExitCodeProcess(
            SafeWaitHandle hProcess,
            out UInt32 lpExitCode);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern uint SearchPathW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpPath,
            [MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
            [MarshalAs(UnmanagedType.LPWStr)] string lpExtension,
            UInt32 nBufferLength,
            [MarshalAs(UnmanagedType.LPTStr)] StringBuilder lpBuffer,
            out IntPtr lpFilePart);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool SetConsoleCP(
            UInt32 wCodePageID);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool SetConsoleOutputCP(
            UInt32 wCodePageID);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool SetHandleInformation(
            SafeFileHandle hObject,
            NativeHelpers.HandleFlags dwMask,
            NativeHelpers.HandleFlags dwFlags);

        [DllImport("kernel32.dll")]
        public static extern UInt32 WaitForSingleObject(
            SafeWaitHandle hHandle,
            UInt32 dwMilliseconds);
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

    public class Result
    {
        public string StandardOut { get; internal set; }
        public string StandardError { get; internal set; }
        public uint ExitCode { get; internal set; }
    }

    public class ProcessUtil
    {
        /// <summary>
        /// Parses a command line string into an argv array according to the Windows rules
        /// </summary>
        /// <param name="lpCommandLine">The command line to parse</param>
        /// <returns>An array of arguments interpreted by Windows</returns>
        public static string[] ParseCommandLine(string lpCommandLine)
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
        /// Searches the path for the executable specified. Will throw a Win32Exception if the file is not found.
        /// </summary>
        /// <param name="lpFileName">The executable to search for</param>
        /// <returns>The full path of the executable to search for</returns>
        public static string SearchPath(string lpFileName)
        {
            StringBuilder sbOut = new StringBuilder(0);
            IntPtr filePartOut = IntPtr.Zero;
            UInt32 res = NativeMethods.SearchPathW(null, lpFileName, null, (UInt32)sbOut.Capacity, sbOut, out filePartOut);
            if (res == 0)
            {
                int lastErr = Marshal.GetLastWin32Error();
                if (lastErr == 2)  // ERROR_FILE_NOT_FOUND
                    throw new FileNotFoundException(String.Format("Could not find file '{0}'.", lpFileName));
                else
                    throw new Win32Exception(String.Format("SearchPathW({0}) failed to get buffer length", lpFileName));
            }

            sbOut.EnsureCapacity((int)res);
            if (NativeMethods.SearchPathW(null, lpFileName, null, (UInt32)sbOut.Capacity, sbOut, out filePartOut) == 0)
                throw new Win32Exception(String.Format("SearchPathW({0}) failed", lpFileName));

            return sbOut.ToString();
        }

        public static Result CreateProcess(string command)
        {
            return CreateProcess(null, command, null, null, String.Empty);
        }

        public static Result CreateProcess(string lpApplicationName, string lpCommandLine, string lpCurrentDirectory,
            IDictionary environment)
        {
            return CreateProcess(lpApplicationName, lpCommandLine, lpCurrentDirectory, environment, String.Empty);
        }

        public static Result CreateProcess(string lpApplicationName, string lpCommandLine, string lpCurrentDirectory,
            IDictionary environment, string stdin)
        {
            return CreateProcess(lpApplicationName, lpCommandLine, lpCurrentDirectory, environment, stdin, null);
        }

        public static Result CreateProcess(string lpApplicationName, string lpCommandLine, string lpCurrentDirectory,
            IDictionary environment, byte[] stdin)
        {
            return CreateProcess(lpApplicationName, lpCommandLine, lpCurrentDirectory, environment, stdin, null);
        }

        public static Result CreateProcess(string lpApplicationName, string lpCommandLine, string lpCurrentDirectory,
            IDictionary environment, string stdin, string outputEncoding)
        {
            byte[] stdinBytes;
            if (String.IsNullOrEmpty(stdin))
                stdinBytes = new byte[0];
            else
            {
                if (!stdin.EndsWith(Environment.NewLine))
                    stdin += Environment.NewLine;
                stdinBytes = new UTF8Encoding(false).GetBytes(stdin);
            }
            return CreateProcess(lpApplicationName, lpCommandLine, lpCurrentDirectory, environment, stdinBytes, outputEncoding);
        }

        /// <summary>
        /// Creates a process based on the CreateProcess API call.
        /// </summary>
        /// <param name="lpApplicationName">The name of the executable or batch file to execute</param>
        /// <param name="lpCommandLine">The command line to execute, typically this includes lpApplication as the first argument</param>
        /// <param name="lpCurrentDirectory">The full path to the current directory for the process, null will have the same cwd as the calling process</param>
        /// <param name="environment">A dictionary of key/value pairs to define the new process environment</param>
        /// <param name="stdin">A byte array to send over the stdin pipe</param>
        /// <param name="outputEncoding">The character encoding for decoding stdout/stderr output of the process.</param>
        /// <returns>Result object that contains the command output and return code</returns>
        public static Result CreateProcess(string lpApplicationName, string lpCommandLine, string lpCurrentDirectory,
            IDictionary environment, byte[] stdin, string outputEncoding)
        {
            NativeHelpers.ProcessCreationFlags creationFlags = NativeHelpers.ProcessCreationFlags.CREATE_UNICODE_ENVIRONMENT |
                NativeHelpers.ProcessCreationFlags.EXTENDED_STARTUPINFO_PRESENT;
            NativeHelpers.PROCESS_INFORMATION pi = new NativeHelpers.PROCESS_INFORMATION();
            NativeHelpers.STARTUPINFOEX si = new NativeHelpers.STARTUPINFOEX();
            si.startupInfo.dwFlags = NativeHelpers.StartupInfoFlags.USESTDHANDLES;

            SafeFileHandle stdoutRead, stdoutWrite, stderrRead, stderrWrite, stdinRead, stdinWrite;
            CreateStdioPipes(si, out stdoutRead, out stdoutWrite, out stderrRead, out stderrWrite, out stdinRead,
                out stdinWrite);
            FileStream stdinStream = new FileStream(stdinWrite, FileAccess.Write);

            // $null from PowerShell ends up as an empty string, we need to convert back as an empty string doesn't
            // make sense for these parameters
            if (lpApplicationName == "")
                lpApplicationName = null;

            if (lpCurrentDirectory == "")
                lpCurrentDirectory = null;

            using (SafeMemoryBuffer lpEnvironment = CreateEnvironmentPointer(environment))
            {
                // Create console with utf-8 CP if no existing console is present
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
                    StringBuilder commandLine = new StringBuilder(lpCommandLine);
                    if (!NativeMethods.CreateProcessW(lpApplicationName, commandLine, IntPtr.Zero, IntPtr.Zero,
                        true, creationFlags, lpEnvironment, lpCurrentDirectory, si, out pi))
                    {
                        throw new Win32Exception("CreateProcessW() failed");
                    }
                }
                finally
                {
                    if (isConsole)
                        NativeMethods.FreeConsole();
                }
            }

            return WaitProcess(stdoutRead, stdoutWrite, stderrRead, stderrWrite, stdinStream, stdin, pi.hProcess,
                outputEncoding);
        }

        internal static void CreateStdioPipes(NativeHelpers.STARTUPINFOEX si, out SafeFileHandle stdoutRead,
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

            si.startupInfo.hStdOutput = stdoutWrite;
            si.startupInfo.hStdError = stderrWrite;
            si.startupInfo.hStdInput = stdinRead;
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

        internal static Result WaitProcess(SafeFileHandle stdoutRead, SafeFileHandle stdoutWrite, SafeFileHandle stderrRead,
            SafeFileHandle stderrWrite, FileStream stdinStream, byte[] stdin, IntPtr hProcess, string outputEncoding = null)
        {
            // Default to using UTF-8 as the output encoding, this should be a logical default for most scenarios.
            outputEncoding = String.IsNullOrEmpty(outputEncoding) ? "utf-8" : outputEncoding;
            Encoding encodingInstance = Encoding.GetEncoding(outputEncoding);

            FileStream stdoutFS = new FileStream(stdoutRead, FileAccess.Read, 4096);
            StreamReader stdout = new StreamReader(stdoutFS, encodingInstance, true, 4096);
            stdoutWrite.Close();

            FileStream stderrFS = new FileStream(stderrRead, FileAccess.Read, 4096);
            StreamReader stderr = new StreamReader(stderrFS, encodingInstance, true, 4096);
            stderrWrite.Close();

            stdinStream.Write(stdin, 0, stdin.Length);
            stdinStream.Close();

            string stdoutStr, stderrStr = null;
            GetProcessOutput(stdout, stderr, out stdoutStr, out stderrStr);
            UInt32 rc = GetProcessExitCode(hProcess);

            return new Result
            {
                StandardOut = stdoutStr,
                StandardError = stderrStr,
                ExitCode = rc
            };
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

        internal static UInt32 GetProcessExitCode(IntPtr processHandle)
        {
            SafeWaitHandle hProcess = new SafeWaitHandle(processHandle, true);
            NativeMethods.WaitForSingleObject(hProcess, 0xFFFFFFFF);

            UInt32 exitCode;
            if (!NativeMethods.GetExitCodeProcess(hProcess, out exitCode))
                throw new Win32Exception("GetExitCodeProcess() failed");
            return exitCode;
        }
    }
}
