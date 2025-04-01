using Microsoft.Win32.SafeHandles;
using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Security;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

// Used by async_wrapper.ps1, not for general use.
//AllowUnsafe

namespace Ansible._Async
{
    internal class NativeHelpers
    {
        public const int CREATE_SUSPENDED = 0x00000004;
        public const int CREATE_NEW_CONSOLE = 0x00000010;
        public const int CREATE_UNICODE_ENVIRONMENT = 0x00000400;
        public const int EXTENDED_STARTUPINFO_PRESENT = 0x00080000;
        public const int CREATE_BREAKAWAY_FROM_JOB = 0x01000000;

        public const int DUPLICATE_CLOSE_SOURCE = 0x00000001;
        public const int DUPLICATE_SAME_ACCESS = 0x00000002;

        public const int JobObjectBasicLimitInformation = 2;

        public const int JOB_OBJECT_LIMIT_BREAKAWAY_OK = 0x00000800;

        public const int PROCESS_DUP_HANDLE = 0x00000040;
        public const int PROCESS_CREATE_PROCESS = 0x00000080;

        public const int PROC_THREAD_ATTRIBUTE_PARENT_PROCESS = 0x00020000;
        public const int PROC_THREAD_ATTRIBUTE_HANDLE_LIST = 0x00020002;

        public const int STARTF_USESHOWWINDOW = 0x00000001;
        public const int STARTF_USESTDHANDLES = 0x00000100;

        public const short SW_HIDE = 0;

        [StructLayout(LayoutKind.Sequential)]
        public struct JOBOBJECT_BASIC_LIMIT_INFORMATION
        {
            public long PerProcessUserTimeLimit;
            public long PerJobUserTimeLimit;
            public int LimitFlags;
            public IntPtr MinimumWorkingSetSize;
            public IntPtr MaximumWorkingSetSize;
            public int ActiveProcessLimit;
            public UIntPtr Affinity;
            public int PriorityClass;
            public int SchedulingClass;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct SECURITY_ATTRIBUTES
        {
            public int nLength;
            public IntPtr lpSecurityDescriptor;
            public int bInheritHandle;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct STARTUPINFO
        {
            public int cb;
            public IntPtr lpReserved;
            public IntPtr lpDesktop;
            public IntPtr lpTitle;
            public int dwX;
            public int dwY;
            public int dwXSize;
            public int dwYSize;
            public int dwXCountChars;
            public int dwYCountChars;
            public int dwFillAttribute;
            public int dwFlags;
            public short wShowWindow;
            public short cbReserved2;
            public IntPtr lpReserved2;
            public IntPtr hStdInput;
            public IntPtr hStdOutput;
            public IntPtr hStdError;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct STARTUPINFOEX
        {
            public STARTUPINFO startupInfo;
            public IntPtr lpAttributeList;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct PROCESS_INFORMATION
        {
            public IntPtr hProcess;
            public IntPtr hThread;
            public int dwProcessId;
            public int dwThreadId;
        }
    }

    internal class NativeMethods
    {
        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern IntPtr CreateEventW(
            ref NativeHelpers.SECURITY_ATTRIBUTES lpEventAttributes,
            bool bManualReset,
            bool bInitialState,
            IntPtr lpName);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool CreateProcessW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpApplicationName,
            StringBuilder lpCommandLine,
            IntPtr lpProcessAttributes,
            IntPtr lpThreadAttributes,
            bool bInheritHandles,
            int dwCreationFlags,
            IntPtr lpEnvironment,
            IntPtr lpCurrentDirectory,
            ref NativeHelpers.STARTUPINFOEX lpStartupInfo,
            out NativeHelpers.PROCESS_INFORMATION lpProcessInformation);

        [DllImport("kernel32.dll")]
        public static extern void DeleteProcThreadAttributeList(
            IntPtr lpAttributeList);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool DuplicateHandle(
            IntPtr hSourceProcessHandle,
            IntPtr hSourceHandle,
            IntPtr hTargetProcessHandle,
            out IntPtr lpTargetHandle,
            int dwDesiredAccess,
            bool bInheritHandle,
            int dwOptions);

        [DllImport("kernel32.dll")]
        public static extern IntPtr GetCurrentProcess();

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool GetExitCodeProcess(
            IntPtr hProcess,
            out int lpExitCode);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool InitializeProcThreadAttributeList(
            IntPtr lpAttributeList,
            int dwAttributeCount,
            int dwFlags,
            ref IntPtr lpSize);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool IsProcessInJob(
            IntPtr ProcessHandle,
            IntPtr JobHandle,
            out bool Result);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern IntPtr OpenProcess(
            Int32 dwDesiredAccess,
            bool bInheritHandle,
            Int32 dwProcessId);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool QueryInformationJobObject(
            IntPtr hJob,
            int JobObjectInformationClass,
            ref NativeHelpers.JOBOBJECT_BASIC_LIMIT_INFORMATION lpJobObjectInformation,
            int cbJobObjectInformationLength,
            IntPtr lpReturnLength);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern int ResumeThread(
            IntPtr hThread);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static unsafe extern bool UpdateProcThreadAttribute(
            SafeProcThreadAttrList lpAttributeList,
            int dwFlags,
            UIntPtr Attribute,
            void* lpValue,
            UIntPtr cbSize,
            IntPtr lpPreviousValue,
            IntPtr lpReturnSize);
    }

    public class ProcessInformation : IDisposable
    {
        public SafeWaitHandle Process { get; private set; }
        public SafeWaitHandle Thread { get; private set; }
        public int ProcessId { get; private set; }
        public int ThreadId { get; private set; }
        public Task<string> StdoutReader { get; private set; }
        public Task<string> StderrReader { get; private set; }

        public ProcessInformation(
            SafeWaitHandle process,
            SafeWaitHandle thread,
            int processId,
            int threadId,
            Task<string> stdoutReader,
            Task<string> stderrReader)
        {
            Process = process;
            Thread = thread;
            ProcessId = processId;
            ThreadId = threadId;
            StdoutReader = stdoutReader;
            StderrReader = stderrReader;
        }

        public void Dispose()
        {
            Process.Dispose();
            Thread.Dispose();
            GC.SuppressFinalize(this);
        }
        ~ProcessInformation() { Dispose(); }
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

    public class ManagedWaitHandle : WaitHandle
    {
        public ManagedWaitHandle(SafeWaitHandle handle)
        {
            SafeWaitHandle = handle;
        }
    }

    internal sealed class SafeProcThreadAttrList : SafeHandle
    {
        public SafeProcThreadAttrList(IntPtr handle) : base(handle, true) { }

        public override bool IsInvalid { get { return handle == IntPtr.Zero; } }

        protected override bool ReleaseHandle()
        {
            NativeMethods.DeleteProcThreadAttributeList(handle);
            Marshal.FreeHGlobal(handle);
            return true;
        }
    }

    public class AsyncUtil
    {
        public static bool CanCreateBreakawayProcess()
        {
            bool isInJob;
            if (!NativeMethods.IsProcessInJob(NativeMethods.GetCurrentProcess(), IntPtr.Zero, out isInJob))
            {
                throw new Win32Exception("IsProcessInJob() failed");
            }

            if (!isInJob)
            {
                return true;
            }

            NativeHelpers.JOBOBJECT_BASIC_LIMIT_INFORMATION jobInfo = new NativeHelpers.JOBOBJECT_BASIC_LIMIT_INFORMATION();
            bool jobRes = NativeMethods.QueryInformationJobObject(
                IntPtr.Zero,
                NativeHelpers.JobObjectBasicLimitInformation,
                ref jobInfo,
                Marshal.SizeOf<NativeHelpers.JOBOBJECT_BASIC_LIMIT_INFORMATION>(),
                IntPtr.Zero);
            if (!jobRes)
            {
                throw new Win32Exception("QueryInformationJobObject() failed");
            }

            return (jobInfo.LimitFlags & NativeHelpers.JOB_OBJECT_LIMIT_BREAKAWAY_OK) != 0;
        }

        public static ProcessInformation CreateAsyncProcess(
            string applicationName,
            string commandLine,
            SafeHandle stdin,
            SafeHandle stdout,
            SafeHandle stderr,
            SafeHandle mutexHandle,
            SafeHandle parentProcess,
            StreamReader stdoutReader,
            StreamReader stderrReader)
        {
            StringBuilder commandLineBuffer = new StringBuilder(commandLine);
            int creationFlags = NativeHelpers.CREATE_NEW_CONSOLE |
                NativeHelpers.CREATE_SUSPENDED |
                NativeHelpers.CREATE_UNICODE_ENVIRONMENT |
                NativeHelpers.EXTENDED_STARTUPINFO_PRESENT;
            if (parentProcess == null)
            {
                creationFlags |= NativeHelpers.CREATE_BREAKAWAY_FROM_JOB;
            }

            NativeHelpers.STARTUPINFOEX si = new NativeHelpers.STARTUPINFOEX();
            si.startupInfo.cb = Marshal.SizeOf(typeof(NativeHelpers.STARTUPINFOEX));
            si.startupInfo.dwFlags = NativeHelpers.STARTF_USESHOWWINDOW | NativeHelpers.STARTF_USESTDHANDLES;
            si.startupInfo.wShowWindow = NativeHelpers.SW_HIDE;
            si.startupInfo.hStdInput = stdin.DangerousGetHandle();
            si.startupInfo.hStdOutput = stdout.DangerousGetHandle();
            si.startupInfo.hStdError = stderr.DangerousGetHandle();

            int attrCount = 1;
            IntPtr rawParentProcessHandle = IntPtr.Zero;
            if (parentProcess != null)
            {
                attrCount++;
                rawParentProcessHandle = parentProcess.DangerousGetHandle();
            }

            using (SafeProcThreadAttrList attrList = CreateProcThreadAttribute(attrCount))
            {
                si.lpAttributeList = attrList.DangerousGetHandle();

                IntPtr[] handlesToInherit = new IntPtr[4]
                {
                    stdin.DangerousGetHandle(),
                    stdout.DangerousGetHandle(),
                    stderr.DangerousGetHandle(),
                    mutexHandle.DangerousGetHandle()
                };
                unsafe
                {
                    fixed (IntPtr* handlesToInheritPtr = &handlesToInherit[0])
                    {
                        UpdateProcThreadAttribute(
                            attrList,
                            NativeHelpers.PROC_THREAD_ATTRIBUTE_HANDLE_LIST,
                            handlesToInheritPtr,
                            IntPtr.Size * 4);

                        if (rawParentProcessHandle != IntPtr.Zero)
                        {
                            UpdateProcThreadAttribute(
                                attrList,
                                NativeHelpers.PROC_THREAD_ATTRIBUTE_PARENT_PROCESS,
                                &rawParentProcessHandle,
                                IntPtr.Size);
                        }

                        NativeHelpers.PROCESS_INFORMATION pi = new NativeHelpers.PROCESS_INFORMATION();
                        bool res = NativeMethods.CreateProcessW(
                            applicationName,
                            commandLineBuffer,
                            IntPtr.Zero,
                            IntPtr.Zero,
                            true,
                            (int)creationFlags,
                            IntPtr.Zero,
                            IntPtr.Zero,
                            ref si,
                            out pi);
                        if (!res)
                        {
                            throw new Win32Exception("CreateProcessW() failed");
                        }

                        return new ProcessInformation(
                            new SafeWaitHandle(pi.hProcess, true),
                            new SafeWaitHandle(pi.hThread, true),
                            pi.dwProcessId,
                            pi.dwThreadId,
                            Task.Run(() => stdoutReader.ReadToEnd()),
                            Task.Run(() => stderrReader.ReadToEnd()));
                    }
                }
            }
        }

        public static SafeWaitHandle CreateInheritableEvent()
        {
            NativeHelpers.SECURITY_ATTRIBUTES sa = new NativeHelpers.SECURITY_ATTRIBUTES();
            sa.nLength = Marshal.SizeOf(sa);
            sa.bInheritHandle = 1;

            IntPtr hEvent = NativeMethods.CreateEventW(ref sa, true, false, IntPtr.Zero);
            if (hEvent == IntPtr.Zero)
            {
                throw new Win32Exception("CreateEventW() failed");
            }
            return new SafeWaitHandle(hEvent, true);
        }

        public static SafeHandle DuplicateHandleToProcess(
            SafeHandle handle,
            SafeHandle targetProcess)
        {
            IntPtr targetHandle;
            bool res = NativeMethods.DuplicateHandle(
                NativeMethods.GetCurrentProcess(),
                handle.DangerousGetHandle(),
                targetProcess.DangerousGetHandle(),
                out targetHandle,
                0,
                true,
                NativeHelpers.DUPLICATE_SAME_ACCESS);
            if (!res)
            {
                throw new Win32Exception("DuplicateHandle() failed");
            }

            // This will not dispose the handle, it is assumed
            // the caller will close it manually with CloseHandleInProcess.
            return new SafeWaitHandle(targetHandle, false);
        }

        public static void CloseHandleInProcess(
            SafeHandle handle,
            SafeHandle targetProcess)
        {
            IntPtr _ = IntPtr.Zero;
            bool res = NativeMethods.DuplicateHandle(
                targetProcess.DangerousGetHandle(),
                handle.DangerousGetHandle(),
                IntPtr.Zero,
                out _,
                0,
                false,
                NativeHelpers.DUPLICATE_CLOSE_SOURCE);
            if (!res)
            {
                throw new Win32Exception("DuplicateHandle() failed to close handle");
            }
        }

        public static int GetProcessExitCode(SafeHandle process)
        {
            int exitCode;
            bool res = NativeMethods.GetExitCodeProcess(process.DangerousGetHandle(), out exitCode);
            if (!res)
            {
                throw new Win32Exception("GetExitCodeProcess() failed");
            }
            return exitCode;
        }

        public static SafeHandle OpenProcessAsParent(int processId)
        {
            IntPtr hProcess = NativeMethods.OpenProcess(
                NativeHelpers.PROCESS_DUP_HANDLE | NativeHelpers.PROCESS_CREATE_PROCESS,
                false,
                processId);
            if (hProcess == IntPtr.Zero)
            {
                throw new Win32Exception("OpenProcess() failed");
            }
            return new SafeWaitHandle(hProcess, true);
        }

        public static void ResumeThread(SafeHandle thread)
        {
            int res = NativeMethods.ResumeThread(thread.DangerousGetHandle());
            if (res == -1)
            {
                throw new Win32Exception("ResumeThread() failed");
            }
        }

        private static SafeProcThreadAttrList CreateProcThreadAttribute(int count)
        {
            IntPtr attrSize = IntPtr.Zero;
            NativeMethods.InitializeProcThreadAttributeList(IntPtr.Zero, count, 0, ref attrSize);

            IntPtr attributeList = Marshal.AllocHGlobal((int)attrSize);
            try
            {
                if (!NativeMethods.InitializeProcThreadAttributeList(attributeList, count, 0, ref attrSize))
                {
                    throw new Win32Exception("InitializeProcThreadAttributeList() failed");
                }

                return new SafeProcThreadAttrList(attributeList);
            }
            catch
            {
                Marshal.FreeHGlobal(attributeList);
                throw;
            }
        }

        private static unsafe void UpdateProcThreadAttribute(
            SafeProcThreadAttrList attributeList,
            int attribute,
            void* value,
            int size)
        {
            bool res = NativeMethods.UpdateProcThreadAttribute(
                attributeList,
                0,
                (UIntPtr)attribute,
                value,
                (UIntPtr)size,
                IntPtr.Zero,
                IntPtr.Zero);
            if (!res)
            {
                string msg = string.Format("UpdateProcThreadAttribute() failed to set attribute 0x{0:X8}", attribute);
                throw new Win32Exception(msg);
            }
        }
    }
}
